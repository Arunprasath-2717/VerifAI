"""Document ingestion, validation, sanitization, hashing, and chunking pipeline."""

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import get_settings

# Permitted extensions and content-types
SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".json", ".text"}
SUPPORTED_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "application/json",
    "text/x-markdown",
}

# Dangerous characters in filenames (path traversal, control chars, null bytes)
_PATH_TRAVERSAL_RE = re.compile(r"(\.\.[/\\]|[/\\])")
_UNSAFE_FILENAME_CHARS_RE = re.compile(r"[^\w\.\-\s]")


class IngestionValidationError(ValueError):
    """Raised when an uploaded document fails validation checks."""

    pass


class DuplicateDocumentError(ValueError):
    """Raised when duplicate content hash already exists for owner."""

    pass


@dataclass(frozen=True)
class DocumentChunkData:
    """In-memory chunk representation prepared during ingestion."""

    chunk_index: int
    text: str
    start_offset: int
    end_offset: int
    metadata_json: dict[str, Any]


@dataclass(frozen=True)
class IngestionResult:
    """Outcome of validated and normalized document ingestion."""

    filename: str
    title: str
    content_type: str
    size_bytes: int
    content_hash: str
    text: str
    chunks: list[DocumentChunkData]
    metadata_json: dict[str, Any]


def sanitize_filename(filename: str | None) -> str:
    """Sanitize uploaded filename to prevent path traversal or injection.

    Rejects traversal sequences (e.g., '../', '..\\') and extracts a safe basename.
    """
    if not filename or not filename.strip():
        return "document.txt"

    clean_name = filename.strip()

    # Reject explicit path traversal attempts
    if _PATH_TRAVERSAL_RE.search(clean_name) or "\x00" in clean_name:
        raise IngestionValidationError(
            f"Invalid filename '{filename}': path traversal or unsafe characters."
        )

    # Use Path.name to guarantee basename only
    base_name = Path(clean_name).name
    sanitized = _UNSAFE_FILENAME_CHARS_RE.sub("_", base_name).strip()

    if not sanitized:
        return "document.txt"

    return sanitized


def validate_file_format(filename: str, content_type: str | None = None) -> str:
    """Validate that the file format is supported and return canonical MIME type."""
    ext = Path(filename).suffix.lower()

    if ext and ext in SUPPORTED_EXTENSIONS:
        if ext == ".json":
            return "application/json"
        if ext in (".md", ".markdown"):
            return "text/markdown"
        return "text/plain"

    if content_type:
        clean_ct = content_type.lower().split(";")[0].strip()
        if clean_ct in SUPPORTED_MIME_TYPES:
            return clean_ct

    supported_list = ", ".join(sorted(SUPPORTED_EXTENSIONS))
    raise IngestionValidationError(
        f"Unsupported file format for '{filename}'. Allowed: {supported_list}"
    )


def extract_and_normalize_text(raw_bytes: bytes, content_type: str) -> str:
    """Decode raw bytes into clean, normalized text."""
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw_bytes.decode("latin-1")
        except Exception as exc:
            raise IngestionValidationError(
                f"Failed to decode document content as text: {exc}"
            ) from exc

    if content_type == "application/json":
        try:
            parsed = json.loads(text)
            # If JSON is an object or array, format as readable text
            if isinstance(parsed, (dict, list)):
                text = json.dumps(parsed, indent=2)
        except json.JSONDecodeError as exc:
            raise IngestionValidationError(f"Malformed JSON content: {exc}") from exc

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise IngestionValidationError(
            "Document content is empty after text extraction."
        )

    return normalized


def compute_content_hash(text: str) -> str:
    """Calculate SHA-256 hexadecimal digest of document text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_document_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[DocumentChunkData]:
    """Split normalized document text into deterministic overlapping chunks.

    Prefers splitting on paragraph boundaries (`\n\n`) and sentence endings,
    falling back to character slicing with overlap.
    """
    settings = get_settings()
    c_size = chunk_size or settings.KB_CHUNK_SIZE
    c_overlap = chunk_overlap or settings.KB_CHUNK_OVERLAP

    if c_overlap >= c_size:
        c_overlap = max(0, c_size // 4)

    # Sliding windows over the ORIGINAL text. Each window is [start, end) with
    # end - start <= c_size and starts strictly increasing, so stored text is
    # always exactly text[start_offset:end_offset] after whitespace trimming.
    chunks: list[DocumentChunkData] = []
    n = len(text)
    step = max(1, c_size - c_overlap)
    start = 0
    while start < n:
        end = min(n, start + c_size)
        if end < n:
            # Prefer to cut at the last paragraph or sentence break in the window.
            window = text[start:end]
            cut = max(window.rfind("\n\n"), window.rfind(". "), window.rfind(" "))
            if cut > len(window) // 2:
                end = start + cut + 1
        span = text[start:end]
        body = span.strip()
        if body:
            lead = len(span) - len(span.lstrip())
            real_start = start + lead
            chunks.append(
                DocumentChunkData(
                    chunk_index=len(chunks),
                    text=body,
                    start_offset=real_start,
                    end_offset=real_start + len(body),
                    metadata_json={"window": True},
                )
            )
        if end >= n:
            break
        # Advance by the window step, always moving forward by at least one char.
        start = max(start + 1, min(end, start + step))

    return chunks


def process_document_ingestion(
    raw_content: bytes | str,
    filename: str,
    title: str | None = None,
    content_type: str | None = None,
    max_bytes: int | None = None,
) -> IngestionResult:
    """Execute complete ingestion pipeline: validation, hashing, chunking."""
    settings = get_settings()
    limit_bytes = max_bytes or settings.KB_MAX_DOCUMENT_BYTES

    # 1. Sanitize filename
    clean_filename = sanitize_filename(filename)

    # 2. Validate format
    canonical_content_type = validate_file_format(clean_filename, content_type)

    # 3. Check byte size
    raw_bytes = (
        raw_content.encode("utf-8")
        if isinstance(raw_content, str)
        else bytes(raw_content)
    )
    size_bytes = len(raw_bytes)
    if size_bytes > limit_bytes:
        raise IngestionValidationError(
            f"Document size ({size_bytes} bytes) exceeds maximum configured "
            f"limit of {limit_bytes} bytes."
        )

    # 4. Extract and normalize text
    normalized_text = extract_and_normalize_text(raw_bytes, canonical_content_type)

    # 5. Content hashing
    content_hash = compute_content_hash(normalized_text)

    # 6. Chunks
    chunks = chunk_document_text(normalized_text)

    # 7. Document title
    doc_title = title.strip() if title and title.strip() else clean_filename

    return IngestionResult(
        filename=clean_filename,
        title=doc_title,
        content_type=canonical_content_type,
        size_bytes=size_bytes,
        content_hash=content_hash,
        text=normalized_text,
        chunks=chunks,
        metadata_json={
            "chunk_count": len(chunks),
            "original_filename": filename,
        },
    )
