"""Accuracy regression tests for extraction, classification, and judging.

These cases were taken from an audit in which the pipeline marked plainly false
claims SUPPORTED because judges matched bags of words and numbers anywhere in a
passage. The invariant enforced here: against the built-in reference passages,
false claims are CONTRADICTED, true claims are SUPPORTED, and claims the
evidence cannot settle are UNKNOWN; never a confident wrong verdict.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import clear_settings_cache
from app.modules.claims.classifier import ContentClassifier
from app.modules.claims.extractor import DeterministicClaimExtractor
from app.modules.judging.disagreement import DisagreementEngine
from app.modules.judging.model_judge import OpenSourceModelJudge, parse_model_verdict
from app.modules.judging.models import JudgeEvaluationData
from app.modules.verification.orchestrator import VerificationOrchestrator
from app.schemas.verification import (
    ContentType,
    JudgeDecision,
    VerdictType,
    VerificationCreateRequest,
)

FALSE_CLAIMS = [
    "Water freezes at 100 degrees Celsius.",
    "Water boils at 0 degrees Celsius.",
    "Paris is not the capital of France.",
    "Berlin is the capital of France.",
    "Lyon is the capital of France.",
    "Neil Armstrong landed on Mars in 1969.",
    "Apollo 11 landed on the Moon in 1975.",
    "The World Wide Web and the Internet are the same technology.",
    "Python was created by James Gosling and first released in 1991.",
    "Nitrogen makes up approximately 21 percent of Earth's atmosphere.",
    "ARPANET was permanently shut down in 1990.",
    "Python was first released in 1989.",
]

TRUE_CLAIMS = [
    "Water freezes at 0 degrees Celsius.",
    "Water boils at 100 degrees Celsius.",
    "Paris is the capital of France.",
    "Buzz Aldrin landed the Apollo Lunar Module on July 20, 1969.",
    "Neil Armstrong landed on the Moon.",
    "Python was created by Guido van Rossum.",
    "Python was first released in 1991.",
    "The speed of light is exactly 299,792,458 metres per second.",
    "Nitrogen makes up approximately 78 percent of Earth's atmosphere.",
    "Water has the chemical formula H2O.",
    "The Eiffel Tower is located in Paris, France.",
    "ARPANET adopted TCP/IP in 1983.",
    "Tim Berners-Lee proposed the World Wide Web at CERN in 1989.",
    "The World Wide Web and the Internet are not the same technology.",
]

# True claims the reference passages cannot establish; the judges must abstain
# rather than contradict (e.g. a France passage says nothing about Tokyo).
UNSETTLED_TRUE_CLAIMS = [
    "Tokyo is the capital city of Japan.",
    "Neil Armstrong was born in 1930.",
    "Oxygen makes up approximately 21 percent of Earth's atmosphere.",
]


async def _verdict(text: str) -> VerdictType | None:
    response = await VerificationOrchestrator().verify(
        VerificationCreateRequest(text=text)
    )
    assert response.total_claims == 1
    return response.claims[0].verdict


@pytest.mark.anyio
@pytest.mark.parametrize("claim", FALSE_CLAIMS)
async def test_false_claims_are_contradicted(claim: str) -> None:
    assert await _verdict(claim) == VerdictType.CONTRADICTED


@pytest.mark.anyio
@pytest.mark.parametrize("claim", TRUE_CLAIMS)
async def test_true_claims_are_supported(claim: str) -> None:
    assert await _verdict(claim) == VerdictType.SUPPORTED


@pytest.mark.anyio
@pytest.mark.parametrize("claim", UNSETTLED_TRUE_CLAIMS)
async def test_unsettled_true_claims_abstain(claim: str) -> None:
    assert await _verdict(claim) == VerdictType.UNKNOWN


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Paris has about 2.1 million residents.",
            ["Paris has about 2.1 million residents"],
        ),
        (
            "Pi is approximately 3.14159 and e is 2.718.",
            ["Pi is approximately 3.14159 and e is 2.718"],
        ),
        (
            "Visit https://example.com/a.b for details.",
            ["Visit https://example.com/a.b for details"],
        ),
        (
            "Dr. Smith works at NASA. He was born in 1950.",
            ["Dr. Smith works at NASA", "He was born in 1950"],
        ),
        (
            "See e.g. the U.S. report. It is long.",
            ["See e.g. the U.S. report", "It is long"],
        ),
        (
            "Prices rose 3.5% in 2023! Wages fell; rents did not.\nNew line here",
            [
                "Prices rose 3.5% in 2023",
                "Wages fell",
                "rents did not",
                "New line here",
            ],
        ),
    ],
)
def test_extractor_boundaries(text: str, expected: list[str]) -> None:
    claims = DeterministicClaimExtractor().extract(text)
    assert [c.text for c in claims] == expected
    for c in claims:
        assert text[c.start_offset : c.end_offset] == c.text


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Factual claims must not escape verification via incidental wording.
        ("Run-time of Titanic is 3 hours", ContentType.FACTUAL),
        ("Open-source Linux was released in 1850", ContentType.FACTUAL),
        ("Mount Everest is the greatest mountain on Mars", ContentType.FACTUAL),
        ("The Moon landing happened if you count 1950", ContentType.FACTUAL),
        ("Doctors should know that aspirin was invented in 2015", ContentType.FACTUAL),
        # Genuine non-factual forms keep their routing.
        ("Run the installer first.", ContentType.INSTRUCTION),
        ("VerifAI is the best AI verification system ever.", ContentType.OPINION),
        ("I think Paris is lovely.", ContentType.OPINION),
        ("Prices would fall if demand dropped.", ContentType.HYPOTHETICAL),
        ("If it rains, the match is cancelled.", ContentType.HYPOTHETICAL),
    ],
)
def test_classifier_routing(text: str, expected: ContentType) -> None:
    assert ContentClassifier().classify(text).content_type == expected


# ---------------------------------------------------------------------------
# Model judge parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("SUPPORTED", JudgeDecision.SUPPORTED),
        ("  contradicted.\n", JudgeDecision.CONTRADICTED),
        ('"Unknown"', JudgeDecision.UNKNOWN),
        ("UNSUPPORTED", None),
        ("NOT SUPPORTED", None),
        ("CONTRADICTED (not SUPPORTED)", None),
        ("The claim is supported by the evidence.", None),
        ("", None),
    ],
)
def test_parse_model_verdict_is_exact(raw: str, expected: JudgeDecision | None) -> None:
    assert parse_model_verdict(raw) == expected


def _mock_model_reply(text: str) -> MagicMock:
    reply = MagicMock(status_code=200)
    reply.json.return_value = {"response": text}
    client = MagicMock()
    client.post = AsyncMock(return_value=reply)
    client_cm = MagicMock()
    client_cm.__aenter__ = AsyncMock(return_value=client)
    client_cm.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=client_cm)


@pytest.mark.anyio
async def test_model_judge_reports_unparseable_output_as_unavailable() -> None:
    judge = OpenSourceModelJudge(endpoint_url="http://judge.invalid/api/generate")
    with patch(
        "app.modules.judging.model_judge.httpx.AsyncClient",
        _mock_model_reply("NOT SUPPORTED"),
    ):
        result = await judge.evaluate("Claim.", [])
    assert result.judgment == JudgeDecision.UNAVAILABLE
    assert result.metadata["status"] == "UNPARSEABLE_OUTPUT"


@pytest.mark.anyio
async def test_model_judge_parses_exact_verdict() -> None:
    judge = OpenSourceModelJudge(endpoint_url="http://judge.invalid/api/generate")
    with patch(
        "app.modules.judging.model_judge.httpx.AsyncClient",
        _mock_model_reply("CONTRADICTED"),
    ):
        result = await judge.evaluate("Claim.", [])
    assert result.judgment == JudgeDecision.CONTRADICTED


def test_orchestrator_wires_configured_model_judge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JUDGE_MODEL_ENDPOINT", "http://judge.invalid/api/generate")
    clear_settings_cache()
    try:
        judge = VerificationOrchestrator().tie_breaker_judge
        assert isinstance(judge, OpenSourceModelJudge)
    finally:
        monkeypatch.delenv("JUDGE_MODEL_ENDPOINT")
        clear_settings_cache()
    assert VerificationOrchestrator().tie_breaker_judge is None


# ---------------------------------------------------------------------------
# strict_consensus
# ---------------------------------------------------------------------------


def _eval(decision: JudgeDecision) -> JudgeEvaluationData:
    return JudgeEvaluationData(
        judge_id=uuid.uuid4(), judge_name=f"judge-{decision}", judgment=decision
    )


def test_strict_consensus_requires_agreement() -> None:
    evals = [
        _eval(JudgeDecision.CONTRADICTED),
        _eval(JudgeDecision.INSUFFICIENT_EVIDENCE),
    ]
    result = DisagreementEngine().arbitrate(evals, strict_consensus=True)
    assert result.consensus_verdict == VerdictType.UNKNOWN


def test_relaxed_consensus_accepts_decisive_over_abstaining_judge() -> None:
    evals = [
        _eval(JudgeDecision.CONTRADICTED),
        _eval(JudgeDecision.INSUFFICIENT_EVIDENCE),
    ]
    result = DisagreementEngine().arbitrate(evals, strict_consensus=False)
    assert result.consensus_verdict == VerdictType.CONTRADICTED
    assert result.degraded_evaluation is True


def test_relaxed_consensus_never_resolves_opposed_judgments() -> None:
    evals = [_eval(JudgeDecision.SUPPORTED), _eval(JudgeDecision.CONTRADICTED)]
    result = DisagreementEngine().arbitrate(evals, strict_consensus=False)
    assert result.consensus_verdict == VerdictType.UNKNOWN
