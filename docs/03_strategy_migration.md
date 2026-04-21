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
Rewrite the logic to use the `OpenAlgoClient` (the REST client) instead of the old standalone fetchers.

```python
# hermes_strategies/intraday/morning_breakout.py
from data_pipeline.openalgo_connector import OpenAlgoClient

class MorningBreakoutStrategy:
    def __init__(self):
        # Hermes automatically configures the client from your .env
        self.client = OpenAlgoClient()
        
    def generate_signals(self, symbol):
        # 1. Fetch data via REST API (no file mounts needed)
        df = self.client.get_historical_data(
            symbol=symbol, 
            exchange="NSE", 
            interval="15minute",
            start_date=...,
            end_date=...
        )
        
        # 2. Apply your FNO / Intraday logic
        # ...
        return signals
```

## 3. Working with the AI Agents
The AI Agents (in the `agent/` directory) are designed to help you write, test, and debug these strategies. 
- **Agent Memory**: (`agent/memory.py`) The agent can read your old strategies from `temp_repos` and automatically suggest the equivalent `hermes_strategies` code.
- **Backtester**: (`backtester/`) Once a strategy is ported, use the backtester module to validate it against the OpenAlgo historical data before deploying it or converting it to a Streak.tech scanner.

## Summary

### Audit Persistence with SQLite/DuckDB

The platform now stores every generated iteration (code, metrics, and markdown log) in a compact database (`hermes.db`) instead of the sprawling `hermes_wiki/` folder. This provides:

- **Full audit trail** – code snippets, back‑test metrics, and the original markdown are retained.
- **Reduced repository size** – a single `hermes.db` file (few KB) replaces dozens of markdown files.
- **Easy querying** – use SQL (`SELECT * FROM strategies WHERE session_id = …`) or the helper functions `save_iteration`, `get_history` in `agent/db.py`.
- **Debug friendliness** – you can inspect per‑iteration details directly from the DB without scanning the filesystem.

**How it works**

1. `agent/db.py` creates the `strategies` table on start‑up (`init_db()`).
2. `HermesRunner` calls `save_iteration(...)` after each iteration, passing the markdown content that would have been written to the wiki.
3. A final failure entry is also stored if the loop exhausts the maximum iterations.
4. UI components retrieve history via `get_history(session_id)`.

**Tip:** To view the audit data locally, run:

```bash
python3 - <<'PY'
import duckdb, json
conn = duckdb.connect('hermes.db')
print(conn.execute("SELECT session_id, iteration, success FROM strategies ORDER BY session_id, iteration").fetchdf())
PY
```

For production deployments you may choose to move `hermes.db` to persistent storage (e.g., cloud bucket) and point `DB_PATH` in `agent/db.py` accordingly.

By keeping the old code in `temp_repos/` and the new, clean code in `hermes_strategies/`, you maintain a clear separation between legacy scripts and the new AI-driven architecture.
