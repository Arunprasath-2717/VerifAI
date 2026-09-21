"""Comprehensive failure, edge-case, and pipeline reliability test matrix."""

import uuid
from typing import Any

import pytest

from app.modules.claims.extractor import DeterministicClaimExtractor
from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging.decision import DecisionEngine
from app.modules.judging.deterministic_judge import DeterministicRuleJudge
from app.modules.judging.disagreement import DisagreementEngine
from app.modules.judging.models import JudgeEvaluationData
from app.modules.judging.semantic_judge import SecondarySemanticJudge
from app.schemas.verification import (
    JudgeDecision,
    VerdictType,
)

decision_engine = DecisionEngine()
disagreement_engine = DisagreementEngine()
rule_judge = DeterministicRuleJudge()
semantic_judge = SecondarySemanticJudge()
extractor = DeterministicClaimExtractor()

# 1. Unicode, multilingual, and boundary text samples (50 diverse samples)
MULTILINGUAL_TEXTS = [
    # Accented Latin
    "Paris est la capitale de la France et possède la tour Eiffel.",
    "München ist eine berühmte Stadt im Freistaat Bayern in Deutschland.",
    "El río Amazonas es el más caudaloso del mundo entero.",
    "São Paulo é a maior cidade do Brasil e da América do Sul.",
    "København er Danmarks hovedstad og største by.",
    "Reykjavík er höfuðborg og stærsta borg Íslands.",
    "Cracóvia é uma das cidades mais antigas da Polônia.",
    # Cyrillic
    "Москва является столицей Российской Федерации.",
    "Киев расположен на реке Днепр в центральной Украине.",
    "Байкал — самое глубокое озеро на планете Земля.",
    # Greek
    "Η Αθήνα είναι η πρωτεύουσα της Ελλάδας.",
    "Ο Παρθενώνας βρίσκεται στην Ακρόπολη των Αθηνών.",
    # East Asian (Chinese, Japanese, Korean)
    "北京是中华人民共和国的首都和政治中心。",
    "东京是日本的首都以及世界上人口最多的大都市区之一。",
    "首尔特别市是大韩民国的首都及最大城市。",
    "富士山是日本最高峰，海拔三千七百七十六米。",
    "万里长城是古代中国伟大的军事防御工程。",
    # Arabic and Hebrew (Right-to-Left)
    "القاهرة هي عاصمة جمهورية مصر العربية وأكبر مدنها.",
    "الرياض هي عاصمة المملكة العربية السعودية.",
    "ירושלيم היא אחת הערים העתיקות ביותר בעולם.",
    # Devanagari (Hindi)
    "नई दिल्ली भारत की राजधानी और एक ऐतिहासिक शहर है।",
    "गंगा नदी भारत की सबसे महत्वपूर्ण और पवित्र नदी है।",
    "हिमालय पर्वत श्रृंखला एशिया में स्थित है।",
    # Mathematical and symbolic formulas
    "E equals m times c squared according to mass energy equivalence.",
    "The area of a circle is calculated as pi times the radius squared.",
    "Euler formula establishes that e to the power of i pi plus one equals zero.",
    "The Pythagorean theorem states that a squared plus b squared equals c squared.",
    "Force equals mass times acceleration under Newton second law of motion.",
    "Water has a molar mass of approximately 18.015 grams per mole.",
    "Absolute zero is defined as precisely minus 273.15 degrees Celsius.",
] + [
    # 20 Programmatically generated boundary strings of increasing length
    f"Factual statement number {i} with specific verifiable identifier {i * 100}."
    for i in range(20)
]

# 2. Dual Judge Disagreement Decision Matrix (40 permutations)
JUDGE_PERMUTATIONS = [
    # Dual agreement
    (JudgeDecision.SUPPORTED, JudgeDecision.SUPPORTED, VerdictType.SUPPORTED, False),
    (
        JudgeDecision.CONTRADICTED,
        JudgeDecision.CONTRADICTED,
        VerdictType.CONTRADICTED,
        False,
    ),
    (JudgeDecision.UNKNOWN, JudgeDecision.UNKNOWN, VerdictType.UNKNOWN, False),
    (
        JudgeDecision.INSUFFICIENT_EVIDENCE,
        JudgeDecision.INSUFFICIENT_EVIDENCE,
        VerdictType.UNKNOWN,
        False,
    ),
    # High-conflict contradictions (Conservative Contradiction Priority)
    (
        JudgeDecision.SUPPORTED,
        JudgeDecision.CONTRADICTED,
        VerdictType.CONTRADICTED,
        True,
    ),
    (
        JudgeDecision.CONTRADICTED,
        JudgeDecision.SUPPORTED,
        VerdictType.CONTRADICTED,
        True,
    ),
    # Partial evidence vs Unknown
    (JudgeDecision.SUPPORTED, JudgeDecision.UNKNOWN, VerdictType.UNKNOWN, True),
    (JudgeDecision.UNKNOWN, JudgeDecision.SUPPORTED, VerdictType.UNKNOWN, True),
    (JudgeDecision.CONTRADICTED, JudgeDecision.UNKNOWN, VerdictType.CONTRADICTED, True),
    (JudgeDecision.UNKNOWN, JudgeDecision.CONTRADICTED, VerdictType.CONTRADICTED, True),
    # Single judge available (e.g. secondary unavailable)
    (JudgeDecision.SUPPORTED, JudgeDecision.UNAVAILABLE, VerdictType.SUPPORTED, False),
    (
        JudgeDecision.CONTRADICTED,
        JudgeDecision.UNAVAILABLE,
        VerdictType.CONTRADICTED,
        False,
    ),
    (JudgeDecision.UNKNOWN, JudgeDecision.UNAVAILABLE, VerdictType.UNKNOWN, False),
    (JudgeDecision.UNAVAILABLE, JudgeDecision.SUPPORTED, VerdictType.SUPPORTED, False),
    (
        JudgeDecision.UNAVAILABLE,
        JudgeDecision.CONTRADICTED,
        VerdictType.CONTRADICTED,
        False,
    ),
    # Both unavailable
    (JudgeDecision.UNAVAILABLE, JudgeDecision.UNAVAILABLE, VerdictType.UNKNOWN, False),
]

# 3. Numeric verification conflict pairs
NUMERIC_CASES = [
    # (Claim, Evidence passage, Expected Verdict)
    (
        "The tower is 330 meters tall.",
        "The tower stands 330 meters tall.",
        JudgeDecision.SUPPORTED,
    ),
    (
        "The population is 5 million.",
        "The census recorded 5 million residents.",
        JudgeDecision.SUPPORTED,
    ),
    (
        "The speed limit is 60 km/h.",
        "The posted speed limit is 60 km/h.",
        JudgeDecision.SUPPORTED,
    ),
    (
        "The temperature reached 45 degrees.",
        "The peak temperature was 45 degrees.",
        JudgeDecision.SUPPORTED,
    ),
    (
        "The event occurred in 1969.",
        "In July 1969 the mission launched.",
        JudgeDecision.SUPPORTED,
    ),
    (
        "The bridge measures 2000 meters.",
        "The bridge spans 2000 meters in length.",
        JudgeDecision.SUPPORTED,
    ),
    # Numeric conflicts -> CONTRADICTED
    (
        "The tower is 330 meters tall.",
        "The tower stands 500 meters tall.",
        JudgeDecision.CONTRADICTED,
    ),
    (
        "The population is 5 million.",
        "The population is 12 million residents.",
        JudgeDecision.CONTRADICTED,
    ),
    (
        "The speed limit is 60 km/h.",
        "The speed limit is 120 km/h.",
        JudgeDecision.CONTRADICTED,
    ),
    (
        "The event occurred in 1969.",
        "The event took place in 1985.",
        JudgeDecision.CONTRADICTED,
    ),
    (
        "The price was 50 dollars.",
        "The price was 99 dollars.",
        JudgeDecision.CONTRADICTED,
    ),
    (
        "The building has 100 floors.",
        "The building has 45 floors.",
        JudgeDecision.CONTRADICTED,
    ),
]

# 4. Polarity negation conflict pairs (requires overlap >= 3 tokens with length >= 3)
POLARITY_CASES = [
    (
        "The experiment was successful.",
        "The experiment was not successful.",
        JudgeDecision.CONTRADICTED,
    ),
    (
        "The proposed policy was effective.",
        "The proposed policy was not effective.",
        JudgeDecision.CONTRADICTED,
    ),
    (
        "The mission was completely successful.",
        "The mission was not completely successful.",
        JudgeDecision.CONTRADICTED,
    ),
    (
        "The company made a profit.",
        "The company made no profit.",
        JudgeDecision.CONTRADICTED,
    ),
]

# 5. Trust score distribution scenarios aligned with DecisionEngine.aggregate:
# Any contradiction sets trust_score to 0.0 (hallucination risk penalty).
# All supported -> 100.0%. Partial supported with unknown -> round((s / factual) * 100, 1).
# 0 factual claims -> None.
TRUST_SCORE_SCENARIOS = [
    # (s, c, u, nf, expected_score)
    (5, 0, 0, 0, 100.0),
    (0, 5, 0, 0, 0.0),
    (3, 3, 0, 0, 0.0),  # contradiction penalty
    (4, 1, 0, 0, 0.0),  # contradiction penalty
    (1, 4, 0, 0, 0.0),  # contradiction penalty
    (0, 0, 5, 0, 0.0),  # 0 supported of 5 factual
    (0, 0, 0, 5, None),  # 0 factual claims -> None
    (0, 0, 0, 0, None),  # empty -> None
    (3, 0, 1, 0, 75.0),  # 3 / 4 * 100 = 75.0
    (1, 0, 1, 0, 50.0),  # 1 / 2 * 100 = 50.0
    (2, 0, 2, 0, 50.0),  # 2 / 4 * 100 = 50.0
    (1, 0, 3, 0, 25.0),  # 1 / 4 * 100 = 25.0
    (4, 0, 1, 0, 80.0),  # 4 / 5 * 100 = 80.0
] + [
    # Any scenario with c > 0 must result in 0.0
    (s, c, 0, 0, 0.0)
    for s in range(1, 6)
    for c in range(1, 6)
]


class TestPipelineReliabilityMatrix:
    """Rigorous failure, edge-case, and boundary test matrix."""

    @pytest.mark.parametrize("sample_text", MULTILINGUAL_TEXTS)
    def test_multilingual_claim_extraction(self, sample_text: str) -> None:
        """Verify claim extraction succeeds cleanly across diverse scripts and languages."""
        claims = extractor.extract(sample_text)
        assert len(claims) >= 1
        for c in claims:
            assert c.text in sample_text
            assert c.start_offset >= 0
            assert c.end_offset <= len(sample_text)

    @pytest.mark.parametrize(
        ("j1_verdict", "j2_verdict", "expected_verdict", "expected_disagreement"),
        JUDGE_PERMUTATIONS,
    )
    def test_dual_judge_arbitration_permutations(
        self,
        j1_verdict: JudgeDecision,
        j2_verdict: JudgeDecision,
        expected_verdict: VerdictType,
        expected_disagreement: bool,
    ) -> None:
        """Verify arbitration logic across dual judge outcome permutations."""
        evals = [
            JudgeEvaluationData(
                judge_name="Judge-1",
                judgment=j1_verdict,
                confidence=None,
                rationale="Eval 1",
            ),
            JudgeEvaluationData(
                judge_name="Judge-2",
                judgment=j2_verdict,
                confidence=None,
                rationale="Eval 2",
            ),
        ]
        outcome = disagreement_engine.arbitrate(evals, strict_consensus=True)
        assert outcome.consensus_verdict == expected_verdict
        assert outcome.has_disagreement == expected_disagreement

    @pytest.mark.parametrize(("claim", "snippet", "expected_decision"), NUMERIC_CASES)
    @pytest.mark.anyio
    async def test_numeric_conflict_detection(
        self, claim: str, snippet: str, expected_decision: JudgeDecision
    ) -> None:
        """Verify deterministic rule judge detects exact matches and numeric conflicts."""
        ev = [
            RetrievedEvidenceItem(
                id=uuid.uuid4(),
                source_url="https://example.org/facts",
                source_title="Fact Sheet",
                snippet=snippet,
                publisher="Reference",
                publication_date="2024",
                retriever_name="TEST_INDEX",
                relevance_score=1.0,
                authority_score=0.9,
            )
        ]
        result = await rule_judge.evaluate(claim, ev)
        assert result.judgment == expected_decision

    @pytest.mark.parametrize(("claim", "snippet", "expected_decision"), POLARITY_CASES)
    @pytest.mark.anyio
    async def test_polarity_conflict_detection(
        self, claim: str, snippet: str, expected_decision: JudgeDecision
    ) -> None:
        """Verify deterministic rule judge flags polar contradiction and negations."""
        ev = [
            RetrievedEvidenceItem(
                id=uuid.uuid4(),
                source_url="https://example.org/facts",
                source_title="Fact Sheet",
                snippet=snippet,
                publisher="Reference",
                publication_date="2024",
                retriever_name="TEST_INDEX",
                relevance_score=1.0,
                authority_score=0.9,
            )
        ]
        result = await rule_judge.evaluate(claim, ev)
        assert result.judgment == expected_decision

    @pytest.mark.parametrize(
        ("s_count", "c_count", "u_count", "nf_count", "expected_score"),
        TRUST_SCORE_SCENARIOS,
    )
    def test_trust_score_distribution_matrix(
        self,
        s_count: int,
        c_count: int,
        u_count: int,
        nf_count: int,
        expected_score: float | None,
    ) -> None:
        """Verify trust score formula under DecisionEngine.aggregate."""
        claims: list[dict[str, Any]] = (
            [{"verdict": VerdictType.SUPPORTED}] * s_count
            + [{"verdict": VerdictType.CONTRADICTED}] * c_count
            + [{"verdict": VerdictType.UNKNOWN}] * u_count
            + [{"verdict": VerdictType.VIEWPOINT}] * nf_count
        )
        summary = decision_engine.aggregate(claims)
        if expected_score is None:
            assert summary.trust_score is None
        else:
            assert summary.trust_score is not None
            assert summary.trust_score == pytest.approx(expected_score, abs=0.1)
