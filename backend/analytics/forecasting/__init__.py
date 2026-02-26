"""
analytics/forecasting — Time-series forecasting models.

Public API
----------
    from analytics.forecasting import BaseForecastor, SimpleForecaster
    from analytics.forecasting import LSTMForecastor
    from analytics.forecasting import ProphetForecaster
    from analytics.forecasting import Chronos2Forecaster
    from analytics.forecasting import ProphetXGBForecaster
"""

from analytics.forecasting.base import BaseForecastor, SimpleForecaster
from analytics.forecasting.lstm import LSTMForecastor
from analytics.forecasting.prophet import ProphetForecaster
from analytics.forecasting.prophet_xgb import ProphetXGBForecaster
from analytics.forecasting.chronos2 import Chronos2Forecaster

__all__ = [
    "BaseForecastor",
    "SimpleForecaster",
    "LSTMForecastor",
    "ProphetForecaster",
    "ProphetXGBForecaster",
    "Chronos2Forecaster",
]
