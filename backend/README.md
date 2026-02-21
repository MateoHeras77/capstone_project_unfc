# Backend — Investment Analytics API

FastAPI backend for the Educational Investment Platform.

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app (lifespan, middleware, router mount)
│   └── api/
│       ├── dependencies.py      # Shared FastAPI Depends helpers (get_db)
│       └── v1/
│           ├── router.py        # Aggregates all v1 routers
│           └── endpoints/
│               ├── assets.py    # GET /assets, POST /assets/sync/{symbol}
│               ├── prices.py    # GET /prices/{symbol}
│               └── forecast.py  # POST /forecast/{base,lstm,prophet}
├── analytics/
│   └── forecasting/
│       ├── base.py              # BaseForecastor (ABC) + SimpleForecaster (EWM)
│       ├── lstm.py              # LSTMForecastor (TensorFlow)
│       └── prophet.py           # ProphetForecaster (Facebook Prophet)
├── core/
│   ├── config.py                # pydantic-settings BaseSettings (from .env)
│   └── database.py              # Supabase client singleton
├── data_engine/
│   ├── coordinator.py           # Smart-cache orchestrator (yfinance → Supabase)
│   └── fetcher.py               # yfinance wrapper (isolated external calls)
├── schemas/
│   ├── assets.py                # AssetOut, PriceOut, SyncResponse
│   └── forecast.py              # ForecastRequest, ForecastResponse
├── tests/
│   ├── conftest.py              # Shared fixtures (mock_db, app_client)
│   └── test_sync.py             # Sync smoke-tests
└── supabase/
    └── migrations/              # SQL migration files
```

---

## Quick Start

### 1. Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (or pip)
- [Supabase CLI](https://supabase.com/docs/guides/cli)

### 2. Environment

Create `backend/.env` (never commit this):

```bash
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=<your-local-anon-key>
DEBUG=true
```

For production, set `SUPABASE_URL`, `SUPABASE_KEY`, and optionally `FRONTEND_URL` as real environment variables.

### 3. Local Supabase

```bash
# From the backend/ directory:
supabase start           # start local stack
supabase migration up    # apply schema migrations
```

Verify tables in [Supabase Studio](http://localhost:54323).

### 4. Install dependencies

```bash
cd backend
uv sync           # or: pip install -e .
```

### 5. Run the API

```bash
python main.py
# or:
uvicorn app.main:app --reload
```

- API:      http://localhost:8000
- Swagger:  http://localhost:8000/docs
- ReDoc:    http://localhost:8000/redoc

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/api/v1/assets/` | List all cached assets |
| POST | `/api/v1/assets/sync/{symbol}` | Fetch & cache a symbol from Yahoo Finance |
| GET | `/api/v1/prices/{symbol}` | Historical OHLCV data (newest first) |
| POST | `/api/v1/forecast/base` | EWM baseline forecast (fast, no GPU) |
| POST | `/api/v1/forecast/lstm` | LSTM neural-network forecast |
| POST | `/api/v1/forecast/prophet` | Facebook Prophet forecast |

---

## Running Tests

```bash
# Unit tests only (no DB, no network):
pytest tests/ -v -m "not integration"

# Integration tests (requires running local Supabase):
pytest tests/ -v -m integration
```

---

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Separation of concerns** | Routes are thin HTTP adapters; logic lives in `analytics/` and `data_engine/`. |
| **Single source for external calls** | All yfinance calls go through `data_engine/fetcher.py` only. |
| **Typed everywhere** | Every function has type hints and a docstring. |
| **Fail fast** | `pydantic-settings` validates env vars at startup — no silent misconfigurations. |
| **Smart cache** | `coordinator.py` upserts data idempotently; duplicate timestamps are ignored by the DB. |

