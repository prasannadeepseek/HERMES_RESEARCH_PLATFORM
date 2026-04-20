
## Iteration_2_SUCCESS (Session: Session_SBIN_1776705731)
ROI: 7.49%
DD: -3.74%
Concept: Bollinger Band breakout with RSI confirmation
Failures: []

Code:
```python
def evaluate(df, params):
    # Strategy: Bollinger Band breakout with RSI confirmation
    bb = get_bbands(df['close'], window=params.get('bb_window', 20), std=params.get('bb_std', 2.0))
    rsi = run_indicator('RSI', df['close'], window=params.get('rsi_window', 14))
    
    # Entry: Price breaks above upper band and RSI confirms momentum
    entries = (df['close'] > bb.upper) & (rsi > params.get('rsi_entry', 50))
    
    # Exit: Price breaks below lower band or RSI shows weakness
    exits = (df['close'] < bb.lower) | (rsi < params.get('rsi_exit', 30))
    
    return entries, exits, None, None

PARAM_RANGES = {
    "bb_window": range(10, 30, 2),
    "bb_std": [1.5, 2.0, 2.5],
    "rsi_window": range(10, 30, 2),
    "rsi_entry": range(45, 65, 5),
    "rsi_exit": range(25, 45, 5)
}
```
