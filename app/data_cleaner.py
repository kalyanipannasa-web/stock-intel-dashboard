"""
Data cleaning & feature engineering module.
Takes raw OHLCV data and adds calculated metrics:
- daily_return: percent change from open to close
- ma_7: 7-day moving average of close
- high_52w / low_52w: rolling 52-week high and low
- volatility_30d: custom metric — annualized rolling standard deviation
"""

import pandas as pd
import numpy as np
from typing import Optional


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw stock data:
    - Drop rows with missing OHLC values
    - Remove duplicate dates (keep last)
    - Ensure dates are sorted ascending
    - Verify no negative prices
    """
    initial_rows = len(df)

    # Drop rows where any of the critical price columns are NaN
    df = df.dropna(subset=["Open", "High", "Low", "Close"])

    # Remove duplicate dates (data quality safety net)
    df = df.drop_duplicates(subset=["Date"], keep="last")

    # Sort by date ascending — required for rolling calculations
    df = df.sort_values("Date").reset_index(drop=True)

    # Sanity check: drop any rows with non-positive prices (data error)
    df = df[(df["Close"] > 0) & (df["Open"] > 0)]

    dropped = initial_rows - len(df)
    if dropped > 0:
        print(f"  🧹 Cleaned: dropped {dropped} bad rows")

    return df


def add_daily_return(df: pd.DataFrame) -> pd.DataFrame:
    """
    Daily Return = (Close - Open) / Open
    Expressed as a percentage.
    """
    df["daily_return"] = ((df["Close"] - df["Open"]) / df["Open"]) * 100
    return df


def add_moving_average(df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    """
    N-day moving average of Close price.
    First (N-1) rows will be NaN — that's expected.
    """
    df[f"ma_{window}"] = df["Close"].rolling(window=window, min_periods=window).mean()
    return df


def add_52week_high_low(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rolling 52-week (252 trading days) high and low of Close price.
    For early rows where < 252 days exist, uses available data (min_periods=1).
    """
    df["high_52w"] = df["Close"].rolling(window=252, min_periods=1).max()
    df["low_52w"] = df["Close"].rolling(window=252, min_periods=1).min()
    return df


def add_volatility(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """
    CUSTOM METRIC — Volatility Score (annualized).

    Calculation:
    1. Take the 30-day rolling standard deviation of daily returns
    2. Annualize it by multiplying by sqrt(252) — standard finance convention
       (252 trading days per year)

    Interpretation:
    - Volatility 15% = stock typically moves ±15% over a year (low risk)
    - Volatility 40% = stock typically moves ±40% over a year (high risk)

    Used in real finance for risk assessment (Sharpe ratio, Bollinger Bands, VaR).
    """
    if "daily_return" not in df.columns:
        raise ValueError("daily_return must be calculated before volatility")

    rolling_std = df["daily_return"].rolling(window=window, min_periods=window).std()
    df[f"volatility_{window}d"] = rolling_std * np.sqrt(252)
    return df


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the full cleaning + feature engineering pipeline on one company's data.
    """
    df = clean_dataframe(df)
    df = add_daily_return(df)
    df = add_moving_average(df, window=7)
    df = add_52week_high_low(df)
    df = add_volatility(df, window=30)
    return df


def enrich_all(data_dict: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    Apply enrich() to every company in a dictionary of DataFrames.
    """
    results = {}
    print(f"\n🔧 Enriching {len(data_dict)} companies with calculated metrics...\n")
    for symbol, df in data_dict.items():
        enriched = enrich(df)
        results[symbol] = enriched
        latest = enriched.iloc[-1]
        print(
            f"  ✅ {symbol:18s} → {len(enriched)} rows | "
            f"latest return: {latest['daily_return']:+.2f}% | "
            f"vol: {latest.get('volatility_30d', 0):.1f}%"
        )
    return results


# Smoke test
if __name__ == "__main__":
    from data_fetcher import fetch_stock_data, fetch_all_companies

    print("=" * 60)
    print("TEST 1: Enrich single company (Infosys, 1 year)")
    print("=" * 60)
    df = fetch_stock_data("INFY.NS", period="1y")
    enriched = enrich(df)
    print(f"\nLast 5 rows of enriched data:\n")
    print(enriched.tail()[
        ["Date", "Close", "daily_return", "ma_7", "high_52w", "low_52w", "volatility_30d"]
    ].to_string(index=False))

    print("\n" + "=" * 60)
    print("TEST 2: Enrich all companies (1 year)")
    print("=" * 60)
    raw = fetch_all_companies(period="1y")
    enriched_all = enrich_all(raw)

    print("\n📊 Volatility ranking (most → least risky in last 30 days):")
    rankings = []
    for symbol, df in enriched_all.items():
        vol = df["volatility_30d"].iloc[-1]
        rankings.append((symbol, vol))
    rankings.sort(key=lambda x: x[1], reverse=True)
    for symbol, vol in rankings:
        print(f"  {symbol:18s} → annualized volatility: {vol:.1f}%")