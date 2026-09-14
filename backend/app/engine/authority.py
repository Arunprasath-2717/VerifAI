"""Authority registry and domain authority prior modeling — Phase 2E.

The domain tier provides an INITIAL PRIOR, not absolute proof of factual truth.
The final evidence quality integrates:
    Publisher Authority + Article-level evidence + Independence + Temporal validity.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple

from app.engine.models import AuthorityTier

logger = logging.getLogger("verifai.engine.authority")

# ---------------------------------------------------------------------------
# Multi-part public suffixes for accurate root domain extraction
# ---------------------------------------------------------------------------
_MULTI_PART_SUFFIXES = {
    "co.uk", "gov.uk", "ac.uk", "org.uk", "com.au", "gov.au", "edu.au",
    "co.nz", "co.jp", "ne.jp", "go.jp", "co.in", "gov.in", "nic.in",
    "gc.ca", "fed.us", "state.tx.us",
}


def extract_root_domain(domain: str) -> str:
    """Extract root domain, handling common multi-part suffixes.

    e.g.:
        "news.bbc.co.uk" -> "bbc.co.uk"
        "edition.cnn.com" -> "cnn.com"
        "pubmed.ncbi.nlm.nih.gov" -> "nih.gov"
    """
    cleaned = domain.lower().strip()
    if cleaned.startswith("www."):
        cleaned = cleaned[4:]

    parts = cleaned.split(".")
    if len(parts) <= 2:
        return cleaned

    # Check for 2-part TLD (e.g., co.uk)
    two_part = f"{parts[-2]}.{parts[-1]}"
    if two_part in _MULTI_PART_SUFFIXES and len(parts) >= 3:
        return f"{parts[-3]}.{two_part}"

    # Special handling for US federal/nih subdomains
    if cleaned.endswith(".nih.gov"):
        return "nih.gov"

    return f"{parts[-2]}.{parts[-1]}"


# ---------------------------------------------------------------------------
# Domain Authority Registry
# ---------------------------------------------------------------------------

_TIER_1_DOMAINS: Dict[str, float] = {
    # Medical & Academic Institutions
    "nih.gov": 0.92,
    "cdc.gov": 0.92,
    "who.int": 0.92,
    "nature.com": 0.90,
    "science.org": 0.90,
    "nejm.org": 0.92,
    "thelancet.com": 0.92,
    "pubmed.ncbi.nlm.nih.gov": 0.92,
    "arxiv.org": 0.85,
    "biorxiv.org": 0.85,
    "scholar.google.com": 0.85,
    # Primary IFCN Fact-Checkers
    "politifact.com": 0.88,
    "snopes.com": 0.88,
    "factcheck.org": 0.88,
    "fullfact.org": 0.88,
}

_TIER_2_DOMAINS: Dict[str, float] = {
    # International News Agencies & High-standard Journalism
    "reuters.com": 0.85,
    "apnews.com": 0.85,
    "afp.com": 0.84,
    "bbc.com": 0.82,
    "bbc.co.uk": 0.82,
    "nytimes.com": 0.80,
    "theguardian.com": 0.78,
    "washingtonpost.com": 0.78,
    "wsj.com": 0.82,
    "bloomberg.com": 0.82,
    "ft.com": 0.82,
    "economist.com": 0.82,
    "britannica.com": 0.80,
}

_TIER_3_DOMAINS: Dict[str, float] = {
    # Collaborative / Community Knowledge
    "wikipedia.org": 0.68,
    "en.wikipedia.org": 0.68,
    "github.com": 0.65,
    "stackoverflow.com": 0.65,
    "stackexchange.com": 0.65,
}

_TIER_5_DOMAINS: Dict[str, float] = {
    # Known Disinformation / Tabloid / Unreliable Content Farms
    "infowars.com": 0.10,
    "naturalnews.com": 0.10,
    "thegatewaypundit.com": 0.15,
    "dailymail.co.uk": 0.35,
}


def get_domain_authority(domain: str) -> Tuple[AuthorityTier, float]:
    """Return the (AuthorityTier, authority_prior_score) for a domain.

    Scores are prior values in [0.0, 1.0].
    """
    root = extract_root_domain(domain)
    clean_domain = domain.lower().strip()
    if clean_domain.startswith("www."):
        clean_domain = clean_domain[4:]

    # Check Tier 1
    if clean_domain in _TIER_1_DOMAINS:
        return AuthorityTier.TIER_1_INSTITUTIONAL, _TIER_1_DOMAINS[clean_domain]
    if root in _TIER_1_DOMAINS:
        return AuthorityTier.TIER_1_INSTITUTIONAL, _TIER_1_DOMAINS[root]
    # Check official governmental / educational top-level domains
    if root.endswith(".gov") or root.endswith(".edu") or root.endswith(".int"):
        return AuthorityTier.TIER_1_INSTITUTIONAL, 0.88

    # Check Tier 2
    if clean_domain in _TIER_2_DOMAINS:
        return AuthorityTier.TIER_2_MAJOR_NEWS, _TIER_2_DOMAINS[clean_domain]
    if root in _TIER_2_DOMAINS:
        return AuthorityTier.TIER_2_MAJOR_NEWS, _TIER_2_DOMAINS[root]

    # Check Tier 3
    if clean_domain in _TIER_3_DOMAINS:
        return AuthorityTier.TIER_3_COLLABORATIVE, _TIER_3_DOMAINS[clean_domain]
    if root in _TIER_3_DOMAINS:
        return AuthorityTier.TIER_3_COLLABORATIVE, _TIER_3_DOMAINS[root]

    # Check Tier 5
    if clean_domain in _TIER_5_DOMAINS:
        return AuthorityTier.TIER_5_UNRELIABLE, _TIER_5_DOMAINS[clean_domain]
    if root in _TIER_5_DOMAINS:
        return AuthorityTier.TIER_5_UNRELIABLE, _TIER_5_DOMAINS[root]

    # Default Tier 4: General unverified web
    return AuthorityTier.TIER_4_GENERAL_WEB, 0.40
