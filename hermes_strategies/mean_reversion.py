import talib
import numpy as np
from typing import Dict, Any, Optional

class MeanReversionStrategy:
    """
    Identifies mean reversion opportunities using Bollinger Bands and RSI.
    Tuned for Swing Trading: targets middle band but uses wider stops.
    """

    def analyze(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze price data for mean reversion signals.

        Args:
            data (dict): Must contain 'close' as a list or np.ndarray of recent closing prices.

        Returns:
            dict or None: Signal dictionary if a setup is detected, else None.
        """
        closes = np.asarray(data.get('close', []))
        if closes.size < 20:
            # Not enough data for 20-period indicators
            return None

        # Calculate Bollinger Bands (20, 2) and RSI (14)
        upper, middle, lower = talib.BBANDS(closes, timeperiod=20, nbdevup=2, nbdevdn=2)
        rsi = talib.RSI(closes, timeperiod=14)[-1]

        last_close = closes[-1]
        signal = None

        # Swing trading SL %
        sl_pct_long = 0.94   # 6% stop loss for swing
        sl_pct_short = 1.06  # 6% stop loss for short

        # Long setup: price below lower band and oversold RSI
        if last_close < lower[-1] and rsi < 35:
            signal = {
                'entry': last_close,
                'sl': round(last_close * sl_pct_long, 2),
                'target': round(middle[-1], 2),  # Target is mean reversion (20-day SMA)
                'score': 7,
                'type': 'mean_reversion',
                'direction': 'long',
                'timeframe': 'swing'
            }
        
        # Short setup: price above upper band and overbought RSI
        elif last_close > upper[-1] and rsi > 65:
            signal = {
                'entry': last_close,
                'sl': round(last_close * sl_pct_short, 2),
                'target': round(middle[-1], 2),
                'score': 6,
                'type': 'mean_reversion',
                'direction': 'short',
                'timeframe': 'swing'
            }

        return signal
