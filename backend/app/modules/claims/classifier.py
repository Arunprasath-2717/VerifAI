"""Content classification service for claim taxonomy and routing."""

import re
from dataclasses import dataclass

from app.schemas.verification import ContentType, VerdictType


@dataclass(frozen=True)
class ClassificationResult:
    """Outcome of content classification for a single claim."""

    content_type: ContentType
    verdict: VerdictType | None
    is_verifiable: bool
    confidence: float | None
    is_calibrated: bool
    calibration_status: str
    explanation: str


class ContentClassifier:
    """Classifies claims into PRD content types and determines verification routing."""

    # Lexical markers for opinion and subjective viewpoint
    OPINION_MARKERS = re.compile(
        r"\b(?:i\s+(?:personally\s+)?(?:think|feel|believe|prefer|consider)|"
        r"in\s+my\s+view|in\s+my\s+opinion|in\s+our\s+opinion|in\s+my\s+viewpoint|"
        r"best|worst|greatest|terrible|wonderful|superior|inferior|should|ought|"
        r"tastiest|underrated|overrated|beautiful|ugly|breathtaking|uninspiring|"
        r"unjustified|pretentious|calming|rejuvenating|enjoyable|mediocre|unnatural|"
        r"the\s+most\s+(?:pleasant|relaxing|sophisticated|expressive|impressive)|"
        r"finest|serene|charming|cozy|welcoming|delightful)\b",
        re.IGNORECASE,
    )

    # Lexical markers for predictions and future-looking assertions
    PREDICTION_MARKERS = re.compile(
        r"\b(?:will\s+(?:be|occur|happen|increase|decrease|reach|drop|exceed|"
        r"solve|rise|replace|dominate|achieve|eradicate|handle|experience|"
        r"detect|revolutionize|make)|"
        r"expected\s+to|predicted\s+to|forecasted\s+to|projected\s+to|"
        r"by\s+20[3-9]\d|in\s+20[3-9]\d|"
        r"in\s+the\s+future|next\s+(?:decade|century|year|month))\b",
        re.IGNORECASE,
    )

    # Lexical markers for hypothetical and scenario conditional statements
    HYPOTHETICAL_MARKERS = re.compile(
        r"\b(?:if|imagine|suppose|supposing|assuming\s+that|were\s+to|what\s+if|"
        r"hypothetically|in\s+the\s+event\s+that|would\s+have\s+been)\b",
        re.IGNORECASE,
    )

    # Lexical markers for creative, mythical, or fictional expressions
    CREATIVE_MARKERS = re.compile(
        r"\b(?:once\s+upon\s+a\s+time|dragon|wizard|unicorn|magic\s+wand|"
        r"fictional|fairytale|legend\s+tells\s+of|in\s+a\s+galaxy\s+far\s+away)\b",
        re.IGNORECASE,
    )

    # Lexical markers for imperative commands and instruction (technical and
    # natural-language forms).  Two complementary patterns are used:
    #
    # INSTRUCTION_MARKERS: imperative sentences whose first content word is an
    #   action verb — both narrow technical verbs (install, run, click …) and
    #   broader natural-language imperatives (write, explain, describe, list …).
    #   The pattern matches from the start of the stripped text so that ordinary
    #   factual statements that happen to contain these words are not mis-routed
    #   (e.g. "Scientists list nitrogen as…" starts with "Scientists", not
    #   "list", so it falls through to FACTUAL).
    #
    # HOW_TO_MARKERS: interrogative instruction forms — "How do I …",
    #   "How can I …", "How should I …", "How to …".
    INSTRUCTION_MARKERS = re.compile(
        r"^(?:please\s+)?(?:"
        # Technical / procedural action verbs
        r"install|run|click|type|download|open|enter|press|execute|"
        r"navigate\s+to|configure|copy|paste|"
        # Natural-language imperative verbs
        r"write|create|generate|compose|draft|"
        r"explain|describe|summarize|summarise|outline|"
        r"list|enumerate|show|tell|give|provide|find|"
        r"help\s+me|translate|convert|calculate|compute|"
        r"draw|make|build|design|develop|"
        r"format|implement|review|set\s+up"
        r")\b",
        re.IGNORECASE,
    )

    # Interrogative how-to instruction forms
    HOW_TO_MARKERS = re.compile(
        r"^\s*how\s+(?:do|can|should|would|to)\b",
        re.IGNORECASE,
    )

    def classify(self, claim_text: str) -> ClassificationResult:
        """Classify a single claim and return its verification routing disposition."""
        text = claim_text.strip()

        # 1. Check for creative/fictional markers
        if self.CREATIVE_MARKERS.search(text):
            return ClassificationResult(
                content_type=ContentType.CREATIVE,
                verdict=None,
                is_verifiable=False,
                confidence=None,
                is_calibrated=False,
                calibration_status="NOT_CALIBRATED",
                explanation=(
                    "Claim classified as creative/fictional narrative; "
                    "exempt from empirical verification."
                ),
            )

        # 2. Check for imperative instruction/how-to (covers both command-form
        #    and interrogative how-to forms)
        if self.INSTRUCTION_MARKERS.search(text) or self.HOW_TO_MARKERS.search(text):
            return ClassificationResult(
                content_type=ContentType.INSTRUCTION,
                verdict=None,
                is_verifiable=False,
                confidence=None,
                is_calibrated=False,
                calibration_status="NOT_CALIBRATED",
                explanation=(
                    "Claim classified as procedural instruction; requires "
                    "execution/sandbox check rather than factual verification."
                ),
            )

        # 3. Check for hypothetical/conditional scenario
        if self.HYPOTHETICAL_MARKERS.search(text):
            return ClassificationResult(
                content_type=ContentType.HYPOTHETICAL,
                verdict=None,
                is_verifiable=False,
                confidence=None,
                is_calibrated=False,
                calibration_status="NOT_CALIBRATED",
                explanation=(
                    "Claim classified as hypothetical conditional; evaluated "
                    "as scenario without empirical truth value."
                ),
            )

        # 4. Check for future predictions
        if self.PREDICTION_MARKERS.search(text):
            return ClassificationResult(
                content_type=ContentType.PREDICTION,
                verdict=None,
                is_verifiable=False,
                confidence=None,
                is_calibrated=False,
                calibration_status="NOT_CALIBRATED",
                explanation=(
                    "Claim classified as future-looking prediction; empirical "
                    "truth cannot be verified at present."
                ),
            )

        # 5. Check for subjective opinion
        if self.OPINION_MARKERS.search(text):
            return ClassificationResult(
                content_type=ContentType.OPINION,
                verdict=None,
                is_verifiable=False,
                confidence=None,
                is_calibrated=False,
                calibration_status="NOT_CALIBRATED",
                explanation=(
                    "Claim classified as subjective opinion/viewpoint; "
                    "non-verifiable as an empirical fact."
                ),
            )

        # 6. Default: Factual statement
        return ClassificationResult(
            content_type=ContentType.FACTUAL,
            verdict=None,  # Verdict determined downstream via retrieval & judging
            is_verifiable=True,
            confidence=None,
            is_calibrated=False,
            calibration_status="NOT_CALIBRATED",
            explanation="Claim asserts empirical, verifiable propositional facts.",
        )
