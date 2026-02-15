# Options Delta & IV Calculator

A web application that calculates options **Delta** and **Implied Volatility (IV)** for any stock ticker using live data from Yahoo Finance.

## Features

- Real-time options chain data via yfinance
- Black-Scholes Delta and IV calculations
- IV solved numerically using Brent's method
- Delta projections across DTE buckets (0d, 1-7d, 8-30d, 31-90d, 91-180d, 181-365d)
- Sortable tables (click column headers)
- Expiration date selector

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:8000 and enter a ticker (e.g. AAPL).

## Stack

- **Backend**: FastAPI + uvicorn
- **Frontend**: Single-page HTML/JS/CSS (no build step)
- **Data**: yfinance
- **Math**: scipy, numpy (Black-Scholes model)
