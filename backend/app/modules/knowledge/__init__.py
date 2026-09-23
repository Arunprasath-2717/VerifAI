"""Private Knowledge Base (KB) for namespace-isolated ingestion and retrieval."""

from app.modules.knowledge.ingestion import (
    DuplicateDocumentError,
    IngestionResult,
    IngestionValidationError,
    chunk_document_text,
    process_document_ingestion,
    sanitize_filename,
)
from app.modules.knowledge.retriever import KBSearchResult, PrivateKBRetriever
from app.modules.knowledge.service import KnowledgeBaseService, resolve_owner_id

__all__ = [
    "KnowledgeBaseService",
    "PrivateKBRetriever",
    "KBSearchResult",
    "process_document_ingestion",
    "chunk_document_text",
    "sanitize_filename",
    "IngestionValidationError",
    "DuplicateDocumentError",
    "IngestionResult",
    "resolve_owner_id",
]
