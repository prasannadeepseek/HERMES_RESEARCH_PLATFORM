import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from data_pipeline.openalgo_connector import OpenAlgoDataConnector
from agent.runner import HermesRunner

load_dotenv()

def run_dixon_research():
    symbol = "DIXON"
    exchange = "NSE"
    interval = "5minute" # Using the Hermes internal interval name
    
    print(f"--- Starting Deep Research for {symbol} ({interval}) ---")
    
    # 1. Fetch Data
    connector = OpenAlgoDataConnector()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60) # Fetch 60 days of 5m data
    
    print(f"Fetching data from {start_date.date()} to {end_date.date()}...")
    df = connector.get_historical_data(
        symbol=symbol, 
        exchange=exchange, 
        interval=interval,
        start_date=start_date, 
        end_date=end_date
    )
    
    if df.empty:
        print("Error: No data retrieved. Check connection.")
        return

    print(f"Successfully loaded {len(df)} rows.")

    # 2. Configure Agent Goals
    config = {
        "name": f"{symbol}_Research_Session",
        "target_roi": 5.0,        # As requested
        "max_drawdown": 5.0,      # As requested
        "max_iterations": 5       # Give it more attempts
    }

    # 3. Run Agent
    runner = HermesRunner(
        session_id=f"DeepDive_{int(datetime.now().timestamp())}", 
        df=df, 
        config=config
    )

    print("\n--- AI Agent is now thinking and backtesting ---")
    success = runner.execute_research_loop(max_iterations=config["max_iterations"])

    if success:
        print("\n✅ SUCCESS: Found a strategy meeting your goals!")
    else:
        print("\n❌ FAILED: Could not meet goals within 5 iterations.")

if __name__ == "__main__":
    run_dixon_research()
