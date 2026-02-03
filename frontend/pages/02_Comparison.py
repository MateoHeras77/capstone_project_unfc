import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Comparison View", page_icon="📊")
st.markdown("# Asset Comparison")

@st.cache_data
def get_assets():
    try:
        response = requests.get(f"{API_URL}/assets")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
    return []

assets = get_assets()
symbols = [a['symbol'] for a in assets]

selected_symbols = st.multiselect(
    "Select Assets to Compare",
    options=symbols,
    default=symbols[:2] if len(symbols) >= 2 else symbols
)

if selected_symbols:
    comparison_data = []
    
    for symbol in selected_symbols:
        try:
            # Fetch latest price (try 1wk first, then 1mo)
            res = requests.get(f"{API_URL}/prices/{symbol}", params={"interval": "1wk"})
            data = res.json() if res.status_code == 200 else []
            
            if not data:
                 res = requests.get(f"{API_URL}/prices/{symbol}", params={"interval": "1mo"})
                 data = res.json() if res.status_code == 200 else []
            
            if data:
                latest = data[0] # Order is desc
                comparison_data.append({
                    "Symbol": symbol,
                    "Latest Date": latest['timestamp'],
                    "Close Price": latest['close_price'],
                    "Volume": latest['volume']
                })
        except Exception:
            pass
            
    if comparison_data:
        # Use st.write to avoid PyArrow LargeUtf8 serialization issues
        st.write(comparison_data)
    else:
        st.info("No data available for selected assets.")
