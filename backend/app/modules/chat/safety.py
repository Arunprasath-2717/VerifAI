"""Outbound inference safety gate.

Never forward or persist likely passwords, private keys, access tokens or
connection strings from prompts or previous conversation context. The same
sanitizer protects responses prior to further model calls and persistence.
Pattern rules are intentionally conservative and are not a DLP guarantee.
"""

from __future__ import annotations

import re

from app.core.errors import BadRequestError

# Match values, not mentions of credential concepts ("design a secret vault").
_SECRET = [
    re.compile(
        r"-----BEGIN (?:[A-Z ]* )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z ]* )?PRIVATE KEY-----",  # noqa: E501
        re.I,
    ),
    re.compile(
        r"\b(?:sk-(?:proj-|or-v1-)?|gsk_|nvapi-|gh[pousr]_|github_pat_|xox[baprs]-|AIzaSy|AKIA|ASIA|hf_|glpat-)[a-zA-Z0-9_\-]{12,}\b"  # noqa: E501
    ),
    re.compile(r"\bBearer\s+[A-Za-z0-9_.\-]{18,}\b", re.I),
    re.compile(
        r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqps?)://[^\s/@:]+:[^\s/@]+@",  # noqa: E501
        re.I,
    ),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(
        r"(?i)\b(?:api[_ -]?key|secret[_ -]?(?:key|token)?|access[_ -]?token|refresh[_ -]?token|"  # noqa: E501
        r"client[_ -]?secret|password|passwd|pwd|authorization|private[_ -]?key|session[_ -]?cookie)"  # noqa: E501
        r"\b\s*(?:[:=]|(?:is|equals)\s+)\s*[\"']?(?!<|your[-_ ]|example|placeholder|redacted|dummy)"  # noqa: E501
        r"[A-Za-z0-9+/=_:!@#$%*.-]{8,}",
    ),
]


def contains_credentials(value: str) -> bool:
    return bool(value and any(rule.search(value) for rule in _SECRET))


def assert_safe_outbound_prompt(value: str) -> None:
    if contains_credentials(value):
        # Never echo the detected secret or a snippet in an exception/log.
        raise BadRequestError(
            "Potential password, API key, access token or private key detected. "
            "Remove credentials before sending this prompt.",
            details={"field": "prompt", "reason": "SENSITIVE_CREDENTIAL"},
        )


def redact_credentials(value: str) -> str:
    """Redact generated output before saving, showing or reusing in synthesis."""
    if not value:
        return value
    for rule in _SECRET:
        value = rule.sub("[REDACTED_CREDENTIAL]", value)
    return value


def safe_context(value: str) -> str:
    """Drop an entire legacy message rather than forward partial credentials."""
    return "" if contains_credentials(value) else value
