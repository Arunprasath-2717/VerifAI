"""Tests for Verification domain models, schema metadata, and relationships."""

import uuid
from datetime import UTC, datetime

from benchmark.schemas import ContentType, VerdictType
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.base import Base
from app.models.verification import (
    AuditRecord,
    ExtractedClaim,
    JudgeVerdict,
    RetrievedEvidence,
    VerificationJob,
)
from app.modules.judging.models import JudgeDecision


def test_model_table_names() -> None:
    """Verify ORM model table names conform to schema design."""
    assert VerificationJob.__tablename__ == "verifications"
    assert ExtractedClaim.__tablename__ == "claims"
    assert RetrievedEvidence.__tablename__ == "evidence_items"
    assert JudgeVerdict.__tablename__ == "judge_evaluations"
    assert AuditRecord.__tablename__ == "audit_records"


def test_verification_job_instantiation() -> None:
    """Verify VerificationJob instance creation with valid fields."""
    job_id = uuid.uuid4()
    job = VerificationJob(
        id=job_id,
        input_text="Water is composed of hydrogen and oxygen.",
        content_type=ContentType.FACTUAL.value,
        status="PENDING",
        trust_score=100.0,
        summary="Claim verified as supported.",
        total_claims=1,
        supported_claims=1,
        contradicted_claims=0,
        unknown_claims=0,
        non_factual_claims=0,
        calibration_status="NOT_CALIBRATED",
        is_calibrated=False,
    )
    assert job.id == job_id
    assert job.status == "PENDING"
    assert job.input_text == "Water is composed of hydrogen and oxygen."
    assert job.trust_score == 100.0
    assert job.claims == []
    assert job.audit_records == []


def test_extracted_claim_instantiation() -> None:
    """Verify ExtractedClaim instance fields, foreign keys, and defaults."""
    job_id = uuid.uuid4()
    claim_id = uuid.uuid4()
    claim = ExtractedClaim(
        id=claim_id,
        verification_id=job_id,
        claim_index=0,
        claim_text="Water has formula H2O.",
        start_offset=0,
        end_offset=22,
        content_type=ContentType.FACTUAL.value,
        verdict=VerdictType.SUPPORTED.value,
        explanation="Directly verified by evidence.",
    )
    assert claim.id == claim_id
    assert claim.verification_id == job_id
    assert claim.claim_index == 0
    assert claim.claim_text == "Water has formula H2O."
    assert claim.start_offset == 0
    assert claim.end_offset == 22
    assert claim.verdict == "SUPPORTED"
    assert claim.evidence_items == []
    assert claim.judge_evaluations == []


def test_retrieved_evidence_instantiation() -> None:
    """Verify RetrievedEvidence fields and provenance tracking."""
    claim_id = uuid.uuid4()
    ev_id = uuid.uuid4()
    evidence = RetrievedEvidence(
        id=ev_id,
        claim_id=claim_id,
        retriever_name="local_index",
        source_title="Water Chemistry",
        source_url="https://en.wikipedia.org/wiki/Water",
        snippet="Water is a chemical compound with the chemical formula H2O.",
        authority_score=0.95,
        relevance_score=0.92,
    )
    assert evidence.id == ev_id
    assert evidence.claim_id == claim_id
    assert evidence.retriever_name == "local_index"
    assert evidence.authority_score == 0.95
    assert evidence.relevance_score == 0.92


def test_judge_verdict_instantiation() -> None:
    """Verify JudgeVerdict fields and raw response payload storage."""
    claim_id = uuid.uuid4()
    verdict_id = uuid.uuid4()
    verdict = JudgeVerdict(
        id=verdict_id,
        claim_id=claim_id,
        judge_name="deterministic_rule_judge",
        judgment=JudgeDecision.SUPPORTED.value,
        confidence=1.0,
        rationale="Exact numeric match",
        evaluation_metadata={"matched_entities": ["water", "H2O"], "latency_ms": 1.5},
    )
    assert verdict.id == verdict_id
    assert verdict.claim_id == claim_id
    assert verdict.judge_name == "deterministic_rule_judge"
    assert verdict.judgment == "SUPPORTED"
    assert verdict.confidence == 1.0
    assert verdict.evaluation_metadata is not None
    assert verdict.evaluation_metadata["matched_entities"] == ["water", "H2O"]
    assert verdict.evaluation_metadata["latency_ms"] == 1.5


def test_audit_record_instantiation() -> None:
    """Verify AuditRecord fields and traceability structure."""
    job_id = uuid.uuid4()
    record_id = uuid.uuid4()
    record = AuditRecord(
        id=record_id,
        verification_id=job_id,
        stage="EXTRACTION",
        event_type="CLAIMS_EXTRACTED",
        status="SUCCESS",
        message="Extracted 1 claims from input text",
        details={"char_count": 42},
        timestamp=datetime.now(UTC),
    )
    assert record.id == record_id
    assert record.verification_id == job_id
    assert record.stage == "EXTRACTION"
    assert record.event_type == "CLAIMS_EXTRACTED"
    assert record.status == "SUCCESS"
    assert record.details == {"char_count": 42}


def test_in_memory_sqlite_schema_creation_and_cascades() -> None:
    """Verify database schema creation and cascade deletions using in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        job = VerificationJob(
            input_text="Sample input.",
            content_type="FACTUAL",
            status="COMPLETED",
        )
        session.add(job)
        session.flush()

        claim = ExtractedClaim(
            verification_id=job.id,
            claim_index=0,
            claim_text="Sample claim.",
            start_offset=0,
            end_offset=13,
            content_type="FACTUAL",
            verdict="SUPPORTED",
        )
        session.add(claim)

        audit = AuditRecord(
            verification_id=job.id,
            stage="PIPELINE_COMPLETE",
            event_type="JOB_COMPLETED",
            status="SUCCESS",
            message="Verification finished successfully",
        )
        session.add(audit)
        session.flush()

        evidence = RetrievedEvidence(
            claim_id=claim.id,
            retriever_name="test_retriever",
            snippet="Sample evidence snippet.",
        )
        session.add(evidence)

        verdict = JudgeVerdict(
            claim_id=claim.id,
            judge_name="rule_judge",
            judgment="SUPPORTED",
        )
        session.add(verdict)
        session.commit()

        # Query and verify relationships
        queried_job = session.query(VerificationJob).filter_by(id=job.id).first()
        assert queried_job is not None
        assert len(queried_job.claims) == 1
        assert len(queried_job.audit_records) == 1
        assert len(queried_job.claims[0].evidence_items) == 1
        assert len(queried_job.claims[0].judge_evaluations) == 1

        # Delete job and verify cascade deletion of claim, evidence, and audit records
        session.delete(queried_job)
        session.commit()

        assert session.query(VerificationJob).count() == 0
        assert session.query(ExtractedClaim).count() == 0
        assert session.query(RetrievedEvidence).count() == 0
        assert session.query(JudgeVerdict).count() == 0
        assert session.query(AuditRecord).count() == 0
