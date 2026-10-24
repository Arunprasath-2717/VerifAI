"""Pydantic v2 schemas for namespace-isolated private Knowledge Base (KB)."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceSourceEnum(StrEnum):
    """Origin taxonomy of retrieved evidence."""

    PRIVATE_KB = "PRIVATE_KB"
    EXTERNAL = "EXTERNAL"


class KBSufficiencyStatus(StrEnum):
    """Sufficiency evaluation for retrieved knowledge base evidence."""

    KB_RELEVANT = "KB_RELEVANT"
    KB_INSUFFICIENT = "KB_INSUFFICIENT"
    KB_EMPTY = "KB_EMPTY"


class DocumentCreateRequest(BaseModel):
    """Payload for adding a new document to the private knowledge base."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Human-readable title for the document.",
    )
    text: str = Field(
        ...,
        min_length=1,
        description="Raw document text content.",
    )
    filename: str = Field(
        default="document.txt",
        max_length=256,
        description="Original filename or label.",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional brief description of document contents.",
    )
    content_type: str = Field(
        default="text/plain",
        max_length=64,
        description="MIME type or file format indicator.",
    )
    owner_id: str | None = Field(
        default=None,
        max_length=128,
        description="Explicit namespace or owner identifier.",
    )


class ChunkResponse(BaseModel):
    """Serialized discrete chunk representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    owner_id: str
    chunk_index: int
    text: str
    start_offset: int
    end_offset: int
    metadata_json: dict[str, Any] | None = None
    created_at: datetime


class DocumentResponse(BaseModel):
    """Document summary response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: str
    filename: str
    title: str
    description: str | None = None
    content_type: str
    size_bytes: int
    content_hash: str
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    """Detailed document response including chunk passages."""

    chunks: list[ChunkResponse] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    """Response containing list of documents for a namespace."""

    model_config = ConfigDict(from_attributes=True)

    owner_id: str
    total_documents: int
    documents: list[DocumentResponse] = Field(default_factory=list)


class KnowledgeSearchRequest(BaseModel):
    """Request payload for searching the private knowledge base."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Claim text or search query.",
    )
    owner_id: str | None = Field(
        default=None,
        max_length=128,
        description="Target namespace/owner ID to search.",
    )
    max_passages: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum number of chunks to return.",
    )
    threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional override for relevance sufficiency threshold.",
    )
    min_overlap_tokens: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Optional override for minimum token overlap.",
    )


class KnowledgeSearchResultItem(BaseModel):
    """Ranked evidence chunk retrieved from the private KB."""

    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID
    chunk_id: uuid.UUID
    owner_id: str
    document_title: str
    filename: str
    chunk_index: int
    snippet: str
    relevance_score: float
    overlap_tokens: int
    evidence_source: str = EvidenceSourceEnum.PRIVATE_KB.value
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchResponse(BaseModel):
    """Full search outcome from the private knowledge base."""

    model_config = ConfigDict(from_attributes=True)

    query: str
    owner_id: str
    sufficiency: KBSufficiencyStatus
    threshold_used: float
    min_overlap_tokens_used: int
    total_chunks_matched: int
    results: list[KnowledgeSearchResultItem] = Field(default_factory=list)
