"""Local open-source model judge adapter with honest unavailability reporting."""

import uuid

import httpx

from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging.interface import BaseJudge
from app.modules.judging.models import JudgeEvaluationData
from app.schemas.verification import JudgeDecision


class OpenSourceModelJudge(BaseJudge):
    """Adapter for local open-source LLM judge (e.g. Ollama or vLLM).

    Strictly preserves research integrity: if the local model endpoint
    is not configured or is unreachable, honestly reports UNAVAILABLE
    rather than fabricating fake model outputs.
    """

    def __init__(
        self,
        endpoint_url: str | None = None,
        model_name: str = "llama3:8b",
        name: str = "Judge-LocalLLM",
    ) -> None:
        self._endpoint_url = endpoint_url
        self._model_name = model_name
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def evaluate(
        self,
        claim_text: str,
        evidence_items: list[RetrievedEvidenceItem],
    ) -> JudgeEvaluationData:
        """Execute model evaluation or return honest UNAVAILABLE status."""
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
                metadata={"status": "NOT_CONFIGURED"},
            )

        # Attempt probe of configured local endpoint
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                prompt = (
                    f"Given evidence: {[item.snippet for item in evidence_items]}\n"
                    f"Is the claim supported, contradicted, or unknown: '{claim_text}'?"
                )
                payload = {
                    "model": self._model_name,
                    "prompt": prompt,
                    "stream": False,
                }
                resp = await client.post(self._endpoint_url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data.get("response", "").upper()
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
                        metadata={"status": "LIVE_INFERENCE_SUCCESS"},
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
                metadata={"status": "ENDPOINT_UNREACHABLE"},
            )

        return JudgeEvaluationData(
            judge_id=uuid.uuid4(),
            judge_name=self.name,
            model_version=self._model_name,
            judgment=JudgeDecision.UNAVAILABLE,
            confidence=None,
            rationale="Local model returned unexpected response.",
            evidence_references=[],
            metadata={"status": "UNEXPECTED_RESPONSE"},
        )
