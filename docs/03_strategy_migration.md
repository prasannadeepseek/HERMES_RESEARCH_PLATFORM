# Strategy Migration & Development

The Hermes platform is designed to consolidate your previous trading systems (Swing Trader Pro, FII/DII Tracker, etc.) into unified AI-assisted workflows.

## 1. Where Legacy Code Lives
Your old repositories have been preserved inside `temp_repos/` for reference:
- `temp_repos/swing-trader-pro/`: Contains your Upstox broker integrations, risk engine, and FNO hedge detection logic.
- `temp_repos/trading-system/`: Contains GCC setups and intraday methodologies.
- `temp_repos/fii-dii-tracker/`: Contains the FII/DII tracking strategies.

## 2. The Hermes Strategy Format
We want to transition these scripts from standalone Python files into structured modules under the `hermes_strategies/` directory.

A standard Hermes Strategy should include:
1. **Data Requirements**: What data does it need (from OpenAlgo)?
2. **Signal Generation**: The core logic (e.g., crossing EMAs, VWAP bounces).
3. **Streak Translation**: Logic to translate the signal generation into Streak.tech readable conditions.

### Example Migration Workflow

**Step 1: Identify the Old Logic**
Locate `temp_repos/swing-trader-pro/swing-trader-pro/scripts/morning_setup.py`.

**Step 2: Create a New Module**
Create a new file `hermes_strategies/intraday/morning_breakout.py`.

**Step 3: Adapt the Code**
Rewrite the logic to use the `OpenAlgoDataConnector` instead of the old `nse_fetcher.py`.

```python
# hermes_strategies/intraday/morning_breakout.py
from data_pipeline.openalgo_connector import OpenAlgoDataConnector

class MorningBreakoutStrategy:
    def __init__(self):
        self.data_connector = OpenAlgoDataConnector()
        
    def generate_signals(self, symbol):
        # 1. Fetch data
        df = self.data_connector.get_historical_data(symbol, ...)
        
        # 2. Apply your FNO / Intraday logic
        # ...
        return signals
```

## 3. Working with the AI Agents
The AI Agents (in the `agent/` directory) are designed to help you write, test, and debug these strategies. 
- **Agent Memory**: (`agent/memory.py`) The agent can read your old strategies from `temp_repos` and automatically suggest the equivalent `hermes_strategies` code.
- **Backtester**: (`backtester/`) Once a strategy is ported, use the backtester module to validate it against the OpenAlgo historical data before deploying it or converting it to a Streak.tech scanner.

## Summary
By keeping the old code in `temp_repos/` and the new, clean code in `hermes_strategies/`, you maintain a clear separation between legacy scripts and the new AI-driven architecture.
