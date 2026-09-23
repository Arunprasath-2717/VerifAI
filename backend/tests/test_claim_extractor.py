"""Tests for DeterministicClaimExtractor: character offset invariants and edge cases."""

import pytest

from app.modules.claims.extractor import DeterministicClaimExtractor


@pytest.fixture
def extractor() -> DeterministicClaimExtractor:
    return DeterministicClaimExtractor()


def test_single_claim_extraction_offsets(
    extractor: DeterministicClaimExtractor,
) -> None:
    """Verify offset invariant text[start:end] == claim_text for single sentence."""
    text = "Water is composed of hydrogen and oxygen."
    claims = extractor.extract(text)

    assert len(claims) == 1
    c = claims[0]
    assert c.index == 0
    assert c.text == "Water is composed of hydrogen and oxygen"
    assert c.start_offset == 0
    assert c.end_offset == len("Water is composed of hydrogen and oxygen")
    # INVARIANT
    assert text[c.start_offset : c.end_offset] == c.text


def test_multi_claim_extraction_offsets(extractor: DeterministicClaimExtractor) -> None:
    """Verify offset invariant for multiple sentences separated by punctuation."""
    text = "Paris is the capital of France. Apollo 11 landed on the Moon in 1969."
    claims = extractor.extract(text)

    assert len(claims) == 2
    for c in claims:
        assert c.text == text[c.start_offset : c.end_offset]
        assert len(c.text) > 0

    assert claims[0].index == 0
    assert claims[0].text == "Paris is the capital of France"
    assert claims[1].index == 1
    assert claims[1].text == "Apollo 11 landed on the Moon in 1969"


def test_numbered_list_claims(extractor: DeterministicClaimExtractor) -> None:
    """Verify extraction handles numbered lists while preserving exact slice offsets."""
    text = "1. Mars is the fourth planet from the Sun. 2. Jupiter is the largest."
    claims = extractor.extract(text)

    assert len(claims) == 2
    for c in claims:
        assert text[c.start_offset : c.end_offset] == c.text


def test_empty_and_whitespace_input(extractor: DeterministicClaimExtractor) -> None:
    """Verify empty or whitespace-only input returns empty claim list."""
    assert extractor.extract("") == []
    assert extractor.extract("    \n\t  ") == []


def test_max_claims_limit(extractor: DeterministicClaimExtractor) -> None:
    """Verify max_claims limit is strictly respected."""
    text = "One. Two. Three. Four. Five. Six."
    claims = extractor.extract(text, max_claims=3)

    assert len(claims) == 3
    for c in claims:
        assert text[c.start_offset : c.end_offset] == c.text


def test_leading_trailing_whitespace_and_newlines(
    extractor: DeterministicClaimExtractor,
) -> None:
    """Verify extraction handles leading/trailing newlines and internal tabs cleanly."""
    text = "  \n\n Albert Einstein proposed the theory of relativity.   \n"
    claims = extractor.extract(text)

    assert len(claims) == 1
    c = claims[0]
    assert c.text == "Albert Einstein proposed the theory of relativity"
    assert text[c.start_offset : c.end_offset] == c.text


def test_repeated_sentences_distinct_offsets(
    extractor: DeterministicClaimExtractor,
) -> None:
    """Verify repeated sentences have distinct, strictly monotonic start/end offsets."""
    text = "The sky is blue. The sky is blue."
    claims = extractor.extract(text)

    assert len(claims) == 2
    assert claims[0].text == "The sky is blue"
    assert claims[1].text == "The sky is blue"
    assert claims[0].start_offset < claims[1].start_offset
    assert claims[0].end_offset <= claims[1].start_offset
    for c in claims:
        assert text[c.start_offset : c.end_offset] == c.text


def test_unicode_and_special_quotes(extractor: DeterministicClaimExtractor) -> None:
    """Verify extraction handles non-ASCII characters and typographic quotes."""
    text = "Marie Curie découvrit le radium. “Science is wonderful,” she stated."
    claims = extractor.extract(text)

    assert len(claims) >= 1
    for c in claims:
        assert text[c.start_offset : c.end_offset] == c.text
