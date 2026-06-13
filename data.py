"""
Data Fetching Module - 100% Free via yfinance
Supports stocks, ETFs, indices, crypto, forex
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional


def fetch_ohlcv(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch OHLCV data using yfinance (FREE, no API key needed).

    Parameters
    ----------
    symbol   : Ticker symbol e.g. "AAPL", "^GSPC", "BTC-USD", "EURUSD=X"
    period   : Data period  – "1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"
    interval : Bar interval – "1m","2m","5m","15m","30m","60m","90m","1h",
                               "1d","5d","1wk","1mo","3mo"
    start    : Start date string "YYYY-MM-DD" (overrides period)
    end      : End date string  "YYYY-MM-DD"

    Returns
    -------
    DataFrame with columns: Open, High, Low, Close, Volume
    """
    ticker = yf.Ticker(symbol)

    if start:
        df = ticker.history(start=start, end=end, interval=interval)
    else:
        df = ticker.history(period=period, interval=interval)

    if df.empty:
        raise ValueError(f"No data returned for symbol '{symbol}'. Check the ticker.")

    df.index = pd.to_datetime(df.index)
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.dropna(subset=["Close"], inplace=True)
    df.sort_index(inplace=True)
    return df


def get_symbol_info(symbol: str) -> dict:
    """Return basic info about a ticker (name, currency, exchange)."""
    try:
        info = yf.Ticker(symbol).info
        return {
            "name":     info.get("longName", symbol),
            "currency": info.get("currency", ""),
            "exchange": info.get("exchange", ""),
            "sector":   info.get("sector", ""),
        }
    except Exception:
        return {"name": symbol, "currency": "", "exchange": "", "sector": ""}


# ─── Quick presets for common markets ────────────────────────────────────────
POPULAR_SYMBOLS = {
    # US Indices
    "SP500":   "^GSPC",
    "DOW":     "^DJI",
    "NASDAQ":  "^IXIC",
    "VIX":     "^VIX",
    # Stocks
    "APPLE":   "AAPL",
    "TESLA":   "TSLA",
    "GOOGLE":  "GOOGL",
    # Crypto
    "BITCOIN": "BTC-USD",
    "ETH":     "ETH-USD",
    # Forex
    "EURUSD":  "EURUSD=X",
    "GBPUSD":  "GBPUSD=X",
    # Commodities
    "GOLD":    "GC=F",
    "OIL":     "CL=F",
}
