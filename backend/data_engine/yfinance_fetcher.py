"""
=============================================================================
YFINANCE FETCHER - External Market Data Provider
=============================================================================

WARNING: ISOLATION BOUNDARY
---------------------------
This module handles ALL external API calls to Yahoo Finance.
DO NOT create yfinance calls anywhere else in the codebase.

This module is wrapped by DataCoordinator. Phase 3/4 developers should
NOT import this module directly - use the API endpoints instead.
=============================================================================
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional


class YFinanceFetcher:
    """
    Handles fetching historical market data from yfinance.
    
    This class is INTERNAL to the data_engine module.
    External code should use DataCoordinator or API endpoints.
    
    Supported intervals:
    - '1wk' (Weekly) - PRIMARY, used throughout the application
    - '1mo' (Monthly) - Kept for potential future use
    """
    
    def __init__(self):
        """Initialize the fetcher. No external connections made here."""
        pass

    def fetch_history(
        self, 
        symbol: str, 
        interval: str = "1wk", 
        period: str = "max"
    ) -> pd.DataFrame:
        """
        Fetches historical OHLCV data for a given symbol.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'BTC-USD', '^GSPC')
            interval: '1wk' (weekly) or '1mo' (monthly)
            period: Time period to fetch ('max', '5y', '2y', etc.)
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
            
        Raises:
            ValueError: If interval is not '1wk' or '1mo'
        """
        if interval not in ["1wk", "1mo"]:
            raise ValueError("Interval must be '1wk' or '1mo' for this project.")
            
        # Create ticker object and fetch history
        ticker = yf.Ticker(symbol)
        df = ticker.history(interval=interval, period=period)
        
        # Reset index to make Date a column instead of index
        df = df.reset_index()
        
        # Standardize column names to lowercase with underscores
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # Rename 'date' to 'timestamp' for consistency with database schema
        if 'date' in df.columns:
            df = df.rename(columns={'date': 'timestamp'})
            
        return df

    def get_latest_price(self, symbol: str) -> float:
        """
        Quickly gets the most recent close price for a symbol.
        
        This is a utility method for real-time checks.
        Not used in the current caching workflow.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            The latest closing price, or 0.0 if unavailable
        """
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
        return 0.0
