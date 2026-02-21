"""
analytics/forecasting/lstm.py
─────────────────────────────
LSTM neural network forecaster for closing price prediction.

Architecture
------------
Input (lookback_window, 1)
  → LSTM(64, return_sequences=True) → Dropout(0.2)
  → LSTM(32) → Dropout(0.2)
  → Dense(16, relu) → Dense(1)
  → inverse-scaled price

Uncertainty is estimated from held-out validation residuals, not a
fixed percentage, so intervals widen realistically with data variance.

Requires
--------
    pip install tensorflow>=2.15.0
"""

import logging
import warnings
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from analytics.forecasting.base import BaseForecastor

logger = logging.getLogger(__name__)

# Optional import — graceful degradation if TF not installed.
try:
    import tensorflow as tf
    from tensorflow.keras import layers

    _TF_AVAILABLE = True
except ImportError:
    _TF_AVAILABLE = False
    warnings.warn(
        "TensorFlow not installed — LSTMForecastor is unavailable. "
        "Install with: pip install tensorflow",
        stacklevel=2,
    )


class LSTMForecastor(BaseForecastor):
    """
    LSTM-based multi-step price forecaster with residual confidence intervals.

    Args:
        lookback_window:  Number of historical time steps fed into the LSTM.
        epochs:           Number of training epochs.
        batch_size:       Mini-batch size during training.
        test_size:        Fraction of data reserved for validation.
        confidence_level: Probability mass for the confidence interval.
        random_state:     Seed for reproducibility.

    Raises:
        ImportError: If TensorFlow is not installed when instantiated.
    """

    def __init__(
        self,
        lookback_window: int = 20,
        epochs: int = 50,
        batch_size: int = 16,
        test_size: float = 0.2,
        confidence_level: float = 0.95,
        random_state: int = 42,
    ) -> None:
        if not _TF_AVAILABLE:
            raise ImportError(
                "TensorFlow is required for LSTMForecastor. "
                "Install with: pip install tensorflow"
            )

        self.lookback_window = lookback_window
        self.epochs = epochs
        self.batch_size = batch_size
        self.test_size = test_size
        self.confidence_level = confidence_level
        self.random_state = random_state

        self.model: Optional[tf.keras.Model] = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self._scaled_prices: Optional[np.ndarray] = None
        self._prices: Optional[pd.Series] = None
        self._val_residual_std: float = 0.0
        self._freq_days: int = 7
        self._is_fitted: bool = False

        tf.random.set_seed(random_state)
        np.random.seed(random_state)

    # ── internal helpers ──────────────────────────────────────────────────

    def _create_sequences(
        self, data: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Slide a window over `data` to produce (X, y) sequence pairs.

        Args:
            data: 1-D scaled price array.

        Returns:
            X: shape (n_samples, lookback_window, 1)
            y: shape (n_samples, 1)
        """
        X, y = [], []
        for i in range(self.lookback_window, len(data)):
            X.append(data[i - self.lookback_window : i])
            y.append(data[i])
        return np.array(X).reshape(-1, self.lookback_window, 1), np.array(y).reshape(
            -1, 1
        )

    def _build_model(self) -> None:
        """Construct and compile the Keras model."""
        self.model = tf.keras.Sequential(
            [
                layers.LSTM(64, return_sequences=True, input_shape=(self.lookback_window, 1)),
                layers.Dropout(0.2),
                layers.LSTM(32),
                layers.Dropout(0.2),
                layers.Dense(16, activation="relu"),
                layers.Dense(1),
            ],
            name="lstm_price_forecaster",
        )
        self.model.compile(optimizer="adam", loss="mse")

    # ── fit ──────────────────────────────────────────────────────────────

    def fit(self, prices: pd.Series) -> None:
        """
        Scale, sequence, and train the LSTM on historical prices.

        Args:
            prices: pd.Series with DatetimeIndex, oldest → newest.

        Raises:
            ValueError: If not enough samples to create even one sequence.
        """
        min_needed = self.lookback_window + 1
        self._validate_prices(prices, min_samples=min_needed)

        logger.info("Fitting LSTM on %d samples (lookback=%d)", len(prices), self.lookback_window)
        self._prices = prices.copy()
        self._freq_days = self._infer_freq_days(prices.index)

        # Scale to [0, 1]
        arr = prices.values.reshape(-1, 1).astype(np.float64)
        self._scaled_prices = self.scaler.fit_transform(arr)

        # Build windowed sequences
        X, y = self._create_sequences(self._scaled_prices)
        if len(X) == 0:
            raise ValueError(
                f"No sequences created — reduce lookback_window "
                f"(currently {self.lookback_window}, need at least {self.lookback_window + 1} samples)"
            )

        # Temporal train / validation split (no shuffle to preserve time order)
        split = int(len(X) * (1 - self.test_size))
        X_train, y_train = X[:split], y[:split]
        X_val, y_val = X[split:], y[split:]

        self._build_model()
        self.model.fit(
            X_train,
            y_train,
            epochs=self.epochs,
            batch_size=self.batch_size,
            validation_data=(X_val, y_val) if len(X_val) > 0 else None,
            verbose=0,
        )

        # Derive CI width from actual validation residuals
        if len(X_val) > 0:
            preds_scaled = self.model.predict(X_val, verbose=0)
            preds = self.scaler.inverse_transform(preds_scaled).flatten()
            actuals = self.scaler.inverse_transform(y_val).flatten()
            self._val_residual_std = float(np.std(actuals - preds))
        else:
            # Fallback: 5 % of the price range
            self._val_residual_std = float((prices.max() - prices.min()) * 0.05)

        self._is_fitted = True
        logger.info("LSTM fitted — validation residual std: %.4f", self._val_residual_std)

    # ── forecast ─────────────────────────────────────────────────────────

    def forecast(self, periods: int = 4) -> Dict[str, Any]:
        """
        Iterative multi-step prediction with residual-based CIs.

        Each step appends the previous prediction to the input window,
        so uncertainty compounds naturally over the horizon.

        Args:
            periods: Number of future time steps to forecast.

        Returns:
            Standard forecast dict (see BaseForecastor.forecast docstring).

        Raises:
            ValueError: If called before fit().
        """
        if not self._is_fitted or self.model is None:
            raise ValueError("Call fit() before forecast()")

        from scipy.stats import norm

        z = norm.ppf((1 + self.confidence_level) / 2)
        last_date = self._prices.index[-1]
        step = timedelta(days=self._freq_days)

        # Seed the rolling window with the last `lookback_window` scaled prices
        seq = self._scaled_prices[-self.lookback_window :].flatten().copy()

        raw_preds: List[float] = []
        for _ in range(periods):
            x_in = seq[-self.lookback_window :].reshape(1, self.lookback_window, 1)
            pred = float(self.model.predict(x_in, verbose=0)[0, 0])
            raw_preds.append(pred)
            seq = np.append(seq, pred)

        # Inverse-transform to the original price scale
        point_forecast = self.scaler.inverse_transform(
            np.array(raw_preds).reshape(-1, 1)
        ).flatten()

        dates: List[str] = []
        lower_bound: List[float] = []
        upper_bound: List[float] = []

        for h, price in enumerate(point_forecast, start=1):
            date = last_date + step * h
            # Uncertainty grows with sqrt(horizon) — same convention as SimpleForecaster
            margin = z * self._val_residual_std * np.sqrt(h)

            dates.append(date.strftime("%Y-%m-%dT%H:%M:%S"))
            lower_bound.append(round(max(price - margin, 0.0), 4))
            upper_bound.append(round(price + margin, 4))

        return {
            "dates": dates,
            "point_forecast": [round(p, 4) for p in point_forecast.tolist()],
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "confidence_level": self.confidence_level,
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Return LSTM model metadata."""
        info = super().get_model_info()
        info.update(
            {
                "lookback_window": self.lookback_window,
                "epochs": self.epochs,
                "batch_size": self.batch_size,
                "confidence_level": self.confidence_level,
                "is_fitted": self._is_fitted,
                "val_residual_std": round(self._val_residual_std, 6) if self._is_fitted else None,
            }
        )
        return info
