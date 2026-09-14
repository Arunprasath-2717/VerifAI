"""Source quality scorer — Phase 2E Hardening.

Computes a deterministic, transparent quality score for each web source.
The score reflects *evidence quality*, NOT factual truth.

Formula:
    quality = (
        0.55 * authority_score    # publisher & domain authority prior
      + 0.30 * relevance_score    # claim-to-snippet entity/keyword overlap
      + 0.15 * freshness_score    # publication date presence & temporal validity
    ) * protocol_multiplier       # HTTPS gives 1.0; insecure HTTP receives 0.7 penalty

Key Hardening Principles (Phase 2E):
1. HTTPS is a transport baseline, NOT evidence of credibility (0 bonus; plain HTTP penalised).
2. Search rank is purely discovery, NOT evidence of factual correctness (0 authority contribution).
3. Domain tier is an initial prior, tempered by article-level relevance, independence, and freshness.
"""

from __future__ import annotations

import logging
import re
from typing import Optional, Set

from app.engine.authority import get_domain_authority
from app.engine.models import AuthorityTier, NormalizedSource, ScoredSource

logger = logging.getLogger("verifai.engine.scorer")

# ---------------------------------------------------------------------------
# Weights — sum to 1.0
# ---------------------------------------------------------------------------
_W_AUTHORITY = 0.55
_W_RELEVANCE = 0.30
_W_FRESHNESS = 0.15

# Stop words for relevance overlap
_STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "if", "then", "of", "at", "by",
    "for", "with", "about", "against", "between", "into", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down", "in",
    "out", "on", "off", "over", "under", "again", "further", "then", "once",
    "is", "am", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "having", "do", "does", "did", "doing", "would", "should", "could",
    "ought", "i", "you", "he", "she", "it", "we", "they", "this", "that",
}


def _tokenize(text: str) -> Set[str]:
    """Tokenize lowercase alphanumeric tokens excluding common stop words."""
    tokens = re.findall(r"\b[a-z0-9]{2,}\b", text.lower())
    return {t for t in tokens if t not in _STOP_WORDS}


def _relevance_score(source: NormalizedSource, claim_text: Optional[str] = None) -> float:
    """Score relevance based on claim-to-evidence keyword/entity overlap.

    If claim_text is not provided, falls back to snippet completeness.
    """
    if not source.snippet or len(source.snippet.strip()) < 10:
        return 0.15

    if not claim_text:
        # Fallback to completeness
        score = 0.3
        if source.title and len(source.title) > 5:
            score += 0.3
        if len(source.snippet) > 40:
            score += 0.4
        return min(1.0, score)

    claim_tokens = _tokenize(claim_text)
    if not claim_tokens:
        return 0.5

    evidence_text = f"{source.title} {source.snippet}"
    evidence_tokens = _tokenize(evidence_text)

    overlap = claim_tokens.intersection(evidence_tokens)
    overlap_ratio = len(overlap) / len(claim_tokens)

    # Base score of 0.2 + up to 0.8 for strong token/entity overlap
    return min(1.0, max(0.1, 0.2 + 0.8 * overlap_ratio))


def _freshness_score(source: NormalizedSource) -> float:
    """Score publication date presence and freshness."""
    return 1.0 if source.publication_date else 0.0


def _protocol_multiplier(url: str) -> float:
    """HTTPS receives 1.0 (baseline). Insecure HTTP receives a 0.70 penalty."""
    if url.lower().startswith("https://"):
        return 1.0
    if url.lower().startswith("http://"):
        return 0.70
    return 0.50


# ---------------------------------------------------------------------------
# Backward-compatibility helpers
# ---------------------------------------------------------------------------

NEUTRAL_DOMAIN_SCORE = 0.40


def _domain_score(domain: str) -> float:
    """Return the authority prior for domain."""
    _, prior = get_domain_authority(domain)
    return prior


def _content_score(source: NormalizedSource) -> float:
    """Return content relevance score."""
    return _relevance_score(source)


def _protocol_score(source: NormalizedSource) -> float:
    """Return protocol score (1.0 for HTTPS, 0.7 for HTTP)."""
    return _protocol_multiplier(source.url)


def _rank_score(rank: int, max_rank: int = 10) -> float:
    """Rank decay function."""
    if rank <= 0:
        return 0.0
    return max(0.0, 1.0 - (rank - 1) / max(max_rank, 1))


def score_source(source: NormalizedSource, claim_text: Optional[str] = None) -> ScoredSource:
    """Compute a transparent, bounded [0.0, 1.0] quality score for *source*."""
    tier, authority_prior = get_domain_authority(source.domain)

    # If the source has accredited wire attribution, reflect the wire authority
    if source.wire_attribution:
        wire_tier, wire_score = get_domain_authority(f"{source.wire_attribution.lower()}.com")
        if wire_score > authority_prior:
            authority_prior = (authority_prior * 0.4) + (wire_score * 0.6)
            tier = wire_tier

    relevance = _relevance_score(source, claim_text)
    freshness = _freshness_score(source)
    proto_mult = _protocol_multiplier(source.url)

    raw_quality = (
        _W_AUTHORITY * authority_prior
        + _W_RELEVANCE * relevance
        + _W_FRESHNESS * freshness
    ) * proto_mult

    final_quality = round(min(1.0, max(0.0, raw_quality)), 4)

    return ScoredSource(
        source=source,
        quality_score=final_quality,
        authority_tier=tier,
        authority_score=authority_prior,
        relevance_score=relevance,
        freshness_score=freshness,
        independence_score=1.0,
        cluster_id=source.cluster_id,
    )

