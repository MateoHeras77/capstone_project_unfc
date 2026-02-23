"""
analytics/forecasting/chronos2.py
Chronos-2 foundation model (zero-shot) forecaster.

Matches your BaseForecastor interface:
- fit(prices: pd.Series)
- forecast(periods: int)
- get_model_info()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from analytics.forecasting.base import BaseForecastor


@dataclass
class Chronos2Config:
    model_id: str = "amazon/chronos-2"
    device_map: str = "cpu"          # switch to "cuda" if you have a GPU
    batch_size: int = 256
    context_length: Optional[int] = 1024  # cap history for speed; None = use all


class Chronos2Forecaster(BaseForecastor):
    """
    Chronos-2 is zero-shot: no training step. fit() validates and stores series.
    """

    _PIPELINE = None
    _PIPELINE_MODEL_ID: Optional[str] = None
    _PIPELINE_DEVICE: Optional[str] = None

    def __init__(self, confidence_level: float = 0.95, config: Chronos2Config | None = None):
        self.confidence_level = confidence_level
        self.config = config or Chronos2Config()

        self._prices: pd.Series | None = None
        self._is_fitted = False

        self._ensure_pipeline()

    def _ensure_pipeline(self) -> None:
        try:
            from chronos import Chronos2Pipeline
        except ImportError as e:
            raise ImportError(
                "Missing dependency. Install `chronos-forecasting>=2.0` (and torch)."
            ) from e

        if (
            Chronos2Forecaster._PIPELINE is None
            or Chronos2Forecaster._PIPELINE_MODEL_ID != self.config.model_id
            or Chronos2Forecaster._PIPELINE_DEVICE != self.config.device_map
        ):
            Chronos2Forecaster._PIPELINE = Chronos2Pipeline.from_pretrained(
                self.config.model_id,
                device_map=self.config.device_map,
            )
            Chronos2Forecaster._PIPELINE_MODEL_ID = self.config.model_id
            Chronos2Forecaster._PIPELINE_DEVICE = self.config.device_map

    def fit(self, prices: pd.Series) -> None:
        self._validate_prices(prices, min_samples=5)

        prices = prices.sort_index()

        # Optional: cap context for speed/latency consistency
        if self.config.context_length and len(prices) > self.config.context_length:
            prices = prices.iloc[-self.config.context_length :]

        self._prices = prices.copy()
        self._is_fitted = True

    def forecast(self, periods: int = 4) -> Dict[str, Any]:
        if not self._is_fitted or self._prices is None:
            raise ValueError("Call fit() before forecast()")

        # Build DataFrame in the shape Chronos2Pipeline.predict_df expects
        df = pd.DataFrame(
            {
                "item_id": "series",
                "timestamp": pd.to_datetime(self._prices.index),
                "target": self._prices.values.astype(float),
            }
        )

        # Confidence -> quantile bounds (e.g. 95% -> 2.5% and 97.5%)
        alpha = (1.0 - float(self.confidence_level)) / 2.0
        q_low = round(alpha, 3)
        q_mid = 0.5
        q_high = round(1.0 - alpha, 3)
        quantiles = sorted({q_low, q_mid, q_high})

        pred_df = Chronos2Forecaster._PIPELINE.predict_df(
            df,
            prediction_length=int(periods),
            quantile_levels=quantiles,
            id_column="item_id",
            timestamp_column="timestamp",
            target="target",
            batch_size=int(self.config.batch_size),
            context_length=self.config.context_length,
            validate_inputs=True,
        ).sort_values("timestamp")

        # Point forecast: prefer median
        if "0.5" in pred_df.columns:
            point = pred_df["0.5"].astype(float).to_numpy()
        elif 0.5 in pred_df.columns:
            point = pred_df[0.5].astype(float).to_numpy()
        elif "predictions" in pred_df.columns:
            point = pred_df["predictions"].astype(float).to_numpy()
        else:
            raise RuntimeError(f"Unexpected Chronos output columns: {list(pred_df.columns)}")

        # Bounds if available; fall back to point
        def _get_col(q: float):
            s = str(q)
            if s in pred_df.columns:
                return pred_df[s].astype(float).to_numpy()
            if q in pred_df.columns:
                return pred_df[q].astype(float).to_numpy()
            return None

        low = _get_col(q_low)
        high = _get_col(q_high)
        if low is None or high is None:
            low = point
            high = point

        dates = [pd.Timestamp(d).to_pydatetime().isoformat() for d in pred_df["timestamp"]]

        return {
            "dates": dates,
            "point_forecast": [round(float(x), 4) for x in point],
            "lower_bound": [round(float(x), 4) for x in low],
            "upper_bound": [round(float(x), 4) for x in high],
            "confidence_level": float(self.confidence_level),
        }

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info.update(
            {
                "model_family": "Chronos-2",
                "model_id": self.config.model_id,
                "device_map": self.config.device_map,
                "batch_size": self.config.batch_size,
                "context_length": self.config.context_length,
                "confidence_level": self.confidence_level,
                "is_fitted": self._is_fitted,
            }
        )
        return info