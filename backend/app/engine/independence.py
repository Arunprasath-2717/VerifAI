"""Source independence and syndication clustering — Phase 2E.

Prevents sybil attacks, copycat blogs, and wire syndications (e.g. Reuters -> Yahoo -> MSN)
from artificially inflating consensus into multiple independent corroborations.

Different domains != independent sources.
Tracks origin by:
- Wire attribution (Reuters, AP, AFP, PR Newswire, etc.)
- Shared root domain
- Lexical content fingerprinting (Jaccard similarity on n-grams)
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Dict, List, Optional, Set, Tuple

from app.engine.authority import extract_root_domain
from app.engine.models import ScoredSource, SourceCluster

logger = logging.getLogger("verifai.engine.independence")

# ---------------------------------------------------------------------------
# Known Wire Services & Syndication Patterns
# ---------------------------------------------------------------------------
_WIRE_PATTERNS = [
    (r"\b(reuters)\b", "reuters"),
    (r"\b(associated press|\bap news|\bap\b(?:\s*—|\s*-|\s*:))", "ap"),
    (r"\b(agence france[- ]presse|\bafp\b)", "afp"),
    (r"\b(pr newswire)\b", "pr_newswire"),
    (r"\b(business wire)\b", "business_wire"),
    (r"\b(bloomberg news)\b", "bloomberg"),
]


def detect_wire_attribution(title: str, snippet: str) -> Optional[str]:
    """Detect if the article is a syndicated wire story."""
    combined = f"{title} {snippet}".lower()
    for pattern, name in _WIRE_PATTERNS:
        if re.search(pattern, combined):
            return name
    return None


def compute_article_fingerprint(text: str) -> str:
    """Generate a stable normalized MD5 hash of alphanumeric tokens."""
    tokens = re.findall(r"\b[a-z0-9]+\b", text.lower())
    normalized = " ".join(tokens[:50])  # first 50 tokens (lead paragraph)
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()[:12]


def _shingles(text: str, n: int = 3) -> Set[str]:
    """Generate character n-grams for fuzzy duplicate detection."""
    clean = re.sub(r"\s+", " ", text.lower().strip())
    if len(clean) < n:
        return {clean}
    return {clean[i:i + n] for i in range(len(clean) - n + 1)}


def _jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Compute Jaccard similarity between two shingle sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0


def cluster_sources(
    scored_sources: List[ScoredSource],
    similarity_threshold: float = 0.60,
) -> Tuple[List[ScoredSource], List[SourceCluster]]:
    """Cluster sources by wire origin, root domain, and content similarity.

    Down-weights redundant/syndicated members so a syndicated story only
    counts as 1 independent signal.
    """
    if not scored_sources:
        return [], []

    # Map of cluster_id -> list of ScoredSource indices
    clusters: Dict[str, List[int]] = {}
    cluster_origins: Dict[str, str] = {}
    source_shingles: List[Set[str]] = [
        _shingles(f"{s.source.title} {s.source.snippet}") for s in scored_sources
    ]

    for idx, ss in enumerate(scored_sources):
        src = ss.source
        wire = src.wire_attribution or detect_wire_attribution(src.title, src.snippet)
        if wire:
            wire = wire.lower().strip()
        root = src.root_domain or extract_root_domain(src.domain)

        # Update source metadata
        src.wire_attribution = wire
        src.root_domain = root
        src.article_fingerprint = compute_article_fingerprint(f"{src.title} {src.snippet}")

        matched_cluster_id: Optional[str] = None

        # 1. Match by wire attribution (e.g. 2 different sites both reprinting Reuters)
        if wire:
            wire_key = f"wire:{wire}"
            for c_id, origin in cluster_origins.items():
                if origin == wire_key:
                    matched_cluster_id = c_id
                    break
            if not matched_cluster_id:
                matched_cluster_id = wire_key
                cluster_origins[matched_cluster_id] = wire_key

        # 2. Match by high content similarity (near-duplicate text / copycat blogs)
        if not matched_cluster_id:
            for c_id, members in clusters.items():
                for m_idx in members:
                    sim = _jaccard_similarity(source_shingles[idx], source_shingles[m_idx])
                    if sim >= similarity_threshold:
                        matched_cluster_id = c_id
                        break
                if matched_cluster_id:
                    break

        # 3. Match by shared root domain
        if not matched_cluster_id:
            domain_key = f"domain:{root}"
            for c_id, origin in cluster_origins.items():
                if origin == domain_key:
                    matched_cluster_id = c_id
                    break
            if not matched_cluster_id:
                matched_cluster_id = f"cluster_{len(clusters) + 1}_{root}"
                cluster_origins[matched_cluster_id] = domain_key

        clusters.setdefault(matched_cluster_id, []).append(idx)

    # Build clusters and update independence scores
    updated_sources: List[ScoredSource] = list(scored_sources)
    source_clusters: List[SourceCluster] = []

    for c_id, member_indices in clusters.items():
        count = len(member_indices)
        cluster_sources_list = [scored_sources[i] for i in member_indices]
        member_urls = [s.source.url for s in cluster_sources_list]
        primary_url = member_urls[0]
        root_dom = cluster_sources_list[0].source.root_domain or "unknown"
        wire_attr = cluster_sources_list[0].source.wire_attribution
        best_quality = max(s.quality_score for s in cluster_sources_list)

        # Cluster metadata
        cluster_obj = SourceCluster(
            cluster_id=c_id,
            primary_source_url=primary_url,
            member_urls=member_urls,
            root_domain=root_dom,
            wire_attribution=wire_attr,
            representative_quality=best_quality,
            effective_weight=1.0,  # 1 independent signal unit
        )
        source_clusters.append(cluster_obj)

        # Scale member independence scores so sum equals 1.0 for the cluster
        for m_idx in member_indices:
            s = updated_sources[m_idx]
            s.cluster_id = c_id
            s.source.cluster_id = c_id
            s.independence_score = round(1.0 / count, 3)

    return updated_sources, source_clusters
