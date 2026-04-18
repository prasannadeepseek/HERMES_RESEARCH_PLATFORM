# Hermes Swing Strategies Guide

This guide explains how to use the pre-built swing trading strategies in the Hermes Research Platform. These strategies are specifically tuned for multi-day/multi-week positional trading.

## Available Strategies

All strategies are located in the `hermes_strategies/` directory. They all share a common interface: the `analyze(data)` method.

### 1. Trend Momentum Strategy (`trend_momentum.py`)
- **Logic:** Waits for the 20-day SMA to cross above the 50-day SMA (uptrend), RSI > 50 (momentum), and MACD rising. Ensures strong conviction before entry.
- **Swing Tuning:** 12% target, stop-loss at the 20-day low (minimum 5% below entry).
- **Data Required:** `close` — at least **50 daily closing prices** as a list or NumPy array.
- **Dependencies:** `TA-Lib` (C library + Python package)

### 2. Mean Reversion Strategy (`mean_reversion.py`)
- **Logic:** Uses Bollinger Bands (20, 2) to find price extremes. Entry when price drops below the lower band and RSI < 35. Target is the middle band (mean reversion).
- **Swing Tuning:** 6% stop-loss, target is the 20-day SMA middle band.
- **Data Required:** `close` — at least **20 daily closing prices** as a list or NumPy array.
- **Dependencies:** `TA-Lib` (C library + Python package)

### 3. Delivery Analysis Strategy (`delivery_analysis.py`)
- **Logic:** Detects institutional accumulation via delivery volume spikes. Entry when delivery % > 40 and the 3-day average ratio > 1.5 (well above normal).
- **Swing Tuning:** 15% target, 8% stop-loss, valid signal for 5 trading days.
- **Data Required:** `delivery_pct`, `delivery_3day_avg`, `close` — these must be fetched from NSE bhavcopy or a similar delivery data source.
- **Dependencies:** None (pure Python)

## Input Data Format

All `analyze(data)` methods accept a Python dictionary:

```python
# For Trend Momentum and Mean Reversion:
data = {
    'close': [150.2, 151.5, 149.8, ...]  # list or np.ndarray
}

# For Delivery Analysis:
data = {
    'delivery_pct': 45.2,          # float: today's delivery percentage
    'delivery_3day_avg': 1.8,      # float: ratio of today's delivery to 3-day avg
    'close': 2450.0                # float: today's closing price
}
```

## How to Use Them

### 1. Live Screening
```python
from hermes_strategies.trend_momentum import TrendMomentumStrategy

data_feed = {'close': [150.2, 151.5, 149.8, ...]}  # 50+ values

strategy = TrendMomentumStrategy()
signal = strategy.analyze(data_feed)

if signal:
    print(f"Found {signal['direction']} setup!")
    print(f"Entry: {signal['entry']}, Target: {signal['target']}, SL: {signal['sl']}")
    print(f"Score: {signal['score']}/10, Valid for: {signal.get('validity_days', 'N/A')} days")
```

### Signal Output Format

All strategies return either `None` (no setup) or a dictionary:

| Key | Type | Description |
|---|---|---|
| `entry` | `float` | Suggested entry price |
| `sl` | `float` | Stop-loss price |
| `target` | `float` | Profit target price |
| `direction` | `str` | `'long'` or `'short'` |
| `score` | `int` | Signal strength 1–10 |
| `type` | `str` | Strategy identifier |
| `timeframe` | `str` | `'swing'` or `'positional'` |
| `validity_days` | `int` | Days this signal is considered valid (delivery strategy only) |

### 2. Backtesting
We have provided a simple, event-driven backtesting engine in `backtester/swing_backtester.py`. This script simulates daily screening and manages position stop-losses and targets.

To run a backtest on historical data:
```bash
# Make sure your environment is activated
source .venv/bin/activate

# Run the backtester
python backtester/swing_backtester.py
```

For a full explanation of both backtesting engines, see [05_backtesting_guide.md](./05_backtesting_guide.md).

## Adding a New Strategy

1. Create a new file in `hermes_strategies/` (e.g., `vwap_bounce.py`).
2. Implement a class with an `analyze(data: dict) -> Optional[dict]` method.
3. Return a signal dict matching the format above, or `None` if no setup.
4. Import and test it in `backtester/swing_backtester.py`.

> [!NOTE]
> When the AI agent auto-generates and exports a strategy, it goes through a **security gate** that checks for dangerous code patterns before writing the file to disk. See [06_security_model.md](./06_security_model.md) for details.

