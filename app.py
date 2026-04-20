import streamlit as st
import pandas as pd
import numpy as np
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from agent.registry import HermesRegistry
from agent.memory import HermesMemory

load_dotenv()

st.set_page_config(page_title="Hermes AI Research Platform", page_icon="🦉", layout="wide")

st.title("🦉 Hermes AI Research Platform")
st.markdown("Automated algorithmic trading strategy generation and backtesting.")

# Sidebar for configuration
with st.sidebar:
    st.header("🎯 Strategy Goals")
    target_roi = st.number_input("Target ROI (%)", min_value=1.0, value=20.0, step=1.0)
    max_dd = st.number_input("Max Drawdown (%)", min_value=1.0, value=5.0, step=0.5)
    max_iterations = st.slider("Max Research Iterations", min_value=1, max_value=10, value=5)
    auto_deploy = st.toggle("🚀 Auto-Deploy Success to OpenAlgo", value=True)

    st.divider()
    with st.expander("🔑 Advanced API Settings"):
        st.subheader("LLM Configuration")
        ui_model = st.text_input("Model Name", value=os.getenv("MODEL_NAME", "openrouter/anthropic/claude-3.5-sonnet"))
        ui_api_base = st.text_input("API Base URL (Optional)", value=os.getenv("LLM_API_BASE", ""))
        ui_api_key = st.text_input("API Key (Override)", type="password")
        
        st.divider()
        st.subheader("🤖 Local Fallback")
        enable_fallback = st.toggle("Enable Local LLM Fallback", value=os.getenv("ENABLE_LOCAL_FALLBACK", "false").lower() == "true")
        if enable_fallback:
            st.info("Hermes will try to use a local Ollama instance if the cloud API fails.")
            os.environ["ENABLE_LOCAL_FALLBACK"] = "true"
        else:
            os.environ["ENABLE_LOCAL_FALLBACK"] = "false"
        
        st.subheader("Fallback Data (TrueData)")
        td_user = st.text_input("TrueData Username", value=os.getenv("TRUEDATA_USERNAME", ""))
        td_pass = st.text_input("TrueData Password", type="password")

    st.divider()
    st.subheader("🌐 MiroFish Grounding")
    memory = HermesMemory()
    if os.path.exists(memory.insights_file):
        with open(memory.insights_file, "r") as f:
            insights = f.read().split("\n")[-10:] # Show last 10 lines
            st.caption("\n".join(insights))
    else:
        st.info("No grounding insights yet.")

# Main layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Agent Thought Process & Logs")
    log_container = st.empty()
    log_container.code("Waiting for instructions...\n\n- Hermes is idle.\n- MCP Server integration ready.\n- Vectorbt backtesting core ready.")

with col2:
    st.subheader("Data Source")
    data_source = st.selectbox("Historical Data", ["OpenAlgo (DuckDB)", "Yahoo Finance (Sandbox)"], index=0)
    symbol = st.text_input("Symbol", value="DIXON")
    exchange = st.selectbox("Exchange", ["NSE", "NFO", "BSE", "MCX", "CDS"], index=0)
    interval = st.selectbox("Interval", ["1d", "1minute", "5minute", "15minute", "30minute", "1hour"], index=0)
    
    if st.button("Start Research Phase", type="primary", use_container_width=True):
        st.info(f"🚀 Starting Research: {symbol} (Target: {target_roi}% ROI, {max_dd}% DD)")
        
        # 1. Fetch Data
        df = pd.DataFrame()
        with st.spinner(f"Fetching data for {symbol} from {data_source}..."):
            if data_source == "OpenAlgo (DuckDB)":
                from data_pipeline.openalgo_connector import OpenAlgoDataConnector
                connector = OpenAlgoDataConnector()
                end_date = datetime.now()
                # Request more data for smaller intervals to ensure a good backtest
                days_to_fetch = 365 if interval == "1d" else 30
                start_date = end_date - timedelta(days=days_to_fetch)
                
                df = connector.get_historical_data(
                    symbol=symbol, 
                    exchange=exchange, 
                    interval=interval,
                    start_date=start_date, 
                    end_date=end_date
                )
                if df.empty:
                    st.warning("No data returned from OpenAlgo. Falling back to sandbox data.")
            
            if df.empty:
                # Sandbox fallback
                dates = pd.date_range(end=datetime.now(), periods=1000, freq='D')
                df = pd.DataFrame({
                    "close": np.random.randn(1000).cumsum() + 100,
                    "high": np.random.randn(1000).cumsum() + 105,
                    "low": np.random.randn(1000).cumsum() + 95,
                    "open": np.random.randn(1000).cumsum() + 100,
                    "volume": np.random.randint(100, 1000, 1000)
                }, index=dates)

        # 2. Config for Agent
        config = {
            "name": f"Research_{symbol}",
            "target_roi": target_roi,
            "max_drawdown": max_dd,
            "interval": interval
        }
        
        # 3. Initialize Runner with UI Overrides
        from agent.runner import HermesRunner
        runner = HermesRunner(
            session_id=f"Session_{symbol}_{int(time.time())}", 
            df=df, 
            config=config,
            llm_config={
                "model_name": ui_model,
                "api_base": ui_api_base,
                "api_key": ui_api_key if ui_api_key else None
            }
        )
        
        # 4. Execute Loop
        with st.status("Hermes is researching and backtesting...", expanded=True) as status:
            success = runner.execute_research_loop(
                max_iterations=max_iterations, 
                status_callback=lambda msg: status.write(msg),
                auto_deploy=auto_deploy
            )
            status.update(label="Research Phase Complete!", state="complete", expanded=False)
            
            if success:
                st.success("✅ Success! Strategy meeting all goals has been generated and exported.")
                
                # Fetch the best iteration to show Robustness
                registry = HermesRegistry()
                best = registry.get_best_iteration(runner.session_id)
                if best:
                    cols = st.columns(3)
                    cols[0].metric("Final ROI", f"{best['metrics'].get('Total_Return_Pct', 0):.2f}%")
                    cols[1].metric("Max Drawdown", f"{best['metrics'].get('Max_Drawdown_Pct', 0):.2f}%")
                    cols[2].metric("Robustness (OASIS)", f"{best.get('robustness_score', 0):.1f}%")
                    
                    if best.get('robustness_score', 0) >= 60:
                        st.success("🛡️ OASIS Stress Test Passed (Verified Robust)")
                    else:
                        st.warning("⚠️ OASIS Stress Test Warning (Fragile Strategy)")
                
                st.balloons()
            else:
                st.error("❌ Failed to find a strategy meeting the criteria.")

        # Show logs in the UI
        registry = HermesRegistry()
        history = registry.get_session_history(runner.session_id)
        
        log_text = ""
        for h in history:
            log_text += f"Iteration {h['iteration']}: ROI {h['metrics'].get('Total_Return_Pct', 0):.2f}%, DD {h['metrics'].get('Max_Drawdown_Pct', 0):.2f}% | Concept: {h.get('concept', 'N/A')}\n"
            if h['failures']:
                log_text += f"  - Failures: {h['failures']}\n"
        
        log_container.code(log_text if log_text else "No iterations completed.")
