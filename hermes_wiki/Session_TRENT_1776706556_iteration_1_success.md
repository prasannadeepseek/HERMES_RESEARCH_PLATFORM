
## Iteration_1_SUCCESS (Session: Session_TRENT_1776706556)
ROI: 18.71%
DD: -4.51%
Concept: Bollinger Band breakout with RSI confirmation and volume filter
Failures: []

Code:
```python
def evaluate(df, params):
    # Strategy: Bollinger Band breakout with RSI confirmation and volume filter
    bb = get_bbands(df['close'], window=params.get('bb_window', 20), std=params.get('bb_std', 2.0))
    rsi = run_indicator('RSI', df['close'], window=params.get('rsi_window', 14))
    entries = (df['close'] > bb.upper) & (rsi > params.get('rsi_entry', 50)) & (df['volume'] > params.get('min_volume', 1000))
    exits = (df['close'] < bb.lower) | (rsi < params.get('rsi_exit', 30)) | (df['volume'] < params.get('min_volume', 1000))
    return entries, exits, None, None

PARAM_RANGES = {
    "bb_window": range(10, 30, 2),
    "bb_std": [1.5, 2.0, 2.5],
    "rsi_window": range(10, 30, 2),
    "rsi_entry": range(45, 65, 5),
    "rsi_exit": range(25, 45, 5),
    "min_volume": [500, 1000, 1500, 2000]
}
```
