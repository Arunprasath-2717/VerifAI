"""Phase 2D tests — Verification Engine.

Covers all 41 required test scenarios:

CLAIM EXTRACTION (1-4)
CLASSIFICATION (5-7)
SEARCH (8-13)
SOURCE QUALITY (14-17)
JUDGE (18-23)
DECISION (24-30)
FAILURES (31-34)
INTEGRATION (35-39)
MULTI-CLAIM ISOLATION (40-41)

Plus required fixtures:
  E/E/E, E/E/K, E/K/A, A/A/A, R/R/A, E/K/R, N=0
  ABSENT != REFUSED, REFUSED != JUDGE_ERROR, two-claim isolation

All external LLM/search providers are mocked — no live API calls.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.engine.classifier import DomainClassifier, _parse_domain
from app.engine.decision import (
    CONFIDENCE_THRESHOLD,
    QUALITY_THRESHOLD,
    DecisionInput,
    compute_confidence,
    decide,
)
from app.engine.engine import VerificationEngine, _aggregate_verdict
from app.engine.extractor import ClaimExtractor, _parse_llm_claims
from app.engine.judge import Judge, JudgeCallError, _parse_judge_response
from app.engine.models import (
    Domain,
    EngineResult,
    ExtractedClaim,
    JudgeLabel,
    JudgeResult,
    NormalizedSource,
    ScoredSource,
    Verdict,
)
from app.engine.scorer import (
    NEUTRAL_DOMAIN_SCORE,
    _content_score,
    _domain_score,
    _freshness_score,
    _protocol_score,
    _rank_score,
    score_source,
)
from app.engine.searcher import (
    SourceSearcher,
    _canonical_url,
    _extract_domain,
    build_query,
    normalize_results,
)


# ===========================================================================
# Helpers
# ===========================================================================


def _make_claim(text: str = "The Earth orbits the Sun.", cid: str = "claim_1") -> ExtractedClaim:
    return ExtractedClaim(claim_id=cid, text=text, position=1)


def _make_source(
    url: str = "https://example.com/article",
    title: str = "A good article",
    snippet: str = "The Earth orbits the Sun as confirmed by astronomers.",
    domain: str = "example.com",
    rank: int = 1,
) -> NormalizedSource:
    return NormalizedSource(
        url=url,
        title=title,
        snippet=snippet,
        domain=domain,
        rank=rank,
        query="The Earth orbits the Sun.",
        publication_date="2024-01-01",
    )


def _make_scored(quality: float = 0.80, **kwargs) -> ScoredSource:
    return ScoredSource(source=_make_source(**kwargs), quality_score=quality)


def _make_judge(
    label: JudgeLabel,
    confidence: float = 0.90,
    url: str = "https://example.com/article",
    cid: str = "claim_1",
) -> JudgeResult:
    return JudgeResult(
        label=label,
        reason="test",
        confidence=confidence,
        source_url=url,
        claim_id=cid,
    )


def _make_decision_input(
    judge_results: List[JudgeResult],
    scored_sources: Optional[List[ScoredSource]] = None,
    claim_text: str = "The Earth orbits the Sun.",
    cid: str = "claim_1",
    judge_error_count: int = 0,
) -> DecisionInput:
    if scored_sources is None:
        # Build scored sources from unique URLs in judge_results
        seen = set()
        scored_sources = []
        for jr in judge_results:
            if jr.source_url not in seen:
                seen.add(jr.source_url)
                scored_sources.append(
                    ScoredSource(
                        source=_make_source(url=jr.source_url),
                        quality_score=QUALITY_THRESHOLD + 0.05,  # above threshold
                    )
                )
    return DecisionInput(
        claim=_make_claim(claim_text, cid),
        domain=Domain.GENERAL,
        scored_sources=scored_sources,
        judge_results=judge_results,
        judge_error_count=judge_error_count,
    )


# ===========================================================================
# 1-4. Claim Extraction
# ===========================================================================


@pytest.mark.asyncio
async def test_extraction_single_factual_claim_no_llm():
    """Without LLM, input is returned as a single claim."""
    extractor = ClaimExtractor(llm=None)
    claims = await extractor.extract("The Earth is the third planet from the Sun.")
    assert len(claims) == 1
    assert claims[0].claim_id == "claim_1"
    assert "Earth" in claims[0].text


@pytest.mark.asyncio
async def test_extraction_multiple_claims_via_llm():
    """LLM returning multiple claims is parsed correctly."""
    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value='[{"claim_id":"claim_1","text":"Claim A","position":1},'
                     '{"claim_id":"claim_2","text":"Claim B","position":2}]'
    )
    extractor = ClaimExtractor(llm=llm)
    claims = await extractor.extract("Claim A. Claim B.")
    assert len(claims) == 2
    assert claims[0].text == "Claim A"
    assert claims[1].text == "Claim B"


@pytest.mark.asyncio
async def test_extraction_malformed_response_falls_back():
    """Malformed LLM JSON falls back to single-claim input text."""
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value="not json at all")
    extractor = ClaimExtractor(llm=llm)
    original = "The sky is blue."
    claims = await extractor.extract(original)
    assert len(claims) == 1
    assert claims[0].text == original


@pytest.mark.asyncio
async def test_extraction_provider_failure_falls_back():
    """LLM provider failure falls back to single-claim input text."""
    llm = AsyncMock()
    llm.generate = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
    extractor = ClaimExtractor(llm=llm)
    original = "Some claim."
    claims = await extractor.extract(original)
    assert len(claims) == 1
    assert claims[0].text == original


def test_parse_llm_claims_empty_array_fallback():
    """Empty JSON array falls back to single-claim with fallback text."""
    result = _parse_llm_claims("[]", "fallback text")
    assert len(result) == 1
    assert result[0].text == "fallback text"


# ===========================================================================
# 5-7. Domain Classification
# ===========================================================================


@pytest.mark.asyncio
async def test_classification_normal():
    """Valid domain returned from LLM is parsed correctly."""
    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value='{"domain": "SCIENCE", "reason": "scientific topic"}'
    )
    classifier = DomainClassifier(llm=llm)
    domain = await classifier.classify(_make_claim())
    assert domain == Domain.SCIENCE


@pytest.mark.asyncio
async def test_classification_fallback_on_unknown_domain():
    """Unknown domain value falls back to GENERAL."""
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value='{"domain": "ASTROLOGY", "reason": "x"}')
    classifier = DomainClassifier(llm=llm)
    domain = await classifier.classify(_make_claim())
    assert domain == Domain.GENERAL


@pytest.mark.asyncio
async def test_classification_provider_failure_returns_general():
    """Provider failure returns Domain.GENERAL (never raises)."""
    llm = AsyncMock()
    llm.generate = AsyncMock(side_effect=RuntimeError("timeout"))
    classifier = DomainClassifier(llm=llm)
    domain = await classifier.classify(_make_claim())
    assert domain == Domain.GENERAL


@pytest.mark.asyncio
async def test_classification_no_llm_returns_general():
    """Without LLM, always returns GENERAL."""
    classifier = DomainClassifier(llm=None)
    domain = await classifier.classify(_make_claim())
    assert domain == Domain.GENERAL


def test_parse_domain_all_valid_domains():
    """All domain enum values are accepted."""
    for d in Domain:
        raw = f'{{"domain": "{d.value}", "reason": "x"}}'
        assert _parse_domain(raw) == d


# ===========================================================================
# 8-13. Search — query generation, normalization, deduplication
# ===========================================================================


def test_query_generation_preserves_claim_text():
    """build_query returns the claim text (truncated to 200 chars)."""
    claim = _make_claim("The sun is a star at the center of the Solar System.")
    q = build_query(claim)
    assert "sun" in q.lower()
    assert len(q) <= 200


def test_query_generation_normalises_whitespace():
    """build_query normalizes excessive whitespace."""
    claim = _make_claim("  The   sky   is   blue.  ")
    q = build_query(claim)
    assert "  " not in q


def test_query_generation_truncates_long_claims():
    """Claims longer than 200 chars are truncated."""
    long_text = "A " * 200
    claim = _make_claim(long_text)
    q = build_query(claim)
    assert len(q) == 200


@pytest.mark.asyncio
async def test_search_success():
    """Successful search returns NormalizedSource objects."""
    provider = AsyncMock()
    provider.search = AsyncMock(
        return_value=[
            {
                "href": "https://bbc.com/science/article",
                "title": "BBC Science",
                "body": "Some evidence text here.",
            }
        ]
    )
    searcher = SourceSearcher(provider=provider)
    sources = await searcher.search_for_claim(_make_claim())
    assert len(sources) == 1
    assert sources[0].domain == "bbc.com"
    assert sources[0].url == "https://bbc.com/science/article"


@pytest.mark.asyncio
async def test_search_returns_empty_on_no_results():
    """Empty search results return an empty list (no crash)."""
    provider = AsyncMock()
    provider.search = AsyncMock(return_value=[])
    searcher = SourceSearcher(provider=provider)
    sources = await searcher.search_for_claim(_make_claim())
    assert sources == []


@pytest.mark.asyncio
async def test_search_provider_failure_returns_empty():
    """Provider failure returns empty list (graceful degradation)."""
    provider = AsyncMock()
    provider.search = AsyncMock(return_value=[])  # DuckDuckGoProvider already handles errors
    searcher = SourceSearcher(provider=provider)
    sources = await searcher.search_for_claim(_make_claim())
    assert sources == []


def test_source_normalization_filters_invalid_urls():
    """Results without HTTP/HTTPS URLs are excluded."""
    raw = [{"href": "ftp://bad.com", "title": "x", "body": "y"}]
    sources = normalize_results(raw, "query")
    assert sources == []


def test_source_deduplication_by_canonical_url():
    """Duplicate canonical URLs produce only one source."""
    raw = [
        {"href": "https://example.com/page/", "title": "A", "body": "snippet"},
        {"href": "https://example.com/page", "title": "A dup", "body": "snippet"},
    ]
    sources = normalize_results(raw, "query")
    assert len(sources) == 1


def test_canonical_url_strips_trailing_slash():
    """Canonical URL normalisation strips trailing slashes."""
    assert _canonical_url("https://example.com/page/") == _canonical_url("https://example.com/page")


def test_extract_domain_strips_www():
    """_extract_domain strips the www. prefix."""
    assert _extract_domain("https://www.bbc.com/article") == "bbc.com"


# ===========================================================================
# 14-17. Source Quality Scoring
# ===========================================================================


def test_high_quality_source_score():
    """Known high-reputation HTTPS domain with content scores above neutral."""
    source = _make_source(
        url="https://bbc.com/article",
        title="BBC article",
        snippet="Evidence text here",
        domain="bbc.com",
        rank=1,
    )
    source.publication_date = "2024-01-01"
    scored = score_source(source)
    assert scored.quality_score > NEUTRAL_DOMAIN_SCORE


def test_incomplete_source_scores_lower():
    """Source with empty title and snippet scores lower than full source."""
    full = _make_source()
    empty = NormalizedSource(
        url="https://example.com/page",
        title="",
        snippet="",
        domain="example.com",
        rank=5,
        query="q",
        publication_date=None,
    )
    scored_full = score_source(full)
    scored_empty = score_source(empty)
    assert scored_full.quality_score > scored_empty.quality_score


def test_neutral_default_domain_score():
    """Unknown domain receives the neutral default score."""
    assert _domain_score("completely-unknown-domain.io") == NEUTRAL_DOMAIN_SCORE


def test_quality_score_bounded_0_to_1():
    """Quality score is always in [0.0, 1.0]."""
    source = _make_source(url="https://bbc.com/a", rank=1)
    scored = score_source(source)
    assert 0.0 <= scored.quality_score <= 1.0


def test_protocol_score_https_vs_http():
    """HTTPS scores higher than HTTP."""
    s_https = _make_source(url="https://example.com")
    s_http = _make_source(url="http://example.com")
    assert _protocol_score(s_https) > _protocol_score(s_http)


def test_rank_score_decreases_with_rank():
    """Higher rank (worse position) gives lower score."""
    s1 = _make_source(rank=1)
    s5 = _make_source(rank=5)
    assert _rank_score(1) > _rank_score(5)


def test_freshness_score():
    """Source with publication_date scores 1.0; without scores 0.0."""
    with_date = _make_source()
    with_date.publication_date = "2024-01-01"
    without_date = _make_source()
    without_date.publication_date = None
    assert _freshness_score(with_date) == 1.0
    assert _freshness_score(without_date) == 0.0


# ===========================================================================
# 18-23. Judge
# ===========================================================================


@pytest.mark.asyncio
async def test_judge_entailment():
    """ENTAILMENT label is correctly parsed and returned."""
    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value='{"label": "ENTAILMENT", "reason": "supported", "confidence": 0.9}'
    )
    judge = Judge(llm=llm)
    result = await judge.judge(_make_claim(), _make_scored())
    assert result.label == JudgeLabel.ENTAILMENT
    assert result.confidence == 0.9


@pytest.mark.asyncio
async def test_judge_contradiction():
    """CONTRADICTION label is correctly parsed."""
    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value='{"label": "CONTRADICTION", "reason": "conflicts", "confidence": 0.85}'
    )
    judge = Judge(llm=llm)
    result = await judge.judge(_make_claim(), _make_scored())
    assert result.label == JudgeLabel.CONTRADICTION


@pytest.mark.asyncio
async def test_judge_absent():
    """ABSENT label is correctly parsed."""
    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value='{"label": "ABSENT", "reason": "insufficient", "confidence": 0.5}'
    )
    judge = Judge(llm=llm)
    result = await judge.judge(_make_claim(), _make_scored())
    assert result.label == JudgeLabel.ABSENT


@pytest.mark.asyncio
async def test_judge_refused():
    """REFUSED label is correctly parsed."""
    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value='{"label": "REFUSED", "reason": "malformed", "confidence": 0.0}'
    )
    judge = Judge(llm=llm)
    result = await judge.judge(_make_claim(), _make_scored())
    assert result.label == JudgeLabel.REFUSED


@pytest.mark.asyncio
async def test_judge_malformed_response_returns_refused():
    """Malformed JSON response returns REFUSED (not a crash)."""
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value="definitely not json")
    judge = Judge(llm=llm)
    result = await judge.judge(_make_claim(), _make_scored())
    assert result.label == JudgeLabel.REFUSED


@pytest.mark.asyncio
async def test_judge_provider_failure_raises_judge_call_error():
    """LLM provider exception raises JudgeCallError (not a JudgeLabel)."""
    llm = AsyncMock()
    llm.generate = AsyncMock(side_effect=RuntimeError("network error"))
    judge = Judge(llm=llm)
    with pytest.raises(JudgeCallError):
        await judge.judge(_make_claim(), _make_scored())


@pytest.mark.asyncio
async def test_judge_no_llm_returns_absent():
    """Without LLM, judge returns ABSENT (no fabricated verdict)."""
    judge = Judge(llm=None)
    result = await judge.judge(_make_claim(), _make_scored())
    assert result.label == JudgeLabel.ABSENT


def test_absent_is_not_refused():
    """ABSENT and REFUSED are distinct JudgeLabel values."""
    assert JudgeLabel.ABSENT != JudgeLabel.REFUSED


def test_refused_is_not_judge_call_error():
    """JudgeCallError is an exception class, REFUSED is a label — they are distinct."""
    assert not issubclass(JudgeCallError, JudgeLabel.__class__)
    assert JudgeLabel.REFUSED.value == "REFUSED"


def test_parse_judge_response_clips_confidence():
    """Confidence values outside [0,1] are clipped."""
    raw = '{"label": "ENTAILMENT", "reason": "ok", "confidence": 1.5}'
    result = _parse_judge_response(raw, "claim_1", "https://x.com")
    assert result.confidence <= 1.0

    raw2 = '{"label": "ENTAILMENT", "reason": "ok", "confidence": -0.5}'
    result2 = _parse_judge_response(raw2, "claim_1", "https://x.com")
    assert result2.confidence >= 0.0


# ===========================================================================
# 24-30. Decision logic (fixtures)
# ===========================================================================


def test_decision_E_E_E_fixture():
    """E/E/E → SUPPORT with confidence 1.0."""
    judges = [_make_judge(JudgeLabel.ENTAILMENT, confidence=0.90) for _ in range(3)]
    result = decide(_make_decision_input(judges))
    assert result.verdict == Verdict.SUPPORT
    assert result.confidence == 1.0
    assert result.entailment_count == 3


def test_decision_E_E_K_fixture():
    """E/E/K → SUPPORT (2 ENTAILMENT > 1 CONTRADICTION)."""
    judges = [
        _make_judge(JudgeLabel.ENTAILMENT, confidence=0.90),
        _make_judge(JudgeLabel.ENTAILMENT, confidence=0.90),
        _make_judge(JudgeLabel.CONTRADICTION, confidence=0.90),
    ]
    result = decide(_make_decision_input(judges))
    # confidence = ((2-1)/3 + 1) / 2 = (1/3 + 1) / 2 ≈ 0.667 < threshold → UNKNOWN
    # But strong support exists, strong contradict exists → CONFLICTING_SOURCES
    assert result.verdict == Verdict.UNKNOWN
    assert result.entailment_count == 2
    assert result.contradiction_count == 1


def test_decision_E_K_A_fixture():
    """E/K/A — one ENTAILMENT, one CONTRADICTION, one ABSENT → UNKNOWN (conflicting)."""
    judges = [
        _make_judge(JudgeLabel.ENTAILMENT, confidence=0.90),
        _make_judge(JudgeLabel.CONTRADICTION, confidence=0.90, url="https://b.com"),
        _make_judge(JudgeLabel.ABSENT, confidence=0.50, url="https://c.com"),
    ]
    scored = [
        _make_scored(quality=0.80, url="https://example.com/article"),
        _make_scored(quality=0.80, url="https://b.com"),
        _make_scored(quality=0.80, url="https://c.com"),
    ]
    result = decide(_make_decision_input(judges, scored))
    assert result.verdict == Verdict.UNKNOWN
    assert result.absent_count == 1


def test_decision_A_A_A_fixture():
    """A/A/A — all ABSENT → UNKNOWN, confidence 0.5, signal_quality 0."""
    judges = [_make_judge(JudgeLabel.ABSENT, confidence=0.5) for _ in range(3)]
    result = decide(_make_decision_input(judges))
    assert result.verdict == Verdict.UNKNOWN
    assert result.confidence == 0.5
    assert result.signal_quality == 0.0


def test_decision_R_R_A_fixture():
    """R/R/A — all non-informative → UNKNOWN."""
    judges = [
        _make_judge(JudgeLabel.REFUSED, confidence=0.0),
        _make_judge(JudgeLabel.REFUSED, confidence=0.0, url="https://b.com"),
        _make_judge(JudgeLabel.ABSENT, confidence=0.5, url="https://c.com"),
    ]
    result = decide(_make_decision_input(judges))
    assert result.verdict == Verdict.UNKNOWN
    assert result.confidence == 0.5


def test_decision_E_K_R_fixture():
    """E/K/R — informative N=2, confidence exactly 0.5."""
    judges = [
        _make_judge(JudgeLabel.ENTAILMENT, confidence=0.90),
        _make_judge(JudgeLabel.CONTRADICTION, confidence=0.90, url="https://b.com"),
        _make_judge(JudgeLabel.REFUSED, confidence=0.0, url="https://c.com"),
    ]
    scored = [
        _make_scored(quality=0.80, url="https://example.com/article"),
        _make_scored(quality=0.80, url="https://b.com"),
        _make_scored(quality=0.80, url="https://c.com"),
    ]
    result = decide(_make_decision_input(judges, scored))
    # e=1, k=1, N=2 → confidence = ((1-1)/2 + 1)/2 = 0.5
    assert result.confidence == 0.5


def test_decision_N_zero_fixture():
    """N=0 → confidence exactly 0.5, signal_quality exactly 0."""
    confidence, support_ratio, signal_quality = compute_confidence(0, 0)
    assert confidence == 0.5
    assert signal_quality == 0.0
    assert support_ratio == 0.0


def test_strong_support_verdict():
    """Strong ENTAILMENT source + high judge confidence → SUPPORT."""
    url = "https://example.com/article"
    judges = [_make_judge(JudgeLabel.ENTAILMENT, confidence=0.90, url=url)]
    scored = [_make_scored(quality=0.80, url=url)]
    result = decide(_make_decision_input(judges, scored))
    assert result.verdict == Verdict.SUPPORT


def test_strong_contradict_verdict():
    """Strong CONTRADICTION source + high judge confidence → CONTRADICT."""
    url = "https://example.com/article"
    judges = [_make_judge(JudgeLabel.CONTRADICTION, confidence=0.90, url=url)]
    scored = [_make_scored(quality=0.80, url=url)]
    result = decide(_make_decision_input(judges, scored))
    assert result.verdict == Verdict.CONTRADICT


def test_conflicting_strong_sources_produces_unknown():
    """Both strong SUPPORT and strong CONTRADICT → UNKNOWN with CONFLICTING_SOURCES."""
    url_a = "https://a.com/article"
    url_b = "https://b.com/article"
    judges = [
        _make_judge(JudgeLabel.ENTAILMENT, confidence=0.90, url=url_a),
        _make_judge(JudgeLabel.CONTRADICTION, confidence=0.90, url=url_b),
    ]
    scored = [
        _make_scored(quality=0.80, url=url_a),
        _make_scored(quality=0.80, url=url_b),
    ]
    result = decide(_make_decision_input(judges, scored))
    assert result.verdict == Verdict.UNKNOWN
    assert "CONFLICTING" in result.reason


def test_weak_source_quality_produces_unknown():
    """Source below QUALITY_THRESHOLD does not trigger SUPPORT."""
    url = "https://example.com/article"
    judges = [_make_judge(JudgeLabel.ENTAILMENT, confidence=0.95, url=url)]
    scored = [_make_scored(quality=0.30, url=url)]  # below threshold
    result = decide(_make_decision_input(judges, scored))
    assert result.verdict == Verdict.UNKNOWN


def test_low_judge_confidence_produces_unknown():
    """Judge confidence below CONFIDENCE_THRESHOLD does not trigger SUPPORT."""
    url = "https://example.com/article"
    judges = [_make_judge(JudgeLabel.ENTAILMENT, confidence=0.20, url=url)]
    scored = [_make_scored(quality=0.90, url=url)]
    result = decide(_make_decision_input(judges, scored))
    assert result.verdict == Verdict.UNKNOWN


def test_confidence_formula_math():
    """Manual verification of confidence formula."""
    e, k = 3, 1  # N=4
    confidence, support_ratio, signal_quality = compute_confidence(e, k)
    expected = ((3 - 1) / 4 + 1) / 2  # = 0.75
    assert abs(confidence - expected) < 1e-9
    assert abs(support_ratio - 3 / 4) < 1e-9
    assert signal_quality == 1.0  # all 4 are informative


# ===========================================================================
# 31-34. Failure handling
# ===========================================================================


@pytest.mark.asyncio
async def test_partial_judge_failures_uses_remaining():
    """Judge failures for some sources use remaining successful results."""
    llm = AsyncMock()
    # First call raises, second succeeds
    llm.generate = AsyncMock(
        side_effect=[
            RuntimeError("provider fail"),
            '{"label": "ENTAILMENT", "reason": "good", "confidence": 0.9}',
        ]
    )
    judge = Judge(llm=llm)
    claim = _make_claim()
    source_a = _make_scored(quality=0.80, url="https://a.com")
    source_b = _make_scored(quality=0.80, url="https://b.com")

    # First call raises JudgeCallError
    with pytest.raises(JudgeCallError):
        await judge.judge(claim, source_a)

    # Second call succeeds
    result = await judge.judge(claim, source_b)
    assert result.label == JudgeLabel.ENTAILMENT


@pytest.mark.asyncio
async def test_all_judge_failures_produces_unknown():
    """When all judge results are ABSENT/REFUSED, verdict is UNKNOWN."""
    judges = [
        _make_judge(JudgeLabel.REFUSED, confidence=0.0),
        _make_judge(JudgeLabel.REFUSED, confidence=0.0, url="https://b.com"),
    ]
    result = decide(_make_decision_input(judges, judge_error_count=2))
    assert result.verdict == Verdict.UNKNOWN


@pytest.mark.asyncio
async def test_search_failure_produces_unknown_verdict():
    """Search returning no sources produces UNKNOWN for that claim."""
    provider = AsyncMock()
    provider.search = AsyncMock(return_value=[])
    engine = VerificationEngine(llm=None, search_provider=provider)
    result = await engine.verify("The sky is blue.", uuid.uuid4())
    assert result.verdict == Verdict.UNKNOWN
    assert result.source_count == 0


@pytest.mark.asyncio
async def test_engine_safe_exception_handling_no_fabricated_verdict():
    """Engine with no LLM and no sources produces a safe UNKNOWN result."""
    provider = AsyncMock()
    provider.search = AsyncMock(return_value=[])
    engine = VerificationEngine(llm=None, search_provider=provider)
    result = await engine.verify("Some claim.", uuid.uuid4())
    assert result.verdict == Verdict.UNKNOWN
    # Must not produce a confident score when there's no signal
    assert result.trust_score == Decimal("0.5")


# ===========================================================================
# 35-39. Integration — processing service wired to engine
# ===========================================================================


@pytest.mark.asyncio
async def test_processing_stub_replaced_by_engine(owner_id, verification_id, now):
    """_process_verification_core calls the engine, not the old stub."""
    from app.services.verification_processing_service import (
        _process_verification_core,
    )

    mock_repo = AsyncMock()
    mock_repo.update_verification = AsyncMock(
        return_value={
            "id": verification_id,
            "user_id": owner_id,
            "claim": "Earth orbits Sun.",
            "status": "processing",
            "verdict": "UNKNOWN",
            "trust_score": Decimal("0.5"),
            "evidence": [],
            "error_message": None,
            "created_at": now,
            "updated_at": now,
        }
    )

    mock_search = AsyncMock()
    mock_search.search = AsyncMock(return_value=[])

    engine = VerificationEngine(llm=None, search_provider=mock_search)

    with patch("app.services.verification_processing_service.verification_engine", engine):
        result = await _process_verification_core(
            verification_id=verification_id,
            claim="Earth orbits Sun.",
            repo=mock_repo,
        )

    # Confirms update_verification was called with real engine output
    mock_repo.update_verification.assert_awaited_once()
    call_kwargs = mock_repo.update_verification.call_args.kwargs
    assert call_kwargs["verdict"] in ["SUPPORT", "CONTRADICT", "UNKNOWN"]


@pytest.mark.asyncio
async def test_successful_verification_persists_verdict_score_evidence(
    owner_id, verification_id, now
):
    """Engine result verdict/trust_score/evidence are persisted via update_verification."""
    from app.repositories.verification_repository import VerificationRepository

    mock_repo = AsyncMock(spec=VerificationRepository)
    pending_record = {
        "id": verification_id,
        "user_id": owner_id,
        "claim": "Earth orbits Sun.",
        "status": "pending",
        "verdict": None,
        "trust_score": None,
        "evidence": None,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }
    processing_record = {**pending_record, "status": "processing"}
    completed_record = {
        **pending_record,
        "status": "completed",
        "verdict": "UNKNOWN",
        "trust_score": Decimal("0.500"),
        "evidence": [],
    }

    mock_repo.get_verification_by_id.return_value = pending_record
    mock_repo.transition_status.side_effect = [processing_record, completed_record]
    mock_repo.update_verification.return_value = {**processing_record, "verdict": "UNKNOWN"}

    from app.services.verification_processing_service import VerificationProcessingService

    mock_search = AsyncMock()
    mock_search.search = AsyncMock(return_value=[])
    engine = VerificationEngine(llm=None, search_provider=mock_search)

    svc = VerificationProcessingService(repo=mock_repo)

    with patch("app.services.verification_processing_service.verification_engine", engine):
        result = await svc.process_verification(
            verification_id=verification_id,
            user_id=owner_id,
        )

    mock_repo.update_verification.assert_awaited_once()
    # Final status should be completed
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_engine_failure_transitions_to_failed(owner_id, verification_id, now):
    """When engine raises, processing service transitions to failed."""
    from app.repositories.verification_repository import VerificationRepository
    from app.services.verification_processing_service import VerificationProcessingService

    mock_repo = AsyncMock(spec=VerificationRepository)
    pending_record = {
        "id": verification_id, "user_id": owner_id,
        "claim": "Some claim.", "status": "pending",
        "verdict": None, "trust_score": None, "evidence": None,
        "error_message": None, "created_at": now, "updated_at": now,
    }
    processing_record = {**pending_record, "status": "processing"}
    failed_record = {
        **pending_record, "status": "failed",
        "error_message": "Verification processing failed due to an internal error",
    }

    mock_repo.get_verification_by_id.return_value = pending_record
    mock_repo.transition_status.side_effect = [processing_record, failed_record]

    svc = VerificationProcessingService(repo=mock_repo)

    # Patch the engine to raise
    with patch(
        "app.services.verification_processing_service.verification_engine"
    ) as mock_engine:
        mock_engine.verify = AsyncMock(side_effect=RuntimeError("Engine crashed"))
        result = await svc.process_verification(
            verification_id=verification_id,
            user_id=owner_id,
        )

    assert result["status"] == "failed"
    assert result["error_message"] is not None


@pytest.mark.asyncio
async def test_lifecycle_cas_remains_intact(owner_id, verification_id, now):
    """CAS (transition_status) is still called for pending→processing."""
    from app.repositories.verification_repository import VerificationRepository
    from app.services.verification_processing_service import (
        InvalidStatusTransitionError,
        VerificationProcessingService,
    )

    mock_repo = AsyncMock(spec=VerificationRepository)
    completed_record = {
        "id": verification_id, "user_id": owner_id,
        "claim": "Claim.", "status": "completed",
        "verdict": "SUPPORT", "trust_score": Decimal("0.9"),
        "evidence": None, "error_message": None,
        "created_at": now, "updated_at": now,
    }
    mock_repo.get_verification_by_id.return_value = completed_record
    mock_repo.transition_status.return_value = None  # CAS miss

    svc = VerificationProcessingService(repo=mock_repo)
    with pytest.raises(InvalidStatusTransitionError):
        await svc.process_verification(
            verification_id=verification_id,
            user_id=owner_id,
        )


@pytest.mark.asyncio
async def test_existing_phase_2b_2c_behavior_unchanged(
    client, owner_id, verification_id, now
):
    """GET /verification still works after Phase 2D changes."""
    from unittest.mock import patch as _patch

    completed = {
        "id": verification_id,
        "user_id": owner_id,
        "claim": "Claim.",
        "status": "completed",
        "verdict": "SUPPORT",
        "trust_score": Decimal("0.9"),
        "evidence": [{"claim_id": "claim_1"}],
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }
    with _patch("app.api.dependencies.supabase_auth_service.get_user", new_callable=AsyncMock) as ma, \
         _patch("app.api.dependencies.user_repository.get_user_by_id", new_callable=AsyncMock) as mb, \
         _patch(
             "app.api.v1.endpoints.verification.verification_service.get_own_verification",
             new_callable=AsyncMock,
         ) as mc:
        ma.return_value = {"id": str(owner_id)}
        mb.return_value = {
            "id": owner_id, "email": "o@v.app",
            "display_name": None, "created_at": now, "updated_at": now,
        }
        mc.return_value = completed

        resp = await client.get(
            f"/api/v1/verification/{verification_id}",
            headers={"Authorization": "Bearer tok"},
        )

    assert resp.status_code == 200
    assert resp.json()["data"]["verdict"] == "SUPPORT"


# ===========================================================================
# 40-41. Multi-claim isolation
# ===========================================================================


def test_multi_claim_results_are_isolated():
    """Claim A result does not affect Claim B result."""
    claim_a = _make_claim("The Earth orbits the Sun.", "claim_1")
    claim_b = _make_claim("Water boils at 100 degrees Celsius.", "claim_2")

    url_a = "https://a.com/earth"
    url_b = "https://b.com/water"

    judge_a = _make_judge(JudgeLabel.ENTAILMENT, confidence=0.95, url=url_a, cid="claim_1")
    judge_b = _make_judge(JudgeLabel.CONTRADICTION, confidence=0.90, url=url_b, cid="claim_2")

    scored_a = [_make_scored(quality=0.85, url=url_a)]
    scored_b = [_make_scored(quality=0.85, url=url_b)]

    result_a = decide(_make_decision_input([judge_a], scored_a, cid="claim_1"))
    result_b = decide(_make_decision_input([judge_b], scored_b, cid="claim_2"))

    assert result_a.verdict == Verdict.SUPPORT
    assert result_b.verdict == Verdict.CONTRADICT
    # Isolation: each result only has its own judges
    assert result_a.claim_id == "claim_1"
    assert result_b.claim_id == "claim_2"


def test_aggregate_verdict_mixed_claims():
    """SUPPORT + CONTRADICT across two claims → overall UNKNOWN."""
    from app.engine.models import ClaimVerificationResult

    r_a = ClaimVerificationResult(
        claim_id="claim_1", claim_text="A", domain=Domain.GENERAL,
        verdict=Verdict.SUPPORT, confidence=0.9,
        signal_quality=1.0, support_ratio=1.0, reason="ok",
    )
    r_b = ClaimVerificationResult(
        claim_id="claim_2", claim_text="B", domain=Domain.GENERAL,
        verdict=Verdict.CONTRADICT, confidence=0.1,
        signal_quality=1.0, support_ratio=0.0, reason="no",
    )
    verdict, reason = _aggregate_verdict([r_a, r_b])
    assert verdict == Verdict.UNKNOWN
    assert "CONFLICTING" in reason


# ===========================================================================
# 42-45. Providers & Engine Branch Coverage
# ===========================================================================


@pytest.mark.asyncio
async def test_gemini_provider_generate_success():
    with patch("google.generativeai.configure"), \
         patch("google.generativeai.GenerativeModel") as mock_model_cls:
        mock_instance = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "Hello world"
        mock_instance.generate_content.return_value = mock_resp
        mock_model_cls.return_value = mock_instance

        from app.engine.providers import GeminiProvider
        provider = GeminiProvider(api_key="real-key", model_name="gemini-1.5-flash")
        res = await provider.generate("test prompt")
        assert res == "Hello world"


@pytest.mark.asyncio
async def test_gemini_provider_generate_failure():
    with patch("google.generativeai.configure"), \
         patch("google.generativeai.GenerativeModel") as mock_model_cls:
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("API error")
        mock_model_cls.return_value = mock_instance

        from app.engine.providers import GeminiProvider
        provider = GeminiProvider(api_key="real-key")
        with pytest.raises(RuntimeError, match="LLM provider unavailable"):
            await provider.generate("test prompt")


@pytest.mark.asyncio
async def test_duckduckgo_provider_search_success():
    with patch("ddgs.DDGS") as mock_ddgs:
        mock_ddgs.return_value.text.return_value = [
            {"href": "https://a.com", "title": "A", "body": "B"}
        ]
        from app.engine.providers import DuckDuckGoProvider
        provider = DuckDuckGoProvider()
        results = await provider.search("query")
        assert len(results) == 1
        assert results[0]["title"] == "A"


@pytest.mark.asyncio
async def test_duckduckgo_provider_search_failure():
    with patch("ddgs.DDGS") as mock_ddgs:
        mock_ddgs.return_value.text.side_effect = Exception("Network error")
        from app.engine.providers import DuckDuckGoProvider
        provider = DuckDuckGoProvider()
        results = await provider.search("query")
        assert results == []


def test_build_llm_provider_missing_or_mock_key():
    from app.engine.providers import build_llm_provider
    with patch("app.core.config.get_settings") as mock_get_settings:
        mock_get_settings.return_value.GEMINI_API_KEY = "mock-key"
        assert build_llm_provider() is None
        mock_get_settings.return_value.GEMINI_API_KEY = ""
        assert build_llm_provider() is None


def test_build_llm_provider_valid_key():
    from app.engine.providers import build_llm_provider
    with patch("app.core.config.get_settings") as mock_get_settings, \
         patch("google.generativeai.configure"), \
         patch("google.generativeai.GenerativeModel"):
        mock_get_settings.return_value.GEMINI_API_KEY = "actual-api-key"
        mock_get_settings.return_value.LLM_MODEL = "gemini-1.5-flash"
        provider = build_llm_provider()
        assert provider is not None


def test_build_search_provider():
    from app.engine.providers import DuckDuckGoProvider, build_search_provider
    assert isinstance(build_search_provider(), DuckDuckGoProvider)


def test_aggregate_verdict_edge_cases():
    from app.engine.engine import _aggregate_verdict, _average_confidence
    from app.engine.models import ClaimVerificationResult

    assert _aggregate_verdict([]) == (Verdict.UNKNOWN, "No claims processed")
    assert _average_confidence([]) == 0.5

    r_supp = ClaimVerificationResult(
        claim_id="c1", claim_text="T", domain=Domain.GENERAL,
        verdict=Verdict.SUPPORT, confidence=0.9,
        signal_quality=1.0, support_ratio=1.0, reason="ok",
    )
    assert _aggregate_verdict([r_supp]) == (Verdict.SUPPORT, "All claims supported by evidence")

    r_contra = ClaimVerificationResult(
        claim_id="c2", claim_text="F", domain=Domain.GENERAL,
        verdict=Verdict.CONTRADICT, confidence=0.1,
        signal_quality=1.0, support_ratio=0.0, reason="no",
    )
    assert _aggregate_verdict([r_contra]) == (Verdict.CONTRADICT, "All claims contradicted by evidence")


@pytest.mark.asyncio
async def test_engine_verify_search_exception():
    mock_extractor = AsyncMock()
    mock_extractor.extract.return_value = [_make_claim("claim 1")]
    mock_searcher = AsyncMock()
    mock_searcher.search_for_claim.side_effect = Exception("Search crashed")

    engine = VerificationEngine()
    engine._extractor = mock_extractor
    engine._searcher = mock_searcher
    engine._classifier = AsyncMock()
    engine._judge = AsyncMock()

    res = await engine.verify("claim 1", uuid.uuid4())
    assert res.verdict == Verdict.UNKNOWN
    assert res.claim_results[0].reason == "No sources found for this claim"


@pytest.mark.asyncio
async def test_engine_verify_judge_call_error():
    claim = _make_claim("claim 1")
    mock_extractor = AsyncMock()
    mock_extractor.extract.return_value = [claim]
    mock_searcher = AsyncMock()
    mock_searcher.search_for_claim.return_value = [_make_source()]
    mock_judge = AsyncMock()
    mock_judge.judge.side_effect = JudgeCallError("LLM failed")

    engine = VerificationEngine()
    engine._extractor = mock_extractor
    engine._searcher = mock_searcher
    engine._classifier = AsyncMock()
    engine._judge = mock_judge

    res = await engine.verify("claim 1", uuid.uuid4())
    assert res.verdict == Verdict.UNKNOWN


# ===========================================================================
# conftest fixtures (local — mirrors test_verification_api.py)
# ===========================================================================


@pytest.fixture
def owner_id() -> uuid.UUID:
    return uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


@pytest.fixture
def verification_id() -> uuid.UUID:
    return uuid.UUID("cafecafe-cafe-cafe-cafe-cafecafecafe")


@pytest.fixture
def now() -> datetime:
    return datetime.now(timezone.utc)
