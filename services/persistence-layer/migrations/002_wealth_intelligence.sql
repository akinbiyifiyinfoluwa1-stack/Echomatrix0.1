-- EchoMatrix wealth and intelligence persistence extension.

CREATE TABLE IF NOT EXISTS research_findings (
    id SERIAL PRIMARY KEY,
    correlation_id VARCHAR(128),
    topic VARCHAR(200) NOT NULL,
    symbol VARCHAR(64),
    title VARCHAR(300) NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    source VARCHAR(500) NOT NULL DEFAULT '',
    relevance NUMERIC(8,6) NOT NULL DEFAULT 0,
    confidence NUMERIC(8,6) NOT NULL DEFAULT 0,
    tags JSONB NOT NULL DEFAULT '[]',
    market_implications TEXT NOT NULL DEFAULT '',
    risk_flags JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_research_symbol ON research_findings(symbol);

CREATE TABLE IF NOT EXISTS memory_records (
    id SERIAL PRIMARY KEY,
    memory_id VARCHAR(128) NOT NULL UNIQUE,
    memory_type VARCHAR(32) NOT NULL,
    owner_id VARCHAR(128) NOT NULL DEFAULT 'system',
    symbol VARCHAR(64) NOT NULL DEFAULT '',
    title VARCHAR(300) NOT NULL,
    content TEXT NOT NULL,
    confidence NUMERIC(8,6) NOT NULL DEFAULT 0.5,
    tags JSONB NOT NULL DEFAULT '[]',
    source VARCHAR(300) NOT NULL DEFAULT 'echomatrix',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_symbol_type ON memory_records(symbol, memory_type);

CREATE TABLE IF NOT EXISTS workflow_runs (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(128) NOT NULL UNIQUE,
    correlation_id VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL,
    current_stage VARCHAR(64) NOT NULL DEFAULT 'created',
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_correlation ON workflow_runs(correlation_id);

CREATE TABLE IF NOT EXISTS workflow_events (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES workflow_runs(id),
    event_id VARCHAR(128) NOT NULL UNIQUE,
    correlation_id VARCHAR(128) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    source VARCHAR(128) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_events_correlation
ON workflow_events(correlation_id);
