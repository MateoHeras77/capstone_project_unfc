"""
Forecasting module for price prediction models.

This module provides model-agnostic forecasting capabilities for predicting
stock and cryptocurrency prices. It includes implementations of various
forecasting models (LSTM, SARIMA, etc.) that all follow a standard interface.

Usage:
    from backend.data_engine.forecasting import LSTMForecastor
    
    forecaster = LSTMForecastor()
    forecaster.fit(historical_prices)
    forecast = forecaster.forecast(periods=4)
"""

from .base_forecaster import BaseForecastor
from .lstm_model import LSTMForecastor

__all__ = [
    "BaseForecastor",
    "LSTMForecastor"
]
