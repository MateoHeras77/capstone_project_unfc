-- Seed File: Initial Assets
-- This will populate the 'assets' table with common symbols for testing.

INSERT INTO assets (symbol, name, asset_type, currency)
VALUES 
    ('AAPL', 'Apple Inc.', 'stock', 'USD'),
    ('BTC-USD', 'Bitcoin', 'crypto', 'USD'),
    ('ETH-USD', 'Ethereum', 'crypto', 'USD'),
    ('^GSPC', 'S&P 500', 'index', 'USD'),
    ('GC=F', 'Gold', 'stock', 'USD')
ON CONFLICT (symbol) DO NOTHING;
