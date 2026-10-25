"""create_initial_schema

Revision ID: d57e9de0b8e6
Revises:
Create Date: 2026-10-03 10:41:53.030788

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.models.base


# revision identifiers, used by Alembic.
revision: str = "d57e9de0b8e6"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Users
    op.create_table(
        "users",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(
        "ix_users_email_active", "users", ["email", "is_active"], unique=False
    )
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_index(
        "ix_users_username_active", "users", ["username", "is_active"], unique=False
    )

    # 2. Conversations
    op.create_table(
        "conversations",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversations_owner_created",
        "conversations",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversations_owner_id"), "conversations", ["owner_id"], unique=False
    )

    # 3. Messages (references conversations)
    op.create_table(
        "messages",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("conversation_id", app.models.base.GUID(), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_messages_conv_sequence",
        "messages",
        ["conversation_id", "sequence_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_messages_conversation_id"),
        "messages",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "ix_messages_owner_created",
        "messages",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_messages_owner_id"), "messages", ["owner_id"], unique=False
    )

    # 4. Verifications (references conversations and messages, FK to llm_runs added after)
    op.create_table(
        "verifications",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("conversation_id", app.models.base.GUID(), nullable=True),
        sa.Column("message_id", app.models.base.GUID(), nullable=True),
        sa.Column("llm_run_id", app.models.base.GUID(), nullable=True),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("total_claims", sa.Integer(), nullable=False),
        sa.Column("supported_claims", sa.Integer(), nullable=False),
        sa.Column("contradicted_claims", sa.Integer(), nullable=False),
        sa.Column("unknown_claims", sa.Integer(), nullable=False),
        sa.Column("non_factual_claims", sa.Integer(), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=True),
        sa.Column("calibrated_confidence", sa.Float(), nullable=True),
        sa.Column("is_calibrated", sa.Boolean(), nullable=False),
        sa.Column("calibration_status", sa.String(length=32), nullable=False),
        sa.Column("degraded_evaluation", sa.Boolean(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_verifications_conversation_id"),
        "verifications",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_verifications_llm_run_id"),
        "verifications",
        ["llm_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_verifications_message_id"),
        "verifications",
        ["message_id"],
        unique=False,
    )
    op.create_index(
        "ix_verifications_owner_created",
        "verifications",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_verifications_owner_id"), "verifications", ["owner_id"], unique=False
    )
    op.create_index(
        op.f("ix_verifications_status"), "verifications", ["status"], unique=False
    )
    op.create_index(
        "ix_verifications_status_created",
        "verifications",
        ["status", "created_at"],
        unique=False,
    )

    # 5. LLM Runs (references conversations, messages, FK to verifications added after)
    op.create_table(
        "llm_runs",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("conversation_id", app.models.base.GUID(), nullable=False),
        sa.Column("message_id", app.models.base.GUID(), nullable=True),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("verification_id", app.models.base.GUID(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_llm_runs_conversation_id"),
        "llm_runs",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_llm_runs_message_id"), "llm_runs", ["message_id"], unique=False
    )
    op.create_index(
        "ix_llm_runs_owner_created",
        "llm_runs",
        ["owner_id", "started_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_llm_runs_owner_id"), "llm_runs", ["owner_id"], unique=False
    )
    op.create_index(
        "ix_llm_runs_provider_model",
        "llm_runs",
        ["provider", "model_name"],
        unique=False,
    )
    op.create_index(op.f("ix_llm_runs_status"), "llm_runs", ["status"], unique=False)
    op.create_index(
        op.f("ix_llm_runs_verification_id"),
        "llm_runs",
        ["verification_id"],
        unique=False,
    )

    # Circular Foreign Keys between verifications and llm_runs
    op.create_foreign_key(
        "fk_verifications_llm_run_id",
        "verifications",
        "llm_runs",
        ["llm_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_llm_runs_verification_id",
        "llm_runs",
        "verifications",
        ["verification_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 6. Claims (references verifications)
    op.create_table(
        "claims",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("verification_id", app.models.base.GUID(), nullable=False),
        sa.Column("claim_index", sa.Integer(), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("verdict", sa.String(length=32), nullable=True),
        sa.Column("is_verifiable", sa.Boolean(), nullable=False),
        sa.Column("degraded_evaluation", sa.Boolean(), nullable=False),
        sa.Column("arbitration_reason", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("is_calibrated", sa.Boolean(), nullable=False),
        sa.Column("calibration_status", sa.String(length=32), nullable=False),
        sa.Column("unknown_reason", sa.String(length=64), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["verification_id"], ["verifications.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "verification_id", "claim_index", name="uq_claims_verification_index"
        ),
    )
    op.create_index(op.f("ix_claims_verdict"), "claims", ["verdict"], unique=False)
    op.create_index(
        op.f("ix_claims_verification_id"), "claims", ["verification_id"], unique=False
    )
    op.create_index(
        "ix_claims_verification_verdict",
        "claims",
        ["verification_id", "verdict"],
        unique=False,
    )

    # 7. Evidence Items (references claims)
    op.create_table(
        "evidence_items",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("claim_id", app.models.base.GUID(), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("source_title", sa.String(length=512), nullable=True),
        sa.Column("publisher", sa.String(length=256), nullable=True),
        sa.Column("publication_date", sa.String(length=64), nullable=True),
        sa.Column("retrieval_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("query_used", sa.Text(), nullable=True),
        sa.Column("retriever_name", sa.String(length=64), nullable=False),
        sa.Column("evidence_source", sa.String(length=32), nullable=False),
        sa.Column("document_id", app.models.base.GUID(), nullable=True),
        sa.Column("chunk_id", app.models.base.GUID(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("authority_score", sa.Float(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evidence_items_claim_id"), "evidence_items", ["claim_id"], unique=False
    )

    # 8. Judge Evaluations (references claims)
    op.create_table(
        "judge_evaluations",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("claim_id", app.models.base.GUID(), nullable=False),
        sa.Column("judge_name", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("evaluation_type", sa.String(length=32), nullable=False),
        sa.Column("judgment", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("evidence_references", sa.JSON(), nullable=True),
        sa.Column("evaluation_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_judge_evaluations_claim_id"),
        "judge_evaluations",
        ["claim_id"],
        unique=False,
    )

    # 9. Audit Records (references verifications)
    op.create_table(
        "audit_records",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("verification_id", app.models.base.GUID(), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["verification_id"], ["verifications.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_records_stage"), "audit_records", ["stage"], unique=False
    )
    op.create_index(
        op.f("ix_audit_records_timestamp"), "audit_records", ["timestamp"], unique=False
    )
    op.create_index(
        op.f("ix_audit_records_verification_id"),
        "audit_records",
        ["verification_id"],
        unique=False,
    )

    # 10. Knowledge Documents
    op.create_table(
        "knowledge_documents",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("filename", sa.String(length=256), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_id", "content_hash", name="uq_knowledge_doc_owner_hash"
        ),
    )
    op.create_index(
        "ix_knowledge_docs_owner_created",
        "knowledge_documents",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_documents_content_hash"),
        "knowledge_documents",
        ["content_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_documents_owner_id"),
        "knowledge_documents",
        ["owner_id"],
        unique=False,
    )

    # 11. Knowledge Chunks (references knowledge_documents)
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("document_id", app.models.base.GUID(), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id", "chunk_index", name="uq_knowledge_chunk_doc_index"
        ),
    )
    op.create_index(
        op.f("ix_knowledge_chunks_document_id"),
        "knowledge_chunks",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_chunks_owner_doc",
        "knowledge_chunks",
        ["owner_id", "document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_chunks_owner_id"),
        "knowledge_chunks",
        ["owner_id"],
        unique=False,
    )

    # 12. Ingested Payloads (references verifications)
    op.create_table(
        "ingested_payloads",
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("captured_text", sa.Text(), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("client_version", sa.String(length=32), nullable=True),
        sa.Column("capture_metadata", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("verification_id", app.models.base.GUID(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["verification_id"], ["verifications.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ingested_payloads_created_at",
        "ingested_payloads",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingested_payloads_model_name"),
        "ingested_payloads",
        ["model_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingested_payloads_session_id"),
        "ingested_payloads",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingested_payloads_source"),
        "ingested_payloads",
        ["source"],
        unique=False,
    )
    op.create_index(
        "ix_ingested_payloads_source_status",
        "ingested_payloads",
        ["source", "status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingested_payloads_status"),
        "ingested_payloads",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingested_payloads_verification_id"),
        "ingested_payloads",
        ["verification_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_verifications_llm_run_id", "verifications", type_="foreignkey"
    )
    op.drop_constraint("fk_llm_runs_verification_id", "llm_runs", type_="foreignkey")

    op.drop_table("ingested_payloads")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
    op.drop_table("audit_records")
    op.drop_table("judge_evaluations")
    op.drop_table("evidence_items")
    op.drop_table("claims")
    op.drop_table("llm_runs")
    op.drop_table("verifications")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("users")
