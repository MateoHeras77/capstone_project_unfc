"""
data_engine/forecasting — DEPRECATED shim.

All forecasting models have moved to ``analytics/forecasting``.
This package re-exports them for backward compatibility only.
New code should import directly from ``analytics.forecasting``.
"""

from analytics.forecasting.base import BaseForecastor, SimpleForecaster
from analytics.forecasting.lstm import LSTMForecastor
from analytics.forecasting.prophet import ProphetForecaster

__all__ = [
    "BaseForecastor",
    "SimpleForecaster",
    "LSTMForecastor",
    "ProphetForecaster",
]