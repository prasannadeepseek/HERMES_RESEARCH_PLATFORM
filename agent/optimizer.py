import itertools
import pandas as pd
import numpy as np

class HermesOptimizer:
    """
    Performs local parameter optimization to reduce LLM hits.
    Takes generated code, identifies PARAM_RANGES, and finds the best combination.
    """
    def __init__(self, backtester):
        self.backtester = backtester

    def optimize(self, df: pd.DataFrame, evaluate_func, param_ranges: dict, target_config: dict):
        """
        Runs a grid search over param_ranges to find the best metrics.
        """
        if not param_ranges:
            # Nothing to optimize
            return {}, {}

        # Generate all combinations of parameters
        keys = list(param_ranges.keys())
        # Convert range/list to list if necessary
        values = [list(v) if isinstance(v, (range, list)) else [v] for v in param_ranges.values()]
        
        combinations = list(itertools.product(*values))
        
        best_metrics = None
        best_params = None
        best_score = -float('inf') # We'll use ROI as the score for now
        
        print(f"Starting local optimization over {len(combinations)} combinations...")
        
        # Limit to 100 combinations to keep it fast
        if len(combinations) > 100:
            import random
            combinations = random.sample(combinations, 100)
            print(f"Limited search to 100 random combinations.")

        for combo in combinations:
            params = dict(zip(keys, combo))
            try:
                entries, exits, short_entries, short_exits = evaluate_func(df, params)
                metrics, _ = self.backtester.evaluate_signals(
                    df=df, 
                    entries=entries, 
                    exits=exits, 
                    short_entries=short_entries, 
                    short_exits=short_exits
                )
                
                # Simple scoring: ROI - MaxDrawdown/2 (Adjust as needed)
                score = metrics.get("Total_Return_Pct", 0) - (metrics.get("Max_Drawdown_Pct", 0) / 2.0)
                
                # Check if it meets the goals
                goals_met, _ = self.backtester.check_goals(metrics, target_config)
                
                if goals_met and score > best_score:
                    best_score = score
                    best_metrics = metrics
                    best_params = params
                    # If we met the goals and it's better than before, we could potentially stop early,
                    # but let's find the 'best' within the sample.
            except Exception as e:
                # print(f"Optimization trial failed: {e}")
                continue
                
        return best_metrics, best_params
