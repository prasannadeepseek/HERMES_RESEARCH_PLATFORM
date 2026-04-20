
## Iteration_3_FAILURE (Session: Session_SBIN_1776706128)
ROI: 4.09%
DD: -6.59%
Concept: Bollinger Band breakout with RSI confirmation and volatility filter
Failures: ['ROI (4.09%) below target (5.0%)', 'Drawdown (6.59%) exceeds max (2.0%)']

Code:
```python
def evaluate(df, params):
    # Strategy: Bollinger Band breakout with RSI confirmation and volatility filter
    bb = get_bbands(df['close'], window=params.get('bb_window', 20), std=params.get('bb_std', 2.0))
    rsi = run_indicator('RSI', df['close'], window=params.get('rsi_window', 14))
    atr = get_atr(df['high'], df['low'], df['close'], window=params.get('atr_window', 14))
    
    # Entry: Price breaks above upper band with strong momentum and sufficient volatility
    entries = (df['close'] > bb.upper) & (rsi > params.get('rsi_entry', 50)) & (atr > params.get('min_atr', 0.5))
    
    # Exit: Price breaks below lower band, RSI shows weakness, or volatility drops
    exits = (df['close'] < bb.lower) | (rsi < params.get('rsi_exit', 30)) | (atr < params.get('min_atr', 0.5))
    
    return entries, exits, None, None

PARAM_RANGES = {
    "bb_window": range(10, 30, 2),
    "bb_std": [1.5, 2.0, 2.5],
    "rsi_window": range(10, 30, 2),
    "rsi_entry": range(45, 65, 5),
    "rsi_exit": range(25, 45, 5),
    "atr_window": range(10, 20, 2),
    "min_atr": [0.3, 0.5, 0.7, 0.9]
}
```
