"""SQLAlchemy 2.x domain models for VerifAI verification lifecycle."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, Base, TimestampMixin


class VerificationJob(Base, TimestampMixin):
    """Represents an end-to-end verification request and aggregated outcome."""

    __tablename__ = "verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    input_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    query: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING",
        index=True,
    )
    content_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="FACTUAL",
    )
    total_claims: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    supported_claims: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    contradicted_claims: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    unknown_claims: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    non_factual_claims: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    trust_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    calibrated_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    is_calibrated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    calibration_status: Mapped[str] = mapped_column(
        String(32),
        default="NOT_CALIBRATED",
        nullable=False,
    )
    degraded_evaluation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    execution_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationships
    claims: Mapped[list["ExtractedClaim"]] = relationship(
        "ExtractedClaim",
        back_populates="verification",
        cascade="all, delete-orphan",
        order_by="ExtractedClaim.claim_index",
    )
    audit_records: Mapped[list["AuditRecord"]] = relationship(
        "AuditRecord",
        back_populates="verification",
        cascade="all, delete-orphan",
        order_by="AuditRecord.timestamp",
    )

    __table_args__ = (Index("ix_verifications_status_created", "status", "created_at"),)

    def __repr__(self) -> str:
        return (
            f"<VerificationJob(id={self.id}, status='{self.status}', "
            f"claims={self.total_claims})>"
        )


class ExtractedClaim(Base, TimestampMixin):
    """Represents an atomic, decomposed claim extracted from the input text."""

    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    verification_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("verifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claim_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    claim_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    start_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    end_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="FACTUAL",
    )
    verdict: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        default=None,
        index=True,
    )
    is_verifiable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    degraded_evaluation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    arbitration_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    is_calibrated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    calibration_status: Mapped[str] = mapped_column(
        String(32),
        default="NOT_CALIBRATED",
        nullable=False,
    )
    unknown_reason: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationships
    verification: Mapped["VerificationJob"] = relationship(
        "VerificationJob",
        back_populates="claims",
    )
    evidence_items: Mapped[list["RetrievedEvidence"]] = relationship(
        "RetrievedEvidence",
        back_populates="claim",
        cascade="all, delete-orphan",
    )
    judge_evaluations: Mapped[list["JudgeVerdict"]] = relationship(
        "JudgeVerdict",
        back_populates="claim",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "verification_id", "claim_index", name="uq_claims_verification_index"
        ),
        Index("ix_claims_verification_verdict", "verification_id", "verdict"),
    )

    def __repr__(self) -> str:
        return (
            f"<ExtractedClaim(id={self.id}, index={self.claim_index}, "
            f"verdict='{self.verdict}')>"
        )


class RetrievedEvidence(Base, TimestampMixin):
    """Represents a passage of retrieved evidence with source provenance."""

    __tablename__ = "evidence_items"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    source_title: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    publisher: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
    )
    publication_date: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    retrieval_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    snippet: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    query_used: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    retriever_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    relevance_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    authority_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationship
    claim: Mapped["ExtractedClaim"] = relationship(
        "ExtractedClaim",
        back_populates="evidence_items",
    )

    def __repr__(self) -> str:
        return f"<RetrievedEvidence(id={self.id}, retriever='{self.retriever_name}')>"


class JudgeVerdict(Base, TimestampMixin):
    """Represents an independent evaluation of a claim against evidence by a judge."""

    __tablename__ = "judge_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    judge_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    model_version: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    evaluation_type: Mapped[str] = mapped_column(
        String(32),
        default="NLI_ENTAILMENT",
        nullable=False,
    )
    judgment: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    rationale: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    evidence_references: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    evaluation_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationship
    claim: Mapped["ExtractedClaim"] = relationship(
        "ExtractedClaim",
        back_populates="judge_evaluations",
    )

    def __repr__(self) -> str:
        return (
            f"<JudgeVerdict(id={self.id}, judge='{self.judge_name}', "
            f"judgment='{self.judgment}')>"
        )


class AuditRecord(Base):
    """Immutable, timestamped audit event in the verification lifecycle."""

    __tablename__ = "audit_records"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    verification_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("verifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    # Relationship
    verification: Mapped["VerificationJob"] = relationship(
        "VerificationJob",
        back_populates="audit_records",
    )

    def __repr__(self) -> str:
        return (
            f"<AuditRecord(id={self.id}, stage='{self.stage}', "
            f"event='{self.event_type}')>"
        )
