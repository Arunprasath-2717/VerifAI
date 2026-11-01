"""Detect instruction-override attempts inside untrusted claim and evidence text.

Detection is advisory: it flags, it does not block. Legitimate documents can
quote these phrases, so a hit is recorded for review while prompt isolation
(delimiter escaping in prompt.py) does the actual containment.
"""

from __future__ import annotations

import re

# Each category is a narrow, high-signal pattern. Keep them specific: broad
# patterns would flag ordinary prose and make the signal useless.
_PATTERNS: dict[str, re.Pattern[str]] = {
    "instruction_override": re.compile(
        r"\b(?:ignore|disregard|forget)\s+(?:all\s+|any\s+|the\s+|your\s+)?"
        r"(?:previous|prior|above|earlier|preceding)\s+(?:instructions?|prompts?|rules?)\b",
        re.IGNORECASE,
    ),
    "role_reassignment": re.compile(
        r"\byou\s+are\s+now\s+(?:in\s+)?(?:a\s+|an\s+|the\s+)?"
        r"(?:developer|admin|maintenance|debug|jailbreak|unrestricted)\b",
        re.IGNORECASE,
    ),
    "verdict_forcing": re.compile(
        # Only the leading verbs are case-insensitive; the verdict tokens must be
        # uppercase so ordinary prose ("must return false") is not flagged.
        r"\b(?i:always|must)\s+(?i:return|declare|output|respond\s+with)\s+"
        r"(?:verdict\s+)?(?:SUPPORTED|CONTRADICTED)\b"
    ),
    "prompt_exfiltration": re.compile(
        r"\b(?:print|reveal|show|repeat|output)\s+(?:your\s+|the\s+)?"
        r"(?:system\s+prompt|hidden\s+instructions|developer\s+message)\b",
        re.IGNORECASE,
    ),
    "delimiter_escape": re.compile(
        r"</?\s*(?:system|assistant|untrusted_claim|untrusted_evidence)\s*>",
        re.IGNORECASE,
    ),
}


def detect_injection_markers(text: str) -> list[str]:
    """Return the sorted categories of injection markers found in ``text``."""
    if not text:
        return []
    return sorted(name for name, pattern in _PATTERNS.items() if pattern.search(text))


def has_injection_markers(text: str) -> bool:
    return bool(detect_injection_markers(text))
