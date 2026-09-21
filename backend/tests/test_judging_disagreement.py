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
    assert result.rationale is not None
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
    assert result.rationale is not None
    rationale_lower = result.rationale.lower()
    assert (
        "not configured" in rationale_lower
        or "offline" in rationale_lower
        or "unavailable" in rationale_lower
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


def test_disagreement_engine_case_d_two_judges_disagree_third_unavailable() -> None:
    """Case D: Two judges disagree and third judge is unavailable -> UNKNOWN, degraded=True."""
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
    assert res.consensus_verdict == VerdictType.UNKNOWN
    assert res.has_disagreement is True
    assert res.degraded_evaluation is True
    assert res.judges_used == 2
    assert res.third_judge_invoked is False
    assert res.unknown_reason == UnknownReason.CONFLICTING_EVIDENCE
    assert "tie-breaker is unavailable" in (res.arbitration_reason or "")


def test_disagreement_engine_case_b_three_judges_majority_contradicted() -> None:
    """Case B: Two judges disagree, third judge produces majority for CONTRADICTED."""
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
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-TieBreaker",
            judgment=JudgeDecision.CONTRADICTED,
            confidence=0.9,
            rationale="Cross-check confirmed numeric contradiction",
            evidence_references=[],
        ),
    ]
    res = engine.arbitrate(evals)
    assert res.consensus_verdict == VerdictType.CONTRADICTED
    assert res.has_disagreement is True
    assert res.degraded_evaluation is False
    assert res.judges_used == 3
    assert res.third_judge_invoked is True
    assert len(res.judge_evaluations) == 3


def test_disagreement_engine_case_b_three_judges_majority_supported() -> None:
    """Case B: Two judges disagree, third judge produces majority for SUPPORTED."""
    engine = DisagreementEngine()
    evals = [
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-Rule",
            judgment=JudgeDecision.CONTRADICTED,
            confidence=0.6,
            rationale="Weak mismatch",
            evidence_references=[],
        ),
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-Semantic",
            judgment=JudgeDecision.SUPPORTED,
            confidence=0.85,
            rationale="Strong token match",
            evidence_references=[],
        ),
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-TieBreaker",
            judgment=JudgeDecision.SUPPORTED,
            confidence=0.9,
            rationale="Independent evaluation supports claim",
            evidence_references=[],
        ),
    ]
    res = engine.arbitrate(evals)
    assert res.consensus_verdict == VerdictType.SUPPORTED
    assert res.has_disagreement is True
    assert res.degraded_evaluation is False
    assert res.judges_used == 3
    assert res.third_judge_invoked is True
    assert len(res.judge_evaluations) == 3


def test_disagreement_engine_case_c_all_three_judges_disagree() -> None:
    """Case C: All three judges disagree (SUPPORTED, CONTRADICTED, INSUFFICIENT)."""
    engine = DisagreementEngine()
    evals = [
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-1",
            judgment=JudgeDecision.SUPPORTED,
            confidence=0.7,
            rationale="Supported",
            evidence_references=[],
        ),
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-2",
            judgment=JudgeDecision.CONTRADICTED,
            confidence=0.7,
            rationale="Contradicted",
            evidence_references=[],
        ),
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-3",
            judgment=JudgeDecision.INSUFFICIENT_EVIDENCE,
            confidence=None,
            rationale="Insufficient evidence",
            evidence_references=[],
        ),
    ]
    res = engine.arbitrate(evals)
    assert res.consensus_verdict == VerdictType.UNKNOWN
    assert res.has_disagreement is True
    assert res.degraded_evaluation is True
    assert res.judges_used == 3
    assert res.third_judge_invoked is True
    assert res.unknown_reason == UnknownReason.CONFLICTING_EVIDENCE
    assert "All three judges disagreed" in (res.arbitration_reason or "")


def test_disagreement_engine_case_e_invalid_or_unusable_judge_output() -> None:
    """Case E: Invalid or unusable judge outputs trigger safe degraded evaluation."""
    engine = DisagreementEngine()
    # All unavailable
    evals_all_down = [
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-1",
            judgment=JudgeDecision.UNAVAILABLE,
            confidence=None,
            rationale="Service connection timed out",
            evidence_references=[],
        ),
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-2",
            judgment=JudgeDecision.UNAVAILABLE,
            confidence=None,
            rationale="Service offline",
            evidence_references=[],
        ),
    ]
    res_all_down = engine.arbitrate(evals_all_down)
    assert res_all_down.consensus_verdict == VerdictType.UNKNOWN
    assert res_all_down.degraded_evaluation is True
    assert res_all_down.unknown_reason == UnknownReason.INSUFFICIENT_EVIDENCE
    assert "All configured judges reported UNAVAILABLE" in (
        res_all_down.disagreement_details or ""
    )

    # Partial failure: 1 active out of 2
    evals_partial = [
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-1",
            judgment=JudgeDecision.SUPPORTED,
            confidence=0.9,
            rationale="Valid",
            evidence_references=[],
        ),
        JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name="Judge-2",
            judgment=JudgeDecision.UNAVAILABLE,
            confidence=None,
            rationale="Crashed",
            evidence_references=[],
        ),
    ]
    res_partial = engine.arbitrate(evals_partial)
    assert res_partial.consensus_verdict == VerdictType.UNKNOWN
    assert res_partial.has_disagreement is True
    assert res_partial.degraded_evaluation is True
    assert "Insufficient active judges" in (res_partial.disagreement_details or "")


def test_disagreement_engine_preserves_individual_judge_outputs() -> None:
    """Verify individual judge identities, verdicts, confidences, and rationales are preserved."""
    engine = DisagreementEngine()
    id1, id2 = uuid.uuid4(), uuid.uuid4()
    evals = [
        JudgeEvaluationData(
            judge_id=id1,
            judge_name="DeterministicRuleJudge",
            judgment=JudgeDecision.SUPPORTED,
            confidence=0.95,
            rationale="Exact numeric match",
            evidence_references=["ref-1"],
        ),
        JudgeEvaluationData(
            judge_id=id2,
            judge_name="SecondarySemanticJudge",
            judgment=JudgeDecision.SUPPORTED,
            confidence=0.88,
            rationale="High semantic overlap",
            evidence_references=["ref-2"],
        ),
    ]
    res = engine.arbitrate(evals)
    assert len(res.judge_evaluations) == 2
    assert res.judge_evaluations[0].judge_id == id1
    assert res.judge_evaluations[0].judge_name == "DeterministicRuleJudge"
    assert res.judge_evaluations[0].confidence == 0.95
    assert res.judge_evaluations[1].judge_id == id2
    assert res.judge_evaluations[1].confidence == 0.88


def test_decision_engine_aggregation_metrics() -> None:
    """Verify document-level trust score calculation and counts."""
    decision_engine = DecisionEngine()
    claims = [
        {
            "verdict": VerdictType.SUPPORTED,
            "content_type": ContentType.FACTUAL,
            "is_verifiable": True,
        },
        {
            "verdict": VerdictType.SUPPORTED,
            "content_type": ContentType.FACTUAL,
            "is_verifiable": True,
        },
        {
            "verdict": VerdictType.CONTRADICTED,
            "content_type": ContentType.FACTUAL,
            "is_verifiable": True,
        },
        {
            "verdict": VerdictType.UNKNOWN,
            "content_type": ContentType.FACTUAL,
            "is_verifiable": True,
        },
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
        {
            "verdict": VerdictType.SUPPORTED,
            "content_type": ContentType.FACTUAL,
            "is_verifiable": True,
        },
        {
            "verdict": VerdictType.SUPPORTED,
            "content_type": ContentType.FACTUAL,
            "is_verifiable": True,
        },
        {
            "verdict": VerdictType.UNKNOWN,
            "content_type": ContentType.FACTUAL,
            "is_verifiable": True,
        },
        {
            "verdict": VerdictType.UNKNOWN,
            "content_type": ContentType.FACTUAL,
            "is_verifiable": True,
        },
    ]
    summary2 = decision_engine.aggregate(claims_clean)
    assert summary2.trust_score == 50.0


def test_decision_engine_non_factual_exempt() -> None:
    """Verify non-factual content yields exempt None trust score and verdict=None."""
    decision_engine = DecisionEngine()
    claims = [
        {"verdict": None, "is_verifiable": False, "content_type": ContentType.OPINION},
        {"verdict": None, "is_verifiable": False, "content_type": ContentType.CREATIVE},
    ]
    summary = decision_engine.aggregate(claims)

    assert summary.total_claims == 2
    assert summary.supported_claims == 0
    assert summary.contradicted_claims == 0
    assert summary.non_factual_claims == 2
    assert summary.trust_score is None
