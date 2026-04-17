"""
Service layer — pure database query functions.
Endpoints in main.py call these; this keeps endpoints thin and queries reusable/testable.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.models import Company, StockData
from typing import Optional
import numpy as np


def get_all_companies(db: Session) -> list[Company]:
    """Return all companies, ordered by symbol."""
    return db.query(Company).order_by(Company.symbol).all()


def get_company_by_symbol(db: Session, symbol: str) -> Optional[Company]:
    """Return one company or None if not found."""
    return db.query(Company).filter(Company.symbol == symbol).first()


def get_recent_stock_data(db: Session, symbol: str, days: int = 30) -> list[StockData]:
    """Return last N days of stock data for a symbol, oldest → newest."""
    rows = (
        db.query(StockData)
        .filter(StockData.symbol == symbol)
        .order_by(desc(StockData.date))
        .limit(days)
        .all()
    )
    # Reverse so caller gets oldest → newest (better for charting)
    return list(reversed(rows))


def get_summary_stats(db: Session, symbol: str) -> Optional[dict]:
    """
    Return summary statistics for a symbol:
    - latest close + date
    - 52-week high, low, avg close
    - current volatility
    - % distance from 52-week high
    """
    company = get_company_by_symbol(db, symbol)
    if not company:
        return None

    # Latest row
    latest = (
        db.query(StockData)
        .filter(StockData.symbol == symbol)
        .order_by(desc(StockData.date))
        .first()
    )
    if not latest:
        return None

    # Aggregate over last 252 trading days (52 weeks)
    last_252 = (
        db.query(StockData)
        .filter(StockData.symbol == symbol)
        .order_by(desc(StockData.date))
        .limit(252)
        .all()
    )
    closes = [r.close for r in last_252]

    high_52w = max(closes)
    low_52w = min(closes)
    avg_52w = sum(closes) / len(closes)
    distance_from_high = ((high_52w - latest.close) / high_52w) * 100

    return {
        "symbol": company.symbol,
        "name": company.name,
        "sector": company.sector,
        "latest_close": latest.close,
        "latest_date": latest.date,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "avg_close_52w": round(avg_52w, 2),
        "current_volatility_30d": latest.volatility_30d,
        "distance_from_52w_high_pct": round(distance_from_high, 2),
    }


def compare_stocks(db: Session, symbol1: str, symbol2: str, days: int = 90) -> Optional[dict]:
    """
    Compare two stocks over the last N days.
    Returns correlation, % returns, volatilities, and identifies winner.
    """
    company1 = get_company_by_symbol(db, symbol1)
    company2 = get_company_by_symbol(db, symbol2)
    if not company1 or not company2:
        return None

    data1 = get_recent_stock_data(db, symbol1, days=days)
    data2 = get_recent_stock_data(db, symbol2, days=days)

    if not data1 or not data2:
        return None

    # Align lengths — use the shorter one (in case of missing data)
    min_len = min(len(data1), len(data2))
    data1 = data1[-min_len:]
    data2 = data2[-min_len:]

    closes1 = np.array([r.close for r in data1])
    closes2 = np.array([r.close for r in data2])
    returns1 = np.array([r.daily_return for r in data1 if r.daily_return is not None])
    returns2 = np.array([r.daily_return for r in data2 if r.daily_return is not None])

    # Period returns: (last - first) / first * 100
    return_1_pct = ((closes1[-1] - closes1[0]) / closes1[0]) * 100
    return_2_pct = ((closes2[-1] - closes2[0]) / closes2[0]) * 100

    # Pearson correlation of daily returns
    correlation = float(np.corrcoef(returns1[-min(len(returns1), len(returns2)):],
                                    returns2[-min(len(returns1), len(returns2)):])[0, 1])

    return {
        "symbol1": symbol1,
        "symbol2": symbol2,
        "period_days": min_len,
        "correlation": round(correlation, 4),
        "return_1_pct": round(return_1_pct, 2),
        "return_2_pct": round(return_2_pct, 2),
        "volatility_1_pct": data1[-1].volatility_30d,
        "volatility_2_pct": data2[-1].volatility_30d,
        "winner": symbol1 if return_1_pct > return_2_pct else symbol2,
    }