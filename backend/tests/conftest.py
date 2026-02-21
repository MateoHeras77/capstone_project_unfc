"""
tests/conftest.py
──────────────────
Shared pytest fixtures for the backend test suite.

Fixtures
--------
app_client
    ``httpx.AsyncClient`` wired to the FastAPI app with a mocked Supabase
    client so tests never hit the real database.

mock_db
    ``MagicMock`` standing in for the Supabase client, pre-configured with
    sensible defaults so individual tests can override only what they need.

Usage
-----
    async def test_health(app_client):
        resp = await app_client.get("/")
        assert resp.status_code == 200
"""

from typing import AsyncGenerator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_db
from app.main import app


# ── Mock Supabase client ──────────────────────────────────────────────────────


@pytest.fixture
def mock_db() -> MagicMock:
    """
    Return a MagicMock that mimics the Supabase client's fluent query builder.

    The default return value for ``.execute()`` is ``MagicMock(data=[])``.
    Override in individual tests as needed:

        def test_something(mock_db):
            mock_db.table().select().execute.return_value = MagicMock(
                data=[{"id": "1", "symbol": "AAPL"}]
            )
    """
    client = MagicMock()
    # Default: any chain ending in .execute() returns an empty data list.
    client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
        data=[]
    )
    client.table.return_value.select.return_value.execute.return_value = MagicMock(
        data=[]
    )
    return client


# ── Test client ───────────────────────────────────────────────────────────────


@pytest.fixture
async def app_client(mock_db: MagicMock) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTPX client with Supabase dependency overridden by ``mock_db``.

    Startup lifespan is skipped to avoid real DB connections in tests.
    """
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ── Synchronous test client (for non-async tests) ─────────────────────────────


@pytest.fixture
def sync_client(mock_db: MagicMock) -> TestClient:
    """
    Synchronous ``TestClient`` for simpler, non-async tests.

    Uses the same ``mock_db`` override as ``app_client``.
    """
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()
