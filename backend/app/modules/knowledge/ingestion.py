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


_SENTENCE_END_RE = re.compile(r"[.!?](?=\s)")


def _find_cut(text: str, start: int, limit: int) -> tuple[int, str]:
    """Pick a chunk end in (start, limit], preferring natural boundaries.

    Searches only the back half of the window so chunks never shrink below half
    the target size. Returns (end_offset, boundary_kind).
    """
    floor = start + max(1, (limit - start) // 2)
    paragraph = text.rfind("\n\n", floor, limit)
    if paragraph != -1:
        return paragraph, "paragraph"
    sentence_ends = [m.end() for m in _SENTENCE_END_RE.finditer(text, floor, limit)]
    if sentence_ends:
        return sentence_ends[-1], "sentence"
    space = text.rfind(" ", floor, limit)
    if space != -1:
        return space, "word"
    return limit, "hard"


def chunk_document_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[DocumentChunkData]:
    """Split normalized text into deterministic, overlapping chunks.

    Every chunk satisfies ``text[start_offset:end_offset] == chunk.text``.
    Consecutive chunks overlap by up to ``chunk_overlap`` characters (snapped
    forward to a word start) so facts spanning a boundary remain retrievable.
    Chunk ends prefer paragraph breaks, then sentence ends, then spaces.
    """
    settings = get_settings()
    c_size = chunk_size or settings.KB_CHUNK_SIZE
    c_overlap = (
        chunk_overlap if chunk_overlap is not None else settings.KB_CHUNK_OVERLAP
    )
    if c_overlap >= c_size:
        c_overlap = max(0, c_size // 4)

    chunks: list[DocumentChunkData] = []
    n = len(text)
    pos = 0
    while pos < n:
        limit = min(n, pos + c_size)
        cut, kind = (n, "end") if limit >= n else _find_cut(text, pos, limit)

        # Trim surrounding whitespace while keeping offsets exact.
        start, end = pos, cut
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if end > start:
            chunks.append(
                DocumentChunkData(
                    chunk_index=len(chunks),
                    text=text[start:end],
                    start_offset=start,
                    end_offset=end,
                    metadata_json={"boundary": kind},
                )
            )
        if cut >= n:
            break

        # Step back by the overlap, snapped forward to the start of a word, but
        # always make progress.
        next_pos = max(cut - c_overlap, start + 1)
        while next_pos < cut and not text[next_pos - 1].isspace():
            next_pos += 1
        pos = next_pos if next_pos < cut else cut

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
