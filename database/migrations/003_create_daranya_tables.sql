-- ==============================================================================
-- VerifAI Phase 3: Daranya's Modules
-- History + Reports + Audit + Claim Provenance
-- ==============================================================================

-- 1. Audit Events Table
-- Captures state transitions and system events during the verification lifecycle.
CREATE TABLE IF NOT EXISTS audit_events (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verification_id UUID NOT NULL REFERENCES verifications(id) ON DELETE CASCADE,
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stage         VARCHAR(100) NOT NULL, -- e.g., 'pending', 'processing', 'completed', 'failed', 'claim_extraction'
    status        VARCHAR(32) NOT NULL,  -- e.g., 'started', 'success', 'error'
    metadata      JSONB,                 -- Contextual info, e.g., processing times, sub-stage data
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Fast lookup for a specific user's audit timeline or verification timeline
CREATE INDEX IF NOT EXISTS idx_audit_events_verification_id ON audit_events(verification_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_user_id ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at DESC);

-- 2. Reports Table
-- Stores metadata about generated reports (PDF, JSON, CSV).
CREATE TABLE IF NOT EXISTS reports (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verification_id UUID NOT NULL REFERENCES verifications(id) ON DELETE CASCADE,
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    format        VARCHAR(16) NOT NULL,  -- 'pdf', 'json', 'csv'
    report_type   VARCHAR(32) NOT NULL DEFAULT 'standard', -- 'standard', 'compliance'
    status        VARCHAR(32) NOT NULL DEFAULT 'generated', -- 'generating', 'generated', 'failed'
    file_path     TEXT,                  -- Local or S3 path to the generated file (optional if generated on the fly)
    file_size     INTEGER,               -- Size in bytes
    metadata      JSONB,                 -- Any additional report configuration/options
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Fast per-user reports lookup
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_verification_id ON reports(verification_id);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);

-- 3. Supplemental Tables for Provenance (if needed)
-- Note: As per Arun's core schema, the verification engine stores claims, evidence, and sources
-- within the `evidence` JSONB column of the `verifications` table.
-- Provenance APIs will read from that JSONB column.
