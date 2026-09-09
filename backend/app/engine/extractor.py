"""Claim extractor — Phase 2D.

Splits a user-supplied claim text into one or more discrete factual claims
using the configured LLM provider.

When no LLM is available the input is treated as a single claim verbatim
(safe fallback — never fabricates claims).
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import List, Optional

from app.engine.models import ExtractedClaim
from app.engine.providers import LLMProvider

logger = logging.getLogger("verifai.engine.extractor")

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_EXTRACTION_PROMPT = """\
You are a claim-extraction assistant.

Given the INPUT TEXT, identify all distinct factual claims that can be
independently verified.

Rules:
1. Return ONLY the claims present in the input — do not invent new ones.
2. If the entire input is already one simple factual statement, return it
   as a single claim.
3. Do not rewrite or paraphrase the claim text significantly.
4. Return valid JSON only — no prose, no markdown, no explanation.

OUTPUT FORMAT:
[
  {{"claim_id": "claim_1", "text": "...", "position": 1}},
  {{"claim_id": "claim_2", "text": "...", "position": 2}}
]

INPUT TEXT:
{claim_text}
"""


def _parse_llm_claims(raw: str, fallback_text: str) -> List[ExtractedClaim]:
    """Parse the LLM's JSON response into ExtractedClaim objects.

    Falls back to treating the original text as a single claim on any
    parse error so that verification always continues.
    """
    # Strip markdown code fences if the model wraps the JSON
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    try:
        items = json.loads(cleaned)
        if not isinstance(items, list) or not items:
            raise ValueError("Expected a non-empty JSON array")
        claims = []
        for item in items:
            if not isinstance(item, dict) or "text" not in item:
                continue
            pos = int(item.get("position", len(claims) + 1))
            cid = item.get("claim_id", f"claim_{pos}")
            claims.append(ExtractedClaim(claim_id=cid, text=str(item["text"]), position=pos))
        if claims:
            return claims
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        logger.warning("Claim extraction parse failed: %s", exc)

    return [ExtractedClaim(claim_id="claim_1", text=fallback_text, position=1)]


class ClaimExtractor:
    """Extracts verifiable factual claims from raw text.

    When *llm* is ``None`` (no API key configured) the input is returned
    as a single claim without any LLM call.
    """

    def __init__(self, llm: Optional[LLMProvider] = None) -> None:
        self._llm = llm

    async def extract(self, claim_text: str) -> List[ExtractedClaim]:
        """Return a list of extracted factual claims.

        Always returns at least one claim (the original text) — never empty.
        Never raises; any LLM failure falls back to the single-claim path.
        """
        if not self._llm:
            logger.debug("No LLM configured — treating input as single claim")
            return [ExtractedClaim(claim_id="claim_1", text=claim_text, position=1)]

        prompt = _EXTRACTION_PROMPT.format(claim_text=claim_text)
        try:
            raw = await self._llm.generate(prompt, temperature=0.0, max_output_tokens=512)
            return _parse_llm_claims(raw, claim_text)
        except Exception as exc:
            logger.error("Claim extraction LLM call failed: %s", exc)
            return [ExtractedClaim(claim_id="claim_1", text=claim_text, position=1)]
