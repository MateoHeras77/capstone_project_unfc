import streamlit as st

st.set_page_config(
    page_title="Investment Analytics",
    page_icon="📈",
)

st.write("# Welcome to the Educational Investment Platform! 👋")

st.markdown(
    """
    This tool is designed to help you understand financial risk and forecasting.
    
    ### 👈 Select a page from the sidebar to get started
    
    *   **Single Asset View:** Dive deep into one stock or crypto. See its history and eventually run forecasts.
    *   **Comparison View:** Compare multiple assets side-by-side.
    
    ---
    
    ### 🔍 How to find ticker symbols
    
    You can search for any stock or cryptocurrency ticker on **Yahoo Finance**:
    
    👉 [https://ca.finance.yahoo.com/](https://ca.finance.yahoo.com/)
    
    **Examples:**
    - Stocks: `AAPL` (Apple), `TSLA` (Tesla), `GOOGL` (Google)
    - Crypto: `BTC-USD` (Bitcoin), `ETH-USD` (Ethereum)
    - Indices: `^GSPC` (S&P 500), `^DJI` (Dow Jones)
    
    ---
    
    *This is currently a **Validation Build** (Phase 2) to ensure our data engine is persistent and accurate.*
    """
)

