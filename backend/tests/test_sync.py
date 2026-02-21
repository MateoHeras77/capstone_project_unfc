"""
tests/test_sync.py
───────────────────
Integration smoke-tests for the data sync pipeline.

Run with::

    cd backend
    pytest tests/test_sync.py -v

These tests make REAL calls to yfinance and Supabase, so a running local
Supabase instance is required (``supabase start``).
"""

import logging

import pytest

from data_engine.coordinator import DataCoordinator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── Integration tests (require live Supabase + network) ──────────────────────


@pytest.mark.integration
def test_sync_aapl_weekly() -> None:
    """Verify that syncing AAPL weekly data completes without error."""
    coordinator = DataCoordinator()
    # Should not raise; success is silent.
    coordinator.sync_asset("AAPL", "stock", interval="1wk")
    logger.info("AAPL weekly sync: OK")


@pytest.mark.integration
def test_sync_btc_monthly() -> None:
    """Verify that syncing BTC-USD monthly data completes without error."""
    coordinator = DataCoordinator()
    coordinator.sync_asset("BTC-USD", "crypto", interval="1mo")
    logger.info("BTC-USD monthly sync: OK")


# ─── Unit test (no network, no DB) ────────────────────────────────────────────


def test_coordinator_instantiates() -> None:
    """DataCoordinator can be constructed without side effects."""
    from unittest.mock import patch

    # Patch the DB call so no real connection is attempted.
    with patch("data_engine.coordinator.get_supabase_client"):
        coordinator = DataCoordinator()
    assert coordinator is not None
