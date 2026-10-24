"""Regression: unverified Google identity claims must never mint a session."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_google_endpoint_does_not_issue_session_from_claimed_email() -> None:
    """Anonymous email claims must not produce an access token."""
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/auth/google",
            json={"email": "victim@example.com", "name": "Victim"},
        )
    assert response.status_code in {404, 405}
    assert "access_token" not in response.text


def test_firebase_endpoint_rejects_unverified_token() -> None:
    """The retained Firebase path must reject tokens that fail RS256 verification."""
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/auth/firebase",
            json={"id_token": "not-a-real-firebase-token-value"},
        )
    assert response.status_code in {400, 401, 403, 422}
    assert "access_token" not in response.text
