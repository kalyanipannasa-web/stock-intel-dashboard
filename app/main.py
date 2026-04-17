"""
Stock Data Intelligence Dashboard — FastAPI backend.
JarNox Internship Assignment.
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db, engine
from app.models import Base
from app import services, schemas

# Auto-create tables on startup (safe — no-op if they exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Stock Data Intelligence Dashboard",
    description=(
        "A mini financial data platform built for the JarNox internship assignment.\n\n"
        "**Features:**\n"
        "- Real OHLCV data from Yahoo Finance for 10 large-cap Indian stocks\n"
        "- Calculated metrics: daily return, 7-day MA, 52-week high/low\n"
        "- Custom metric: 30-day annualized volatility (rolling std of returns × √252)\n"
        "- Two-stock comparison with Pearson correlation"
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────
# Root / Health endpoints
# ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Stock Intel Dashboard API",
        "docs": "/docs",
        "endpoints": ["/companies", "/data/{symbol}", "/summary/{symbol}", "/compare"],
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}


# ─────────────────────────────────────────────────────────────
# Companies
# ─────────────────────────────────────────────────────────────

@app.get("/companies", response_model=list[schemas.CompanyResponse], tags=["Companies"])
def list_companies(db: Session = Depends(get_db)):
    """Return the list of all 10 available companies."""
    return services.get_all_companies(db)


# ─────────────────────────────────────────────────────────────
# Stock Data
# ─────────────────────────────────────────────────────────────

@app.get("/data/{symbol}", response_model=schemas.StockDataResponse, tags=["Stock Data"])
def get_stock_data(
    symbol: str,
    days: int = Query(30, ge=1, le=730, description="Number of recent days (1–730)"),
    db: Session = Depends(get_db),
):
    """Return the last N days of OHLCV + metrics for a stock."""
    company = services.get_company_by_symbol(db, symbol)
    if not company:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")

    rows = services.get_recent_stock_data(db, symbol, days=days)
    return schemas.StockDataResponse(
        symbol=company.symbol,
        name=company.name,
        sector=company.sector,
        data_points=len(rows),
        data=rows,
    )


# ─────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────

@app.get("/summary/{symbol}", response_model=schemas.SummaryResponse, tags=["Stock Data"])
def get_summary(symbol: str, db: Session = Depends(get_db)):
    """Return 52-week high/low/avg, latest close, volatility, and distance from high."""
    summary = services.get_summary_stats(db, symbol)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
    return summary


# ─────────────────────────────────────────────────────────────
# Compare (BONUS)
# ─────────────────────────────────────────────────────────────

@app.get("/compare", response_model=schemas.ComparisonResponse, tags=["Compare"])
def compare(
    symbol1: str = Query(..., example="INFY.NS"),
    symbol2: str = Query(..., example="TCS.NS"),
    days: int = Query(90, ge=7, le=730, description="Comparison window in days"),
    db: Session = Depends(get_db),
):
    """
    Compare two stocks over a window:
    - Pearson correlation of daily returns (-1 to +1)
    - Total % return over the window
    - Current volatility for each
    - Winner (higher % return)
    """
    result = services.compare_stocks(db, symbol1, symbol2, days=days)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"One or both symbols not found: '{symbol1}', '{symbol2}'"
        )
    return result
# ─────────────────────────────────────────────────────────────
# Predict (BONUS — ML)
# ─────────────────────────────────────────────────────────────

@app.get("/predict/{symbol}", response_model=schemas.PredictionResponse, tags=["Predict"])
def predict(
    symbol: str,
    lookback: int = Query(60, ge=10, le=252, description="Days of history to train on"),
    days: int = Query(7, ge=1, le=30, description="Days to predict forward"),
    db: Session = Depends(get_db),
):
    """
    Predict the next N closing prices using simple linear regression.

    **Educational only — not for actual trading.** Linear regression on price data
    captures the trend but ignores news, earnings, and market microstructure.
    """
    result = services.predict_next_n_days(
        db, symbol, lookback_days=lookback, predict_days=days
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Symbol '{symbol}' not found or insufficient history"
        )
    return result