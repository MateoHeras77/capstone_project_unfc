"""
=============================================================================
LSTM FORECASTER - Long Short-Term Memory Neural Network for Price Prediction
=============================================================================

This module implements an LSTM-based forecasting model for stock price 
prediction. The model uses historical price data to train a neural network
for predicting future price movements.

Architecture:
- Input layer: Sequences of historical prices (lookback window)
- LSTM layers: 2 stacked LSTM layers with dropout
- Dense layers: Fully connected layers for final prediction
- Output: Predicted prices with confidence intervals

Dependencies:
- tensorflow (via keras)
- scikit-learn (for data normalization)
- numpy
- pandas
=============================================================================
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import warnings

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    warnings.warn("TensorFlow not installed. LSTM forecasting will not work.")

from sklearn.preprocessing import MinMaxScaler
from .base_forecaster import BaseForecastor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LSTMForecastor(BaseForecastor):
    """
    LSTM-based forecasting model for stock price prediction.
    
    This model uses Long Short-Term Memory neural networks to capture
    temporal patterns in historical price data and generate forecasts
    with confidence intervals.
    
    Attributes:
        lookback_window: Number of historical time steps to use as input
        epochs: Number of training epochs
        batch_size: Batch size for training
        test_size: Fraction of data to use for validation (0-1)
        confidence_level: Confidence level for prediction intervals (0-1)
    """

    def __init__(
        self,
        lookback_window: int = 20,
        epochs: int = 50,
        batch_size: int = 16,
        test_size: float = 0.2,
        confidence_level: float = 0.95,
        random_state: int = 42
    ):
        """
        Initialize the LSTM forecasting model.
        
        Args:
            lookback_window: Number of previous time steps to use as 
                           input variables (default: 20 weeks ≈ 5 months)
            epochs: Number of training epochs (default: 50)
            batch_size: Batch size for training (default: 16)
            test_size: Fraction of data for validation (default: 0.2)
            confidence_level: Confidence level for prediction intervals 
                            (default: 0.95 = 95% CI)
            random_state: Random seed for reproducibility (default: 42)
            
        Raises:
            ImportError: If TensorFlow is not installed
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError(
                "TensorFlow is required for LSTM forecasting. "
                "Install it with: pip install tensorflow"
            )

        self.lookback_window = lookback_window
        self.epochs = epochs
        self.batch_size = batch_size
        self.test_size = test_size
        self.confidence_level = confidence_level
        self.random_state = random_state

        self.model: Optional[keras.Model] = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.scaled_prices: Optional[np.ndarray] = None
        self.original_prices: Optional[pd.Series] = None
        self.is_fitted = False

        tf.random.set_seed(random_state)
        np.random.seed(random_state)

    def fit(self, prices: pd.Series) -> None:
        """
        Fit the LSTM model to historical price data.
        
        Args:
            prices: A pandas Series with DatetimeIndex (sorted chronologically 
                   from oldest to newest) and closing prices as values.
                   
        Raises:
            ValueError: If prices has fewer than (lookback_window + 1) samples
            TypeError: If prices is not a pandas Series or has invalid index
        """
        # Validate input
        if not isinstance(prices, pd.Series):
            raise TypeError("prices must be a pandas Series")

        if len(prices) < self.lookback_window + 1:
            raise ValueError(
                f"Insufficient data. Need at least {self.lookback_window + 1} "
                f"samples, got {len(prices)}"
            )

        if not isinstance(prices.index, pd.DatetimeIndex):
            raise TypeError("prices must have a DatetimeIndex")

        logger.info(f"Fitting LSTM model with {len(prices)} price samples")

        # Store original prices for later reference
        self.original_prices = prices.copy()

        # Normalize prices to [0, 1] range
        prices_array = prices.values.reshape(-1, 1)
        self.scaled_prices = self.scaler.fit_transform(prices_array)

        # Create sequences for LSTM training
        X_train, y_train = self._create_sequences(self.scaled_prices)

        if len(X_train) == 0:
            raise ValueError(
                f"Could not create sequences. Consider reducing lookback_window "
                f"from {self.lookback_window}"
            )

        # Split into train and validation sets
        split_idx = int(len(X_train) * (1 - self.test_size))
        X_train_split = X_train[:split_idx]
        y_train_split = y_train[:split_idx]
        X_val = X_train[split_idx:]
        y_val = y_train[split_idx:]

        # Build and compile model
        self._build_model()

        # Train the model
        logger.info(f"Training LSTM model for {self.epochs} epochs")
        history = self.model.fit(
            X_train_split, y_train_split,
            epochs=self.epochs,
            batch_size=self.batch_size,
            validation_data=(X_val, y_val),
            verbose=0
        )

        self.is_fitted = True
        logger.info("LSTM model training completed successfully")

    def forecast(self, periods: int = 4) -> Dict[str, List]:
        """
        Generate price forecasts for future periods.
        
        Args:
            periods: Number of periods (weeks) to forecast (default: 4)
            
        Returns:
            Dictionary containing:
            - 'dates': List of ISO format prediction dates
            - 'point_forecast': List of point estimate prices
            - 'lower_bound': List of lower confidence interval bounds
            - 'upper_bound': List of upper confidence interval bounds
            - 'confidence_level': Confidence level used (e.g., 0.95)
            
        Raises:
            ValueError: If model has not been fitted
        """
        if not self.is_fitted or self.model is None:
            raise ValueError(
                "Model must be fitted before calling forecast(). "
                "Call fit() first with historical data."
            )

        logger.info(f"Generating {periods}-period forecast")

        # Start with the last lookback_window scaled prices
        current_sequence = self.scaled_prices[-self.lookback_window:].copy()
        forecasts = []
        uncertainties = []

        # Generate predictions iteratively (multi-step ahead)
        for _ in range(periods):
            # Reshape for model input
            X_input = current_sequence.reshape(1, self.lookback_window, 1)

            # Get prediction
            prediction = self.model.predict(X_input, verbose=0)
            forecasts.append(prediction[0, 0])

            # Calculate uncertainty (could be enhanced with Monte Carlo dropout)
            # For now, use prediction error from validation set
            uncertainty = self._estimate_uncertainty()
            uncertainties.append(uncertainty)

            # Update sequence with new prediction for next iteration
            current_sequence = np.append(
                current_sequence[1:],
                prediction[0, 0]
            )

        # Transform predictions back to original scale
        forecasts_array = np.array(forecasts).reshape(-1, 1)
        original_scale_forecasts = self.scaler.inverse_transform(forecasts_array)

        # Calculate confidence intervals
        original_scale_forecasts = original_scale_forecasts.flatten()

        # Calculate z-score based on confidence level
        # 0.95 confidence → z ≈ 1.96, 0.90 confidence → z ≈ 1.645
        from scipy import stats
        z_score = stats.norm.ppf((1 + self.confidence_level) / 2)

        lower_bounds = [
            forecast - z_score * uncertainty
            for forecast, uncertainty in zip(
                original_scale_forecasts,
                uncertainties
            )
        ]
        upper_bounds = [
            forecast + z_score * uncertainty
            for forecast, uncertainty in zip(
                original_scale_forecasts,
                uncertainties
            )
        ]

        # Generate forecast dates (assuming weekly data)
        last_date = self.original_prices.index[-1]
        forecast_dates = [
            (last_date + timedelta(weeks=i+1)).isoformat()
            for i in range(periods)
        ]

        return {
            "dates": forecast_dates,
            "point_forecast": original_scale_forecasts.tolist(),
            "lower_bound": lower_bounds,
            "upper_bound": upper_bounds,
            "confidence_level": self.confidence_level
        }

    def _build_model(self) -> None:
        """
        Build the LSTM neural network architecture.
        
        Architecture:
        - Input: (batch_size, lookback_window, 1)
        - LSTM(64) + Dropout(0.2)
        - LSTM(32) + Dropout(0.2)
        - Dense(16) + ReLU
        - Dense(1)
        - Output: Normalized price prediction [0, 1]
        """
        self.model = keras.Sequential([
            layers.LSTM(
                64,
                activation="relu",
                input_shape=(self.lookback_window, 1),
                return_sequences=True
            ),
            layers.Dropout(0.2),
            layers.LSTM(32, activation="relu"),
            layers.Dropout(0.2),
            layers.Dense(16, activation="relu"),
            layers.Dense(1)
        ])

        self.model.compile(
            optimizer="adam",
            loss="mse",
            metrics=["mae"]
        )

    def _create_sequences(
        self,
        data: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM training.
        
        Transforms a 1D array into sequences of (X, y) pairs where:
        - X: lookback_window consecutive prices
        - y: The next price (target)
        
        Args:
            data: 1D array of normalized prices
            
        Returns:
            Tuple of (X, y) where:
            - X: Shape (num_sequences, lookback_window, 1)
            - y: Shape (num_sequences, 1)
        """
        X, y = [], []

        for i in range(len(data) - self.lookback_window):
            X.append(data[i:i + self.lookback_window])
            y.append(data[i + self.lookback_window])

        return np.array(X), np.array(y)

    def _estimate_uncertainty(self) -> float:
        """
        Estimate prediction uncertainty.
        
        This uses a simple approach based on model's typical prediction error.
        For production, consider implementing:
        - Monte Carlo Dropout
        - Quantile regression
        - Ensemble methods
        
        Returns:
            Estimated standard deviation of predictions
        """
        # Placeholder: return a fraction of the price scale
        # This ensures intervals widen further into the future
        if self.original_prices is not None:
            price_range = (
                self.original_prices.max() - self.original_prices.min()
            )
            return price_range * 0.05  # 5% of historical price range

        return 0.01

    def get_model_info(self) -> Dict[str, any]:
        """
        Return metadata about the model.
        
        Returns:
            Dictionary containing model name, version, parameters, 
            and training status.
        """
        base_info = super().get_model_info()
        base_info.update({
            "lookback_window": self.lookback_window,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "is_fitted": self.is_fitted,
            "confidence_level": self.confidence_level
        })
        return base_info
