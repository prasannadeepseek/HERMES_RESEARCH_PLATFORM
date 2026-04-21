
## Iteration_1_SUCCESS (Session: Session_NESTLEIND_1776778572)
ROI: 13.60%
DD: -1.94%
Concept: Dual Moving Average Crossover with RSI confirmation and volume filter
Failures: []

Code:
```python
def evaluate(df, params):
    # Strategy: Dual Moving Average Crossover with RSI confirmation and volume filter
    fast_ma = get_ma(df['close'], window=params.get('fast_ma', 10))
    slow_ma = get_ma(df['close'], window=params.get('slow_ma', 30))
    rsi = run_indicator('RSI', df['close'], window=params.get('rsi_window', 14))
    entries = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1)) & (rsi > params.get('rsi_entry', 50)) & (df['volume'] > params.get('min_volume', 1000))
    exits = (fast_ma < slow_ma) | (rsi < params.get('rsi_exit', 30)) | (df['volume'] < params.get('min_volume', 1000))
    return entries, exits, None, None

PARAM_RANGES = {
    "fast_ma": range(8, 16, 2),
    "slow_ma": range(20, 40, 5),
    "rsi_window": range(10, 30, 2),
    "rsi_entry": range(45, 65, 5),
    "rsi_exit": range(25, 45, 5),
    "min_volume": [500, 1000, 1500, 2000]
}
```
