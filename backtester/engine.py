import vectorbt as vbt
import pandas as pd
import numpy as np

class HermesBacktester:
    """
    High-speed vectorbt-based backtesting engine tailored for Intraday and FnO strategies.
    """
    def __init__(self, initial_capital=100000.0, fees=0.001, slippage=0.001):
        self.initial_capital = initial_capital
        # Standardize fees/slippage for realistic FnO testing
        self.fees = fees
        self.slippage = slippage

    def evaluate_signals(self, df: pd.DataFrame, entries: pd.Series, exits: pd.Series, 
                         short_entries: pd.Series = None, short_exits: pd.Series = None,
                         freq: str = "1m", **kwargs):
        """
        Takes raw entry/exit boolean signals and processes them through vectorbt.
        Returns a dictionary of core performance metrics.
        """
        # print(f"DEBUG: evaluate_signals called with {len(locals())} arguments.")
        # Ensure we are using the close price for signal execution
        price = df['close']
        
        # Count signals for debugging
        entry_count = entries.sum() if entries is not None else 0
        print(f"DEBUG: evaluate_signals received {entry_count} entry signals.")

        # Handle simple Long-only strategies if shorts aren't provided
        if short_entries is None:
            short_entries = pd.Series(False, index=df.index)
        if short_exits is None:
            short_exits = pd.Series(False, index=df.index)

        # Run vectorbt Portfolio simulation
        portfolio = vbt.Portfolio.from_signals(
            close=price,
            entries=entries,
            exits=exits,
            short_entries=short_entries,
            short_exits=short_exits,
            init_cash=self.initial_capital,
            fees=self.fees,
            slippage=self.slippage,
            freq=freq
        )

        # Extract Metrics (Ensuring scalar values for stability)
        def to_scalar(val):
            if hasattr(val, 'iloc'):
                return float(val.iloc[0]) if len(val) > 0 else 0.0
            return float(val) if val is not None else 0.0

        metrics = {
            "Total_Return_Pct": to_scalar(portfolio.total_return()) * 100,
            "Max_Drawdown_Pct": to_scalar(portfolio.max_drawdown()) * 100,
            "Win_Rate_Pct": to_scalar(portfolio.trades.win_rate()) * 100,
            "Sharpe_Ratio": to_scalar(portfolio.sharpe_ratio()),
            "Total_Trades": int(to_scalar(len(portfolio.trades))),
            "Profit_Factor": to_scalar(portfolio.trades.profit_factor())
        }
        
        # Replace NaN/Inf with 0 for cleaner LLM processing
        for k, v in metrics.items():
            if pd.isna(v) or np.isinf(v):
                metrics[k] = 0.0

        return metrics, portfolio

    def check_goals(self, metrics: dict, config: dict) -> tuple:
        """
        Evaluates the backtest metrics against the user's custom strategy_config.yaml goals.
        """
        goals_met = True
        failures = []
        
        # Check ROI
        if "target_roi" in config:
            if metrics["Total_Return_Pct"] < config["target_roi"]:
                goals_met = False
                failures.append(f"ROI ({metrics['Total_Return_Pct']:.2f}%) below target ({config['target_roi']}%)")
                
        # Check Max Drawdown
        if "max_drawdown" in config:
            # Note: Drawdown is usually negative, so we check absolute value or use <= if negative
            dd = abs(metrics["Max_Drawdown_Pct"])
            if dd > config["max_drawdown"]:
                goals_met = False
                failures.append(f"Drawdown ({dd:.2f}%) exceeds max ({config['max_drawdown']}%)")
                
        # Check Win Rate
        if "min_win_rate" in config:
            if metrics["Win_Rate_Pct"] < config["min_win_rate"]:
                goals_met = False
                failures.append(f"Win Rate ({metrics['Win_Rate_Pct']:.2f}%) below target ({config['min_win_rate']}%)")

        return goals_met, failures

    def generate_regime_data(self, df: pd.DataFrame, regime: str = "volatile"):
        """
        Creates synthetic 'OASIS' regime data to stress test strategies locally.
        """
        synth = df.copy()
        np.random.seed(42)
        
        if regime == "volatile":
            # Increase noise/volatility by 3x
            noise = np.random.normal(0, df['close'].std() * 0.05, len(df))
            synth['close'] = synth['close'] + noise
        elif regime == "crash":
            # Inject a 10% flash crash in the middle
            mid = len(df) // 2
            synth.iloc[mid:mid+10, synth.columns.get_loc('close')] *= 0.90
        elif regime == "trending":
            # Add a strong artificial trend
            trend = np.linspace(0, df['close'].mean() * 0.2, len(df))
            synth['close'] = synth['close'] + trend
            
        return synth

    def run_oasis_stress_test(self, df: pd.DataFrame, eval_func, params: dict):
        """
        Runs the strategy through multiple synthetic regimes to check robustness.
        Returns a 'Robustness Score' (0-100).
        """
        regimes = ["volatile", "crash", "trending"]
        pass_count = 0
        
        for r in regimes:
            synth_df = self.generate_regime_data(df, regime=r)
            try:
                entries, exits, short_entries, short_exits = eval_func(synth_df, params)
                metrics, _ = self.evaluate_signals(
                    df=synth_df, 
                    entries=entries, 
                    exits=exits, 
                    short_entries=short_entries, 
                    short_exits=short_exits
                )
                
                # If it doesn't blow up (ROI > -50%), we count it as a partial pass
                if metrics.get("Total_Return_Pct", -100) > -50:
                    pass_count += 1
            except:
                continue
                
        return (pass_count / len(regimes)) * 100
