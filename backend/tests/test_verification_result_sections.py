"""Verification-result sections survive history list and detail APIs.

Uses an in-memory SQLite database and never touches the application DB.
"""

import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 — register all SQLAlchemy tables
from app.api.v1.endpoints.history import (
    get_history_verification,
    list_verification_history,
)
from app.core.config import Settings
from app.models.base import Base
from app.models.verification import (
    AuditRecord,
    ExtractedClaim,
    JudgeVerdict,
    RetrievedEvidence,
    VerificationJob,
)


class AsyncSQLiteAdapter:
    def __init__(self, session):
        self.session = session

    async def execute(self, query):
        return self.session.execute(query)


def test_history_preserves_evidence_judges_and_audit_events():
    engine = create_engine("sqlite:///:memory:")
    try:
        Base.metadata.create_all(engine)
        maker = sessionmaker(engine, expire_on_commit=False)
        verification_id, claim_id = uuid.uuid4(), uuid.uuid4()
        timestamp = datetime.now(UTC)
        with maker() as session:
            session.add_all(
                [
                    VerificationJob(
                        id=verification_id,
                        owner_id="default_dev_user",
                        input_text="Example proposition",
                        query="Example proposition",
                        total_claims=1,
                        supported_claims=1,
                        status="COMPLETED",
                        created_at=timestamp,
                    ),
                    ExtractedClaim(
                        id=claim_id,
                        verification_id=verification_id,
                        claim_index=0,
                        claim_text="Example proposition",
                        start_offset=0,
                        end_offset=19,
                        content_type="FACTUAL",
                        verdict="SUPPORTED",
                    ),
                    *[
                        RetrievedEvidence(
                            claim_id=claim_id,
                            snippet=f"Recorded excerpt {i}",
                            source_title=f"Actual stored source {i}",
                            source_url=f"https://example.org/source/{i}",
                            publisher="Test publisher",
                            retriever_name="test",
                            evidence_source="EXTERNAL",
                        )
                        for i in range(3)
                    ],
                    JudgeVerdict(
                        claim_id=claim_id,
                        judge_name="Recorded Judge",
                        judgment="SUPPORTED",
                        confidence=0.88,
                        rationale="Persisted per-claim judgment",
                    ),
                    AuditRecord(
                        verification_id=verification_id,
                        stage="RETRIEVAL",
                        event_type="RETRIEVED",
                        status="COMPLETED",
                        message="Recorded retrieval stage",
                        timestamp=timestamp,
                    ),
                ]
            )
            session.commit()

        async def verify():
            settings = Settings(_env_file=None, ENVIRONMENT="testing")
            with maker() as session:
                result = await list_verification_history(
                    verdict=None,
                    job_status=None,
                    start_date=None,
                    end_date=None,
                    search=None,
                    limit=20,
                    offset=0,
                    current_user=None,
                    db=AsyncSQLiteAdapter(session),
                    settings=settings,
                )
                assert result.total == 1
                assert len(result.items) == 1
                item = result.items[0]
                assert item.verification_id == verification_id
                assert len(item.claims) == 1
                assert len(item.claims[0].evidence) == 3
                assert item.claims[0].evidence[2].snippet in {
                    "Recorded excerpt 0",
                    "Recorded excerpt 1",
                    "Recorded excerpt 2",
                }
                assert len(item.claims[0].judges) == 1
                assert item.claims[0].judges[0].judge_name == "Recorded Judge"
                assert len(item.audit_trail) == 1
                assert item.audit_trail[0].message == "Recorded retrieval stage"

            with maker() as session:
                detail = await get_history_verification(
                    verification_id=verification_id,
                    current_user=None,
                    db=AsyncSQLiteAdapter(session),
                    settings=settings,
                )
                assert len(detail.claims[0].evidence) == 3
                assert (
                    detail.claims[0].judges[0].rationale
                    == "Persisted per-claim judgment"
                )
                assert len(detail.audit_trail) == 1

        asyncio.run(verify())
    finally:
        engine.dispose()
