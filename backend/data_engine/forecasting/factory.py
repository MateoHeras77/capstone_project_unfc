"""
=============================================================================
FORECASTING FACTORY - Model Selection and Management
=============================================================================

This module provides utilities for instantiating and managing different
forecasting models. It implements the factory pattern to enable easy
switching between different forecasting implementations.

Usage:
    from backend.data_engine.forecasting.factory import ForecastingFactory
    
    # Get an LSTM forecaster
    forecaster = ForecastingFactory.create_forecaster(model_type="lstm")
    
    # Or customize parameters
    forecaster = ForecastingFactory.create_forecaster(
        model_type="lstm",
        lookback_window=30,
        epochs=100
    )
"""

from typing import Dict, Any, Optional, Type
from .base_forecaster import BaseForecastor
from .lstm_model import LSTMForecastor
import logging

logger = logging.getLogger(__name__)


class ForecastingFactory:
    """
    Factory for creating and managing forecasting model instances.
    
    Provides centralized model instantiation following the factory design pattern.
    This enables easy addition of new forecasting models and switching between them.
    """

    # Registry of available models
    _models: Dict[str, Type[BaseForecastor]] = {
        "lstm": LSTMForecastor,
        # Future models can be added here
        # "sarima": SARIMAForecastor,
        # "prophet": ProphetForecastor,
    }

    @classmethod
    def create_forecaster(
        cls,
        model_type: str = "lstm",
        **kwargs: Any
    ) -> BaseForecastor:
        """
        Create a forecasting model instance.
        
        Args:
            model_type: Type of forecasting model to create. 
                       Options: "lstm" (default)
            **kwargs: Additional keyword arguments passed to the model's 
                     __init__ method. See specific model documentation for 
                     available parameters.
                     
        Returns:
            An instance of the requested forecasting model.
            
        Raises:
            ValueError: If model_type is not recognized
            
        Example:
            forecaster = ForecastingFactory.create_forecaster(
                model_type="lstm",
                lookback_window=30,
                epochs=100
            )
        """
        model_type = model_type.lower()

        if model_type not in cls._models:
            available = ", ".join(cls._models.keys())
            raise ValueError(
                f"Unknown model type: '{model_type}'. "
                f"Available models: {available}"
            )

        model_class = cls._models[model_type]
        logger.info(f"Creating {model_type} forecaster with params: {kwargs}")

        try:
            return model_class(**kwargs)
        except TypeError as e:
            raise ValueError(
                f"Invalid parameters for {model_type}: {e}"
            )

    @classmethod
    def register_model(
        cls,
        name: str,
        model_class: Type[BaseForecastor]
    ) -> None:
        """
        Register a new forecasting model class.
        
        This method allows extending the factory with custom forecasting models
        that implement the BaseForecastor interface.
        
        Args:
            name: Name to register the model under (e.g., "lstm", "custom")
            model_class: Class that inherits from BaseForecastor
            
        Raises:
            TypeError: If model_class does not inherit from BaseForecastor
            ValueError: If name already exists
            
        Example:
            class CustomForecaster(BaseForecastor):
                # Implementation...
                pass
            
            ForecastingFactory.register_model("custom", CustomForecaster)
        """
        if not issubclass(model_class, BaseForecastor):
            raise TypeError(
                f"{model_class.__name__} must inherit from BaseForecastor"
            )

        if name in cls._models:
            raise ValueError(
                f"Model '{name}' is already registered. "
                f"Use a different name or update the existing model."
            )

        cls._models[name] = model_class
        logger.info(f"Registered new forecasting model: {name}")

    @classmethod
    def list_available_models(cls) -> list[str]:
        """
        List all available forecasting models.
        
        Returns:
            List of available model type names
        """
        return list(cls._models.keys())

    @classmethod
    def get_model_info(cls, model_type: str) -> Dict[str, Any]:
        """
        Get information about a specific model type.
        
        Args:
            model_type: Type of forecasting model
            
        Returns:
            Dictionary containing model information
            
        Raises:
            ValueError: If model_type is not recognized
        """
        if model_type not in cls._models:
            raise ValueError(f"Unknown model type: {model_type}")

        model_class = cls._models[model_type]
        return {
            "name": model_type,
            "class": model_class.__name__,
            "module": model_class.__module__,
            "doc": model_class.__doc__
        }
