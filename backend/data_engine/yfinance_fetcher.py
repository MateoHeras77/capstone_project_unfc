"""
data_engine/yfinance_fetcher.py — DEPRECATED backward-compat shim.

The canonical implementation has moved to ``data_engine/fetcher.py``.
This file re-exports ``YFinanceFetcher`` so existing imports keep working.

New code should use::

    from data_engine.fetcher import YFinanceFetcher
"""

# Re-export from the new canonical location.
from data_engine.fetcher import YFinanceFetcher  # noqa: F401

__all__ = ["YFinanceFetcher"]
