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
    
    This is currently a **Validation Build** (Phase 2) to ensure our data engine is persistent and accurate.
    """
)
