"""Source quality scorer — Phase 2D.

Computes a deterministic, transparent quality score for each web source.
The score reflects *evidence quality*, NOT truth.

Formula (all sub-scores normalized to [0, 1]):

    quality = (
        0.30 * domain_score         # domain reputation mapping
      + 0.25 * content_score        # title + snippet completeness
      + 0.20 * protocol_score       # HTTPS
      + 0.15 * freshness_score      # publication date present
      + 0.10 * rank_score           # search rank (lower = better)
    )

Domain reputation:
    Kept intentionally small and transparent.
    Unknown domains receive a neutral score of 0.5.
    The mapping will be calibrated using labeled data in a later phase.

TODO(calibration): Validate thresholds against ECE and labeled benchmark data.
"""

from __future__ import annotations

import logging
from typing import Dict

from app.engine.models import NormalizedSource, ScoredSource

logger = logging.getLogger("verifai.engine.scorer")

# ---------------------------------------------------------------------------
# Domain reputation mapping
# ---------------------------------------------------------------------------
# Small, transparent starting mapping.  Scores are in [0.0, 1.0].
# Unknown domains get NEUTRAL_DOMAIN_SCORE.
# DO NOT expand this list without benchmark validation.

NEUTRAL_DOMAIN_SCORE = 0.5

_DOMAIN_SCORES: Dict[str, float] = {
    # Academic / government
    "arxiv.org": 0.85,
    "pubmed.ncbi.nlm.nih.gov": 0.90,
    "nih.gov": 0.90,
    "cdc.gov": 0.90,
    "who.int": 0.90,
    "nature.com": 0.88,
    "science.org": 0.88,
    "scholar.google.com": 0.80,
    # News
    "bbc.com": 0.80,
    "bbc.co.uk": 0.80,
    "reuters.com": 0.82,
    "apnews.com": 0.82,
    "nytimes.com": 0.78,
    "theguardian.com": 0.76,
    "washingtonpost.com": 0.76,
    # Reference
    "en.wikipedia.org": 0.70,
    "britannica.com": 0.75,
    # Technology
    "github.com": 0.72,
    "stackoverflow.com": 0.68,
}


def _domain_score(domain: str) -> float:
    """Return the reputation score for *domain* (neutral if unknown)."""
    return _DOMAIN_SCORES.get(domain.lower(), NEUTRAL_DOMAIN_SCORE)


def _content_score(source: NormalizedSource) -> float:
    """Score based on title and snippet completeness."""
    score = 0.0
    if source.title and len(source.title) > 5:
        score += 0.5
    if source.snippet and len(source.snippet) > 20:
        score += 0.5
    return score


def _protocol_score(source: NormalizedSource) -> float:
    """Full score for HTTPS, half for HTTP, zero otherwise."""
    url = source.url.lower()
    if url.startswith("https://"):
        return 1.0
    if url.startswith("http://"):
        return 0.5
    return 0.0


def _freshness_score(source: NormalizedSource) -> float:
    """Score 1.0 when a publication date is present, 0.0 otherwise."""
    return 1.0 if source.publication_date else 0.0


def _rank_score(rank: int, max_rank: int = 10) -> float:
    """Higher score for lower (better) search rank.

    rank=1 → 1.0, rank=max_rank → ~0.0.
    """
    if rank <= 0:
        return 0.0
    return max(0.0, 1.0 - (rank - 1) / max(max_rank, 1))


# ---------------------------------------------------------------------------
# Weights — must sum to 1.0
# ---------------------------------------------------------------------------

_W_DOMAIN = 0.30
_W_CONTENT = 0.25
_W_PROTOCOL = 0.20
_W_FRESHNESS = 0.15
_W_RANK = 0.10


def score_source(source: NormalizedSource) -> ScoredSource:
    """Compute a quality score for *source* and return a ScoredSource.

    The score is strictly bounded to [0.0, 1.0].
    """
    raw_score = (
        _W_DOMAIN * _domain_score(source.domain)
        + _W_CONTENT * _content_score(source)
        + _W_PROTOCOL * _protocol_score(source)
        + _W_FRESHNESS * _freshness_score(source)
        + _W_RANK * _rank_score(source.rank)
    )
    bounded = min(1.0, max(0.0, raw_score))
    return ScoredSource(source=source, quality_score=round(bounded, 4))
