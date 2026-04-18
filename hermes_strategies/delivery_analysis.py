from typing import Optional, Dict, Any

class DeliveryAnalysisStrategy:
    """
    Analyzes delivery volume patterns to generate trading signals based on delivery percentage and averages.
    Tuned for Swing / Positional Trading. High delivery signifies long-term institutional interest.
    """

    def analyze(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze delivery volume patterns and return a signal dict if criteria are met.

        Args:
            data (dict): Must contain 'delivery_pct', 'delivery_3day_avg', and 'close' keys.

        Returns:
            dict or None: Signal dictionary if a pattern is detected, else None.
        """
        # Defensive: Ensure required keys exist and are valid numbers
        try:
            delivery_pct = float(data.get('delivery_pct', 0))
            delivery_3day_avg = float(data.get('delivery_3day_avg', 0))
            close = float(data.get('close', 0))
        except (TypeError, ValueError):
            return None

        if close <= 0:
            return None

        # Swing Parameters
        # Institutional delivery signals often take days/weeks to unfold.
        # We need wider stops and higher targets.
        target_pct = 1.15  # 15% target
        sl_pct = 0.92      # 8% stop loss

        # High delivery volume (strong accumulation sign)
        if delivery_pct > 40 and delivery_3day_avg > 1.5:
            return {
                'score': 9, # High score for swing trades
                'reason': 'high_delivery_volume_accumulation',
                'validity_days': 5, # Valid for 5 days in swing trading
                'entry': close,
                'sl': round(close * sl_pct, 2),
                'target': round(close * target_pct, 2),
                'direction': 'long',
                'timeframe': 'positional'
            }
        
        # Low delivery volume (lack of interest)
        elif delivery_pct < 25:
            return {
                'score': 3,
                'reason': 'low_delivery_volume_distribution',
                'validity_days': 1
            }
            
        return None
