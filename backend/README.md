# Backend - Foundation Setup (Phase 1)

This directory contains the core logic for the Data Engine, Forecasting, and Optimization modules.

## Environment Setup

To connect to Supabase, you must set the following environment variables. You can create a `.env` file in this directory:

```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_or_service_key
```

## Database Initialization

1.  Ensure you have the Supabase CLI installed.
2.  Start your local Supabase instance if not already running: `supabase start`.
3.  Apply the migrations to your local database: `supabase migration up`.
4.  Verification: Checks the local [Supabase Studio](http://localhost:54323) to see the `assets` and `historical_prices` tables.

## Components

*   **`core/database.py`**: Initializes the Supabase client.
*   **`data_engine/yfinance_fetcher.py`**: A wrapper for `yfinance` to pull weekly/monthly data.
*   **`data_engine/data_coordinator.py`**: The logic that checks if data exists in Supabase before fetching it from the market.

## Usage (Experimental)

Once the variables are set and the schema is created, you can test the sync by running a simple script:

```python
from backend.data_engine.data_coordinator import DataCoordinator

coordinator = DataCoordinator()
coordinator.sync_asset("BTC-USD", "crypto", interval="1wk")
```
