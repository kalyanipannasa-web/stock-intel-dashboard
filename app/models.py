"""
SQLAlchemy ORM models — define the database schema as Python classes.
"""

from sqlalchemy import Column, Integer, String, Float, BigInteger, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Company(Base):
    """Master table — 10 large-cap Indian stocks."""
    __tablename__ = "companies"

    symbol = Column(String(20), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    sector = Column(String(50), nullable=False)

    # Relationship — gives us company.stock_data to access related rows
    stock_data = relationship("StockData", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company(symbol='{self.symbol}', name='{self.name}')>"


class StockData(Base):
    """Daily OHLCV + calculated metrics for each company."""
    __tablename__ = "stock_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), ForeignKey("companies.symbol"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Raw OHLCV
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)

    # Phase 2 calculated metrics (nullable because early rows lack enough history)
    daily_return = Column(Float, nullable=True)
    ma_7 = Column(Float, nullable=True)
    high_52w = Column(Float, nullable=True)
    low_52w = Column(Float, nullable=True)
    volatility_30d = Column(Float, nullable=True)

    # Reverse relationship
    company = relationship("Company", back_populates="stock_data")

    # Critical: prevents duplicate (symbol, date) rows — makes seed re-runnable
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_symbol_date"),
    )

    def __repr__(self):
        return f"<StockData({self.symbol} {self.date} close={self.close})>"