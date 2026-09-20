"""Tests for ContentClassifier: taxonomy categories and verification routing."""

import pytest

from app.modules.claims.classifier import ContentClassifier
from app.schemas.verification import ContentType, VerdictType


@pytest.fixture
def classifier() -> ContentClassifier:
    return ContentClassifier()


def test_classify_factual_statement(classifier: ContentClassifier) -> None:
    """Verify empirical statements are marked FACTUAL and routed for verification."""
    text = (
        "The boiling point of water at standard sea-level pressure "
        "is 100 degrees Celsius."
    )
    result = classifier.classify(text)

    assert result.content_type == ContentType.FACTUAL
    assert result.is_verifiable is True
    assert result.verdict is None
    assert result.is_calibrated is False
    assert result.calibration_status == "NOT_CALIBRATED"


def test_classify_opinion_statement(classifier: ContentClassifier) -> None:
    """Verify opinion statements are marked OPINION, exempt, and mapped to VIEWPOINT."""
    text = "In my opinion, chocolate ice cream is the best dessert ever made."
    result = classifier.classify(text)

    assert result.content_type == ContentType.OPINION
    assert result.is_verifiable is False
    assert result.verdict == VerdictType.VIEWPOINT
    assert "opinion" in result.explanation.lower()


def test_classify_prediction_statement(classifier: ContentClassifier) -> None:
    """Verify future statements are marked PREDICTION and mapped to FUTURE_LOOKING."""
    text = "Global temperatures will increase by two degrees by 2050."
    result = classifier.classify(text)

    assert result.content_type == ContentType.PREDICTION
    assert result.is_verifiable is False
    assert result.verdict == VerdictType.FUTURE_LOOKING
    assert "future-looking" in result.explanation.lower()


def test_classify_hypothetical_statement(classifier: ContentClassifier) -> None:
    """Verify conditional statements are marked HYPOTHETICAL and mapped to SCENARIO."""
    text = "If gravity were reversed, people would float into the stratosphere."
    result = classifier.classify(text)

    assert result.content_type == ContentType.HYPOTHETICAL
    assert result.is_verifiable is False
    assert result.verdict == VerdictType.SCENARIO


def test_classify_creative_statement(classifier: ContentClassifier) -> None:
    """Verify mythical statements are marked CREATIVE and mapped to CREATIVE."""
    text = "Once upon a time, a magical unicorn defended the enchanted forest."
    result = classifier.classify(text)

    assert result.content_type == ContentType.CREATIVE
    assert result.is_verifiable is False
    assert result.verdict == VerdictType.CREATIVE


def test_classify_instruction_statement(classifier: ContentClassifier) -> None:
    """Verify commands are marked INSTRUCTION and mapped to INCONCLUSIVE."""
    text = "Please install the python dependencies using pip."
    result = classifier.classify(text)

    assert result.content_type == ContentType.INSTRUCTION
    assert result.is_verifiable is False
    assert result.verdict == VerdictType.INCONCLUSIVE


def test_classify_empty_string(classifier: ContentClassifier) -> None:
    """Verify empty text defaults safely to FACTUAL without crashing."""
    result = classifier.classify("")
    assert result.content_type == ContentType.FACTUAL
    assert result.is_verifiable is True


# ---------------------------------------------------------------------------
# Regression tests: natural-language instruction detection (Phase 3 fix)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "Write a poem about the sky.",
        "Explain how this process works.",
        "Describe the steps required to complete this task.",
        "List the main ingredients for making bread.",
        "Summarize the key findings of the report.",
        "Create a table of the planets in the solar system.",
        "Please install the Python dependencies using pip.",
        "Generate a short story about a robot.",
        "Tell me about the history of Rome.",
        "Show how the algorithm handles edge cases.",
    ],
)
def test_classify_natural_language_instruction(
    classifier: ContentClassifier, text: str
) -> None:
    """Verify natural-language imperative sentences are classified INSTRUCTION."""
    result = classifier.classify(text)
    assert result.content_type == ContentType.INSTRUCTION, (
        f"Expected INSTRUCTION for {text!r}, got {result.content_type}"
    )
    assert result.is_verifiable is False
    assert result.verdict == VerdictType.INCONCLUSIVE


@pytest.mark.parametrize(
    "text",
    [
        "How do I install Python on Ubuntu?",
        "How can I improve my writing skills?",
        "How should I configure the database connection?",
        "How to create a virtual environment in Python?",
    ],
)
def test_classify_interrogative_how_to(
    classifier: ContentClassifier, text: str
) -> None:
    """Verify interrogative how-to questions are classified INSTRUCTION."""
    result = classifier.classify(text)
    assert result.content_type == ContentType.INSTRUCTION, (
        f"Expected INSTRUCTION for {text!r}, got {result.content_type}"
    )
    assert result.is_verifiable is False
    assert result.verdict == VerdictType.INCONCLUSIVE


@pytest.mark.parametrize(
    "text",
    [
        # These sentences contain instruction-adjacent words but are factual
        # assertions, not imperatives — they must NOT be mis-classified.
        "Scientists list nitrogen as the most abundant atmospheric gas.",
        "The manual describes the steps for installation.",
        "Researchers explain the mechanism of photosynthesis in detail.",
        "The Eiffel Tower was designed by Gustave Eiffel.",
        "Water boils at 100 degrees Celsius at sea level.",
    ],
)
def test_instruction_markers_do_not_misclassify_factual(
    classifier: ContentClassifier, text: str
) -> None:
    """Verify factual statements are not mis-routed as INSTRUCTION."""
    result = classifier.classify(text)
    assert result.content_type == ContentType.FACTUAL, (
        f"Expected FACTUAL for {text!r}, got {result.content_type}"
    )
    assert result.is_verifiable is True
