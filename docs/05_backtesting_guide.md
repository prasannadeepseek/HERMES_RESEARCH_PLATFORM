# Backtesting Guide

Hermes has two backtesting engines for different use cases. Understanding when to use each is important for getting meaningful results.

## Engine 1: `backtester/engine.py` — `HermesBacktester` (AI Agent Engine)

This is the **primary engine** used by the AI agent loop. It is powered by **vectorbt** and is designed for high-speed, automated evaluation of boolean signal series.

### How It Works

The AI agent generates an `evaluate(df, params)` function that returns four boolean Pandas Series:
- `entries` — where to go long
- `exits` — where to exit longs
- `short_entries` — where to go short  
- `short_exits` — where to exit shorts

These signals are passed into `HermesBacktester.evaluate_signals()`, which runs a full portfolio simulation.

### Default Parameters

| Parameter | Default | Description |
|---|---|---|
| `initial_capital` | `100,000` | Starting capital in INR |
| `fees` | `0.001` (0.1%) | Brokerage + exchange fees per trade |
| `slippage` | `0.001` (0.1%) | Slippage per trade |

### Returned Metrics

```python
metrics = {
    "Total_Return_Pct": float,   # Total return as percentage
    "Max_Drawdown_Pct": float,   # Maximum drawdown as percentage (absolute value)
    "Win_Rate_Pct": float,       # Win rate as percentage
    "Sharpe_Ratio": float,       # Sharpe ratio
    "Total_Trades": int,         # Number of trades taken
    "Profit_Factor": float       # Gross profit / Gross loss
}
```

> [!NOTE]
> All `NaN` and `Inf` values in metrics are replaced with `0.0` before being passed to the LLM or logged to the registry, preventing JSON serialization errors.

### Goal Checking

`check_goals(metrics, config)` evaluates whether the strategy meets the user's targets. The `config` dict from the Streamlit UI can contain:

| Key | Description |
|---|---|
| `target_roi` | Minimum Total Return (%) required |
| `max_drawdown` | Maximum acceptable drawdown (%) |
| `min_win_rate` | Minimum win rate (%) required |

---

## Engine 2: `backtester/swing_backtester.py` — `SimpleBacktester` (Manual Engine)

This is a simpler, **event-driven backtester** designed for manual strategy research and prototyping. Unlike the vectorbt engine, it processes one day at a time, making it easier to debug and understand trade logic.

### How It Works

1. Iterates over historical data day by day (after a lookback window of 50 bars).
2. Each day, it feeds a rolling 50-bar window to the strategy's `analyze(data)` method.
3. If a signal is generated and no position is open, it opens a trade.
4. Each subsequent day checks if the stop-loss or target has been hit.

### Position Sizing

Each trade uses **10% of total current capital** (simplified fixed-fractional sizing). For production use, this should be replaced with a volatility-adjusted position sizer (e.g., ATR-based).

### Usage Example

```python
from backtester.swing_backtester import SimpleBacktester
from hermes_strategies.trend_momentum import TrendMomentumStrategy
import vectorbt as vbt

# Fetch data
data = vbt.YFData.download("RELIANCE.NS", period="2y").get()

# Run the backtest
strat = TrendMomentumStrategy()
bt = SimpleBacktester(data, strat, initial_capital=100000)
bt.run()
```

**Sample Output:**
```
Starting backtest with 100000 capital...
[2023-01-15] OPEN LONG at 2450.00 | Target: 2744.00 | SL: 2328.00
[2023-02-02] CLOSE LONG at 2744.00 (Target Hit) | PnL: 5880.00 (12.00%)

--- BACKTEST SUMMARY ---
Final Capital: 115234.50
Total Return: 15.23%
Total Trades: 8
Win Rate: 62.50%
Average PnL per trade: 1904.31
```

### Run from CLI
```bash
source .venv/bin/activate
python backtester/swing_backtester.py
```

---

## Choosing the Right Engine

| Use Case | Engine |
|---|---|
| AI agent strategy generation and iteration | `HermesBacktester` (engine.py) |
| Manual strategy research and debugging | `SimpleBacktester` (swing_backtester.py) |
| Intraday / FNO strategies with minute data | `HermesBacktester` (set `freq="1m"`) |
| Swing / positional strategies with daily data | `SimpleBacktester` or `HermesBacktester` (set `freq="1d"`) |

## Next Steps
See [06_security_model.md](./06_security_model.md) for a full breakdown of how the platform keeps LLM-generated code safe.
