-- ==============================================================================
-- VerifAI — PostgreSQL Database Initialization Schema
-- Provides full schema DDL, indexes, constraints, and cascade policies matching
-- SQLAlchemy 2.x ORM models 1:1.
-- ==============================================================================

-- Enable UUID and cryptographic extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. USERS & ACCESS CONTROL
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(64) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'USER',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ------------------------------------------------------------------------------
-- 2. CHAT & CONVERSATIONS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id VARCHAR(128) NOT NULL,
    title VARCHAR(256) NOT NULL DEFAULT 'New Conversation',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_owner ON conversations(owner_id);
CREATE INDEX IF NOT EXISTS idx_conversations_owner_created ON conversations(owner_id, created_at DESC);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    owner_id VARCHAR(128) NOT NULL,
    role VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    sequence_number INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_owner ON messages(owner_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_seq ON messages(conversation_id, sequence_number ASC);

CREATE TABLE IF NOT EXISTS llm_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    owner_id VARCHAR(128) NOT NULL,
    provider VARCHAR(64) NOT NULL,
    model_name VARCHAR(128) NOT NULL,
    model_version VARCHAR(64),
    prompt TEXT NOT NULL,
    response TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    latency_ms DOUBLE PRECISION,
    error_code VARCHAR(64),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_llm_runs_conversation ON llm_runs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_llm_runs_owner ON llm_runs(owner_id);
CREATE INDEX IF NOT EXISTS idx_llm_runs_status ON llm_runs(status);

-- ------------------------------------------------------------------------------
-- 3. VERIFICATION ENGINE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id VARCHAR(128) NOT NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    llm_run_id UUID REFERENCES llm_runs(id) ON DELETE SET NULL,
    input_text TEXT NOT NULL,
    query TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    content_type VARCHAR(32) NOT NULL DEFAULT 'FACTUAL',
    total_claims INTEGER NOT NULL DEFAULT 0,
    supported_claims INTEGER NOT NULL DEFAULT 0,
    contradicted_claims INTEGER NOT NULL DEFAULT 0,
    unknown_claims INTEGER NOT NULL DEFAULT 0,
    non_factual_claims INTEGER NOT NULL DEFAULT 0,
    trust_score DOUBLE PRECISION,
    calibrated_confidence DOUBLE PRECISION,
    is_calibrated BOOLEAN NOT NULL DEFAULT FALSE,
    calibration_status VARCHAR(32) NOT NULL DEFAULT 'NOT_CALIBRATED',
    degraded_evaluation BOOLEAN NOT NULL DEFAULT FALSE,
    summary TEXT,
    error_message TEXT,
    completed_at TIMESTAMPTZ,
    execution_metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_verifications_owner ON verifications(owner_id);
CREATE INDEX IF NOT EXISTS idx_verifications_status ON verifications(status);
CREATE INDEX IF NOT EXISTS idx_verifications_status_created ON verifications(status, created_at);
CREATE INDEX IF NOT EXISTS idx_verifications_owner_created ON verifications(owner_id, created_at DESC);

CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verification_id UUID NOT NULL REFERENCES verifications(id) ON DELETE CASCADE,
    claim_index INTEGER NOT NULL,
    claim_text TEXT NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    content_type VARCHAR(32) NOT NULL DEFAULT 'FACTUAL',
    verdict VARCHAR(32),
    is_verifiable BOOLEAN NOT NULL DEFAULT TRUE,
    degraded_evaluation BOOLEAN NOT NULL DEFAULT FALSE,
    arbitration_reason TEXT,
    confidence DOUBLE PRECISION,
    is_calibrated BOOLEAN NOT NULL DEFAULT FALSE,
    calibration_status VARCHAR(32) NOT NULL DEFAULT 'NOT_CALIBRATED',
    unknown_reason VARCHAR(64),
    explanation TEXT,
    metadata_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_claims_verification_index UNIQUE (verification_id, claim_index)
);

CREATE INDEX IF NOT EXISTS idx_claims_verification ON claims(verification_id);
CREATE INDEX IF NOT EXISTS idx_claims_verdict ON claims(verdict);
CREATE INDEX IF NOT EXISTS idx_claims_verification_verdict ON claims(verification_id, verdict);

CREATE TABLE IF NOT EXISTS evidence_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    source_url VARCHAR(2048),
    source_title VARCHAR(512),
    publisher VARCHAR(256),
    publication_date VARCHAR(64),
    retrieval_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    snippet TEXT NOT NULL,
    query_used TEXT,
    retriever_name VARCHAR(64) NOT NULL,
    evidence_source VARCHAR(32) NOT NULL DEFAULT 'EXTERNAL',
    document_id UUID,
    chunk_id UUID,
    relevance_score DOUBLE PRECISION,
    authority_score DOUBLE PRECISION,
    metadata_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidence_items_claim ON evidence_items(claim_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_source ON evidence_items(evidence_source);

CREATE TABLE IF NOT EXISTS judge_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    judge_name VARCHAR(64) NOT NULL,
    model_version VARCHAR(64),
    evaluation_type VARCHAR(32) NOT NULL DEFAULT 'NLI_ENTAILMENT',
    judgment VARCHAR(32) NOT NULL,
    confidence DOUBLE PRECISION,
    reasoning TEXT,
    execution_time_ms DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_judge_evaluations_claim ON judge_evaluations(claim_id);
CREATE INDEX IF NOT EXISTS idx_judge_evaluations_judgment ON judge_evaluations(judgment);

CREATE TABLE IF NOT EXISTS audit_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verification_id UUID NOT NULL REFERENCES verifications(id) ON DELETE CASCADE,
    stage VARCHAR(32) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    status VARCHAR(16) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_records_verification ON audit_records(verification_id);
CREATE INDEX IF NOT EXISTS idx_audit_records_stage ON audit_records(stage);
CREATE INDEX IF NOT EXISTS idx_audit_records_timestamp ON audit_records(timestamp DESC);

-- ------------------------------------------------------------------------------
-- 4. KNOWLEDGE BASE & RETRIEVAL
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id VARCHAR(128) NOT NULL,
    filename VARCHAR(256) NOT NULL,
    title VARCHAR(256) NOT NULL,
    description TEXT,
    content_type VARCHAR(64) NOT NULL,
    size_bytes INTEGER NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    metadata_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_knowledge_doc_owner_hash UNIQUE (owner_id, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_docs_owner ON knowledge_documents(owner_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_owner_created ON knowledge_documents(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_hash ON knowledge_documents(content_hash);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    owner_id VARCHAR(128) NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    metadata_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_knowledge_chunk_doc_index UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_doc ON knowledge_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_owner ON knowledge_chunks(owner_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_owner_doc ON knowledge_chunks(owner_id, document_id);

-- ------------------------------------------------------------------------------
-- 5. INGESTION & CAPTURE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ingested_payloads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(32) NOT NULL DEFAULT 'CHROME_EXTENSION',
    source_url TEXT,
    model_name VARCHAR(128),
    prompt TEXT,
    captured_text TEXT NOT NULL,
    session_id VARCHAR(128),
    client_version VARCHAR(32),
    capture_metadata JSONB,
    status VARCHAR(32) NOT NULL DEFAULT 'RECEIVED',
    verification_id UUID REFERENCES verifications(id) ON DELETE SET NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ingested_payloads_source ON ingested_payloads(source);
CREATE INDEX IF NOT EXISTS idx_ingested_payloads_status ON ingested_payloads(status);
CREATE INDEX IF NOT EXISTS idx_ingested_payloads_session ON ingested_payloads(session_id);
CREATE INDEX IF NOT EXISTS idx_ingested_payloads_verification ON ingested_payloads(verification_id);
CREATE INDEX IF NOT EXISTS idx_ingested_payloads_created ON ingested_payloads(created_at);
CREATE INDEX IF NOT EXISTS idx_ingested_payloads_source_status ON ingested_payloads(source, status);
