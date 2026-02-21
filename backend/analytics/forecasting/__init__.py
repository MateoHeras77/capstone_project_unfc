"""
analytics/forecasting — Time-series forecasting models.

Public API
----------
    from analytics.forecasting import BaseForecastor, SimpleForecaster
    from analytics.forecasting import LSTMForecastor
    from analytics.forecasting import ProphetForecaster
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
