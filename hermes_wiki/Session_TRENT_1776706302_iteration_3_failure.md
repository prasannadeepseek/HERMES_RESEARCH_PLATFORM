
## Iteration_3_FAILURE (Session: Session_TRENT_1776706302)
ROI: -9.23%
DD: -12.04%
Concept: Dual Moving Average Crossover with RSI filter
Failures: ['ROI (-9.23%) below target (5.0%)', 'Drawdown (12.04%) exceeds max (2.0%)']

Code:
```python
def evaluate(df, params):
    # Strategy: Dual Moving Average Crossover with RSI filter
    fast_ma = get_ma(df['close'], window=params.get('fast_ma', 10))
    slow_ma = get_ma(df['close'], window=params.get('slow_ma', 30))
    rsi = run_indicator('RSI', df['close'], window=params.get('rsi_window', 14))

    # Entry: Fast MA crosses above slow MA with RSI confirmation
    entries = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1)) & (rsi > params.get('rsi_entry', 50))

    # Exit: Fast MA crosses below slow MA or RSI shows weakness
    exits = (fast_ma < slow_ma) | (rsi < params.get('rsi_exit', 30))

    return entries, exits, None, None

PARAM_RANGES = {
    "fast_ma": range(5, 20, 3),
    "slow_ma": range(20, 50, 5),
    "rsi_window": range(10, 30, 2),
    "rsi_entry": range(45, 65, 5),
    "rsi_exit": range(25, 45, 5)
}
```
