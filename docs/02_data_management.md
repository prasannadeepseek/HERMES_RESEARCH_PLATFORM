# Data Management & OpenAlgo Integration

Hermes fetches all market data by calling the **OpenAlgo REST API**. OpenAlgo is the broker gateway that handles authentication, rate limiting, and data caching. Hermes never accesses OpenAlgo's internal files or databases directly — all communication is over HTTP.

## 1. Architecture

```
┌─────────────────────┐         hermes_net (Docker)        ┌──────────────────────┐
│   Hermes UI         │  ─── POST /api/v1/history ──────▶  │  OpenAlgo            │
│   (port 8501)       │  ◀── OHLCV DataFrame ────────────  │  (port 5000)         │
│                     │                                     │                      │
│   OpenAlgoClient    │  ─── POST /api/v1/placeorder ───▶  │  Zerodha / Upstox    │
│   (REST client)     │  ◀── order_id, status ───────────  │  Broker API          │
└─────────────────────┘                                     └──────────────────────┘
```

**Key principle**: Hermes and OpenAlgo are completely independent. OpenAlgo can be updated with `make update-openalgo` without any changes to Hermes.

---

## 2. The OpenAlgoClient

**File:** `data_pipeline/openalgo_connector.py`

The `OpenAlgoClient` class handles all interactions with OpenAlgo's HTTP API. It reads connection settings from environment variables:

| Env Variable | Docker Default | Local Dev |
|---|---|---|
| `OPENALGO_HOST` | `http://openalgo:5000` (set by compose) | `http://127.0.0.1:5000` |
| `OPENALGO_API_KEY` | Set in `hermes_research_platform/.env` | Same |

### Available Methods

| Method | Endpoint | Description |
|---|---|---|
| `ping()` | `POST /api/v1/funds` | Check connectivity + API key validity |
| `get_historical_data()` | `POST /api/v1/history` | OHLCV historical data for backtesting |
| `get_quotes()` | `POST /api/v1/quotes` | Live LTP and market depth |
| `place_order()` | `POST /api/v1/placeorder` | Place a market/limit order |
| `place_smart_order()` | `POST /api/v1/placesmartorder` | Order with automatic position sizing |
| `cancel_order()` | `POST /api/v1/cancelorder` | Cancel a pending order |
| `close_all_positions()` | `POST /api/v1/closeposition` | Close all open positions |
| `get_positions()` | `POST /api/v1/positionbook` | Current open positions |
| `get_orderbook()` | `POST /api/v1/orderbook` | Today's order history |
| `get_funds()` | `POST /api/v1/funds` | Available margin / balance |

---

## 3. Fetching Historical Data

### `get_historical_data()` Parameters

| Parameter | Type | Description |
|---|---|---|
| `symbol` | `str` | Ticker e.g. `"RELIANCE"`, `"NIFTY50"` |
| `exchange` | `str` | Exchange e.g. `"NSE"`, `"BSE"`, `"NFO"`, `"MCX"` |
| `interval` | `str` | Candle interval — see table below |
| `start_date` | `datetime` | Start of the data range |
| `end_date` | `datetime` | End of the data range |

### Supported Intervals

| Interval | Description |
|---|---|
| `1minute` | 1-minute candles (Intraday) |
| `5minute` | 5-minute candles (Intraday) |
| `15minute` | 15-minute candles (Intraday) |
| `30minute` | 30-minute candles (Intraday) |
| `1hour` | Hourly candles |
| `1d` | Daily candles (Swing/Positional) |

### Example Usage

```python
from datetime import datetime, timedelta
from data_pipeline.openalgo_connector import OpenAlgoClient

client = OpenAlgoClient()  # Reads OPENALGO_HOST + OPENALGO_API_KEY from env

# Fetch 30 days of daily data for Reliance
df = client.get_historical_data(
    symbol="RELIANCE",
    exchange="NSE",
    interval="1d",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
)

print(df.head())
# Returns: timestamp (index) | open | high | low | close | volume
```

### Connection Test

```python
client = OpenAlgoClient()
if client.ping():
    print("✅ Connected to OpenAlgo")
else:
    print("❌ Cannot reach OpenAlgo — is it running? Check: make status")
```

---

## 4. Placing Orders

```python
from data_pipeline.openalgo_connector import OpenAlgoClient

client = OpenAlgoClient()

# Market buy — Zerodha/Upstox intraday
result = client.place_order(
    symbol="RELIANCE",
    exchange="NSE",
    action="BUY",
    quantity=10,
    product="MIS",       # MIS=intraday, CNC=delivery, NRML=F&O
    price_type="MARKET",
    strategy="MyHermesStrategy",
)
print(result)
# {"status": "success", "orderid": "240412000123456"}
```

### Smart Order (Recommended for Strategies)

Smart orders check your current position before placing. If you're already long 10 shares and the strategy fires again, it won't buy another 10.

```python
result = client.place_smart_order(
    symbol="RELIANCE",
    exchange="NSE",
    action="BUY",
    quantity=10,
    position_size=10,  # Desired position — OpenAlgo handles the diff
    product="MIS",
    strategy="MyHermesStrategy",
)
```

---

## 5. Alternative Data Sources

If you need data outside OpenAlgo (FII/DII, options chain, etc.):
1. Write a specific fetcher inside `data_pipeline/`.
2. Save static datasets (instrument tokens, historical CSVs) into the `data/` directory.

The Hermes UI also supports:
- **TrueData CSV** — upload your own CSV files
- **Yahoo Finance (Sandbox)** — free OHLCV data for testing (not recommended for production)

---

## Next Steps

With data accessible, proceed to [03_strategy_migration.md](./03_strategy_migration.md) to start adding your trading strategies.
