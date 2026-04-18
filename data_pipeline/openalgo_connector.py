import os
import duckdb
import pandas as pd
from datetime import datetime

class OpenAlgoDataConnector:
    """
    Connects directly to OpenAlgo's Historify DuckDB instance to retrieve historical market data
    without duplicating the database.
    """
    def __init__(self, db_path=None):
        # OpenAlgo typically stores its historical db locally if Historify is used
        # We try to locate it relative to the openalgo volume mapping in Docker
        self.db_path = db_path or os.getenv("OPENALGO_DUCKDB_PATH", "/openalgo/data/historify.duckdb")
        
    def _connect(self):
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"OpenAlgo DuckDB not found at {self.db_path}")
        # Connect in read-only mode to prevent locking issues with the live OpenAlgo instance
        return duckdb.connect(self.db_path, read_only=True)

    def get_historical_data(self, symbol: str, exchange: str, interval: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Retrieves historical data directly from OpenAlgo's local DuckDB.
        """
        conn = None
        try:
            conn = self._connect()
            # This is a generic query. The actual schema depends on OpenAlgo's Historify setup.
            # Assuming a generic OHLCV table for now.
            query = """
                SELECT timestamp, open, high, low, close, volume 
                FROM market_data 
                WHERE symbol = ? 
                  AND exchange = ?
                  AND interval = ?
                  AND timestamp >= ?
                  AND timestamp <= ?
                ORDER BY timestamp ASC
            """
            df = conn.execute(query, [symbol, exchange, interval, start_date.isoformat(), end_date.isoformat()]).df()
            return df
        except Exception as e:
            print(f"Error fetching from OpenAlgo DB: {e}")
            # Fallback could be hitting the OpenAlgo REST API
            return pd.DataFrame()
        finally:
            if conn is not None:
                conn.close()
