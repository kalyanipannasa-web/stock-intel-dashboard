"""
Data fetcher module — pulls historical stock data from Yahoo Finance.
Used by the seed script (Phase 3) to populate the SQLite database.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


# Master list of companies for the dashboard
COMPANIES = [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Energy"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "sector": "IT"},
    {"symbol": "INFY.NS", "name": "Infosys", "sector": "IT"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Banking"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "Banking"},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Banking"},
    {"symbol": "WIPRO.NS", "name": "Wipro", "sector": "IT"},
    {"symbol": "ITC.NS", "name": "ITC", "sector": "FMCG"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever", "sector": "FMCG"},
    {"symbol": "LT.NS", "name": "Larsen & Toubro", "sector": "Engineering"},
]


def fetch_stock_data(
    symbol: str,
    period: str = "2y",
    interval: str = "1d"
) -> Optional[pd.DataFrame]:
    """
    Fetch historical OHLCV data for a single stock symbol.

    Args:
        symbol: Yahoo Finance ticker (e.g., 'INFY.NS')
        period: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max'
        interval: '1m', '5m', '15m', '1h', '1d', '1wk', '1mo'

    Returns:
        DataFrame with columns: Date, Open, High, Low, Close, Volume
        Returns None if fetch fails or returns empty data.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)

        if df.empty:
            print(f"⚠️  No data returned for {symbol}")
            return None

        # Reset index so Date becomes a column instead of the index
        df = df.reset_index()

        # Keep only the columns we need
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]

        # Add symbol column for later DB inserts
        df["Symbol"] = symbol

        # Convert Date column to date (drop time component)
        df["Date"] = pd.to_datetime(df["Date"]).dt.date

        print(f"✅ {symbol}: fetched {len(df)} rows ({df['Date'].min()} → {df['Date'].max()})")
        return df

    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None


def fetch_all_companies(period: str = "2y") -> dict[str, pd.DataFrame]:
    """
    Fetch data for all companies in the COMPANIES list.

    Returns:
        Dictionary mapping symbol → DataFrame.
        Symbols that failed to fetch are skipped.
    """
    results = {}
    print(f"\n📥 Fetching {len(COMPANIES)} companies for period={period}...\n")

    for company in COMPANIES:
        symbol = company["symbol"]
        df = fetch_stock_data(symbol, period=period)
        if df is not None:
            results[symbol] = df

    print(f"\n✅ Successfully fetched {len(results)}/{len(COMPANIES)} companies")
    return results


# Quick smoke test — runs only when this file is executed directly
if __name__ == "__main__":
    # Test 1: Fetch a single company
    print("=" * 60)
    print("TEST 1: Single company fetch (Infosys, 1 month)")
    print("=" * 60)
    df = fetch_stock_data("INFY.NS", period="1mo")
    if df is not None:
        print(f"\nFirst 5 rows:\n{df.head()}")
        print(f"\nColumn types:\n{df.dtypes}")

    # Test 2: Fetch all companies (last 1 month for speed)
    print("\n" + "=" * 60)
    print("TEST 2: All companies fetch (1 month)")
    print("=" * 60)
    all_data = fetch_all_companies(period="1mo")

    # Summary
    print("\n📊 Summary:")
    for symbol, df in all_data.items():
        latest_close = df["Close"].iloc[-1]
        print(f"  {symbol:18s} → latest close: ₹{latest_close:,.2f}")