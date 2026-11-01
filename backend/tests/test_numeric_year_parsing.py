"""Regression: fractional measurements must never be parsed as calendar years."""

from app.modules.judging.text_analysis import check_year_conflict


def test_decimal_with_four_characters_does_not_crash_year_check() -> None:
    assert (
        check_year_conflict(
            "The event occurred in 1969.",
            "In 2024, the temperature reached 29.5 degrees.",
        )
        is None
    )


def test_matching_year_is_not_a_contradiction() -> None:
    assert (
        check_year_conflict(
            "The event occurred in 1969.",
            "The event occurred in 1969 at 29.5 degrees.",
        )
        is None
    )
