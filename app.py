import streamlit as st
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Hermes AI Research Platform", page_icon="🦉", layout="wide")

st.title("🦉 Hermes AI Research Platform")
st.markdown("Automated algorithmic trading strategy generation and backtesting.")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    llm_provider = st.selectbox("LLM Provider", ["OpenRouter", "Local (Gemma 4)"], index=0)
    openalgo_url = st.text_input("OpenAlgo URL", value=os.getenv("OPENALGO_HOST", "http://127.0.0.1:5000"))
    
    st.divider()
    st.header("🎯 Strategy Goals")
    target_roi = st.number_input("Target ROI (%)", min_value=1.0, value=20.0, step=1.0)
    max_dd = st.number_input("Max Drawdown (%)", min_value=1.0, value=5.0, step=0.5)

# Main layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Agent Thought Process & Logs")
    # Placeholder for logs
    log_container = st.empty()
    log_container.code("Waiting for instructions...\n\n- Hermes is idle.\n- MCP Server integration ready.\n- Vectorbt backtesting core ready.")

with col2:
    st.subheader("Data Source")
    data_source = st.selectbox("Historical Data", ["OpenAlgo (DuckDB)", "TrueData CSV", "Yahoo Finance (Sandbox)"])
    symbol = st.text_input("Symbol", value="NIFTY")
    
    if st.button("Start Research Phase", type="primary", use_container_width=True):
        st.info(f"Initializing Hermes with {llm_provider}...")
        
        # 1. Prepare Configuration
        config = {
            "name": f"{symbol}_AI_Strategy",
            "target_roi": target_roi,
            "max_drawdown": max_dd
        }
        
        # 2. Mock Data for MVP (In reality, fetch from OpenAlgoConnector)
        st.write("Loading Historical Data...")
        import pandas as pd
        import numpy as np
        dates = pd.date_range("2020-01-01", periods=1000, freq="1d")
        df = pd.DataFrame({
            "close": np.random.randn(1000).cumsum() + 100,
            "open": np.random.randn(1000).cumsum() + 100,
        }, index=dates)
        
        # 3. Initialize Runner
        from agent.runner import HermesRunner
        runner = HermesRunner(session_id=f"Session_{symbol}_{int(time.time())}", df=df, config=config)
        
        # 4. Execute Loop
        with st.spinner("Agent is researching and backtesting..."):
            success = runner.execute_research_loop(max_iterations=3)
            
        if success:
            st.success("Research Complete! Strategy Exported.")
        else:
            st.error("Failed to find a strategy meeting the criteria.")

st.divider()

st.subheader("🧠 Context & Memory")
col3, col4, col5 = st.columns(3)
with col3:
    st.metric(label="Wiki Summaries", value="0 files")
with col4:
    st.metric(label="Redundant Skills Generated", value="0 scripts")
with col5:
    st.metric(label="Strategies in Registry", value="0")
