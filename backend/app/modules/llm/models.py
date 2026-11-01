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
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        is_estimated_usage: bool = False,
        retry_count: int = 0,
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
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.is_estimated_usage = is_estimated_usage
        self.retry_count = retry_count

        # Reconcile usage metadata if passed in metadata dict
        usage_dict = self.metadata.get("usage", {})
        if usage_dict:
            if self.input_tokens is None:
                self.input_tokens = (
                    usage_dict.get("prompt_tokens")
                    or usage_dict.get("prompt_token_count")
                    or usage_dict.get("input_tokens")
                )
            if self.output_tokens is None:
                self.output_tokens = (
                    usage_dict.get("completion_tokens")
                    or usage_dict.get("candidates_token_count")
                    or usage_dict.get("output_tokens")
                )
