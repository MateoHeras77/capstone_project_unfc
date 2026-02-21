"""
data_engine — Market data fetching and smart-cache layer.

Public API
----------
    from data_engine import DataCoordinator, YFinanceFetcher
"""

from data_engine.coordinator import DataCoordinator
from data_engine.fetcher import YFinanceFetcher

__all__ = ["DataCoordinator", "YFinanceFetcher"]
