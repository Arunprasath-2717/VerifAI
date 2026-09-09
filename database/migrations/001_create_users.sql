-- ==============================================================================
-- VerifAI Migration 001: Create Application Users Table
-- ==============================================================================
-- Maps 1-to-1 with Supabase Auth identity (auth.users.id).
-- Contains minimal user profile information required for VerifAI MVP.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast lookup by email during authentication synchronization
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
