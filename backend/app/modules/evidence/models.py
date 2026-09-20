"""Domain transfer models for evidence passages and provenance."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class RetrievedEvidenceItem:
    """A passage of evidence supporting or contradicting a claim, with provenance."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    source_url: str | None = None
    source_title: str | None = None
    publisher: str | None = None
    publication_date: str | None = None
    retrieval_timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    snippet: str = ""
    query_used: str | None = None
    retriever_name: str = "LOCAL"
    relevance_score: float | None = None
    authority_score: float | None = None
    metadata_json: dict[str, Any] = field(default_factory=dict)
