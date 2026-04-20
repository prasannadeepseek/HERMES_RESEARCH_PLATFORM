
## Iteration_1_FAILURE (Session: Session_TRENT_1776706302)
ROI: -13.90%
DD: -14.08%
Concept: MACD crossover with volume confirmation
Failures: ['ROI (-13.90%) below target (5.0%)', 'Drawdown (14.08%) exceeds max (2.0%)']

Code:
```python
def evaluate(df, params):
    # Strategy: MACD crossover with volume confirmation
    macd = get_macd(df['close'], fast=params.get('fast', 12), slow=params.get('slow', 26), signal=params.get('signal', 9))
    entries = (macd.macd > macd.signal) & (macd.macd.shift(1) <= macd.signal.shift(1)) & (df['volume'] > params.get('min_volume', 1000))
    exits = (macd.macd < macd.signal) | (macd.macd.shift(1) >= macd.signal.shift(1))
    return entries, exits, None, None

PARAM_RANGES = {
    "fast": range(8, 16, 2),
    "slow": range(20, 30, 2),
    "signal": range(7, 13, 2),
    "min_volume": [500, 1000, 1500, 2000]
}
```
