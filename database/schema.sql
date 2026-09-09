-- ==============================================================================
-- VerifAI Complete Database Reference Schema
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

