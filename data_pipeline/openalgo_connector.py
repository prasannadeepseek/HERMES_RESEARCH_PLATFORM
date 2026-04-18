"""
OpenAlgo REST API Client for Hermes Research Platform
======================================================
Communicates with the OpenAlgo broker gateway via its documented REST API.

NO direct file system access. NO DuckDB mounts.
Hermes and OpenAlgo are independent services on the same Docker network (hermes_net).
The OpenAlgo container is reachable at http://openalgo:5000 inside Docker,
or http://127.0.0.1:5000 when running locally.

Supported brokers (configured in this deployment): Zerodha, Upstox
"""
import os
import requests
import pandas as pd
from datetime import datetime
from typing import Optional


class OpenAlgoClient:
    """
    REST API client for the OpenAlgo broker gateway (marketcalls/openalgo).

    Reads OPENALGO_HOST and OPENALGO_API_KEY from environment variables.
    All broker operations (historical data, order placement, positions, quotes)
    go through OpenAlgo's documented HTTP API — no file mounts or DuckDB needed.

    Typical Docker usage:
        OPENALGO_HOST=http://openalgo:5000   (set automatically by docker-compose)
        OPENALGO_API_KEY=<key from OpenAlgo UI>

    Local dev usage:
        OPENALGO_HOST=http://127.0.0.1:5000
    """

    def __init__(self, host: Optional[str] = None, api_key: Optional[str] = None):
        self.host = (host or os.getenv("OPENALGO_HOST", "http://127.0.0.1:5000")).rstrip("/")
        self.api_key = api_key or os.getenv("OPENALGO_API_KEY", "")
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
        })

    def _post(self, endpoint: str, payload: dict) -> dict:
        """Internal helper for POST requests to the OpenAlgo API."""
        payload["apikey"] = self.api_key
        url = f"{self.host}{endpoint}"
        try:
            resp = self._session.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot reach OpenAlgo at {self.host}. "
                "Ensure OpenAlgo is running and OPENALGO_HOST is set correctly."
            )
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"OpenAlgo API error [{resp.status_code}]: {resp.text}") from e

    def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Internal helper for GET requests to the OpenAlgo API."""
        url = f"{self.host}{endpoint}"
        _params = {"apikey": self.api_key}
        if params:
            _params.update(params)
        try:
            resp = self._session.get(url, params=_params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot reach OpenAlgo at {self.host}. "
                "Ensure OpenAlgo is running and OPENALGO_HOST is set correctly."
            )
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"OpenAlgo API error [{resp.status_code}]: {resp.text}") from e

    # -------------------------------------------------------------------------
    # Health / Connectivity
    # -------------------------------------------------------------------------

    def ping(self) -> bool:
        """
        Check if OpenAlgo is reachable and the API key is valid.
        Returns True on success, False on any failure.
        """
        try:
            result = self._post("/api/v1/funds", {})
            return result.get("status") == "success"
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Historical Data
    # -------------------------------------------------------------------------

    def get_historical_data(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from OpenAlgo's Historify API.

        Args:
            symbol:     Ticker e.g. "RELIANCE", "NIFTY50"
            exchange:   Exchange e.g. "NSE", "BSE", "NFO", "MCX"
            interval:   Candle interval — "1minute", "5minute", "15minute",
                        "30minute", "1hour", "1d"
            start_date: Start of the data range
            end_date:   End of the data range

        Returns:
            pd.DataFrame with columns: [timestamp, open, high, low, close, volume]
            Returns an empty DataFrame on error.

        Supported brokers in this deployment: Zerodha, Upstox
        """
        payload = {
            "symbol": symbol,
            "exchange": exchange,
            "interval": interval,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }
        try:
            result = self._post("/api/v1/history", payload)
            if result.get("status") != "success" or not result.get("data"):
                print(f"[OpenAlgoClient] No data returned for {symbol}: {result.get('message', 'unknown')}")
                return pd.DataFrame()

            df = pd.DataFrame(result["data"])
            # Normalise column names across broker differences
            df.columns = [c.lower() for c in df.columns]
            if "datetime" in df.columns:
                df.rename(columns={"datetime": "timestamp"}, inplace=True)
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df.set_index("timestamp", inplace=True)
            return df

        except Exception as e:
            print(f"[OpenAlgoClient] Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()

    # -------------------------------------------------------------------------
    # Live Quotes
    # -------------------------------------------------------------------------

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get live LTP and market depth for a symbol.

        Returns dict with keys: ltp, open, high, low, close, volume, etc.
        Returns empty dict on error.
        """
        try:
            result = self._post("/api/v1/quotes", {"symbol": symbol, "exchange": exchange})
            if result.get("status") == "success":
                return result.get("data", {})
            return {}
        except Exception as e:
            print(f"[OpenAlgoClient] Error fetching quotes for {symbol}: {e}")
            return {}

    # -------------------------------------------------------------------------
    # Order Management
    # -------------------------------------------------------------------------

    def place_order(
        self,
        symbol: str,
        exchange: str,
        action: str,          # "BUY" or "SELL"
        quantity: int,
        product: str = "MIS", # "MIS" (intraday) or "CNC" (delivery) or "NRML" (F&O)
        price_type: str = "MARKET",
        price: float = 0,
        trigger_price: float = 0,
        disclosed_quantity: int = 0,
        strategy: str = "Hermes",
    ) -> dict:
        """
        Place an order via OpenAlgo.

        Supported on: Zerodha, Upstox (and all other configured brokers).

        Args:
            symbol:             Trading symbol e.g. "RELIANCE"
            exchange:           Exchange e.g. "NSE", "BSE", "NFO"
            action:             "BUY" or "SELL"
            quantity:           Number of shares / lots
            product:            "MIS" for intraday, "CNC" for delivery, "NRML" for F&O
            price_type:         "MARKET", "LIMIT", "SL", "SL-M"
            price:              Limit price (0 for market orders)
            trigger_price:      Stop loss trigger price
            disclosed_quantity: Disclosed quantity (0 for standard orders)
            strategy:           Strategy tag shown in OpenAlgo's order log

        Returns:
            dict with keys: status, orderid, message
        """
        payload = {
            "symbol": symbol,
            "exchange": exchange,
            "action": action.upper(),
            "quantity": str(quantity),
            "product": product,
            "pricetype": price_type,
            "price": str(price),
            "trigger_price": str(trigger_price),
            "disclosed_quantity": str(disclosed_quantity),
            "strategy": strategy,
        }
        try:
            result = self._post("/api/v1/placeorder", payload)
            return result
        except Exception as e:
            print(f"[OpenAlgoClient] Error placing order for {symbol}: {e}")
            return {"status": "error", "message": str(e)}

    def place_smart_order(
        self,
        symbol: str,
        exchange: str,
        action: str,
        quantity: int,
        position_size: int,
        product: str = "MIS",
        price_type: str = "MARKET",
        price: float = 0,
        strategy: str = "Hermes",
    ) -> dict:
        """
        Place a smart order that automatically handles position sizing.
        OpenAlgo checks current position and only orders the difference.
        This prevents double-buying if the strategy fires multiple times.
        """
        payload = {
            "symbol": symbol,
            "exchange": exchange,
            "action": action.upper(),
            "quantity": str(quantity),
            "position_size": str(position_size),
            "product": product,
            "pricetype": price_type,
            "price": str(price),
            "trigger_price": "0",
            "disclosed_quantity": "0",
            "strategy": strategy,
        }
        try:
            result = self._post("/api/v1/placesmartorder", payload)
            return result
        except Exception as e:
            print(f"[OpenAlgoClient] Error placing smart order for {symbol}: {e}")
            return {"status": "error", "message": str(e)}

    def cancel_order(self, order_id: str, strategy: str = "Hermes") -> dict:
        """Cancel a pending order by its OpenAlgo order ID."""
        try:
            return self._post("/api/v1/cancelorder", {"orderid": order_id, "strategy": strategy})
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def close_all_positions(self, strategy: str = "Hermes") -> dict:
        """Close all open positions for the given strategy tag."""
        try:
            return self._post("/api/v1/closeposition", {"strategy": strategy})
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # -------------------------------------------------------------------------
    # Portfolio / Account
    # -------------------------------------------------------------------------

    def get_positions(self) -> list:
        """
        Get current open positions.
        Returns list of position dicts, or empty list on error.
        """
        try:
            result = self._post("/api/v1/positionbook", {})
            if result.get("status") == "success":
                return result.get("data", [])
            return []
        except Exception as e:
            print(f"[OpenAlgoClient] Error fetching positions: {e}")
            return []

    def get_orderbook(self) -> list:
        """
        Get today's order history.
        Returns list of order dicts, or empty list on error.
        """
        try:
            result = self._post("/api/v1/orderbook", {})
            if result.get("status") == "success":
                return result.get("data", [])
            return []
        except Exception as e:
            print(f"[OpenAlgoClient] Error fetching orderbook: {e}")
            return []

    def get_funds(self) -> dict:
        """
        Get available funds / margin from broker.
        Returns dict with balance info, or empty dict on error.
        """
        try:
            result = self._post("/api/v1/funds", {})
            if result.get("status") == "success":
                return result.get("data", {})
            return {}
        except Exception as e:
            print(f"[OpenAlgoClient] Error fetching funds: {e}")
            return {}


# ---------------------------------------------------------------------------
# Backwards-compatibility alias
# Old code that imported OpenAlgoDataConnector will still work.
# It will use the REST API instead of DuckDB — no file mounts needed.
# ---------------------------------------------------------------------------
class OpenAlgoDataConnector(OpenAlgoClient):
    """
    Backwards-compatibility shim.
    Alias of OpenAlgoClient for code that imported OpenAlgoDataConnector.
    All data now comes from the REST API, not the DuckDB file mount.
    """
    pass
