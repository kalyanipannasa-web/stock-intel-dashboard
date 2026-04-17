"""
Pydantic schemas — define the shape of API request/response data.
FastAPI uses these to auto-validate, serialize, and generate Swagger docs.
"""

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class CompanyResponse(BaseModel):
    """Company info for the /companies endpoint."""
    symbol: str = Field(..., example="INFY.NS")
    name: str = Field(..., example="Infosys")
    sector: str = Field(..., example="IT")

    class Config:
        from_attributes = True  # allows building from SQLAlchemy ORM objects


class StockDataPoint(BaseModel):
    """One day of stock data for the /data/{symbol} endpoint."""
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    daily_return: Optional[float] = None
    ma_7: Optional[float] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    volatility_30d: Optional[float] = None

    class Config:
        from_attributes = True


class StockDataResponse(BaseModel):
    """Wrapper for /data/{symbol} — includes metadata + the data array."""
    symbol: str
    name: str
    sector: str
    data_points: int
    data: list[StockDataPoint]


class SummaryResponse(BaseModel):
    """Response for /summary/{symbol} — key statistics."""
    symbol: str
    name: str
    sector: str
    latest_close: float
    latest_date: date
    high_52w: float
    low_52w: float
    avg_close_52w: float
    current_volatility_30d: Optional[float]
    distance_from_52w_high_pct: float = Field(
        ..., description="% below 52-week high; negative = at/above high"
    )


class ComparisonResponse(BaseModel):
    """Response for /compare — two stocks side by side."""
    symbol1: str
    symbol2: str
    period_days: int
    correlation: float = Field(..., description="Pearson correlation of daily returns; -1 to +1")
    return_1_pct: float = Field(..., description=f"% return of symbol1 over period")
    return_2_pct: float = Field(..., description=f"% return of symbol2 over period")
    volatility_1_pct: Optional[float]
    volatility_2_pct: Optional[float]
    winner: str = Field(..., description="Symbol with higher % return")

    # ──────────────────────────────────────────────────────────────
# Phase 8 — ML PREDICTION schemas
# ──────────────────────────────────────────────────────────────

class HistoryPoint(BaseModel):
    date: str
    close: float


class PredictionPoint(BaseModel):
    date: str
    predicted_close: float


class PredictionResponse(BaseModel):
    symbol: str
    lookback_days: int
    predict_days: int
    model: str
    r_squared: float = Field(..., description="Coefficient of determination, 0 to 1")
    trend: str = Field(..., description="'up', 'down', or 'flat'")
    history: list[HistoryPoint]
    predictions: list[PredictionPoint]
    disclaimer: str