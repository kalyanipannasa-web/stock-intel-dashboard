"""
One-time seed script — fetches stock data, enriches it, and inserts into SQLite.
Run with: python -m app.seed_data

Idempotent: re-running won't duplicate rows (uses upsert pattern).
"""

import pandas as pd
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from app.database import engine, SessionLocal, Base
from app.models import Company, StockData
from app.data_fetcher import COMPANIES, fetch_all_companies
from app.data_cleaner import enrich_all


def init_database():
    """Create tables if they don't exist."""
    print("📦 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("  ✅ Tables created (or already exist)")


def seed_companies(db):
    """Insert/update the master companies table."""
    print(f"\n🏢 Seeding {len(COMPANIES)} companies...")

    for company_dict in COMPANIES:
        # Upsert pattern: insert or replace on conflict (SQLite-specific)
        stmt = sqlite_insert(Company).values(**company_dict)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol"],
            set_={"name": stmt.excluded.name, "sector": stmt.excluded.sector}
        )
        db.execute(stmt)

    db.commit()
    print(f"  ✅ Companies table seeded")


def seed_stock_data(db, enriched_data: dict[str, pd.DataFrame]):
    """Insert stock_data rows for all companies."""
    print(f"\n📊 Seeding stock_data for {len(enriched_data)} companies...")

    total_rows = 0
    for symbol, df in enriched_data.items():
        rows = []
        for _, row in df.iterrows():
            rows.append({
                "symbol": symbol,
                "date": row["Date"],
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
                "daily_return": _safe_float(row.get("daily_return")),
                "ma_7": _safe_float(row.get("ma_7")),
                "high_52w": _safe_float(row.get("high_52w")),
                "low_52w": _safe_float(row.get("low_52w")),
                "volatility_30d": _safe_float(row.get("volatility_30d")),
            })

        # Bulk upsert — handles re-running gracefully
        stmt = sqlite_insert(StockData).values(rows)
        update_dict = {
            col: stmt.excluded[col]
            for col in ["open", "high", "low", "close", "volume",
                        "daily_return", "ma_7", "high_52w", "low_52w", "volatility_30d"]
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "date"],
            set_=update_dict
        )
        db.execute(stmt)
        db.commit()

        print(f"  ✅ {symbol:18s} → {len(rows)} rows inserted/updated")
        total_rows += len(rows)

    print(f"\n  📈 Total rows in stock_data: {total_rows}")


def _safe_float(value):
    """Convert NaN/None to None (SQL NULL), otherwise return float."""
    if value is None or pd.isna(value):
        return None
    return float(value)


def main():
    print("=" * 60)
    print("STOCK INTEL DASHBOARD — DATABASE SEED")
    print("=" * 60)

    # Step 1: Create tables
    init_database()

    # Step 2: Fetch + enrich (uses Phase 1 + Phase 2 modules)
    raw_data = fetch_all_companies(period="2y")  # 2 years of history
    enriched_data = enrich_all(raw_data)

    # Step 3: Insert into DB
    db = SessionLocal()
    try:
        seed_companies(db)
        seed_stock_data(db, enriched_data)
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("✅ DATABASE SEED COMPLETE")
    print(f"   Database file: data/stocks.db")
    print("=" * 60)


if __name__ == "__main__":
    main()