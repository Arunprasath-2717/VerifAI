"""Local open-source model judge adapter with honest unavailability reporting."""

import uuid

import httpx

from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging.interface import BaseJudge
from app.modules.judging.models import JudgeEvaluationData
from app.modules.judging.prompt import (
    PROMPT_TEMPLATE_VERSION,
    build_judge_prompt,
)
from app.schemas.verification import JudgeDecision


class OpenSourceModelJudge(BaseJudge):
    """Adapter for local open-source LLM judge (e.g. Ollama or vLLM).

    Enforces deterministic evaluation:
    - Default temperature: 0.0
    - Default seed: 42 (when supported by provider)
    - Records prompt version, prompt hash, provider, and seed support status.
    - Preserves research integrity: if endpoint is unreachable or not configured,
      honestly reports UNAVAILABLE without fabricating model outputs.
    """

    def __init__(
        self,
        endpoint_url: str | None = None,
        model_name: str = "llama3:8b",
        name: str = "Judge-LocalLLM",
        provider: str = "ollama",
        temperature: float = 0.0,
        seed: int = 42,
        supports_seeds: bool = True,
    ) -> None:
        self._endpoint_url = endpoint_url
        self._model_name = model_name
        self._name = name
        self._provider = provider
        self.temperature = temperature
        self.seed = seed
        self.supports_seeds = supports_seeds

    @property
    def name(self) -> str:
        return self._name

    @property
    def provider(self) -> str:
        return self._provider

    async def evaluate(
        self,
        claim_text: str,
        evidence_items: list[RetrievedEvidenceItem],
    ) -> JudgeEvaluationData:
        """Execute model evaluation with prompt isolation and deterministic settings."""
        prompt_text, prompt_hash = build_judge_prompt(claim_text, evidence_items)

        config_metadata = {
            "provider": self._provider,
            "model": self._model_name,
            "temperature": self.temperature,
            "seed": self.seed if self.supports_seeds else None,
            "supports_seeds": self.supports_seeds,
            "seed_support_status": "SUPPORTED"
            if self.supports_seeds
            else "UNSUPPORTED",
            "prompt_template_version": PROMPT_TEMPLATE_VERSION,
            "prompt_hash": prompt_hash,
            "parser_version": "v1.0",
        }

        if not self._endpoint_url:
            return JudgeEvaluationData(
                judge_id=uuid.uuid4(),
                judge_name=self.name,
                model_version=self._model_name,
                judgment=JudgeDecision.UNAVAILABLE,
                confidence=None,
                rationale=(
                    "Local model endpoint is not configured in current environment."
                ),
                evidence_references=[],
                metadata={"status": "NOT_CONFIGURED", **config_metadata},
            )

        # Attempt probe of configured local endpoint
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                payload = {
                    "model": self._model_name,
                    "prompt": prompt_text,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        **({"seed": self.seed} if self.supports_seeds else {}),
                    },
                }
                resp = await client.post(self._endpoint_url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data.get("response", "").strip().upper()
                    if "SUPPORTED" in raw_text:
                        judgment = JudgeDecision.SUPPORTED
                    elif "CONTRADICTED" in raw_text:
                        judgment = JudgeDecision.CONTRADICTED
                    else:
                        judgment = JudgeDecision.UNKNOWN

                    return JudgeEvaluationData(
                        judge_id=uuid.uuid4(),
                        judge_name=self.name,
                        model_version=self._model_name,
                        judgment=judgment,
                        confidence=None,
                        rationale=f"Model output: {raw_text[:200]}",
                        evidence_references=[str(i.id) for i in evidence_items],
                        metadata={
                            "status": "LIVE_INFERENCE_SUCCESS",
                            **config_metadata,
                        },
                    )
        except Exception as exc:
            return JudgeEvaluationData(
                judge_id=uuid.uuid4(),
                judge_name=self.name,
                model_version=self._model_name,
                judgment=JudgeDecision.UNAVAILABLE,
                confidence=None,
                rationale=f"Local model endpoint unreachable ({type(exc).__name__}).",
                evidence_references=[],
                metadata={"status": "ENDPOINT_UNREACHABLE", **config_metadata},
            )

        return JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name=self.name,
            model_version=self._model_name,
            judgment=JudgeDecision.UNAVAILABLE,
            confidence=None,
            rationale="Local model returned unexpected response.",
            evidence_references=[],
            metadata={"status": "UNEXPECTED_RESPONSE", **config_metadata},
        )
