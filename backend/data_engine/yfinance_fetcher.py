import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional

class YFinanceFetcher:
    """
    Handles fetching historical market data from yfinance at Weekly/Monthly intervals.
    """
    
    def __init__(self):
        pass

    def fetch_history(self, symbol: str, interval: str = "1wk", period: str = "max") -> pd.DataFrame:
        """
        Fetches historical data for a given symbol.
        Intervals: '1wk' (Weekly), '1mo' (Monthly).
        """
        if interval not in ["1wk", "1mo"]:
            raise ValueError("Interval must be '1wk' or '1mo' for this project.")
            
        ticker = yf.Ticker(symbol)
        df = ticker.history(interval=interval, period=period)
        
        # Reset index to make Date a column
        df = df.reset_index()
        
        # Standardize columns
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # Ensure 'timestamp' column exists from 'date'
        if 'date' in df.columns:
            df = df.rename(columns={'date': 'timestamp'})
            
        return df

    def get_latest_price(self, symbol: str) -> float:
        """Quickly gets the most recent close price."""
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
        return 0.0
