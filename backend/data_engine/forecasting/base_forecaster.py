"""
=============================================================================
BASE FORECASTER - Abstract Interface for Forecasting Models
=============================================================================

This module defines the standard interface for all forecasting models.
All forecasting implementations (LSTM, SARIMA, Prophet, etc.) should inherit
from BaseForecastor and implement the required methods.

Purpose:
- Ensure model-agnostic design as specified in Phase 3
- Standardize input/output formats
- Enable easy swapping of different forecasting models
=============================================================================
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import pandas as pd


class BaseForecastor(ABC):
    """
    Abstract base class for forecasting models.
    
    Defines the standard interface that all forecasting models must implement
    to be used in the financial analytics platform.
    """

    @abstractmethod
    def fit(self, prices: pd.Series) -> None:
        """
        Fit the forecasting model to historical price data.
        
        Args:
            prices: A pandas Series with TimeIndex (sorted dates) and 
                   closing prices as values. Data should be sorted 
                   chronologically from oldest to newest.
                   
        Raises:
            ValueError: If prices has fewer than the minimum required samples.
        """
        pass

    @abstractmethod
    def forecast(self, periods: int = 4) -> Dict[str, List]:
        """
        Generate price forecasts for a given number of future periods.
        
        Args:
            periods: Number of periods to forecast. Default is 4 (weeks).
                    
        Returns:
            A dictionary with the following structure:
            {
                'dates': List[str],           # ISO format dates of predictions
                'point_forecast': List[float], # Point estimates
                'lower_bound': List[float],    # Lower confidence interval
                'upper_bound': List[float],    # Upper confidence interval
                'confidence_level': float      # E.g., 0.95 for 95% CI
            }
            
        Raises:
            ValueError: If model has not been fitted yet.
        """
        pass

    def get_model_info(self) -> Dict[str, str]:
        """
        Return metadata about the model.
        
        Returns:
            Dictionary containing model name, version, and parameters.
        """
        return {
            "model_name": self.__class__.__name__,
            "version": "1.0"
        }
