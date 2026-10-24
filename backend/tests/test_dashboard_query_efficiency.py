"""Regression checks for dashboard SQL query count and daily totals.

Uses in-memory SQLite only; never writes to the application's PostgreSQL.
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 — register complete SQLAlchemy metadata
from app.api.v1.endpoints.dashboard import get_dashboard_stats
from app.core.config import Settings
from app.models.base import Base
from app.models.chat import Conversation
from app.models.verification import ExtractedClaim, RetrievedEvidence, VerificationJob


class AsyncExecuteAdapter:
    """Satisfy the endpoint's async execute interface with SQLite's sync driver."""

    def __init__(self, session):
        self.session = session

    async def execute(self, query):
        return self.session.execute(query)

    def get_bind(self):
        return self.session.get_bind()


def test_dashboard_aggregates_timestamps_in_four_grouped_queries():
    async def scenario():
        engine = create_engine("sqlite:///:memory:")
        try:
            Base.metadata.create_all(engine)

            maker = sessionmaker(engine, expire_on_commit=False)
            today = datetime.now(UTC).replace(hour=12, minute=0, second=0, microsecond=0)
            recent_id, older_id, other_id = (uuid.uuid4() for _ in range(3))
            recent_claim, other_claim = uuid.uuid4(), uuid.uuid4()
            with maker() as session:
                session.add_all([
                    VerificationJob(
                        id=recent_id, owner_id="default_dev_user", input_text="recent",
                        created_at=today, total_claims=1,
                    ),
                    VerificationJob(
                        id=older_id, owner_id="default_dev_user", input_text="older",
                        created_at=today - timedelta(days=12), total_claims=0,
                    ),
                    VerificationJob(
                        id=other_id, owner_id="unrelated", input_text="other tenant",
                        created_at=today, total_claims=1,
                    ),
                    ExtractedClaim(
                        id=recent_claim, verification_id=recent_id,
                        claim_index=0, claim_text="recent claim",
                        start_offset=0, end_offset=12, created_at=today,
                    ),
                    ExtractedClaim(
                        id=other_claim, verification_id=other_id,
                        claim_index=0, claim_text="not the tenant's claim",
                        start_offset=0, end_offset=22, created_at=today,
                    ),
                    RetrievedEvidence(
                        claim_id=recent_claim, snippet="real saved evidence",
                        retriever_name="test", created_at=today,
                    ),
                    RetrievedEvidence(
                        claim_id=other_claim, snippet="another tenant's evidence",
                        retriever_name="test", created_at=today,
                    ),
                    Conversation(
                        owner_id="default_dev_user", title="recent conversation",
                        created_at=today,
                    ),
                ])
                session.commit()

            statements = []
            def record_statement(_conn, _cursor, statement, _params, _context, _many):
                if statement.lstrip().upper().startswith("SELECT"):
                    statements.append(statement)

            event.listen(engine, "before_cursor_execute", record_statement)
            try:
                with maker() as session:
                    result = await get_dashboard_stats(
                        current_user=None, db=AsyncExecuteAdapter(session),
                        settings=Settings(_env_file=None, ENVIRONMENT="testing"),
                    )
            finally:
                event.remove(engine, "before_cursor_execute", record_statement)

            assert result.verifications_count == 2
            assert result.claims_count == 1
            assert result.evidence_sources_count == 1
            assert result.conversations_count == 1
            assert len(result.weekly_chart_data) == 7
            assert len(result.monthly_chart_data) == 30
            assert sum(day.verifications for day in result.weekly_chart_data) == 1
            assert sum(day.verifications for day in result.monthly_chart_data) == 2
            assert sum(day.claims for day in result.weekly_chart_data) == 1
            assert sum(day.evidence for day in result.weekly_chart_data) == 1
            assert len(result.recent_verifications) == 2

            # The former per-day path ran 111 count queries before base/recent
            # reads; the grouped implementation has a constant query budget.
            assert len(statements) <= 20, len(statements)
            assert len([sql for sql in statements if "GROUP BY" in sql.upper()]) == 4
        finally:
            engine.dispose()

    asyncio.run(scenario())
