import streamlit as st
import plotly.graph_objects as go

# 1. Page Config
st.set_page_config(page_title="Hermes AI Research", layout="wide")

# Initialize session state variables
if 'running' not in st.session_state:
    st.session_state['running'] = False
if 'fig' not in st.session_state:
    st.session_state['fig'] = None

# 2. Sidebar Configuration
with st.sidebar:
    st.title("🦉 Hermes Control")
    symbol = st.selectbox("Symbol", ["SBIN", "TRENT", "DIXON", "RELIANCE"])
    interval = st.select_slider("Interval", options=["5m", "15m", "1h", "1d"])
    if st.busttton("Start Autonomous Research", type="primary"):
        st.session_state.running = True

# 3. Main Dashboard Tabs
tab1, tab2, tab3 = st.tabs(["Research Loop", "Strategy Library", "OpenAlgo Status"])

with tab1:
    if st.session_state.get('running'):
        with st.status("Hermes is researching...", expanded=True) as status:
            st.write("Fetching historical data from OpenAlgo...")
            # Placeholder for data fetching logic
            st.write("LLM is generating strategy hypothesis...")
            # Placeholder for runner logic
            status.update(label="Research Cycle Complete!", state="complete", expanded=False)

    st.subheader("Latest Backtest Results")
    # Example metric placeholders (replace with real values)
    col1, col2, col3 = st.columns(3)
    col1.metric("ROI", "0%")
    col2.metric("Max Drawdown", "0%")
    col3.metric("Robustness", "0%")

    if st.session_state.get('fig'):
        st.plotly_chart(st.session_state.fig, use_container_width=True)

with tab2:
    st.header("Strategy Wiki")
    # List markdown files in hermes_wiki directory
    import os
    wiki_path = os.path.join(os.getcwd(), "hermes_wiki")
    if os.path.isdir(wiki_path):
        for file_name in sorted(os.listdir(wiki_path)):
            if file_name.endswith('.md'):
                st.subheader(file_name)
                with open(os.path.join(wiki_path, file_name), "r", encoding="utf-8") as f:
                    st.markdown(f"""
{f.read()}
""")
    else:
        st.info("Strategy wiki directory not found.")

with tab3:
    st.header("OpenAlgo Status")
    st.info("OpenAlgo connection status placeholder.")
