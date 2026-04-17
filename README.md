# Stock Data Intelligence Dashboard

A mini financial data platform for Indian large-cap stocks — built as the JarNox Software Engineering Internship Assignment.

The app fetches real OHLCV data from Yahoo Finance, enriches it with calculated metrics (daily return, moving averages, 52-week high/low, and a custom volatility score), persists it to SQLite, and exposes everything through a FastAPI REST API with an interactive dashboard built in vanilla HTML + Chart.js.

---

## Features

- **10 Indian large-cap stocks** across IT, Banking, FMCG, Energy, and Engineering sectors
- **2 years of daily OHLCV data** (~4,950 rows) sourced from Yahoo Finance via `yfinance`
- **5 calculated metrics** per row: daily return, 7-day moving average, 52-week high, 52-week low, and a custom 30-day annualized volatility
- **6 REST API endpoints** with auto-generated Swagger documentation
- **Two-stock comparison** with Pearson correlation of daily returns
- **Interactive dashboard** with company list, price chart, 7-day MA overlay, time range filters (30D / 90D / 1Y / 2Y), and 5 stat cards
- **404 error handling** for unknown symbols
- **Idempotent seed script** (re-runnable without duplicating data)

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend Framework | FastAPI | Auto Swagger docs, native Pydantic validation, zero-boilerplate REST APIs |
| Server | Uvicorn | ASGI server with hot-reload for development |
| Data Source | yfinance | Free, supports Indian NSE tickers (`.NS` suffix), no API key required |
| Data Processing | Pandas + NumPy | Industry standard for time-series transformations |
| Database | SQLite + SQLAlchemy ORM | Zero-setup persistence; SQLAlchemy abstraction allows zero-code migration to PostgreSQL/MySQL for production |
| Frontend | Vanilla HTML + CSS + JavaScript | No build step, fast to ship for a single-page dashboard |
| Charting | Chart.js (CDN) | Lightweight, responsive, good defaults |

---

## Architecture

```
Yahoo Finance
     │ (yfinance)
     ▼
data_fetcher.py  ──►  data_cleaner.py  ──►  seed_data.py
                                                 │
                                                 ▼
                                          data/stocks.db
                                          (SQLite)
                                                 │
                                                 ▼
                              services.py  (DB queries)
                                                 │
                                                 ▼
                              main.py  (FastAPI endpoints)
                                                 │
                                                 ▼
                              frontend/  (HTML + Chart.js)
```

---

## Quick Start

### Prerequisites

- Python 3.12 or higher (3.14 not recommended due to limited library wheel support)
- Git
- Internet connection (to fetch initial data from Yahoo Finance)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/kalyanipannasa/stock-intel-dashboard.git
cd stock-intel-dashboard

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
# Windows PowerShell:
.\venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Seed the database (fetches data from Yahoo Finance, ~30 seconds)
python -m app.seed_data

# 6. Run the API server
uvicorn app.main:app --reload
```

The API is now running at **http://127.0.0.1:8000**.

### Open the Dashboard

Open `frontend/index.html` directly in your browser. The dashboard will auto-load companies from the running API.

### Open the API Docs

Visit **http://127.0.0.1:8000/docs** — interactive Swagger UI listing all endpoints with "Try it out" buttons.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API metadata + endpoint list |
| GET | `/health` | Health check |
| GET | `/companies` | List all 10 companies (symbol, name, sector) |
| GET | `/data/{symbol}?days=N` | Last N days of OHLCV + metrics (default 30, max 730) |
| GET | `/summary/{symbol}` | 52-week high/low/avg, latest close, volatility, distance from high |
| GET | `/compare?symbol1=&symbol2=&days=N` | Two-stock comparison: correlation, returns, volatilities, winner |

### Example: Compare INFY vs TCS

```
GET http://127.0.0.1:8000/compare?symbol1=INFY.NS&symbol2=TCS.NS&days=90
```

```json
{
  "symbol1": "INFY.NS",
  "symbol2": "TCS.NS",
  "period_days": 90,
  "correlation": 0.78,
  "return_1_pct": 5.2,
  "return_2_pct": 3.8,
  "volatility_1_pct": 21.0,
  "volatility_2_pct": 20.6,
  "winner": "INFY.NS"
}
```

---

## Custom Metric: 30-Day Annualized Volatility

The assignment asked for one creative metric. I chose **annualized volatility** because it is widely used in real finance (Sharpe ratio, Bollinger Bands, Value-at-Risk) and produces interpretable risk rankings.

### Formula

```
volatility_30d = StdDev(daily_returns over last 30 days) × √252
```

The `√252` factor annualizes the daily volatility (252 is the standard count of trading days per year).

### Interpretation

A volatility of 25% means the stock typically moves ±25% over a year. Lower = more stable, higher = riskier.

### Sample Output (April 2026)

| Symbol | Sector | Annualized Volatility |
|---|---|---|
| LT.NS | Engineering | 35.0% |
| HDFCBANK.NS | Banking | 26.9% |
| RELIANCE.NS | Energy | 25.3% |
| SBIN.NS | Banking | 24.0% |
| HINDUNILVR.NS | FMCG | 22.9% |
| WIPRO.NS | IT | 22.7% |
| ICICIBANK.NS | Banking | 22.7% |
| INFY.NS | IT | 21.1% |
| TCS.NS | IT | 20.6% |
| ITC.NS | FMCG | 18.2% |

The ranking is economically defensible: infrastructure stocks (LT) at the top, FMCG defensives (ITC) at the bottom — matches conventional sector risk classifications.

---

## Project Structure

```
stock-intel-dashboard/
├── app/
│   ├── __init__.py            # marks app/ as a Python package
│   ├── data_fetcher.py        # Phase 1: yfinance wrappers + COMPANIES list
│   ├── data_cleaner.py        # Phase 2: cleaning + 5 calculated metrics
│   ├── database.py            # Phase 3: SQLAlchemy engine + session factory
│   ├── models.py              # Phase 3: Company + StockData ORM models
│   ├── seed_data.py           # Phase 3: idempotent DB seed script
│   ├── schemas.py             # Phase 4: Pydantic response models
│   ├── services.py            # Phase 4: pure DB query functions
│   └── main.py                # Phase 4: FastAPI HTTP endpoints
├── frontend/
│   ├── index.html             # Phase 5: dashboard layout
│   ├── style.css              # Phase 5: styling
│   └── app.js                 # Phase 5: API calls + Chart.js rendering
├── data/
│   └── stocks.db              # SQLite database (generated, gitignored)
├── requirements.txt           # pinned dependencies
├── .gitignore
└── README.md
```

---

## Design Decisions

**FastAPI over Django/Flask** — The brief emphasized REST APIs with Swagger documentation. FastAPI provides interactive OpenAPI docs out of the box via Pydantic models, has first-class async support, and ships with significantly less boilerplate than Django REST Framework for pure API workloads.

**SQLite over PostgreSQL/MySQL** — For a single-user development scope with ~5,000 rows, SQLite is faster to set up and equally capable. The SQLAlchemy ORM abstraction means switching to PostgreSQL or MySQL in production is a one-line change to the connection string.

**Vanilla JS over React** — A single-page dashboard with one chart and one list does not justify React's overhead. Vanilla JS ships faster, has no build step, and the assignment brief explicitly accepts both.

**Three-layer backend architecture** — Endpoints (`main.py`) call services (`services.py`), which query models (`models.py`). Each file has one responsibility, making the code easier to test and review.

---

## Known Limitations

- **Yahoo Finance is unofficial** — `yfinance` scrapes Yahoo's undocumented API. Production systems should use a paid provider like Alpha Vantage, EOD Historical Data, or NSE's official APIs for reliability and SLA.
- **Static data after seed** — Data is fetched once during seed. A scheduled refresh (cron / APScheduler) would keep prices current.
- **No authentication** — All endpoints are public. Production would add JWT or API key auth.
- **CORS allows all origins** — Acceptable for development; should be restricted to known frontend domains in production.
- **No rate limiting** — Easy to add via slowapi or an upstream proxy in production.

---

## Roadmap (Things I Would Build Next)

- **Daily refresh scheduler** — APScheduler running `seed_data` once a day after market close
- **News sentiment integration** — Pull headlines from NSE / Moneycontrol RSS, score with VADER, plot as a third overlay on the chart
- **ML price prediction** — Linear regression over the last 60 days to project the next 7 days as a dashed line on the chart (scikit-learn, ~50 lines)
- **Dockerization** — Single Dockerfile + docker-compose for one-command deployment
- **Deployment** — Render or Oracle Cloud free tier for a public live demo

---

## Author

**kalyanipannasa**
Built for the JarNox Software Engineering Internship Assignment, April 2026.

## Acknowledgments

- Stock data: [Yahoo Finance](https://finance.yahoo.com/) via the [yfinance](https://github.com/ranaroussi/yfinance) Python library
- Charting: [Chart.js](https://www.chartjs.org/)
- API framework: [FastAPI](https://fastapi.tiangolo.com/)