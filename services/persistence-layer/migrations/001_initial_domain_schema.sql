-- EchoMatrix initial relational schema.
-- This migration is intentionally idempotent and mirrors app/domain_models.py.

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(128) NOT NULL UNIQUE,
    email VARCHAR(320) NOT NULL UNIQUE,
    display_name VARCHAR(160) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    account_name VARCHAR(160) NOT NULL,
    provider VARCHAR(64) NOT NULL DEFAULT 'demo',
    account_type VARCHAR(32) NOT NULL DEFAULT 'simulation',
    currency VARCHAR(16) NOT NULL DEFAULT 'USD',
    balance NUMERIC(28,10) NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_account_name UNIQUE(user_id, account_name)
);

CREATE TABLE IF NOT EXISTS instruments (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL DEFAULT '',
    asset_class VARCHAR(32) NOT NULL,
    exchange VARCHAR(80) NOT NULL DEFAULT '',
    base_currency VARCHAR(16) NOT NULL DEFAULT '',
    quote_currency VARCHAR(16) NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS market_observations (
    id SERIAL PRIMARY KEY,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id),
    timeframe VARCHAR(16) NOT NULL DEFAULT 'tick',
    observed_at TIMESTAMPTZ NOT NULL,
    open NUMERIC(28,10),
    high NUMERIC(28,10),
    low NUMERIC(28,10),
    close NUMERIC(28,10),
    volume NUMERIC(32,10),
    payload JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_market_observations_instrument_time
ON market_observations(instrument_id, observed_at DESC);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    instrument_id INTEGER NOT NULL REFERENCES instruments(id),
    correlation_id VARCHAR(128) NOT NULL,
    side VARCHAR(16) NOT NULL,
    order_type VARCHAR(16) NOT NULL DEFAULT 'market',
    quantity NUMERIC(28,10) NOT NULL,
    requested_price NUMERIC(28,10),
    status VARCHAR(32) NOT NULL DEFAULT 'created',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_correlation ON orders(correlation_id);

CREATE TABLE IF NOT EXISTS fills (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    fill_price NUMERIC(28,10) NOT NULL,
    quantity NUMERIC(28,10) NOT NULL,
    fee NUMERIC(28,10) NOT NULL DEFAULT 0,
    filled_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    instrument_id INTEGER NOT NULL REFERENCES instruments(id),
    quantity NUMERIC(28,10) NOT NULL DEFAULT 0,
    average_entry_price NUMERIC(28,10) NOT NULL DEFAULT 0,
    realized_pnl NUMERIC(28,10) NOT NULL DEFAULT 0,
    unrealized_pnl NUMERIC(28,10) NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    equity NUMERIC(28,10) NOT NULL,
    cash NUMERIC(28,10) NOT NULL,
    exposure NUMERIC(28,10) NOT NULL DEFAULT 0,
    drawdown NUMERIC(12,8) NOT NULL DEFAULT 0,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS intelligence_decisions (
    id SERIAL PRIMARY KEY,
    correlation_id VARCHAR(128) NOT NULL,
    symbol VARCHAR(64) NOT NULL,
    stage VARCHAR(64) NOT NULL,
    action VARCHAR(32) NOT NULL,
    confidence NUMERIC(8,6) NOT NULL DEFAULT 0,
    rationale TEXT NOT NULL DEFAULT '',
    payload JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_intelligence_decisions_correlation
ON intelligence_decisions(correlation_id);

CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    correlation_id VARCHAR(128) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    actor VARCHAR(128) NOT NULL DEFAULT 'system',
    action VARCHAR(128) NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_correlation ON audit_events(correlation_id);
