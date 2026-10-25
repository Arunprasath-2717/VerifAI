"""Reports calculations are accurate and bounded independent of record volume."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register complete schema
from app.api.v1.endpoints.reports import get_reports_analytics
from app.core.config import Settings
from app.models.base import Base
from app.models.verification import ExtractedClaim, RetrievedEvidence, VerificationJob


class AsyncExecuteAdapter:
    def __init__(self, session):
        self.session = session

    async def execute(self, query):
        return self.session.execute(query)

    def get_bind(self):
        return self.session.get_bind()


def test_reports_group_totals_with_owner_isolation_and_five_queries():
    async def scenario():
        engine = create_engine("sqlite:///:memory:")
        try:
            Base.metadata.create_all(engine)
            today = datetime.now(UTC).replace(
                hour=12, minute=0, second=0, microsecond=0
            )
            today_id, older_id, foreign_id = (uuid.uuid4() for _ in range(3))
            today_claim_id, foreign_claim_id = uuid.uuid4(), uuid.uuid4()
            maker = sessionmaker(engine, expire_on_commit=False)

            with maker() as session:
                session.add_all(
                    [
                        VerificationJob(
                            id=today_id,
                            owner_id="default_dev_user",
                            input_text="today",
                            created_at=today,
                            trust_score=0.8,
                            total_claims=1,
                            supported_claims=1,
                        ),
                        VerificationJob(
                            id=older_id,
                            owner_id="default_dev_user",
                            input_text="older",
                            created_at=today - timedelta(days=4),
                            trust_score=0.6,
                            total_claims=0,
                        ),
                        VerificationJob(
                            id=foreign_id,
                            owner_id="another_user",
                            input_text="foreign",
                            created_at=today,
                            total_claims=1,
                            contradicted_claims=1,
                        ),
                        ExtractedClaim(
                            id=today_claim_id,
                            verification_id=today_id,
                            claim_index=0,
                            claim_text="supported",
                            start_offset=0,
                            end_offset=9,
                            created_at=today,
                        ),
                        ExtractedClaim(
                            id=foreign_claim_id,
                            verification_id=foreign_id,
                            claim_index=0,
                            claim_text="foreign",
                            start_offset=0,
                            end_offset=7,
                            created_at=today,
                        ),
                        RetrievedEvidence(
                            claim_id=today_claim_id,
                            publisher="Evidence Registry",
                            snippet="measured result",
                            retriever_name="test",
                            created_at=today,
                        ),
                        RetrievedEvidence(
                            claim_id=foreign_claim_id,
                            publisher="Other Publisher",
                            snippet="not this owner's record",
                            retriever_name="test",
                            created_at=today,
                        ),
                    ]
                )
                session.commit()

            statements = []

            def record_sql(_conn, _cursor, sql, _params, _context, _many):
                if sql.lstrip().upper().startswith("SELECT"):
                    statements.append(sql)

            event.listen(engine, "before_cursor_execute", record_sql)
            try:
                with maker() as session:
                    report = await get_reports_analytics(
                        timeframe="7D",
                        current_user=None,
                        db=AsyncExecuteAdapter(session),
                        settings=Settings(_env_file=None, ENVIRONMENT="testing"),
                    )
            finally:
                event.remove(engine, "before_cursor_execute", record_sql)

            assert report.total_verifications == 2
            assert report.total_claims == 1
            assert report.average_trust_score == 0.7
            assert report.supported_rate == 100
            assert report.contradicted_rate == 0
            assert report.unknown_rate == 0
            assert report.model_usage == []
            assert len(report.evidence_sources) == 1
            assert report.evidence_sources[0].count == 1
            assert len(report.chart_data) == 7
            assert sum(point.verifications for point in report.chart_data) == 2
            assert sum(point.claims for point in report.chart_data) == 1
            assert sum(point.evidence for point in report.chart_data) == 1
            assert len(statements) == 5, len(statements)
        finally:
            engine.dispose()

    asyncio.run(scenario())
