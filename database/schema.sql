-- ==============================================================================
-- VerifAI Complete Database Reference Schema
-- Last updated: Phase 2A (Verification Persistence Foundation)
-- ==============================================================================
-- Engine: PostgreSQL 15+ / Supabase
-- Extensions: uuid-ossp (optional/default in Supabase)
-- ==============================================================================

-- Phase 1: Application Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- Phase 2A: Verifications Table
-- ==============================================================================
-- Stores every AI-claim verification request submitted by an authenticated user.
-- Each row represents one complete verification: input claim, AI verdict,
-- evidence sources, trust score, and lifecycle metadata.
-- Depends on: users table (Phase 1)
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

-- Fast per-user history queries (most common access pattern)
CREATE INDEX IF NOT EXISTS idx_verifications_user_id
    ON verifications(user_id);

-- Status-based filtering for admin / background job queries
CREATE INDEX IF NOT EXISTS idx_verifications_status
    ON verifications(status);

-- Composite: user history sorted by newest first
CREATE INDEX IF NOT EXISTS idx_verifications_user_created
    ON verifications(user_id, created_at DESC);

