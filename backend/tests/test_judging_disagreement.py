"""Tests for judging engines, consensus rules, and disagreement arbitration."""

import uuid

import pytest

from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging.decision import DecisionEngine
from app.modules.judging.deterministic_judge import DeterministicRuleJudge
from app.modules.judging.disagreement import DisagreementEngine
from app.modules.judging.model_judge import OpenSourceModelJudge
from app.modules.judging.models import JudgeEvaluationData
from app.modules.judging.semantic_judge import SecondarySemanticJudge
from app.schemas.verification import (
    ContentType,
    JudgeDecision,
    UnknownReason,
    VerdictType,
)


@pytest.mark.anyio
async def test_deterministic_rule_judge_numeric_support() -> None:
    """Verify numeric match yields SUPPORTED judgment."""
    judge = DeterministicRuleJudge()
    claim = "Apollo 11 landed on the Moon in 1969."
    evidence = [
        RetrievedEvidenceItem(
            snippet=(
                "Apollo 11 was the American spaceflight that landed "
                "the first humans on the Moon in 1969."
            ),
            retriever_name="test",
            authority_score=0.9,
            relevance_score=0.9,
        )
    ]
    result = await judge.evaluate(claim, evidence)
    assert result.judgment == JudgeDecision.SUPPORTED
    assert result.confidence is None


@pytest.mark.anyio
async def test_deterministic_rule_judge_numeric_contradiction() -> None:
    """Verify numeric conflict yields CONTRADICTED judgment."""
    judge = DeterministicRuleJudge()
    claim = "Apollo 11 landed on the Moon in 1975."
    evidence = [
        RetrievedEvidenceItem(
            snippet=(
                "Apollo 11 was the American spaceflight that landed "
                "the first humans on the Moon in 1969."
            ),
            retriever_name="test",
            authority_score=0.9,
            relevance_score=0.9,
        )
    ]
    result = await judge.evaluate(claim, evidence)
    assert result.judgment == JudgeDecision.CONTRADICTED
    has_mismatch = (
        "numeric" in result.rationale.lower() or "mismatch" in result.rationale.lower()
    )
    assert has_mismatch


@pytest.mark.anyio
async def test_deterministic_rule_judge_no_evidence() -> None:
    """Verify evaluating with empty evidence yields INSUFFICIENT_EVIDENCE."""
    judge = DeterministicRuleJudge()
    result = await judge.evaluate("Earth revolves around the Sun.", [])
    assert result.judgment == JudgeDecision.INSUFFICIENT_EVIDENCE
    assert result.confidence is None


@pytest.mark.anyio
async def test_secondary_semantic_judge_support() -> None:
    """Verify semantic judge returns SUPPORTED on strong token overlap."""
    judge = SecondarySemanticJudge()
    claim = "Water consists of hydrogen and oxygen molecules."
    evidence = [
        RetrievedEvidenceItem(
            snippet=(
                "Water molecules are composed of hydrogen and oxygen "
                "atoms bonded covalently."
            ),
            retriever_name="test",
        )
    ]
    result = await judge.evaluate(claim, evidence)
    assert result.judgment == JudgeDecision.SUPPORTED
    assert result.confidence is None


@pytest.mark.anyio
async def test_open_source_model_judge_offline_honest_reporting() -> None:
    """Verify open-source model judge honestly reports UNAVAILABLE when offline."""
    judge = OpenSourceModelJudge()
    evidence = [
        RetrievedEvidenceItem(
            snippet="Test snippet.",
            retriever_name="test",
        )
    ]
    result = await judge.evaluate("Test claim.", evidence)
    assert result.judgment == JudgeDecision.UNAVAILABLE
    assert result.confidence is None
    assert (
        "not configured" in result.rationale.lower()
        or "offline" in result.rationale.lower()
        or "unavailable" in result.rationale.lower()
    )


def test_disagreement_engine_full_consensus_support() -> None:
    """Verify two SUPPORTED evaluations produce SUPPORTED verdict."""
    engine = DisagreementEngine()
    evals = [
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-1",
            judgment=JudgeDecision.SUPPORTED,
            confidence=0.9,
            rationale="Pass",
            evidence_references=[],
        ),
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-2",
            judgment=JudgeDecision.SUPPORTED,
            confidence=0.85,
            rationale="Pass",
            evidence_references=[],
        ),
    ]
    res = engine.arbitrate(evals)
    assert res.consensus_verdict == VerdictType.SUPPORTED
    assert res.has_disagreement is False
    assert res.disagreement_details is None


def test_disagreement_engine_contradiction_priority() -> None:
    """Verify CONTRADICTED takes precedence over SUPPORTED for hallucination safety."""
    engine = DisagreementEngine()
    evals = [
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-Rule",
            judgment=JudgeDecision.CONTRADICTED,
            confidence=1.0,
            rationale="Numeric mismatch found",
            evidence_references=[],
        ),
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-Semantic",
            judgment=JudgeDecision.SUPPORTED,
            confidence=0.7,
            rationale="Tokens matched",
            evidence_references=[],
        ),
    ]
    res = engine.arbitrate(evals)
    assert res.consensus_verdict == VerdictType.CONTRADICTED
    assert res.has_disagreement is True
    assert "Conflict detected" in res.disagreement_details


def test_disagreement_engine_supported_vs_insufficient() -> None:
    """Verify SUPPORTED vs INSUFFICIENT resolves to UNKNOWN."""
    engine = DisagreementEngine()
    evals = [
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-Rule",
            judgment=JudgeDecision.SUPPORTED,
            confidence=0.8,
            rationale="Some match",
            evidence_references=[],
        ),
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-Secondary",
            judgment=JudgeDecision.INSUFFICIENT_EVIDENCE,
            confidence=None,
            rationale="Insufficient overlap",
            evidence_references=[],
        ),
    ]
    res = engine.arbitrate(evals)
    assert res.consensus_verdict == VerdictType.UNKNOWN
    assert res.has_disagreement is True
    assert res.unknown_reason == UnknownReason.CONFLICTING_EVIDENCE


def test_decision_engine_aggregation_metrics() -> None:
    """Verify document-level trust score calculation and counts."""
    decision_engine = DecisionEngine()
    claims = [
        {"verdict": VerdictType.SUPPORTED, "content_type": ContentType.FACTUAL},
        {"verdict": VerdictType.SUPPORTED, "content_type": ContentType.FACTUAL},
        {"verdict": VerdictType.CONTRADICTED, "content_type": ContentType.FACTUAL},
        {"verdict": VerdictType.UNKNOWN, "content_type": ContentType.FACTUAL},
    ]
    summary = decision_engine.aggregate(claims)

    assert summary.total_claims == 4
    assert summary.supported_claims == 2
    assert summary.contradicted_claims == 1
    assert summary.unknown_claims == 1
    # Contradiction triggers hallucination risk penalty: trust_score is 0.0%
    assert summary.trust_score == 0.0
    assert summary.is_calibrated is False
    assert summary.calibration_status == "NOT_CALIBRATED"

    # When no contradictions exist, trust score is proportion of supported claims
    claims_clean = [
        {"verdict": VerdictType.SUPPORTED, "content_type": ContentType.FACTUAL},
        {"verdict": VerdictType.SUPPORTED, "content_type": ContentType.FACTUAL},
        {"verdict": VerdictType.UNKNOWN, "content_type": ContentType.FACTUAL},
        {"verdict": VerdictType.UNKNOWN, "content_type": ContentType.FACTUAL},
    ]
    summary2 = decision_engine.aggregate(claims_clean)
    assert summary2.trust_score == 50.0


def test_decision_engine_non_factual_exempt() -> None:
    """Verify non-factual content yields exempt None trust score."""
    decision_engine = DecisionEngine()
    claims = [
        {"verdict": VerdictType.VIEWPOINT, "content_type": ContentType.OPINION},
        {"verdict": VerdictType.CREATIVE, "content_type": ContentType.CREATIVE},
    ]
    summary = decision_engine.aggregate(claims)

    assert summary.total_claims == 2
    assert summary.supported_claims == 0
    assert summary.contradicted_claims == 0
    assert summary.non_factual_claims == 2
    assert summary.trust_score is None
