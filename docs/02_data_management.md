# Data Management & OpenAlgo Integration

Hermes relies on high-quality market data for research, backtesting, and AI analysis. Rather than building a data fetcher from scratch, we integrate directly with **OpenAlgo** (MarketCalls) and its Historify database.

## 1. The OpenAlgo Connection Concept
OpenAlgo locally caches historical market data into a DuckDB file (usually named `historify.duckdb`). 
Hermes connects to this database in **read-only mode** to fetch OHLCV (Open, High, Low, Close, Volume) data. This prevents file locking issues and avoids data duplication.

## 2. Directory Structure Setup
For Hermes to see OpenAlgo's data via Docker, the repositories should be structured adjacently:
```
workspace/
├── hermes_research_platform/
│   ├── docker-compose.yml
│   └── data_pipeline/
│       └── openalgo_connector.py
└── openalgo/
    └── data/
        └── historify.duckdb
```

In the `docker-compose.yml`, the volume mapping is set up as follows:
```yaml
volumes:
  - ../openalgo:/openalgo
```
This tells Docker to mount the adjacent `openalgo` folder into the Hermes container at `/openalgo`.

## 3. Using the Connector
The `OpenAlgoDataConnector` (located in `data_pipeline/openalgo_connector.py`) handles the interaction.

The connector:
- Connects in **read-only mode** to prevent DuckDB locking.
- Uses **parameterized queries** to prevent SQL injection.
- Uses `try/finally` to **guarantee the connection is always closed**, even on errors.
- **Falls back gracefully** to an empty DataFrame if the DB file is not found.

### Constructor Parameters
| Parameter | Default | Description |
|---|---|---|
| `db_path` | `None` | Explicit path to the DuckDB file. Falls back to `OPENALGO_DUCKDB_PATH` env var, then `/openalgo/data/historify.duckdb`. |

### `get_historical_data()` Parameters
| Parameter | Type | Description |
|---|---|---|
| `symbol` | `str` | Ticker symbol e.g. `"RELIANCE"`, `"NIFTY"` |
| `exchange` | `str` | Exchange e.g. `"NSE"`, `"BSE"`, `"NFO"` |
| `interval` | `str` | Candle interval e.g. `"1d"`, `"15minute"`, `"1hour"` |
| `start_date` | `datetime` | Start of the data range |
| `end_date` | `datetime` | End of the data range |

### Example Usage (Python)
```python
from datetime import datetime, timedelta
from data_pipeline.openalgo_connector import OpenAlgoDataConnector

# Initialize the connector (defaults to the Docker path)
connector = OpenAlgoDataConnector()

# Define parameters
symbol = "RELIANCE"
exchange = "NSE"
interval = "15minute"
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Fetch the DataFrame
df = connector.get_historical_data(
    symbol=symbol, 
    exchange=exchange, 
    interval=interval, 
    start_date=start_date, 
    end_date=end_date
)

print(df.head())
# Returns: timestamp | open | high | low | close | volume
```

> [!NOTE]
> If running locally (not in Docker), set the `OPENALGO_DUCKDB_PATH` env variable in your `.env` file to the correct path on your machine.

## 4. Gathering and Storing Alternative Data
If you need data outside of OpenAlgo (e.g., FII/DII data, options chain data):
1. Write specific fetchers inside the `data_pipeline/` directory.
2. Save static or rarely updated datasets (like instrument tokens or historical FII/DII CSVs) into the `data/` directory of the Hermes project.

### Supported Interval Strings
The interval string must match what OpenAlgo's Historify uses. Common values:

| Interval | Description |
|---|---|
| `1minute` | 1-minute candles (Intraday) |
| `5minute` | 5-minute candles (Intraday) |
| `15minute` | 15-minute candles (Intraday) |
| `1hour` | Hourly candles |
| `1d` | Daily candles (Swing/Positional) |

## Next Steps
With data accessible, you can begin migrating and testing strategies. Proceed to [03_strategy_migration.md](./03_strategy_migration.md).
