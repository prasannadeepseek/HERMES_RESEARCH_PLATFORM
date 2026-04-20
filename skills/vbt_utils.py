import vectorbt as vbt
import pandas as pd

def get_ma(close, window):
    """Safe wrapper for Moving Average using Pandas"""
    return close.rolling(window=window).mean()

def get_rsi(close, window):
    """Safe wrapper for RSI using Pandas (Wilder's Smoothing)"""
    delta = close.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    
    # Wilder's Smoothing: alpha = 1/window
    avg_gain = gain.ewm(alpha=1/window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/window, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def get_bbands(close, window, std):
    """Safe wrapper for Bollinger Bands using Pandas (bypasses vbt bug)"""
    ma = close.rolling(window=window).mean()
    sd = close.rolling(window=window).std()
    upper = ma + (sd * std)
    lower = ma - (sd * std)
    # Return an object that mimics vbt.BBANDS structure
    class BB: pass
    b = BB()
    b.upper = upper
    b.lower = lower
    b.ma = ma
    b.middle = ma # Vectorbt uses 'middle' for the moving average
    return b

def get_macd(close, fast, slow, signal):
    """Safe wrapper for MACD using Pandas (bypasses vbt bug)"""
    exp1 = close.ewm(span=fast, adjust=False).mean()
    exp2 = close.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    # Return an object that mimics vbt.MACD structure
    class M: pass
    m = M()
    m.macd = macd_line
    m.signal = signal_line
    return m

def get_atr(high, low, close, window):
    """Safe wrapper for ATR using Pandas"""
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def get_adx(high, low, close, window):
    """Safe wrapper for ADX using Pandas"""
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    minus_dm = minus_dm.abs()
    
    tr = get_atr(high, low, close, window) # Use ATR for normalization
    plus_di = 100 * (plus_dm.rolling(window=window).mean() / tr)
    minus_di = 100 * (minus_dm.rolling(window=window).mean() / tr)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.rolling(window=window).mean()

def run_indicator(name, close, **params):
    """
    Generic entry point for all indicators.
    Tries to use a safe Pandas override if available, otherwise falls back to vectorbt.
    """
    safe_map = {
        "MA": get_ma,
        "RSI": get_rsi,
        "BBANDS": get_bbands,
        "MACD": get_macd,
        "ATR": get_atr,
        "ADX": get_adx
    }
    
    name_upper = name.upper()
    if name_upper in safe_map:
        # ATR and ADX need High/Low/Close
        if name_upper in ["ATR", "ADX"]:
            # Try to get high/low from params or assume they are in the parent scope/df
            # For simplicity in this wrapper, we assume params contains them if needed
            return safe_map[name_upper](**params)
        return safe_map[name_upper](close, **params)
    
    # Fallback to direct vectorbt with keyword safety
    try:
        # Map some common names if they differ from VBT classes
        name_map = {"SMA": "MA", "EMA": "MA"}
        vbt_name = name_map.get(name_upper, name_upper)
        
        indicator_cls = getattr(vbt, vbt_name)
        return indicator_cls.run(close=close, **params)
    except Exception as e:
        # If it fails, return a helpful error for the LLM to fix
        raise RuntimeError(f"Indicator '{name}' failed in environment: {str(e)}")
