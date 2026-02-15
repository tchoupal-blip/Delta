import datetime
from pathlib import Path

import numpy as np
import uvicorn
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from options_math import calc_delta, calc_iv

# DTE buckets: label -> representative days used for delta calculation
DTE_BUCKETS = [
    ("0d", 0),
    ("1-7d", 4),
    ("8-30d", 19),
    ("31-90d", 60),
    ("91-180d", 135),
    ("181-365d", 273),
]

app = FastAPI()

RISK_FREE_RATE = 0.045  # ~4.5%


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    html_path = Path(__file__).parent / "templates" / "index.html"
    return HTMLResponse(html_path.read_text())


@app.get("/api/options/{ticker}")
def get_options(ticker: str):
    ticker = ticker.upper().strip()
    stock = yf.Ticker(ticker)

    # Get current price
    info = stock.fast_info
    try:
        price = float(info.last_price)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Could not fetch price for {ticker}")

    # Get expiration dates
    try:
        expirations = stock.options
    except Exception:
        raise HTTPException(status_code=404, detail=f"No options data for {ticker}")

    if not expirations:
        raise HTTPException(status_code=404, detail=f"No options expirations for {ticker}")

    today = datetime.date.today()
    results = []

    for exp_date_str in expirations:
        exp_date = datetime.date.fromisoformat(exp_date_str)
        T = max((exp_date - today).days / 365.0, 0.0)

        chain = stock.option_chain(exp_date_str)

        calls = _process_chain(chain.calls, price, T, "call")
        puts = _process_chain(chain.puts, price, T, "put")

        results.append({
            "date": exp_date_str,
            "calls": calls,
            "puts": puts,
        })

    return {"ticker": ticker, "price": round(price, 2), "expirations": results}


def _process_chain(df, spot, T, option_type):
    rows = []
    for _, row in df.iterrows():
        strike = float(row["strike"])
        last = float(row["lastPrice"]) if not np.isnan(row["lastPrice"]) else 0
        bid = float(row["bid"]) if not np.isnan(row["bid"]) else 0
        ask = float(row["ask"]) if not np.isnan(row["ask"]) else 0
        mid = (bid + ask) / 2 if (bid + ask) > 0 else last

        iv = calc_iv(mid if mid > 0 else last, spot, strike, T, RISK_FREE_RATE, option_type)
        if iv is not None:
            delta = calc_delta(spot, strike, T, RISK_FREE_RATE, iv, option_type)
        else:
            delta = None

        # Compute delta at each DTE bucket
        delta_by_dte = {}
        for label, days in DTE_BUCKETS:
            if iv is not None:
                T_bucket = days / 365.0
                d = calc_delta(spot, strike, T_bucket, RISK_FREE_RATE, iv, option_type)
                delta_by_dte[label] = round(d, 4)
            else:
                delta_by_dte[label] = None

        rows.append({
            "strike": strike,
            "lastPrice": round(last, 2),
            "bid": round(bid, 2),
            "ask": round(ask, 2),
            "iv": round(iv * 100, 2) if iv is not None else None,
            "delta": round(delta, 4) if delta is not None else None,
            "deltaByDte": delta_by_dte,
        })
    return rows


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
