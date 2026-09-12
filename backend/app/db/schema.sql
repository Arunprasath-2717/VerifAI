-- VerifAI Core Database Schema (PostgreSQL / Supabase / SQLite compatible)
-- Read-only layer queries these tables without modifying core schemas.

CREATE TABLE IF NOT EXISTS sources (
    id VARCHAR(64) PRIMARY KEY,
    url TEXT NOT NULL,
    domain VARCHAR(255) NOT NULL,
    quality_score FLOAT DEFAULT 0.8,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verifications (
    id VARCHAR(64) PRIMARY KEY,
    query TEXT NOT NULL,
    trust_score FLOAT, -- Centralized score produced by core engine
    status VARCHAR(32) DEFAULT 'COMPLETED',
    domain VARCHAR(128) NOT NULL,
    model_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) DEFAULT 'user_default',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS claims (
    id VARCHAR(64) PRIMARY KEY,
    verification_id VARCHAR(64) NOT NULL REFERENCES verifications(id) ON DELETE CASCADE,
    claim_text TEXT NOT NULL,
    verdict VARCHAR(32) NOT NULL, -- SUPPORTED, CONTRADICTED, INCONCLUSIVE
    confidence FLOAT, -- Float 0.0 to 1.0. NULL represents "No verification signal"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence (
    id VARCHAR(64) PRIMARY KEY,
    claim_id VARCHAR(64) NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    source_id VARCHAR(64) REFERENCES sources(id),
    status VARCHAR(32) NOT NULL, -- SUPPORT, CONTRADICT, UNKNOWN
    strength FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS consistency_results (
    id VARCHAR(64) PRIMARY KEY,
    verification_id VARCHAR(64) NOT NULL REFERENCES verifications(id) ON DELETE CASCADE,
    signal_type VARCHAR(32) NOT NULL, -- entailment, contradiction, absent, refused, failed_judgment
    quality_score FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_runs (
    id VARCHAR(64) PRIMARY KEY,
    model_id VARCHAR(64) NOT NULL,
    model_name VARCHAR(128) NOT NULL,
    provider VARCHAR(64) NOT NULL,
    token_count INT DEFAULT 0,
    latency_ms INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS benchmark_results (
    id VARCHAR(64) PRIMARY KEY,
    benchmark_id VARCHAR(64) NOT NULL,
    model_id VARCHAR(64) NOT NULL,
    sampling_basis VARCHAR(64) NOT NULL DEFAULT 'prompt_generation', -- prompt_generation OR response_rewrite
    item_id VARCHAR(64) NOT NULL,
    claim_text TEXT,
    ground_truth VARCHAR(32), -- SUPPORTED, CONTRADICTED, INCONCLUSIVE
    predicted_verdict VARCHAR(32), -- SUPPORTED, CONTRADICTED, INCONCLUSIVE
    precision FLOAT,
    recall FLOAT,
    f1 FLOAT,
    accuracy FLOAT,
    ece FLOAT, -- Expected Calibration Error
    latency_ms INT DEFAULT 0,
    llm_calls INT DEFAULT 0,
    search_calls INT DEFAULT 0,
    token_usage INT DEFAULT 0,
    status VARCHAR(32) DEFAULT 'SUCCESS', -- SUCCESS, FAILED
    resample_count INT DEFAULT 1,
    successful_resamples INT DEFAULT 1,
    failed_resamples INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Derived views for fast aggregations
CREATE VIEW IF NOT EXISTS view_verification_aggregates AS
SELECT 
    v.id AS verification_id,
    v.domain,
    v.model_id,
    v.trust_score,
    v.created_at,
    COUNT(c.id) AS total_claims,
    SUM(CASE WHEN c.verdict = 'SUPPORTED' THEN 1 ELSE 0 END) AS supported_claims,
    SUM(CASE WHEN c.verdict = 'CONTRADICTED' THEN 1 ELSE 0 END) AS contradicted_claims,
    SUM(CASE WHEN c.verdict = 'INCONCLUSIVE' THEN 1 ELSE 0 END) AS inconclusive_claims,
    AVG(c.confidence) AS avg_confidence
FROM verifications v
LEFT JOIN claims c ON v.id = c.verification_id
GROUP BY v.id, v.domain, v.model_id, v.trust_score, v.created_at;
