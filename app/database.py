"""
Database connection and session management.
Uses SQLite for development; SQLAlchemy abstraction allows easy migration
to PostgreSQL/MySQL for production by changing the DATABASE_URL.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path

# Database file location
BASE_DIR = Path(__file__).resolve().parent.parent  # project root
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "stocks.db"

# SQLAlchemy connection string for SQLite
# For PostgreSQL it would be: "postgresql://user:pass@localhost/dbname"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Engine — manages the actual DB connection
# check_same_thread=False is needed because FastAPI uses multiple threads
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # set True to see all SQL queries (useful for debugging)
)

# SessionLocal — factory for database sessions (one per request in FastAPI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base — all our model classes will inherit from this
Base = declarative_base()


def get_db():
    """
    FastAPI dependency — yields a DB session, ensures it's closed after use.
    Used in endpoints like: def my_endpoint(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()