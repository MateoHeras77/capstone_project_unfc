"""
tests/test_assets.py
──────────────────────
HTTP-level tests for the asset and prices endpoints:

  GET    /api/v1/assets
  GET    /api/v1/assets/search?q=...
  GET    /api/v1/assets/{symbol}
  DELETE /api/v1/assets/{symbol}
  GET    /api/v1/prices/{symbol}          (including date-filter params)

All Supabase queries are mocked — no real DB connection is made.

Run with::

    cd backend
    uv run pytest tests/test_assets.py -v
"""
from unittest.mock import MagicMock

import pytest

# ── URL constants ─────────────────────────────────────────────────────────────

_ASSETS_URL = "/api/v1/assets"
_PRICES_URL = "/api/v1/prices"

# ── Shared stub rows ──────────────────────────────────────────────────────────

_AAPL_ASSET = {
    "id": "asset-uuid-aapl",
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "asset_type": "stock",
    "currency": "USD",
    "last_updated": "2024-01-01T00:00:00+00:00",
    "created_at": "2021-01-01T00:00:00+00:00",
}

_AMZN_ASSET = {
    "id": "asset-uuid-amzn",
    "symbol": "AMZN",
    "name": "Amazon.com Inc.",
    "asset_type": "stock",
    "currency": "USD",
    "last_updated": "2024-01-01T00:00:00+00:00",
    "created_at": "2021-01-01T00:00:00+00:00",
}

_PRICE_ROW = {
    "id": "price-uuid-1",
    "asset_id": "asset-uuid-aapl",
    "timestamp": "2024-01-01T00:00:00+00:00",
    "open_price": 185.0,
    "high_price": 190.0,
    "low_price": 183.0,
    "close_price": 188.0,
    "volume": 1000000,
}


# ── GET /api/v1/assets ────────────────────────────────────────────────────────


class TestListAssets:
    """Tests for the list-all-assets endpoint."""

    async def test_200_returns_list(self, app_client, mock_db) -> None:
        """Endpoint must return a list of assets from the database."""
        mock_db.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
            data=[_AAPL_ASSET, _AMZN_ASSET]
        )
        resp = await app_client.get(f"{_ASSETS_URL}/")
        assert resp.status_code == 200
        assert len(resp.json()) == 2
        assert resp.json()[0]["symbol"] == "AAPL"

    async def test_200_empty_when_no_assets(self, app_client, mock_db) -> None:
        """Empty database returns an empty list, not an error."""
        mock_db.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
            data=[]
        )
        resp = await app_client.get(f"{_ASSETS_URL}/")
        assert resp.status_code == 200
        assert resp.json() == []


# ── GET /api/v1/assets/search ─────────────────────────────────────────────────


class TestSearchAssets:
    """Tests for the symbol/name search endpoint."""

    def _wire_ilike(self, mock_db, rows: list) -> None:
        """Configure mock for the ilike → order → limit → execute chain."""
        (
            mock_db.table.return_value
            .select.return_value
            .ilike.return_value
            .order.return_value
            .limit.return_value
            .execute
        ).return_value = MagicMock(data=rows)

    async def test_200_returns_matching_symbols(self, app_client, mock_db) -> None:
        """Search by partial symbol returns matching assets."""
        self._wire_ilike(mock_db, [_AAPL_ASSET])
        resp = await app_client.get(f"{_ASSETS_URL}/search?q=AAPL")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["symbol"] == "AAPL"

    async def test_200_empty_list_when_no_match(self, app_client, mock_db) -> None:
        """Search with no match returns an empty list instead of an error."""
        self._wire_ilike(mock_db, [])
        # name fallback also returns nothing
        resp = await app_client.get(f"{_ASSETS_URL}/search?q=ZZZZ")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_422_query_too_long(self, app_client, mock_db) -> None:
        """Query string longer than 20 chars is rejected by Pydantic."""
        resp = await app_client.get(
            f"{_ASSETS_URL}/search?q=AAAAAAAAAAAAAAAAAAAAAAAAA"
        )
        assert resp.status_code == 422

    async def test_200_no_q_returns_recent(self, app_client, mock_db) -> None:
        """Omitting q falls back to most-recently-updated assets."""
        (
            mock_db.table.return_value
            .select.return_value
            .order.return_value
            .limit.return_value
            .execute
        ).return_value = MagicMock(data=[_AAPL_ASSET])
        resp = await app_client.get(f"{_ASSETS_URL}/search")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


# ── GET /api/v1/assets/{symbol} ───────────────────────────────────────────────


class TestGetAsset:
    """Tests for the single-asset lookup endpoint."""

    async def test_200_returns_asset(self, app_client, mock_db) -> None:
        """Known symbol returns full asset metadata."""
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute
        ).return_value = MagicMock(data=[_AAPL_ASSET])

        resp = await app_client.get(f"{_ASSETS_URL}/AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "AAPL"
        assert data["name"] == "Apple Inc."
        assert data["asset_type"] == "stock"

    async def test_200_lowercase_input_normalised(self, app_client, mock_db) -> None:
        """Lower-case ticker is uppercased before the DB query."""
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute
        ).return_value = MagicMock(data=[_AAPL_ASSET])
        resp = await app_client.get(f"{_ASSETS_URL}/aapl")
        assert resp.status_code == 200
        assert resp.json()["symbol"] == "AAPL"

    async def test_404_unknown_symbol(self, app_client, mock_db) -> None:
        """Unknown symbol returns a clear 404 with the symbol in the detail."""
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute
        ).return_value = MagicMock(data=[])

        resp = await app_client.get(f"{_ASSETS_URL}/UNKNOWN")
        assert resp.status_code == 404
        assert "UNKNOWN" in resp.json()["detail"]


# ── DELETE /api/v1/assets/{symbol} ────────────────────────────────────────────


class TestDeleteAsset:
    """Tests for the asset deletion endpoint."""

    async def test_204_deletes_known_symbol(self, app_client, mock_db) -> None:
        """Deleting a known symbol returns 204 No Content."""
        # Asset lookup returns the asset
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute
        ).return_value = MagicMock(data=[_AAPL_ASSET])
        # Delete call succeeds silently
        mock_db.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        resp = await app_client.delete(f"{_ASSETS_URL}/AAPL")
        assert resp.status_code == 204
        assert resp.content == b""  # 204 must have no response body

    async def test_404_deleting_unknown_symbol(self, app_client, mock_db) -> None:
        """Deleting an unknown symbol returns 404 before hitting the delete query."""
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute
        ).return_value = MagicMock(data=[])

        resp = await app_client.delete(f"{_ASSETS_URL}/UNKNOWN")
        assert resp.status_code == 404
        assert "UNKNOWN" in resp.json()["detail"]


# ── GET /api/v1/prices/{symbol} with date filters ────────────────────────────


class TestPricesDateFilter:
    """Tests for the from_date / to_date query parameters on the prices endpoint."""

    def _wire_prices(self, mock_db, asset_rows: list, price_rows: list) -> None:
        """
        Configure mock for asset lookup (.limit) and price query (.order().limit).

        The asset lookup uses:  .eq().limit().execute()
        The price query uses:   .eq().[.gte()][.lt()].order().limit().execute()

        Because .gte() and .lt() return new child mocks (not the .eq() mock
        itself), both chains are configurable independently.
        """
        # Asset lookup chain
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute
        ).return_value = MagicMock(data=asset_rows)

        # Price query — no date filters: .eq().order().limit().execute()
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .limit.return_value
            .execute
        ).return_value = MagicMock(data=price_rows)

        # Price query — with from_date (.gte) and/or to_date (.lt)
        eq_mock = mock_db.table.return_value.select.return_value.eq.return_value
        # .gte() returns a proxy; .lt() on that returns another proxy
        gte_mock = eq_mock.gte.return_value
        lt_mock = gte_mock.lt.return_value
        for end_mock in (gte_mock, lt_mock):
            (
                end_mock
                .order.return_value
                .limit.return_value
                .execute
            ).return_value = MagicMock(data=price_rows)

    async def test_200_no_date_params(self, app_client, mock_db) -> None:
        """Prices endpoint works without date params (existing behaviour)."""
        self._wire_prices(mock_db, [_AAPL_ASSET], [_PRICE_ROW])
        resp = await app_client.get(f"{_PRICES_URL}/AAPL")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_200_with_from_date(self, app_client, mock_db) -> None:
        """?from_date is accepted and the endpoint returns 200."""
        self._wire_prices(mock_db, [_AAPL_ASSET], [_PRICE_ROW])
        resp = await app_client.get(f"{_PRICES_URL}/AAPL?from_date=2022-01-01")
        assert resp.status_code == 200

    async def test_200_with_both_dates(self, app_client, mock_db) -> None:
        """?from_date + ?to_date together are accepted and return 200."""
        self._wire_prices(mock_db, [_AAPL_ASSET], [_PRICE_ROW])
        resp = await app_client.get(
            f"{_PRICES_URL}/AAPL?from_date=2022-01-01&to_date=2024-12-31"
        )
        assert resp.status_code == 200

    async def test_400_invalid_date_format(self, app_client, mock_db) -> None:
        """Malformed date strings are rejected with 400."""
        self._wire_prices(mock_db, [_AAPL_ASSET], [])
        resp = await app_client.get(f"{_PRICES_URL}/AAPL?from_date=not-a-date")
        assert resp.status_code == 400
        assert "Invalid date format" in resp.json()["detail"]

    async def test_400_from_date_not_before_to_date(
        self, app_client, mock_db
    ) -> None:
        """from_date >= to_date must be rejected with 400."""
        self._wire_prices(mock_db, [_AAPL_ASSET], [])
        resp = await app_client.get(
            f"{_PRICES_URL}/AAPL?from_date=2024-01-01&to_date=2023-01-01"
        )
        assert resp.status_code == 400
        assert "from_date" in resp.json()["detail"]

    async def test_404_unknown_symbol(self, app_client, mock_db) -> None:
        """Unknown symbol in prices endpoint returns 404."""
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute
        ).return_value = MagicMock(data=[])
        resp = await app_client.get(f"{_PRICES_URL}/UNKNOWN")
        assert resp.status_code == 404

    async def test_limit_param_respected(self, app_client, mock_db) -> None:
        """?limit query param is accepted by the endpoint."""
        self._wire_prices(mock_db, [_AAPL_ASSET], [_PRICE_ROW])
        resp = await app_client.get(f"{_PRICES_URL}/AAPL?limit=50")
        assert resp.status_code == 200

    async def test_limit_above_cap_accepted(self, app_client, mock_db) -> None:
        """limit > 1000 is silently capped at 1000 by the Query constraint."""
        self._wire_prices(mock_db, [_AAPL_ASSET], [_PRICE_ROW])
        # FastAPI Query(le=1000) rejects values > 1000 with 422
        resp = await app_client.get(f"{_PRICES_URL}/AAPL?limit=9999")
        assert resp.status_code == 422
