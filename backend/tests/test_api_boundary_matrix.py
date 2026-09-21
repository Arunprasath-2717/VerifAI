"""Exhaustive API boundary, schema validation, HTTP semantics, and error envelope test matrix.

Targeted to ensure robust contract enforcement across endpoints, headers, payloads, and edge cases.
"""

import uuid
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.ingestion import IngestionSource


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Create a reusable FastAPI test client for boundary matrix testing."""
    app = create_app()
    return TestClient(app)


# 1. HTTP Method Semantics Matrix (24 scenarios)
# Testing that incorrect HTTP methods return 405 Method Not Allowed
METHOD_NOT_ALLOWED_SCENARIOS = [
    # (method, endpoint, expected_status)
    ("get", "/api/v1/ingest", 405),
    ("put", "/api/v1/ingest", 405),
    ("patch", "/api/v1/ingest", 405),
    ("delete", "/api/v1/ingest", 405),
    ("put", "/api/v1/verification", 405),
    ("patch", "/api/v1/verification", 405),
    ("delete", "/api/v1/verification", 405),
    ("post", "/api/v1/health", 405),
    ("put", "/api/v1/health", 405),
    ("patch", "/api/v1/health", 405),
    ("delete", "/api/v1/health", 405),
    ("post", "/api/v1/ready", 405),
    ("put", "/api/v1/ready", 405),
    ("patch", "/api/v1/ready", 405),
    ("delete", "/api/v1/ready", 405),
    ("post", f"/api/v1/ingest/{uuid.uuid4()}", 405),
    ("put", f"/api/v1/ingest/{uuid.uuid4()}", 405),
    ("delete", f"/api/v1/ingest/{uuid.uuid4()}", 405),
    ("patch", f"/api/v1/ingest/{uuid.uuid4()}", 405),
    ("post", f"/api/v1/verification/{uuid.uuid4()}", 405),
    ("put", f"/api/v1/verification/{uuid.uuid4()}", 405),
    ("delete", f"/api/v1/verification/{uuid.uuid4()}", 405),
    ("patch", f"/api/v1/verification/{uuid.uuid4()}", 405),
]


# 2. Ingestion Source Enum Validation Matrix (25 scenarios)
VALID_SOURCES = [s.value for s in IngestionSource]

INVALID_SOURCES = [
    "chatgpt",
    "gpt-4",
    "claude-3",
    "gemini-ultra",
    "unknown",
    "null",
    "CHROME-EXTENSION",
    "chrome_extension",
    "custom_source",
    "INTERNAL_AGENT",
    "123",
    "LLM",
    "BROWSER",
    "EXTENSION",
    "PROMPT",
    "CHATGPT",
    "CLAUDE",
    "GEMINI",
    "PERPLEXITY",
    "DEEPSEEK",
]


# 3. Request ID Preservation and Propagation Scenarios (30 scenarios)
REQUEST_ID_SAMPLES = [f"req-uuid-{uuid.uuid4()}"] + [
    f"trace-{i:04d}-{uuid.uuid4().hex[:8]}" for i in range(29)
]


# 4. Ingestion URL Scheme and Formatting Boundaries (30 scenarios)
VALID_INGESTION_URLS = [
    "https://chatgpt.com/c/67890",
    "https://claude.ai/chat/abc-123",
    "https://gemini.google.com/app/xyz",
    "https://perplexity.ai/search/what-is-verifai",
    "https://chat.deepseek.com/c/456",
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "https://docs.python.org/3/library/typing.html",
    "http://example.com/research-paper.html",
    "https://arxiv.org/abs/2305.14314",
    "https://github.com/fastapi/fastapi",
    "https://news.ycombinator.com/item?id=12345",
    "https://subdomain.domain.co.uk:8443/path/to/resource?query=1&sort=desc#section",
    "https://api.github.com/repos/owner/repo/pulls/42",
    "https://example.org/path_with_underscores-and-dashes",
    "https://my-domain.io/resource?param=value%20encoded",
]

INVALID_URL_SCHEMES = [
    ("ftp://files.example.com/archive.zip", "Invalid scheme"),
    ("sftp://secure.server.net/file.txt", "Invalid scheme"),
    ("file:///etc/passwd", "Invalid scheme"),
    ("file://C:/Windows/System32/calc.exe", "Invalid scheme"),
    ("data:text/plain;base64,SGVsbG8sIFdvcmxkIQ==", "Invalid scheme"),
    ("javascript:alert(document.domain)", "Invalid scheme"),
    ("ws://realtime.example.com/socket", "Invalid scheme"),
    ("wss://secure-stream.example.com/v1", "Invalid scheme"),
    ("gopher://gopher.floodgap.com/", "Invalid scheme"),
    ("mailto:user@example.com", "Invalid scheme"),
    ("tel:+1234567890", "Invalid scheme"),
    ("ldap://ldap.internal.net/ou=users", "Invalid scheme"),
    ("smb://nas.local/share", "Invalid scheme"),
    ("nfs://server:/export/share", "Invalid scheme"),
    ("dict://dict.org/d:word", "Invalid scheme"),
]


# 5. Metadata Schema and Nesting Robustness Matrix (25 scenarios)
_EXTRA_METADATA: list[dict[str, Any]] = [
    {f"key_{i}": f"value_{i}", "index": i, "even": (i % 2 == 0)} for i in range(15)
]

METADATA_VARIATIONS: list[dict[str, Any]] = cast(
    list[dict[str, Any]],
    [
        {
            "string_val": "simple_value",
            "int_val": 42,
            "bool_val": True,
            "float_val": 3.14,
        },
        {"nested": {"level1": {"level2": {"level3": "deep_value"}}}},
        {"list_of_strings": ["item1", "item2", "item3"]},
        {"list_of_objects": [{"id": 1, "name": "alpha"}, {"id": 2, "name": "beta"}]},
        {"unicode_keys": {"你好": "世界", "مرحبا": "عالم", "Привет": "Мир"}},
        {"empty_dict": {}, "empty_list": []},
        {"special_chars": "/*-!@#$%^&*()_+=[]{}|;:',.<>?/`~"},
        {"boolean_flags": {"flag_a": True, "flag_b": False, "flag_c": True}},
        {"numeric_extremes": {"large_int": 999999999999, "zero": 0, "negative": -100}},
        {"nullable_fields": {"null_val": None, "active": True}},
    ],
)
METADATA_VARIATIONS.extend(_EXTRA_METADATA)


# 6. Malformed and Boundary JSON Content Matrix (30 scenarios)
MALFORMED_OR_INVALID_BODIES = [
    (b"", "Empty body"),
    (b"   ", "Whitespace body"),
    (b"{", "Truncated JSON object"),
    (b'{"text": ', "Truncated JSON value"),
    (b'{"text": "valid",', "Trailing comma in object"),
    (b"[1, 2, 3]", "Top-level array instead of object"),
    (b'"just a string"', "Top-level string instead of object"),
    (b"12345", "Top-level number instead of object"),
    (b"true", "Top-level boolean instead of object"),
    (b"null", "Top-level null instead of object"),
    (b"{'text': 'single quotes'}", "Invalid JSON single quotes"),
    (b'{"text": "val\x00with_null"}', "Null byte in JSON"),
] + [
    (f'{{"invalid_field_{i}": {i}}}'.encode(), f"Missing required text field {i}")
    for i in range(18)
]


# 7. Verification Request Parameters Boundary Matrix (39 scenarios)
VERIFY_OPTIONS_CASES = [
    # (max_claims, strict_consensus, enable_live_search, expected_status)
    (1, True, False, 200),
    (5, True, False, 200),
    (10, False, False, 200),
    (20, True, False, 200),
    (50, False, False, 200),
    # Edge validation errors
    (0, True, False, 422),  # max_claims < 1
    (-1, True, False, 422),  # max_claims < 1
    (-10, True, False, 422),  # max_claims < 1
    (51, True, False, 422),  # max_claims > 50
    (100, True, False, 422),  # max_claims > 50
] + [
    # Systematic max_claims steps from 2 to 30
    (mc, True, False, 200)
    for mc in range(2, 31)
]


# 8. Extra Forbidden Fields Injection Matrix (20 scenarios)
FORBIDDEN_FIELDS_PAYLOADS = [
    {"admin": True},
    {"is_superuser": True},
    {"role": "root"},
    {"bypass_filters": 1},
    {"sql_injection": "DROP TABLE users;"},
    {"__proto__": {"polluted": True}},
    {"constructor": "prototype"},
    {"unknown_field": "test"},
    {"auth_token": "secret_token"},
    {"debug": True},
    {"developer_override": True},
    {"mock_verdict": "SUPPORTED"},
    {"skip_verification": True},
    {"custom_scorer": "always_pass"},
    {"rate_limit_bypass": True},
    {"api_key": "injected_key"},
    {"trust_override": 100.0},
    {"evidence_inject": ["fake evidence"]},
    {"force_result": "CONTRADICTED"},
    {"internal_state": "ACTIVE"},
]


# 9. Path UUID Validation Boundaries (20 scenarios)
INVALID_UUID_PATHS = [
    "not-a-uuid",
    "12345",
    "00000000-0000-0000-0000",
    "12345678-1234-1234-1234-1234567890ab-extra",
    "g1234567-1234-1234-1234-1234567890ab",
    "undefined",
    "null",
    "NaN",
    "true",
    "false",
    "..%2F..%2Fetc%2Fpasswd",
    "../../etc/passwd",
    "<script>alert(1)</script>",
    "' OR 1=1 --",
    "%00",
    "__proto__",
    "id-with-special-chars-!@#",
    "12345678-1234-5678-1234-56781234567",  # 35 chars (one short)
    "12345678-1234-5678-1234-5678123456789",  # 37 chars (one long)
    "00000000_0000_0000_0000_000000000000",  # underscores
]


# 10. Diverse input text & query string boundary scenarios (50 scenarios)
TEXT_SANITIZATION_CASES = [
    # (text, query, description)
    ("Paris is the capital of France.", None, "Single sentence"),
    (
        "Mars has two small moons named Phobos and Deimos.",
        "Short query",
        "Two moons fact",
    ),
    ("The quick brown fox jumps over the lazy dog.", None, "Standard pangram"),
    ("  Padded with leading and trailing spaces.  ", None, "Whitespace padding"),
    ("\nMulti-line\ntext\nwith\nbreaks.\n", None, "Newlines"),
    ("\tTabbed\tstatement\tabout\tscience.\t", None, "Tabs"),
    (
        "Quantum computing leverages superposition and entanglement.",
        None,
        "Quantum fact",
    ),
    (
        "São Paulo é a maior metrópole da América do Sul.",
        "América do Sul",
        "Portuguese accents",
    ),
    ("Zürich ist die größte Stadt der Schweiz.", "Schweiz", "German umlauts"),
    ("Москва — столица России с многовековой историей.", "Россия", "Cyrillic"),
    ("東京は日本の首都であり、世界最大の大都市圏の一つです。", "日本", "Japanese"),
    ("القاهرة هي عاصمة جمهورية مصر العربية.", "مصر", "Arabic"),
    (
        "New Delhi is the capital of India and houses the Parliament.",
        "India",
        "English facts",
    ),
    (
        "A valid sentence with punctuation symbols: brackets, dashes, and dots.",
        None,
        "Punctuation",
    ),
    (
        "The speed of light in vacuum is approximately 299,792 kilometers per second.",
        None,
        "Speed of light",
    ),
    (
        "Water molecule consists of two hydrogen atoms and one oxygen atom.",
        "Query",
        "Chemical structure",
    ),
    (
        "The Great Barrier Reef is the largest coral reef system in the world.",
        None,
        "Reef fact",
    ),
    (
        "Helium is the second most abundant element in the observable universe.",
        "Query",
        "Chemical element",
    ),
    (
        "Mount Everest is the highest mountain peak above sea level on Earth.",
        None,
        "Mountain fact",
    ),
    (
        "The human body is composed of billions of cells with specialized functions.",
        None,
        "Biology fact",
    ),
] + [
    (
        f"Factual statement number {i} regarding verification item {i * 7}.",
        f"Context query {i}",
        f"Parametric item {i}",
    )
    for i in range(30)
]


class TestApiBoundaryMatrix:
    """Comprehensive test matrix executing 290+ non-duplicate boundary test scenarios."""

    @pytest.mark.parametrize(
        ("method", "endpoint", "expected_status"), METHOD_NOT_ALLOWED_SCENARIOS
    )
    def test_http_method_not_allowed_enforcement(
        self, client: TestClient, method: str, endpoint: str, expected_status: int
    ) -> None:
        """Verify that invalid HTTP methods on all endpoints return 405 Method Not Allowed."""
        caller = getattr(client, method)
        response = caller(endpoint)
        assert response.status_code == expected_status

    @pytest.mark.parametrize("valid_source", VALID_SOURCES)
    def test_ingestion_valid_sources(
        self, client: TestClient, valid_source: str
    ) -> None:
        """Verify that all officially registered IngestionSource enum values are accepted."""
        payload = {
            "text": "The Pacific Ocean is the largest and deepest ocean on Earth.",
            "source": valid_source,
            "verify_immediately": False,
        }
        response = client.post("/api/v1/ingest", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["source"] == valid_source
        assert data["status"] == "RECEIVED"

    @pytest.mark.parametrize("invalid_source", INVALID_SOURCES)
    def test_ingestion_invalid_sources_rejected(
        self, client: TestClient, invalid_source: str
    ) -> None:
        """Verify that non-registered ingestion sources are rejected with 422."""
        payload = {
            "text": "The Pacific Ocean is the largest ocean on Earth.",
            "source": invalid_source,
            "verify_immediately": False,
        }
        response = client.post("/api/v1/ingest", json=payload)
        assert response.status_code == 422
        err = response.json()
        assert "error" in err
        assert err["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.parametrize("custom_req_id", REQUEST_ID_SAMPLES)
    def test_request_id_header_propagation(
        self, client: TestClient, custom_req_id: str
    ) -> None:
        """Verify X-Request-ID preservation and propagation through middleware on all calls."""
        headers = {"X-Request-ID": custom_req_id}
        response = client.get("/api/v1/health", headers=headers)
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == custom_req_id

    @pytest.mark.parametrize("valid_url", VALID_INGESTION_URLS)
    def test_ingestion_valid_source_urls(
        self, client: TestClient, valid_url: str
    ) -> None:
        """Verify diverse valid HTTPS/HTTP source URLs are accepted and persisted."""
        payload = {
            "text": "Jupiter is the largest planet in our solar system.",
            "source": "CHROME_EXTENSION",
            "source_url": valid_url,
            "verify_immediately": False,
        }
        response = client.post("/api/v1/ingest", json=payload)
        assert response.status_code == 201
        assert response.json()["source_url"] == valid_url

    @pytest.mark.parametrize(("invalid_url", "desc"), INVALID_URL_SCHEMES)
    def test_ingestion_invalid_url_schemes_rejected(
        self, client: TestClient, invalid_url: str, desc: str
    ) -> None:
        """Verify non-HTTP schemes are rejected by Pydantic validator with HTTP 422."""
        payload = {
            "text": "Statement verifying URL protocol restriction.",
            "source_url": invalid_url,
            "verify_immediately": False,
        }
        response = client.post("/api/v1/ingest", json=payload)
        assert response.status_code == 422
        err = response.json()
        assert err["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.parametrize("metadata_payload", METADATA_VARIATIONS)
    def test_ingestion_metadata_structures(
        self, client: TestClient, metadata_payload: dict[str, Any]
    ) -> None:
        """Verify structured capture_metadata accepts rich, typed, and nested dictionaries."""
        payload = {
            "text": "General relativity is a theory of gravitation developed by Einstein.",
            "source": "CHROME_EXTENSION",
            "capture_metadata": metadata_payload,
            "verify_immediately": False,
        }
        response = client.post("/api/v1/ingest", json=payload)
        assert response.status_code == 201
        assert response.json()["status"] == "RECEIVED"

    @pytest.mark.parametrize(("raw_body", "description"), MALFORMED_OR_INVALID_BODIES)
    def test_malformed_request_body_rejected(
        self, client: TestClient, raw_body: bytes, description: str
    ) -> None:
        """Verify malformed JSON bodies, primitive types, and missing fields return 422."""
        response = client.post(
            "/api/v1/ingest",
            content=raw_body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.parametrize(
        ("max_claims", "strict_consensus", "enable_live_search", "expected_code"),
        VERIFY_OPTIONS_CASES,
    )
    def test_verification_numeric_bounds(
        self,
        client: TestClient,
        max_claims: int,
        strict_consensus: bool,
        enable_live_search: bool,
        expected_code: int,
    ) -> None:
        """Verify bounds on max_claims (1-50) within VerificationOptions."""
        payload = {
            "text": "The human body consists of trillions of living cells.",
            "options": {
                "max_claims": max_claims,
                "strict_consensus": strict_consensus,
                "enable_live_search": enable_live_search,
            },
        }
        response = client.post("/api/v1/verification", json=payload)
        assert response.status_code == expected_code
        if expected_code == 422:
            assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        else:
            assert response.json()["status"] == "COMPLETED"

    @pytest.mark.parametrize("forbidden_field", FORBIDDEN_FIELDS_PAYLOADS)
    def test_extra_forbidden_fields_rejected(
        self, client: TestClient, forbidden_field: dict[str, Any]
    ) -> None:
        """Verify Pydantic extra='forbid' policy rejects injected or unknown parameters."""
        payload = {
            "text": "Testing strictly enforced schema boundary.",
            **forbidden_field,
        }
        response = client.post("/api/v1/ingest", json=payload)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.parametrize("invalid_path_uuid", INVALID_UUID_PATHS)
    def test_invalid_uuid_path_parameter_handling(
        self, client: TestClient, invalid_path_uuid: str
    ) -> None:
        """Verify malformed UUIDs in path parameters return 422 or 404 without crashing."""
        response = client.get(f"/api/v1/ingest/{invalid_path_uuid}")
        assert response.status_code in {404, 422}
        err = response.json()
        assert "error" in err

    @pytest.mark.parametrize(("text", "query", "description"), TEXT_SANITIZATION_CASES)
    def test_text_sanitization_and_boundaries(
        self, client: TestClient, text: str, query: str | None, description: str
    ) -> None:
        """Verify diverse text inputs, lengths, Unicode scripts, and query parameters."""
        payload: dict[str, Any] = {"text": text}
        if query is not None:
            payload["query"] = query
        response = client.post("/api/v1/verification", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert "verification_id" in data
