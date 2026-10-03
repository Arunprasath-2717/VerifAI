"""Domain and result models for LLM execution."""

import re
from typing import Any

_CREDENTIAL_PATTERN = re.compile(
    r"(?:Bearer\s+[A-Za-z0-9_\-\.]+|sk-[A-Za-z0-9_\-\.]+|gsk_[A-Za-z0-9_\-\.]+|ci_live_[A-Za-z0-9_\-\.]+|AIzaSy[A-Za-z0-9_\-\.]+|key=[A-Za-z0-9_\-\.]+)",
    re.IGNORECASE,
)


def sanitize_credential_text(text: str | None) -> str | None:
    """Scrub sensitive API tokens and keys from error messages and logs."""
    if not text:
        return text
    return _CREDENTIAL_PATTERN.sub("[REDACTED_CREDENTIAL]", text)


class LLMExecutionResult:
    """Encapsulates the truthful outcome of a model execution."""

    def __init__(
        self,
        provider: str,
        model_name: str,
        prompt: str,
        response: str | None = None,
        status: str = "COMPLETED",  # COMPLETED, FAILED, UNAVAILABLE
        model_version: str | None = None,
        latency_ms: float | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.provider = provider
        self.model_name = model_name
        self.prompt = prompt
        self.response = response
        self.status = status
        self.model_version = model_version
        self.latency_ms = latency_ms
        self.error_code = error_code
        self.error_message = sanitize_credential_text(error_message)
        self.metadata = metadata or {}
