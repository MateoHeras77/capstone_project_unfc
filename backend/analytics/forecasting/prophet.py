"""
analytics/forecasting/prophet.py
─────────────────────────────────
Facebook's Prophet time-series forecaster.

Prophet fits trend + seasonality components and returns both point
estimates and native confidence intervals, so no residual trick is needed.

Requires
--------
    pip install prophet>=1.1.5
"""

import logging
from datetime import timedelta
from typing import Any, Dict, List

import pandas as pd

from analytics.forecasting.base import BaseForecastor

logger = logging.getLogger(__name__)


class ProphetForecaster(BaseForecastor):
    """
    Prophet-based time-series forecaster for financial price data.

    Confidence intervals are produced directly by Prophet's internal
    uncertainty quantification — no post-hoc residual estimation needed.

    Args:
        confidence_level: Probability mass for Prophet's interval_width.

    Raises:
        ImportError: If the ``prophet`` package is not installed.
    """

    def __init__(self, confidence_level: float = 0.95) -> None:
        self.confidence_level = confidence_level

        self._prices: pd.Series | None = None
        self._model = None
        self._freq_days: int = 7
        self._is_fitted: bool = False

    # ── fit ──────────────────────────────────────────────────────────────

    def fit(self, prices: pd.Series) -> None:
        """
        Fit a Prophet model to historical price data.

        Prophet requires a DataFrame with ``ds`` (datetime) and ``y``
        (target value) columns.

        Args:
            prices: pd.Series with DatetimeIndex, oldest → newest.
                    Minimum 10 samples required for meaningful seasonality.

        Raises:
            ImportError: If the ``prophet`` package is not installed.
        """
        try:
            from prophet import Prophet
        except ImportError as exc:
            raise ImportError(
                "The 'prophet' package is required for ProphetForecaster. "
                "Install with: pip install prophet"
            ) from exc

        self._validate_prices(prices, min_samples=10)
        self._prices = prices.copy()
        self._freq_days = self._infer_freq_days(prices.index)

        # Prophet needs timezone-naive datetimes
        df = pd.DataFrame(
            {
                "ds": prices.index.tz_localize(None),
                "y": prices.values,
            }
        )

        self._model = Prophet(
            interval_width=self.confidence_level,
            weekly_seasonality=True,
            daily_seasonality=False,
        )
        self._model.fit(df)
        self._is_fitted = True
        logger.info("Prophet fitted on %d samples", len(prices))

    # ── forecast ─────────────────────────────────────────────────────────

    def forecast(self, periods: int = 4) -> Dict[str, Any]:
        """
        Extend the Prophet model into the future.

        Args:
            periods: Number of future time steps to forecast.

        Returns:
            Standard forecast dict (see BaseForecastor.forecast docstring).

        Raises:
            ValueError: If called before fit().
        """
        if not self._is_fitted or self._model is None:
            raise ValueError("Call fit() before forecast()")

        future = self._model.make_future_dataframe(
            periods=periods, freq=f"{self._freq_days}D"
        )
        prediction = self._model.predict(future)
        forecast_rows = prediction.tail(periods)

        last_date = self._prices.index[-1]
        if last_date.tz is not None:
            last_date = last_date.tz_localize(None)
        step = timedelta(days=self._freq_days)
        raw_dates = forecast_rows["ds"].tolist()
        # Ensure forecast dates are strictly after last training date (fixes
        # Prophet versions or freq quirks that can yield past dates).
        dates = []
        for i, d in enumerate(raw_dates):
            pd_ts = pd.Timestamp(d)
            if pd_ts.tz is not None:
                pd_ts = pd_ts.tz_localize(None)
            if pd_ts <= last_date:
                pd_ts = last_date + step * (i + 1)
            dates.append(pd_ts.strftime("%Y-%m-%dT%H:%M:%S"))
        if not dates:
            dates = [
                (last_date + step * (i + 1)).strftime("%Y-%m-%dT%H:%M:%S")
                for i in range(periods)
            ]

        return {
            "dates": dates,
            "point_forecast": forecast_rows["yhat"].round(4).tolist(),
            "lower_bound": forecast_rows["yhat_lower"].round(4).tolist(),
            "upper_bound": forecast_rows["yhat_upper"].round(4).tolist(),
            "confidence_level": self.confidence_level,
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Return Prophet model metadata."""
        info = super().get_model_info()
        info.update(
            {
                "confidence_level": self.confidence_level,
                "freq_days": self._freq_days,
                "is_fitted": self._is_fitted,
            }
        )
        return info
