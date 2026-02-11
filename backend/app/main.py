"""
=============================================================================
INVESTMENT ANALYTICS API - FastAPI Backend
=============================================================================

This API serves as the bridge between the frontend (Streamlit) and the
data layer (Supabase + yfinance).

ENDPOINTS:
----------
GET  /           - Health check
GET  /assets     - List all cached assets
GET  /prices/{symbol} - Get historical prices for an asset
POST /sync/{symbol}   - Fetch and cache new asset data

FOR PHASE 3/4 DEVELOPERS:
-------------------------
Use these endpoints to retrieve data for your models:

1. GET /prices/{symbol}
   Returns: List of {timestamp, open_price, high_price, low_price, close_price, volume}
   Data is WEEKLY. Use this for forecasting and optimization inputs.
   
2. The data is already cached in Supabase. You do NOT need to call yfinance directly.

=============================================================================
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from ..core.database import get_supabase_client
from ..data_engine.data_coordinator import DataCoordinator

# Initialize FastAPI application
app = FastAPI(
    title="Investment Analytics API",
    description="Backend API for the Educational Investment Platform",
    version="0.1.0"
)

# -----------------------------------------------------------------------------
# CORS Configuration
# -----------------------------------------------------------------------------

# Allow requests from production and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://capstone-project-unfc.vercel.app",  # Production frontend
        "http://localhost:5173",    # Vite local
        "http://localhost:8501",    # Streamlit local
        "http://127.0.0.1:8501",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Data Coordinator Instance
# -----------------------------------------------------------------------------
# This coordinates all data fetching and caching operations
coordinator = DataCoordinator()


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"message": "Welcome to the Investment Analytics API"}


@app.get("/assets")
def get_assets():
    """
    Returns all assets currently cached in the database.
    
    Response: List of assets with {id, symbol, name, asset_type, last_updated}
    """
    supabase = get_supabase_client()
    res = supabase.table("assets").select("*").execute()
    return res.data


@app.get("/prices/{symbol}")
def get_prices(symbol: str):
    """
    Returns historical weekly prices for a given asset.
    
    This is the PRIMARY endpoint for Phase 3/4 to retrieve data.
    Data is returned in DESCENDING order by timestamp (newest first).
    
    Args:
        symbol: Ticker symbol (e.g., 'AAPL', 'BTC-USD')
        
    Returns:
        List of price records with OHLCV data
        
    Raises:
        404: If asset is not found in database
    """
    supabase = get_supabase_client()
    
    # First, get the asset ID from the symbol
    asset_res = supabase.table("assets").select("id").eq("symbol", symbol).execute()
    if not asset_res.data:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset_id = asset_res.data[0]['id']
    
    # Fetch all historical prices for this asset
    price_res = supabase.table("historical_prices") \
        .select("*") \
        .eq("asset_id", asset_id) \
        .order("timestamp", desc=True) \
        .execute()
        
    return price_res.data


@app.post("/sync/{symbol}")
def sync_asset(symbol: str, asset_type: str = "stock"):
    """
    Fetches and caches historical data for a new or existing asset.
    
    This triggers a full sync from yfinance to Supabase.
    Use this when adding a new asset or refreshing stale data.
    
    Args:
        symbol: Ticker symbol to sync
        asset_type: Either 'stock' or 'crypto'
        
    Returns:
        Success message with symbol name
        
    Raises:
        500: If sync fails
    """
    try:
        # Always use weekly interval
        coordinator.sync_asset(symbol, asset_type, "1wk")
        return {"status": "success", "message": f"Synced {symbol}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
