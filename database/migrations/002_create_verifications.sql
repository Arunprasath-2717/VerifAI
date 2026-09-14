-- ==============================================================================
-- VerifAI Migration 002: Create Verifications Table
-- ==============================================================================
-- Stores every AI-claim verification request submitted by an authenticated user.
-- Each row represents one complete verification attempt: input claim, AI verdict,
-- evidence sources, trust score, and lifecycle metadata.
--
-- Depends on: 001_create_users.sql (users table must already exist)
-- ==============================================================================

CREATE TYPE IF NOT EXISTS verification_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed'
);

CREATE TABLE IF NOT EXISTS verifications (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    claim         TEXT        NOT NULL,
    status        verification_status NOT NULL DEFAULT 'pending',
    verdict       TEXT,
    trust_score   NUMERIC(4, 3),
    evidence      JSONB,
    error_message TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast per-user history queries (most common access pattern)
CREATE INDEX IF NOT EXISTS idx_verifications_user_id
    ON verifications(user_id);

-- Index for status-based filtering / admin / background job queries
CREATE INDEX IF NOT EXISTS idx_verifications_status
    ON verifications(status);

-- Composite index: user history sorted by newest first
CREATE INDEX IF NOT EXISTS idx_verifications_user_created
    ON verifications(user_id, created_at DESC);
