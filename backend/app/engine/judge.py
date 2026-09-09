"""LLM-as-judge — Phase 2D.

Compares a CLAIM against EVIDENCE from a single source and returns one of:

    ENTAILMENT   — evidence supports the claim
    CONTRADICTION — evidence conflicts with the claim
    ABSENT       — evidence insufficient to determine support/contradiction
    REFUSED      — judge cannot reliably perform the comparison

These labels are distinct from the final SUPPORT/CONTRADICT/UNKNOWN verdict.

ABSENT ≠ REFUSED ≠ a judge exception (JudgeCallError is an exception, not a label).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from app.engine.models import (
    ExtractedClaim,
    JudgeLabel,
    JudgeResult,
    ScoredSource,
)
from app.engine.providers import LLMProvider

logger = logging.getLogger("verifai.engine.judge")

# ---------------------------------------------------------------------------
# Prompt — strict, no chain-of-thought
# ---------------------------------------------------------------------------

_JUDGE_PROMPT = """\
SYSTEM:
You are an evidence-grounded claim verification judge.

Your task is to compare a CLAIM against the provided EVIDENCE.

Return exactly one label:

ENTAILMENT:
The evidence supports the claim.

CONTRADICTION:
The evidence conflicts with the claim.

ABSENT:
The evidence does not provide enough information to determine whether
the claim is supported or contradicted.

REFUSED:
You cannot reliably perform the comparison.

Rules:
1. Judge only from the supplied evidence.
2. Do not use outside knowledge.
3. Do not infer missing facts.
4. Do not treat source authority alone as proof.
5. A related topic is not sufficient evidence.
6. If the evidence does not directly support or contradict the claim, use ABSENT.
7. If the evidence is unsafe, malformed, or impossible to evaluate, use REFUSED.
8. Return valid structured JSON only.

CLAIM:
{claim}

EVIDENCE:
{evidence}

OUTPUT (JSON only):
{{
  "label": "ENTAILMENT | CONTRADICTION | ABSENT | REFUSED",
  "reason": "short explanation",
  "confidence": 0.0
}}
"""

_VALID_LABELS = {label.value for label in JudgeLabel}


class JudgeCallError(Exception):
    """Raised when the LLM call itself fails (network error, provider unavailable).

    This is NOT a JudgeLabel — it is a provider-level exception tracked
    separately in judge_error_count.
    """


def _parse_judge_response(raw: str, claim_id: str, source_url: str) -> JudgeResult:
    """Parse the LLM's JSON into a JudgeResult.

    Falls back to REFUSED when the response cannot be parsed, so that a
    malformed response is distinguished from a missing response (JudgeCallError).
    """
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    try:
        obj = json.loads(cleaned)
        label_str = str(obj.get("label", "")).upper().strip()
        if label_str not in _VALID_LABELS:
            raise ValueError(f"Unknown label: {label_str!r}")
        label = JudgeLabel(label_str)
        reason = str(obj.get("reason", "No reason provided"))[:500]
        confidence = float(obj.get("confidence", 0.5))
        confidence = min(1.0, max(0.0, confidence))
        return JudgeResult(
            label=label,
            reason=reason,
            confidence=confidence,
            source_url=source_url,
            claim_id=claim_id,
        )
    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        logger.warning(
            "Judge parse failed for claim %s / source %s: %s",
            claim_id, source_url[:80], exc,
        )
        return JudgeResult(
            label=JudgeLabel.REFUSED,
            reason="Malformed judge response",
            confidence=0.0,
            source_url=source_url,
            claim_id=claim_id,
        )


class Judge:
    """Compares a claim against evidence from a single source.

    Raises JudgeCallError on provider-level failures.
    Returns a JudgeResult with label REFUSED on parse failures.
    """

    def __init__(self, llm: Optional[LLMProvider] = None) -> None:
        self._llm = llm

    async def judge(
        self,
        claim: ExtractedClaim,
        scored_source: ScoredSource,
    ) -> JudgeResult:
        """Compare *claim* against *scored_source* and return a JudgeResult.

        Raises:
            JudgeCallError: When the LLM provider call itself fails.
        """
        if not self._llm:
            # No LLM configured — return ABSENT (insufficient evidence signal)
            return JudgeResult(
                label=JudgeLabel.ABSENT,
                reason="No LLM provider configured",
                confidence=0.0,
                source_url=scored_source.source.url,
                claim_id=claim.claim_id,
            )

        source = scored_source.source
        evidence_text = f"Title: {source.title}\n\n{source.snippet}"

        prompt = _JUDGE_PROMPT.format(
            claim=claim.text,
            evidence=evidence_text[:2000],  # guard against very long snippets
        )

        try:
            raw = await self._llm.generate(
                prompt, temperature=0.0, max_output_tokens=256
            )
        except Exception as exc:
            logger.error(
                "Judge LLM call failed for claim %s / source %s: %s",
                claim.claim_id, source.url[:80], exc,
            )
            raise JudgeCallError(str(exc)) from exc

        return _parse_judge_response(raw, claim.claim_id, source.url)
