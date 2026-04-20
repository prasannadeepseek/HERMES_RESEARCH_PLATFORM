
## Iteration_2_FAILURE (Session: Session_SBIN_1776706128)
ROI: 2.98%
DD: -7.10%
Concept: Dual Moving Average Crossover with Volatility Filter
Failures: ['ROI (2.98%) below target (5.0%)', 'Drawdown (7.10%) exceeds max (2.0%)']

Code:
```python
def evaluate(df, params):
    # Strategy: Dual Moving Average Crossover with Volatility Filter
    fast_ma = get_ma(df['close'], window=params.get('fast_ma', 10))
    slow_ma = get_ma(df['close'], window=params.get('slow_ma', 30))
    atr = get_atr(df['high'], df['low'], df['close'], window=params.get('atr_window', 14))
    
    # Entry: Fast MA crosses above slow MA with sufficient volatility
    entries = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1)) & (atr > params.get('min_atr', 0.5))
    
    # Exit: Fast MA crosses below slow MA or ATR drops below threshold
    exits = (fast_ma < slow_ma) | (atr < params.get('min_atr', 0.5))
    
    return entries, exits, None, None

PARAM_RANGES = {
    "fast_ma": range(5, 20, 3),
    "slow_ma": range(20, 50, 5),
    "atr_window": range(10, 20, 2),
    "min_atr": [0.3, 0.5, 0.7, 0.9]
}
```
