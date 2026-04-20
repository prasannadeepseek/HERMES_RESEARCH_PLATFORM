
## Iteration_1_FAILURE (Session: Session_SBIN_1776705731)
ROI: 1.03%
DD: -6.82%
Concept: Mean-reversion RSI strategy with dynamic thresholds
Failures: ['ROI (1.03%) below target (5.0%)', 'Drawdown (6.82%) exceeds max (5.0%)']

Code:
```python
def evaluate(df, params):
    # Strategy: Mean-reversion RSI strategy with dynamic thresholds
    rsi_window = params.get('rsi_window', 14)
    rsi = run_indicator('RSI', df['close'], window=rsi_window)
    entries = (rsi < params.get('rsi_lower', 25)) & (rsi.shift(1) >= params.get('rsi_lower', 25))
    exits = (rsi > params.get('rsi_upper', 75)) & (rsi.shift(1) <= params.get('rsi_upper', 75))
    return entries, exits, None, None

PARAM_RANGES = {
    "rsi_window": range(10, 30, 2),
    "rsi_lower": range(20, 40, 5),
    "rsi_upper": range(60, 80, 5)
}
```
