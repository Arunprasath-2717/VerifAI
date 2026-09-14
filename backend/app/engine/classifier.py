"""Domain classifier — Phase 2D.

Classifies a claim into the project's controlled domain vocabulary.
Classification improves search query routing in later phases.

Failure policy: always return Domain.GENERAL rather than raising.
Classification failure must NOT fail the overall verification.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from app.engine.models import Domain, ExtractedClaim
from app.engine.providers import LLMProvider

logger = logging.getLogger("verifai.engine.classifier")

# ---------------------------------------------------------------------------
# Allowed domain values for validation
# ---------------------------------------------------------------------------

_DOMAIN_VALUES = {d.value for d in Domain}

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_CLASSIFICATION_PROMPT = """\
You are a claim domain classifier.

Given the CLAIM, choose the single most appropriate domain from this list:

GENERAL | SCIENCE | TECHNOLOGY | MEDICAL | FINANCE | POLITICS | HISTORY | LAW | OTHER

Rules:
1. Return ONLY valid JSON — no prose, no markdown.
2. If uncertain, use GENERAL.

OUTPUT FORMAT:
{{"domain": "DOMAIN_VALUE", "reason": "one-sentence explanation"}}

CLAIM:
{claim_text}
"""


def _parse_domain(raw: str) -> Domain:
    """Parse the LLM JSON response into a Domain.

    Returns Domain.GENERAL on any parse or value error.
    """
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    try:
        obj = json.loads(cleaned)
        value = str(obj.get("domain", "GENERAL")).upper()
        if value in _DOMAIN_VALUES:
            return Domain(value)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning("Domain classification parse failed: %s", exc)
    return Domain.GENERAL


class DomainClassifier:
    """Classifies a claim into a controlled domain.

    When *llm* is ``None``, returns Domain.GENERAL for every claim.
    """

    def __init__(self, llm: Optional[LLMProvider] = None) -> None:
        self._llm = llm

    async def classify(self, claim: ExtractedClaim) -> Domain:
        """Return the domain classification for *claim*.

        Never raises; any failure yields Domain.GENERAL.
        """
        if not self._llm:
            return Domain.GENERAL

        prompt = _CLASSIFICATION_PROMPT.format(claim_text=claim.text)
        try:
            raw = await self._llm.generate(prompt, temperature=0.0, max_output_tokens=128)
            return _parse_domain(raw)
        except Exception as exc:
            logger.warning(
                "Domain classification failed for claim %s: %s", claim.claim_id, exc
            )
            return Domain.GENERAL
