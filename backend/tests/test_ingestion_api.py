"""Unit and integration tests for Phase 4 ingestion API and extension."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.ingestion import get_optional_db_session
from app.main import create_app
from app.models.ingestion import IngestedPayload


@pytest.fixture
def client() -> TestClient:
    """Provide a test client for FastAPI application."""
    application = create_app()
    return TestClient(application)


class TestIngestionEndpoint:
    """Test suite for POST /api/v1/ingest endpoint."""

    def test_ingest_valid_payload_immediate_verification(
        self, client: TestClient
    ) -> None:
        """Verify successful synchronous ingestion with immediate verification."""
        payload = {
            "text": "Paris is the capital of France.",
            "prompt": "What is the capital of France?",
            "source_url": "https://chatgpt.com/c/12345",
            "model_name": "gpt-4o",
            "source": "CHROME_EXTENSION",
            "client_version": "1.0.0",
            "capture_metadata": {"browser": "Chrome", "os": "Linux"},
            "verify_immediately": True,
        }
        response = client.post("/api/v1/ingest", json=payload)
        assert response.status_code == 201
        data = response.json()

        assert "ingestion_id" in data
        assert data["source"] == "CHROME_EXTENSION"
        assert data["status"] == "VERIFIED"
        assert data["model_name"] == "gpt-4o"
        assert data["source_url"] == "https://chatgpt.com/c/12345"
        assert data["verification_id"] is not None
        assert data["verification"] is not None
        assert data["verification"]["total_claims"] >= 1
        assert data["verification"]["supported_claims"] >= 1
        assert data["error_message"] is None

    def test_ingest_without_immediate_verification(self, client: TestClient) -> None:
        """Verify ingestion can store payload without running immediate pipeline."""
        payload = {
            "text": "The solar system contains eight major planets.",
            "source": "WEB_CHAT",
            "verify_immediately": False,
        }
        response = client.post("/api/v1/ingest", json=payload)
        assert response.status_code == 201
        data = response.json()

        assert data["status"] == "RECEIVED"
        assert data["verification_id"] is None
        assert data["verification"] is None

    def test_ingest_empty_text_rejected(self, client: TestClient) -> None:
        """Reject empty text string with HTTP 422."""
        response = client.post("/api/v1/ingest", json={"text": ""})
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_ingest_whitespace_only_text_rejected(self, client: TestClient) -> None:
        """Reject whitespace-only text with HTTP 422."""
        response = client.post("/api/v1/ingest", json={"text": "   \n\t   "})
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_ingest_text_exceeding_max_chars(self, client: TestClient) -> None:
        """Reject text exceeding 20,000 characters."""
        oversized = "a" * 20001
        response = client.post("/api/v1/ingest", json={"text": oversized})
        assert response.status_code == 422

    def test_ingest_invalid_url_scheme_rejected(self, client: TestClient) -> None:
        """Reject non-http/https URL schemes with HTTP 422."""
        payload = {
            "text": "Some verified content.",
            "source_url": "ftp://files.example.com/data.txt",
        }
        response = client.post("/api/v1/ingest", json=payload)
        assert response.status_code == 422

    def test_ingest_ssrf_url_blocked(self, client: TestClient) -> None:
        """Block cloud metadata and internal IP source URLs with HTTP 400."""
        ssrf_targets = [
            "http://169.254.169.254/latest/meta-data/",
            "http://127.0.0.1:8000/admin",
            "http://localhost:5432",
            "http://10.0.0.1/internal",
            "http://192.168.1.1/router",
        ]
        for url in ssrf_targets:
            payload = {
                "text": "Valid factual statement about Earth.",
                "source_url": url,
            }
            response = client.post("/api/v1/ingest", json=payload)
            assert response.status_code == 400
            data = response.json()
            assert "SSRF" in data["error"]["message"]

    def test_ingest_extra_fields_forbidden(self, client: TestClient) -> None:
        """Reject unexpected extra fields due to extra='forbid'."""
        payload = {
            "text": "Water boils at 100 degrees Celsius.",
            "unauthorized_field": "exploit_attempt",
        }
        response = client.post("/api/v1/ingest", json=payload)
        assert response.status_code == 422

    def test_ingest_invalid_source_enum(self, client: TestClient) -> None:
        """Reject unsupported ingestion sources."""
        payload = {
            "text": "Water boils at 100 degrees Celsius.",
            "source": "UNKNOWN_SOURCE_XYZ",
        }
        response = client.post("/api/v1/ingest", json=payload)
        assert response.status_code == 422

    def test_get_nonexistent_ingestion_id_404(self, client: TestClient) -> None:
        """Return 404 for non-existent ingestion UUID."""
        random_id = uuid.uuid4()
        response = client.get(f"/api/v1/ingest/{random_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["error"]["message"].lower()

    def test_ingest_with_mock_db_session(self) -> None:
        """Test database persistence and commit in DB-enabled environment."""
        app = create_app()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def override_db():
            yield mock_session

        app.dependency_overrides[get_optional_db_session] = override_db
        test_client = TestClient(app)

        payload = {
            "text": "The Eiffel Tower is in Paris, France.",
            "source": "CHROME_EXTENSION",
            "model_name": "gpt-4o",
            "verify_immediately": True,
        }
        response = test_client.post("/api/v1/ingest", json=payload)
        assert response.status_code == 201

        # Assert both verification job and ingested payload entity were added
        # and committed cleanly
        assert mock_session.add.call_count == 2
        added_entities = [call[0][0] for call in mock_session.add.call_args_list]
        payload_entities = [e for e in added_entities if isinstance(e, IngestedPayload)]
        assert len(payload_entities) == 1
        record = payload_entities[0]
        assert record.captured_text == "The Eiffel Tower is in Paris, France."
        assert record.status == "VERIFIED"
        assert record.verification_id is not None
        mock_session.commit.assert_awaited()
