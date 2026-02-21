"""DEPRECATED shim — see analytics/forecasting/base.py"""
from analytics.forecasting.base import BaseForecastor, SimpleForecaster  # noqa: F401
__all__ = ["BaseForecastor", "SimpleForecaster"]
