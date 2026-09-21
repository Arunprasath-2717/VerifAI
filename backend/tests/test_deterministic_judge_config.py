"""Tests for deterministic judge configuration, temperature/seed defaults, and metadata reporting."""

import pytest

from app.modules.evidence.models import RetrievedEvidenceItem
from app.modules.judging.model_judge import OpenSourceModelJudge
from app.modules.judging.prompt import PROMPT_TEMPLATE_VERSION, build_judge_prompt
from app.schemas.verification import JudgeDecision


def test_default_temperature_and_seed_values() -> None:
    """Verify OpenSourceModelJudge defaults to temperature=0.0 and seed=42."""
    judge = OpenSourceModelJudge()
    assert judge.temperature == 0.0
    assert judge.seed == 42
    assert judge.supports_seeds is True
    assert judge.provider == "ollama"


def test_unsupported_seed_capability_reported_honestly() -> None:
    """Verify unsupported seed capability is recorded honestly when disabled or unsupported."""
    judge = OpenSourceModelJudge(supports_seeds=False)
    assert judge.supports_seeds is False


@pytest.mark.anyio
async def test_judge_metadata_preserved_in_evaluation_result() -> None:
    """Verify evaluation returns rich metadata including provider, prompt version, hash, and seed status."""
    judge = OpenSourceModelJudge(
        model_name="qwen2.5:7b-instruct",
        temperature=0.0,
        seed=42,
        supports_seeds=True,
    )
    evidence = [
        RetrievedEvidenceItem(
            snippet="Earth has one natural satellite.",
            retriever_name="astronomy",
        )
    ]
    # In test environment with offline service, it returns UNAVAILABLE with full honest metadata
    res = await judge.evaluate("The Moon orbits the Earth.", evidence)

    assert res.judgment == JudgeDecision.UNAVAILABLE
    assert res.metadata is not None
    assert res.metadata["model"] == "qwen2.5:7b-instruct"
    assert res.metadata["provider"] == "ollama"
    assert res.metadata["temperature"] == 0.0
    assert res.metadata["seed"] == 42
    assert res.metadata["supports_seeds"] is True
    assert res.metadata["seed_support_status"] == "SUPPORTED"
    assert res.metadata["prompt_template_version"] == PROMPT_TEMPLATE_VERSION
    assert "prompt_hash" in res.metadata
    assert len(res.metadata["prompt_hash"]) == 16


@pytest.mark.anyio
async def test_judge_unsupported_seed_metadata() -> None:
    """Verify seed_support_status is reported as 'UNSUPPORTED' when seed capability is False."""
    judge = OpenSourceModelJudge(
        model_name="unsupported-provider-model",
        supports_seeds=False,
    )
    res = await judge.evaluate("Claim", [])

    assert res.metadata["supports_seeds"] is False
    assert res.metadata["seed_support_status"] == "UNSUPPORTED"
    assert res.metadata["seed"] is None


def test_identical_inputs_produce_identical_prompt_text_and_hash() -> None:
    """Verify identical claim and evidence generate byte-identical prompt text and hash."""
    claim = "Water boils at 100 degrees Celsius at standard atmospheric pressure."
    ev = [
        RetrievedEvidenceItem(
            snippet="At 1 atmosphere, water boils at 100 C.",
            retriever_name="physics_kb",
        )
    ]
    p1, h1 = build_judge_prompt(claim, ev)
    p2, h2 = build_judge_prompt(claim, ev)

    assert p1 == p2
    assert h1 == h2


def test_secrets_and_api_keys_not_in_prompt_or_metadata() -> None:
    """Verify secrets or credentials are not embedded into the prompt or logged metadata."""
    judge = OpenSourceModelJudge()
    prompt, _ = build_judge_prompt("Claim", [])

    assert "api_key" not in prompt.lower()
    assert "secret" not in prompt.lower()
    assert "bearer" not in prompt.lower()
    assert "secret" not in judge.name.lower()
