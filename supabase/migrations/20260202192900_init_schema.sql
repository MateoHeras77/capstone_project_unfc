-- Migration: Phase 1 Foundations
-- Description: Sets up the assets and historical_prices tables for Weekly/Monthly tracking.

-- 1. Assets Metadata Table
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT UNIQUE NOT NULL, -- e.g., 'AAPL', 'BTC-USD'
    name TEXT,
    asset_type TEXT CHECK (asset_type IN ('stock', 'crypto', 'index')),
    currency TEXT DEFAULT 'USD',
    last_updated TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Historical Prices Table
CREATE TABLE IF NOT EXISTS historical_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    interval TEXT NOT NULL CHECK (interval IN ('1wk', '1mo')),
    timestamp TIMESTAMPTZ NOT NULL,
    open_price DECIMAL(20, 6),
    high_price DECIMAL(20, 6),
    low_price DECIMAL(20, 6),
    close_price DECIMAL(20, 6) NOT NULL,
    volume BIGINT,
    
    -- Ensure unique entries for an asset at a specific time and interval
    UNIQUE(asset_id, timestamp, interval)
);

-- Indexing for performance
CREATE INDEX IF NOT EXISTS idx_prices_asset_interval ON historical_prices(asset_id, interval, timestamp DESC);
