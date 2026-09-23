"""Deterministic namespace-isolated Knowledge Base evidence retriever."""

import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.config import Settings, get_settings
from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.knowledge.service import KnowledgeBaseService, resolve_owner_id
from app.schemas.knowledge import KBSufficiencyStatus

_STOP_WORDS = {
    "the",
    "and",
    "that",
    "this",
    "with",
    "from",
    "for",
    "are",
    "was",
    "were",
    "been",
    "has",
    "have",
    "had",
    "will",
    "would",
    "can",
    "could",
    "should",
    "during",
    "about",
    "into",
    "than",
    "then",
    "also",
    "very",
    "just",
    "some",
    "any",
    "each",
    "other",
    "its",
    "our",
    "their",
    "such",
    "only",
    "same",
    "both",
    "all",
    "more",
    "most",
    "not",
    "out",
    "over",
}


@dataclass(frozen=True)
class KBSearchResult:
    """Outcome of a private KB search, including sufficiency classification."""

    sufficiency: KBSufficiencyStatus
    evidence_items: list[RetrievedEvidenceItem] = field(default_factory=list)
    top_score: float | None = None
    threshold_used: float = 0.15
    min_overlap_tokens_used: int = 2
    total_candidates: int = 0


class PrivateKBRetriever(BaseEvidenceRetriever):
    """Deterministic namespace-isolated retriever on private KB chunks.

    Implements BaseEvidenceRetriever so it plugs directly into the VerifAI evidence
    provider architecture alongside external retrievers.
    """

    def __init__(
        self,
        service: KnowledgeBaseService,
        owner_id: str | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.service = service
        self.settings = settings or get_settings()
        self.default_owner_id = owner_id

    @property
    def name(self) -> str:
        return "PRIVATE_KB"

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Extract clean alphanumeric lowercase tokens, filtering stop words."""
        tokens = set(re.findall(r"\b[a-z0-9]{3,}\b", text.lower()))
        return tokens - _STOP_WORDS

    async def search(
        self,
        claim_text: str,
        owner_id: str | None = None,
        max_passages: int | None = None,
        threshold: float | None = None,
        min_overlap_tokens: int | None = None,
    ) -> KBSearchResult:
        """Execute scored search across chunks strictly isolated to owner_id."""
        effective_owner = resolve_owner_id(
            owner_id or self.default_owner_id,
            self.settings,
        )

        eff_threshold = (
            threshold if threshold is not None else self.settings.KB_RELEVANCE_THRESHOLD
        )
        eff_min_overlap = (
            min_overlap_tokens
            if min_overlap_tokens is not None
            else self.settings.KB_MIN_OVERLAP_TOKENS
        )
        eff_max_passages = max_passages or self.settings.KB_MAX_PASSAGES

        # 1. Fetch chunks belonging strictly to this namespace
        chunk_pairs = await self.service.get_all_chunks_for_owner(effective_owner)

        if not chunk_pairs:
            return KBSearchResult(
                sufficiency=KBSufficiencyStatus.KB_EMPTY,
                evidence_items=[],
                top_score=None,
                threshold_used=eff_threshold,
                min_overlap_tokens_used=eff_min_overlap,
                total_candidates=0,
            )

        # 2. Tokenize claim
        claim_tokens = self._tokenize(claim_text)
        if not claim_tokens:
            return KBSearchResult(
                sufficiency=KBSufficiencyStatus.KB_INSUFFICIENT,
                evidence_items=[],
                top_score=0.0,
                threshold_used=eff_threshold,
                min_overlap_tokens_used=eff_min_overlap,
                total_candidates=len(chunk_pairs),
            )

        # 3. Score candidate chunks
        scored_candidates: list[tuple[float, int, Any, Any]] = []
        for chunk, doc in chunk_pairs:
            chunk_tokens = self._tokenize(chunk.text)
            overlap_tokens = len(claim_tokens & chunk_tokens)
            if overlap_tokens == 0:
                continue

            # Jaccard-like score with length normalization
            union_len = len(claim_tokens) + len(chunk_tokens) - overlap_tokens
            score = overlap_tokens / union_len if union_len > 0 else 0.0

            scored_candidates.append((score, overlap_tokens, chunk, doc))

        # Sort descending by relevance score, then overlap count
        scored_candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)

        if not scored_candidates:
            return KBSearchResult(
                sufficiency=KBSufficiencyStatus.KB_INSUFFICIENT,
                evidence_items=[],
                top_score=0.0,
                threshold_used=eff_threshold,
                min_overlap_tokens_used=eff_min_overlap,
                total_candidates=len(chunk_pairs),
            )

        top_score, top_overlap, _, _ = scored_candidates[0]

        # 4. Evaluate engineering sufficiency threshold
        is_sufficient = (top_score >= eff_threshold) and (
            top_overlap >= eff_min_overlap
        )
        sufficiency = (
            KBSufficiencyStatus.KB_RELEVANT
            if is_sufficient
            else KBSufficiencyStatus.KB_INSUFFICIENT
        )

        # 5. Build evidence items
        evidence_items: list[RetrievedEvidenceItem] = []
        for score, overlap, chunk, doc in scored_candidates[:eff_max_passages]:
            evidence_items.append(
                RetrievedEvidenceItem(
                    id=uuid.uuid4(),
                    source_url=None,  # Safe: do not expose local filesystem paths
                    source_title=doc.title,
                    publication_date=(
                        doc.created_at.strftime("%Y-%m-%d")
                        if doc.created_at
                        else datetime.now(UTC).strftime("%Y-%m-%d")
                    ),
                    retrieval_timestamp=datetime.now(UTC),
                    snippet=chunk.text,
                    query_used=claim_text,
                    retriever_name=self.name,
                    evidence_source="PRIVATE_KB",
                    document_id=doc.id,
                    chunk_id=chunk.id,
                    chunk_index=chunk.chunk_index,
                    document_title=doc.title,
                    relevance_score=round(score, 4),
                    authority_score=1.0,  # KB carries primary authority
                    metadata_json={
                        "owner_id": effective_owner,
                        "filename": doc.filename,
                        "chunk_index": chunk.chunk_index,
                        "overlap_tokens": overlap,
                        "start_offset": chunk.start_offset,
                        "end_offset": chunk.end_offset,
                    },
                )
            )

        return KBSearchResult(
            sufficiency=sufficiency,
            evidence_items=evidence_items,
            top_score=round(top_score, 4),
            threshold_used=eff_threshold,
            min_overlap_tokens_used=eff_min_overlap,
            total_candidates=len(chunk_pairs),
        )

    async def retrieve(
        self,
        claim_text: str,
        max_passages: int = 3,
    ) -> list[RetrievedEvidenceItem]:
        """BaseEvidenceRetriever compliance: return retrieved evidence items."""
        result = await self.search(
            claim_text=claim_text,
            max_passages=max_passages,
        )
        return result.evidence_items
