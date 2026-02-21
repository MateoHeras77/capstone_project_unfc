"""
Pydantic schemas for forecast request / response.

Both the base and LSTM endpoints share identical I/O shapes so the
frontend can swap models simply by changing the URL.
"""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    """
    Payload sent by the client to any forecast endpoint.

    Attributes:
        ticker:           Ticker symbol for display / logging (e.g. 'AAPL').
        prices:           Historical closing prices (oldest → newest).
        dates:            ISO-8601 date strings parallel to `prices`.
        periods:          Number of future periods to forecast.
        lookback_window:  LSTM sequence length (ignored by EWM model).
        epochs:           LSTM training epochs (ignored by EWM model).
        confidence_level: Probability mass for confidence interval.
    """

    ticker: str
    prices: List[float]
    dates: List[str] = Field(..., description="ISO-8601 date strings")
    periods: int = Field(default=4, ge=1, le=52)
    lookback_window: int = Field(default=20, ge=5, le=60)
    epochs: int = Field(default=50, ge=10, le=200)
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99)


class ForecastResponse(BaseModel):
    """
    Standardised forecast result returned by every forecast endpoint.

    Attributes:
        ticker:           Echo of the requested ticker.
        dates:            ISO-8601 dates for each forecast period.
        point_forecast:   Central estimate for each period.
        lower_bound:      Lower confidence-interval bound.
        upper_bound:      Upper confidence-interval bound.
        confidence_level: Confidence level used for the interval.
        model_info:       Free-form model metadata dict.
    """

    ticker: str
    dates: List[str]
    point_forecast: List[float]
    lower_bound: List[float]
    upper_bound: List[float]
    confidence_level: float
    model_info: Dict[str, Any]
