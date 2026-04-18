# Hermes Swing Strategies Guide

This guide explains how to use the pre-built swing trading strategies in the Hermes Research Platform. These strategies are specifically tuned for multi-day/multi-week positional trading.

## Available Strategies

All strategies are located in the `hermes_strategies/` directory. They all share a common interface: the `analyze(data)` method.

### 1. Trend Momentum Strategy (`trend_momentum.py`)
- **Logic:** Waits for the 20-day Simple Moving Average (SMA) to cross above the 50-day SMA, indicating an uptrend. It then checks if the 14-day RSI is above 50 and if the MACD is rising. This ensures you only buy when there is strong momentum behind the trend.
- **Swing Tuning:** Targets a ~12% profit while keeping a stop-loss at the lowest price of the last 20 days. This wide stop prevents you from being shaken out by daily noise.

### 2. Mean Reversion Strategy (`mean_reversion.py`)
- **Logic:** Uses Bollinger Bands (20, 2) to find extremes. If the price drops below the lower Bollinger Band and the RSI is heavily oversold (< 35), it signals a buying opportunity under the assumption that price will revert to the mean (the middle band).
- **Swing Tuning:** Uses a 6% stop loss and targets the middle Bollinger band. This is a riskier strategy ("catching a falling knife"), hence the slightly tighter stop loss compared to the Trend Momentum strategy.

### 3. Delivery Analysis Strategy (`delivery_analysis.py`)
- **Logic:** Identifies institutional accumulation. If the percentage of trades resulting in delivery (buyers taking the stock home rather than intraday trading) spikes above 40% and is significantly higher than the 3-day average, it flags strong conviction.
- **Swing Tuning:** Very wide targets (15%) and stops (8%), as institutional buying takes time to fully price into the stock.

## How to Use Them

### 1. Live Screening
You can import the strategies into your daily data ingestion scripts or your main `app.py`.

```python
from hermes_strategies.trend_momentum import TrendMomentumStrategy

# Assuming you have recent daily close prices as a list or numpy array
data_feed = { 'close': [150.2, 151.5, 149.8, ... ] }

strategy = TrendMomentumStrategy()
signal = strategy.analyze(data_feed)

if signal:
    print(f"Found {signal['direction']} setup!")
    print(f"Entry: {signal['entry']}, Target: {signal['target']}, SL: {signal['sl']}")
```

### 2. Backtesting
We have provided a simple, event-driven backtesting engine in `backtester/swing_backtester.py`. This script simulates daily screening and manages position stop-losses and targets.

To run a backtest on historical data (e.g., AAPL):
```bash
# Make sure your environment is activated
source .venv/bin/activate

# Run the backtester
python backtester/swing_backtester.py
```

The backtester will print out an execution log of every trade it simulated, along with a final summary showing Win Rate and Total Return.
