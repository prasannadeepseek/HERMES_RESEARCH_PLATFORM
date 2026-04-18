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
                         freq: str = "1m"):
        """
        Takes raw entry/exit boolean signals and processes them through vectorbt.
        Returns a dictionary of core performance metrics.
        """
        # Ensure we are using the close price for signal execution
        price = df['close']

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

        # Extract Metrics
        metrics = {
            "Total_Return_Pct": portfolio.total_return() * 100,
            "Max_Drawdown_Pct": portfolio.max_drawdown() * 100,
            "Win_Rate_Pct": portfolio.trades.win_rate() * 100,
            "Sharpe_Ratio": portfolio.sharpe_ratio(),
            "Total_Trades": len(portfolio.trades),
            "Profit_Factor": portfolio.trades.profit_factor()
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
