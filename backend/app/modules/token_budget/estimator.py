"""Deterministic token estimation and cost calculation."""

import re

# Fast regex for counting word and punctuation tokens
_TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


class TokenEstimator:
    """Calculates deterministic token approximations and versioned cost estimates."""

    @staticmethod
    def estimate_tokens(text: str | None) -> int:
        """Estimate token count deterministically without external API dependencies.

        Uses a blended heuristic: average of word/symbol regex matches and character
        length ratio (~3.8 characters per token), guaranteeing non-zero for
        non-empty text.
        """
        if not text or not text.strip():
            return 0

        stripped = text.strip()
        char_estimate = len(stripped) / 3.8
        token_matches = len(_TOKEN_PATTERN.findall(stripped))

        # Take the max of token matches and char estimate for safe reservation
        estimated = int(max(token_matches, char_estimate))
        return max(1, estimated)

    @staticmethod
    def calculate_cost(
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        pricing_map: dict[str, dict[str, float]] | None = None,
    ) -> float:
        """Estimate cost in USD using versioned model pricing per 1M tokens."""
        if not pricing_map:
            return 0.0

        # Match exact or partial model name
        # (e.g. "gpt-4o-mini-2024-07-18" -> "gpt-4o-mini")
        clean_model = model_name.lower().strip()
        matched_pricing = pricing_map.get("default", {"input": 0.20, "output": 0.80})

        for key, rates in pricing_map.items():
            if key in clean_model:
                matched_pricing = rates
                break

        input_rate_per_m = matched_pricing.get("input", 0.0)
        output_rate_per_m = matched_pricing.get("output", 0.0)

        cost = (input_tokens / 1_000_000.0) * input_rate_per_m + (
            output_tokens / 1_000_000.0
        ) * output_rate_per_m
        return round(cost, 6)
