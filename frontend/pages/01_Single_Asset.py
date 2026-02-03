import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Single Asset View", page_icon="📈")
st.markdown("# Single Asset View")

# Fetch available assets for dropdown
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
asset_options = {a['symbol']: a for a in assets}

selected_symbol = st.selectbox(
    "Select an Asset",
    options=list(asset_options.keys())
)

if selected_symbol:
    # 1. Sync Button
    if st.button(f"Sync Data for {selected_symbol}"):
        with st.spinner("Syncing..."):
            try:
                asset_type = asset_options[selected_symbol]['asset_type']
                res = requests.post(f"{API_URL}/sync/{selected_symbol}", params={"asset_type": asset_type, "interval": "1wk"})
                if res.status_code == 200:
                    st.success(f"Successfully synced {selected_symbol}")
                    st.cache_data.clear() # Clear cache to refresh data
                else:
                    st.error(f"Sync failed: {res.text}")
            except Exception as e:
                st.error(f"Error connecting to API: {e}")

    # 2. Fetch History
    try:
        res = requests.get(f"{API_URL}/prices/{selected_symbol}", params={"interval": "1wk"})
        if res.status_code == 200:
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Fix for PyArrow LargeUtf8 error: Convert ALL object columns to str
                for col in df.select_dtypes(include=['object']).columns:
                    df[col] = df[col].astype(str)
                    
                df = df.sort_values("timestamp")
                
                st.subheader(f"Price History ({selected_symbol})")
                st.line_chart(df, x="timestamp", y="close_price")
                
                with st.expander("View Raw Data"):
                    # Use write instead of dataframe to avoid Arrow serialization issues
                    st.write(df.to_dict(orient='records'))
            else:
                st.info("No data found. Click 'Sync Data' to fetch history.")
    except Exception as e:
        st.error(f"API Error: {e}")
