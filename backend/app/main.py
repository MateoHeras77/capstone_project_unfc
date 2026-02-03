from fastapi import FastAPI, HTTPException
from typing import List, Optional
from ..core.database import get_supabase_client
from ..data_engine.data_coordinator import DataCoordinator

app = FastAPI(title="Investment Analytics API")
coordinator = DataCoordinator()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Investment Analytics API"}

@app.get("/assets")
def get_assets():
    supabase = get_supabase_client()
    res = supabase.table("assets").select("*").execute()
    return res.data

@app.get("/prices/{symbol}")
def get_prices(symbol: str, interval: str = "1wk"):
    supabase = get_supabase_client()
    
    # Get asset ID
    asset_res = supabase.table("assets").select("id").eq("symbol", symbol).execute()
    if not asset_res.data:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset_id = asset_res.data[0]['id']
    
    # Get prices
    price_res = supabase.table("historical_prices") \
        .select("*") \
        .eq("asset_id", asset_id) \
        .eq("interval", interval) \
        .order("timestamp", desc=True) \
        .execute()
        
    return price_res.data

@app.post("/sync/{symbol}")
def sync_asset(symbol: str, asset_type: str = "stock", interval: str = "1wk"):
    try:
        coordinator.sync_asset(symbol, asset_type, interval)
        return {"status": "success", "message": f"Synced {symbol}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
