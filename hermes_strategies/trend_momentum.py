import numpy as np
import talib
from typing import Dict, Any, Optional

class TrendMomentumStrategy:
    """
    Identifies trend momentum opportunities using SMA, RSI, and MACD.
    Tuned for Swing Trading (Positional).
    Expects Daily (1D) close prices.
    """

    def analyze(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze price data for trend momentum signals.

        Args:
            data (dict): Must contain 'close' as a list or np.ndarray of recent closing prices.

        Returns:
            dict or None: Signal dictionary if a setup is detected, else None.
        """
        closes = np.asarray(data.get('close', []))
        if closes.size < 50:
            # Not enough data for 50-period indicators
            return None

        closes = closes[-50:]

        # Trend confirmation
        sma20 = talib.SMA(closes, timeperiod=20)[-1]
        sma50 = talib.SMA(closes, timeperiod=50)[-1]

        # Momentum confirmation
        rsi = talib.RSI(closes, timeperiod=14)[-1]
        macd, macdsignal, macdhist = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)

        # Swing Trading parameters
        target_pct_long = 1.12   # 12% target for swing
        target_pct_short = 0.88  # 12% target for short swing

        # Long setup: uptrend, strong momentum
        if (sma20 > sma50 and rsi > 50 and macd[-1] > macd[-5]):
            # Stop loss at 20-day low to withstand daily volatility
            sl = float(np.min(closes[-20:]))
            # Ensure SL is not too tight (minimum 5% below entry)
            if (closes[-1] - sl) / closes[-1] < 0.05:
                sl = closes[-1] * 0.95

            return {
                'entry': closes[-1],
                'sl': round(sl, 2),
                'target': round(closes[-1] * target_pct_long, 2),
                'score': 8,
                'type': 'trend_momentum',
                'direction': 'long',
                'timeframe': 'swing'
            }
        
        # Short setup: downtrend, weak momentum
        elif (sma20 < sma50 and rsi < 50 and macd[-1] < macd[-5]):
            # Stop loss at 20-day high
            sl = float(np.max(closes[-20:]))
            if (sl - closes[-1]) / closes[-1] < 0.05:
                sl = closes[-1] * 1.05

            return {
                'entry': closes[-1],
                'sl': round(sl, 2),
                'target': round(closes[-1] * target_pct_short, 2),
                'score': 7,
                'type': 'trend_momentum',
                'direction': 'short',
                'timeframe': 'swing'
            }
        
        return None
