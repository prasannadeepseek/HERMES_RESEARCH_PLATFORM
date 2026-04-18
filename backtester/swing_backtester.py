import pandas as pd
import numpy as np
import sys
import os

# Ensure the parent directory is in the path to import strategies
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hermes_strategies.trend_momentum import TrendMomentumStrategy
from hermes_strategies.mean_reversion import MeanReversionStrategy

class SimpleBacktester:
    """
    A simple event-driven backtester for strategy classes that evaluate on sliding windows.
    This simulates daily screening and tracks open positions.
    """
    def __init__(self, data: pd.DataFrame, strategy, initial_capital=100000):
        """
        data: pd.DataFrame with ['Open', 'High', 'Low', 'Close']
        strategy: An instance of a strategy class with an `analyze()` method
        """
        self.data = data
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = [] # Active trades
        self.trade_history = []
        self.lookback_window = 50 # Ensure we feed enough data to strategy
        
    def run(self):
        print(f"Starting backtest with {self.initial_capital} capital...")
        
        # Iterate over historical data day by day
        for i in range(self.lookback_window, len(self.data)):
            current_date = self.data.index[i]
            today_data = self.data.iloc[i]
            
            # 1. Manage existing positions (check if SL or Target hit today)
            for pos in self.positions[:]: # Iterate copy to allow removal
                # For simplicity, we assume we check against High/Low of the day
                if pos['direction'] == 'long':
                    if today_data['Low'] <= pos['sl']:
                        # Stopped out
                        self._close_position(pos, pos['sl'], current_date, "Stop Loss")
                    elif today_data['High'] >= pos['target']:
                        # Target hit
                        self._close_position(pos, pos['target'], current_date, "Target Hit")
                elif pos['direction'] == 'short':
                    if today_data['High'] >= pos['sl']:
                        self._close_position(pos, pos['sl'], current_date, "Stop Loss")
                    elif today_data['Low'] <= pos['target']:
                        self._close_position(pos, pos['target'], current_date, "Target Hit")
            
            # 2. Look for new signals
            # Feed the trailing window to the strategy
            window_data = self.data.iloc[i - self.lookback_window : i + 1]
            # Strategies expect a dict with 'close' prices
            feed_dict = {'close': window_data['Close'].values}
            
            signal = self.strategy.analyze(feed_dict)
            
            # If signal exists and we don't already have an open position
            if signal and len(self.positions) == 0:
                self._open_position(signal, current_date)
                
        # Close any remaining positions at the end
        for pos in self.positions[:]:
            last_price = self.data.iloc[-1]['Close']
            self._close_position(pos, last_price, self.data.index[-1], "End of Backtest")
            
        self.print_summary()

    def _open_position(self, signal, date):
        # Calculate position size (e.g., risk 5% of capital)
        # Simplified: Invest 10% of total capital per trade
        trade_size = self.capital * 0.10
        qty = trade_size / signal['entry']
        
        position = {
            'entry_date': date,
            'entry_price': signal['entry'],
            'sl': signal['sl'],
            'target': signal['target'],
            'direction': signal['direction'],
            'qty': qty,
            'invested': trade_size
        }
        self.positions.append(position)
        print(f"[{date.date()}] OPEN {signal['direction'].upper()} at {signal['entry']:.2f} | Target: {signal['target']:.2f} | SL: {signal['sl']:.2f}")

    def _close_position(self, pos, exit_price, date, reason):
        if pos['direction'] == 'long':
            pnl = (exit_price - pos['entry_price']) * pos['qty']
        else:
            pnl = (pos['entry_price'] - exit_price) * pos['qty']
            
        ret_pct = pnl / pos['invested'] * 100
        self.capital += pnl
        
        print(f"[{date.date()}] CLOSE {pos['direction'].upper()} at {exit_price:.2f} ({reason}) | PnL: {pnl:.2f} ({ret_pct:.2f}%)")
        
        self.trade_history.append({
            'entry_date': pos['entry_date'],
            'exit_date': date,
            'direction': pos['direction'],
            'entry_price': pos['entry_price'],
            'exit_price': exit_price,
            'pnl': pnl,
            'ret_pct': ret_pct,
            'reason': reason
        })
        self.positions.remove(pos)

    def print_summary(self):
        print("\n--- BACKTEST SUMMARY ---")
        print(f"Final Capital: {self.capital:.2f}")
        print(f"Total Return: {((self.capital - self.initial_capital) / self.initial_capital) * 100:.2f}%")
        
        if not self.trade_history:
            print("No trades executed.")
            return
            
        df = pd.DataFrame(self.trade_history)
        win_rate = (len(df[df['pnl'] > 0]) / len(df)) * 100
        print(f"Total Trades: {len(df)}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Average PnL per trade: {df['pnl'].mean():.2f}")
        print(f"Max Drawdown: N/A (Simplified backtester)")

if __name__ == "__main__":
    # Example usage using vectorbt to fetch data
    try:
        import vectorbt as vbt
        print("Fetching historical data for AAPL...")
        # Get 2 years of daily data
        data = vbt.YFData.download("AAPL", period="2y").get()
        
        print("\n=== Testing Trend Momentum Strategy ===")
        strat = TrendMomentumStrategy()
        bt = SimpleBacktester(data, strat)
        bt.run()
        
        print("\n=== Testing Mean Reversion Strategy ===")
        strat2 = MeanReversionStrategy()
        bt2 = SimpleBacktester(data, strat2)
        bt2.run()
        
    except ImportError:
        print("Please install vectorbt to fetch data: pip install vectorbt")
