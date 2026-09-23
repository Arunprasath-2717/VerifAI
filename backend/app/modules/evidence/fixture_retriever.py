"""Clearly named test-fixture evidence retriever for unit and integration testing."""

from app.modules.evidence.interface import BaseEvidenceRetriever
from app.modules.evidence.models import RetrievedEvidenceItem


class TestFixtureRetriever(BaseEvidenceRetriever):
    """Test-double retriever for unit tests and negative control assertions.

    Allows injecting predefined evidence items or triggering simulated exceptions
    without relying on external network calls or presenting mocks as live results.
    """

    __test__ = False

    def __init__(
        self,
        fixture_map: dict[str, list[RetrievedEvidenceItem]] | None = None,
        should_fail: bool = False,
        failure_exception: Exception | None = None,
    ) -> None:
        self._fixtures = fixture_map or {}
        self._should_fail = should_fail
        self._failure_exception = failure_exception or RuntimeError(
            "Simulated retriever failure for testing."
        )

    @property
    def name(self) -> str:
        return "TEST_FIXTURE_RETRIEVER"

    def set_fixture(
        self, claim_key: str, evidence_list: list[RetrievedEvidenceItem]
    ) -> None:
        """Assign explicit evidence items for a claim search term."""
        self._fixtures[claim_key] = evidence_list

    async def retrieve(
        self, claim_text: str, max_passages: int = 3
    ) -> list[RetrievedEvidenceItem]:
        """Return configured test fixtures or raise configured test failure."""
        if self._should_fail:
            raise self._failure_exception

        # Check for matching substring in fixture keys
        for key, items in self._fixtures.items():
            if key.lower() in claim_text.lower():
                return items[:max_passages]

        return []
