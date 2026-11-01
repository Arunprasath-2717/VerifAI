"""Credentials pasted into verification input must never reach a model or storage."""

import pytest
from fastapi.testclient import TestClient

from app.modules.chat import safety

SECRET_SAMPLES = [
    "My key is sk-proj-abcdef1234567890XYZ and it works.",
    "password=Hunter2!!abc",
    "Use token ghp_abcdefghijklmnop1234 here",
    "postgresql://admin:s3cretpass@db.internal:5432/app",
]


@pytest.mark.parametrize("text", SECRET_SAMPLES)
def test_verification_rejects_pasted_credentials(client: TestClient, text: str) -> None:
    response = client.post("/api/v1/verification", json={"text": text})
    assert response.status_code == 400
    assert response.json()["error"]["details"]["reason"] == "SENSITIVE_CREDENTIAL"


def test_rejection_does_not_echo_the_secret(client: TestClient) -> None:
    secret = "sk-proj-abcdef1234567890XYZ"
    response = client.post(
        "/api/v1/verification", json={"text": f"my key is {secret} ok"}
    )
    assert response.status_code == 400
    assert secret not in response.text


def test_benign_claims_are_not_blocked(client: TestClient) -> None:
    response = client.post(
        "/api/v1/verification",
        json={"text": "The API key rotation policy is quarterly."},
    )
    assert response.status_code == 200


def test_secret_detector_matches_documented_shapes() -> None:
    for text in SECRET_SAMPLES:
        assert safety.contains_credentials(text), text
