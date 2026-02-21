"""
app/api/v1/endpoints/forecast.py
──────────────────────────────────
Forecast endpoints.

Routes
------
POST /api/v1/forecast/base    EWM baseline forecast (no GPU needed).
POST /api/v1/forecast/lstm    LSTM neural-network forecast.
POST /api/v1/forecast/prophet Facebook Prophet trend/seasonality forecast.

All three share identical request and response shapes (ForecastRequest /
ForecastResponse) so the frontend only needs to change the URL to switch
models.

Design note
-----------
Model training is CPU/GPU-bound.  Each endpoint offloads the work to a
thread-pool executor so FastAPI's asyncio event loop is never blocked.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from fastapi import APIRouter, HTTPException

from analytics.forecasting import LSTMForecastor, ProphetForecaster, SimpleForecaster
from schemas.forecast import ForecastRequest, ForecastResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# A small pool — model training is CPU-bound, not I/O-bound.
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="forecast")


# ── helpers ───────────────────────────────────────────────────────────────────


def _build_series(req: ForecastRequest) -> pd.Series:
    """
    Convert parallel lists from the request into a dated pd.Series.

    Args:
        req: Validated ForecastRequest from the client.

    Returns:
        pd.Series with DatetimeIndex sorted oldest → newest.

    Raises:
        ValueError: If ``prices`` and ``dates`` have different lengths.
    """
    if len(req.prices) != len(req.dates):
        raise ValueError(
            f"prices ({len(req.prices)}) and dates ({len(req.dates)}) must have the same length"
        )
    index = pd.to_datetime(req.dates)
    return pd.Series(req.prices, index=index, name="close").sort_index()


def _run_base(req: ForecastRequest) -> ForecastResponse:
    """Run SimpleForecaster synchronously (called inside thread pool)."""
    prices = _build_series(req)
    model = SimpleForecaster(
        span=min(req.lookback_window, len(prices) - 1),
        confidence_level=req.confidence_level,
    )
    model.fit(prices)
    result = model.forecast(periods=req.periods)
    return ForecastResponse(
        ticker=req.ticker, model_info=model.get_model_info(), **result
    )


def _run_lstm(req: ForecastRequest) -> ForecastResponse:
    """Run LSTMForecastor synchronously (called inside thread pool)."""
    prices = _build_series(req)
    model = LSTMForecastor(
        lookback_window=req.lookback_window,
        epochs=req.epochs,
        confidence_level=req.confidence_level,
    )
    model.fit(prices)
    result = model.forecast(periods=req.periods)
    return ForecastResponse(
        ticker=req.ticker, model_info=model.get_model_info(), **result
    )


def _run_prophet(req: ForecastRequest) -> ForecastResponse:
    """Run ProphetForecaster synchronously (called inside thread pool)."""
    prices = _build_series(req)
    model = ProphetForecaster(confidence_level=req.confidence_level)
    model.fit(prices)
    result = model.forecast(periods=req.periods)
    return ForecastResponse(
        ticker=req.ticker, model_info=model.get_model_info(), **result
    )


# ── endpoints ─────────────────────────────────────────────────────────────────


@router.post("/base", response_model=ForecastResponse, summary="EWM baseline forecast")
async def base_forecast(request: ForecastRequest) -> ForecastResponse:
    """
    Exponential Weighted Moving Average (EWM) forecast.

    Fast — no TensorFlow required. Good sanity-check benchmark.

    Args:
        request: Ticker, historical prices/dates, and forecast parameters.

    Returns:
        Point forecast with widening confidence bounds.
    """
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(_executor, _run_base, request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Base forecast failed for %s", request.ticker)
        raise HTTPException(status_code=500, detail="Forecast computation failed") from exc


@router.post(
    "/lstm",
    response_model=ForecastResponse,
    summary="LSTM neural-network forecast",
)
async def lstm_forecast(request: ForecastRequest) -> ForecastResponse:
    """
    LSTM deep-learning forecast.

    Requires TensorFlow to be installed in the environment
    (``pip install tensorflow``).  Training runs in a thread pool to
    avoid blocking the event loop.

    Args:
        request: Ticker, historical prices/dates, and forecast parameters.

    Returns:
        Point forecast with residual-based confidence bounds.

    Raises:
        HTTPException 503: If TensorFlow is not installed.
        HTTPException 422: On invalid input data.
    """
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(_executor, _run_lstm, request)
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="TensorFlow is not installed on this server. Use /forecast/base instead.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("LSTM forecast failed for %s", request.ticker)
        raise HTTPException(status_code=500, detail="Forecast computation failed") from exc


@router.post(
    "/prophet",
    response_model=ForecastResponse,
    summary="Facebook Prophet forecast",
)
async def prophet_forecast(request: ForecastRequest) -> ForecastResponse:
    """
    Facebook Prophet trend + seasonality forecast.

    Handles missing data and outliers well. Requires at least 10 samples
    for meaningful seasonality decomposition.

    Args:
        request: Ticker, historical prices/dates, and forecast parameters.

    Returns:
        Point forecast with native Prophet confidence bounds.

    Raises:
        HTTPException 503: If the prophet package is not installed.
        HTTPException 422: On invalid input data.
    """
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(_executor, _run_prophet, request)
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="'prophet' is not installed on this server.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Prophet forecast failed for %s", request.ticker)
        raise HTTPException(status_code=500, detail="Forecast computation failed") from exc
