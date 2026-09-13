import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from supabase import Client, create_client
import yfinance as yf

# 1. Initialize FastAPI Application
app = FastAPI(title="Stock Screening Engine")

# 2. Configure CORS Middleware (Single, global declaration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://midasmonicker.github.io",
        "https://portfolio-tracker-seven-beta.vercel.app",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Initialize Supabase Client
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

supabase: Client = (
    create_client(SUPABASE_URL, SUPABASE_KEY)
    if (SUPABASE_URL and SUPABASE_KEY)
    else None
)


# 4. Core Scanning Logic
def run_daily_scan(tickers: list, vol_threshold=1.2, min_price=5.0):
    """Scans tickers for volume spikes and writes results to Supabase."""
    results = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1mo")
            if len(df) < 15:
                continue

            latest_price = float(df["Close"].iloc[-1])
            latest_volume = int(df["Volume"].iloc[-1])
            avg_vol_20d = float(df["Volume"].iloc[:-1].mean())

            if avg_vol_20d == 0:
                continue

            vol_multiple = round(latest_volume / avg_vol_20d, 2)
            pct_change = round(
                (
                    (latest_price - df["Close"].iloc[-2])
                    / df["Close"].iloc[-2]
                )
                * 100,
                2,
            )

            if latest_price >= min_price and vol_multiple >= vol_threshold:
                record = {
                    "symbol": ticker,
                    "price": round(latest_price, 2),
                    "volume": latest_volume,
                    "avg_volume": int(avg_vol_20d),
                    "vol_multiple": vol_multiple,
                    "pct_change": pct_change,
                    "scan_date": today_str,
                }
                results.append(record)
        except Exception as e:
            print(f"Error scanning {ticker}: {e}")

    print(f"Found {len(results)} qualifying stock picks.")

    if results and supabase:
        response = supabase.table("stock_picks").upsert(results).execute()
        print(f"Successfully upserted {len(results)} records to Supabase.")
    elif not supabase:
        print("ERROR: Supabase client is not initialized.")

    return len(results)


# 5. API Endpoints
@app.get("/")
def read_root():
    """Health-check endpoint for Render logs."""
    return {"status": "online", "message": "Stock Scanner API is running"}


@app.get("/api/picks")
def get_picks():
    """Fetches the stock picks for the latest available scan_date."""
    if not supabase:
        return {"error": "Supabase client uninitialized", "picks": []}

    try:
        # Fetch the most recent scan_date in the database
        latest_date_res = (
            supabase.table("stock_picks")
            .select("scan_date")
            .order("scan_date", desc=True)
            .limit(1)
            .execute()
        )

        if not latest_date_res.data:
            return {"date": None, "picks": []}

        latest_date = latest_date_res.data[0]["scan_date"]

        # Fetch all picks matching that latest date
        picks_res = (
            supabase.table("stock_picks")
            .select("*")
            .eq("scan_date", latest_date)
            .execute()
        )

        return {"date": latest_date, "picks": picks_res.data}
    except Exception as e:
        return {"error": str(e), "picks": []}


# 6. Standalone Execution Entrypoint
if __name__ == "__main__":
    sample_basket = [
        "AAPL",
        "AMD",
        "NVDA",
        "PLTR",
        "SOFI",
        "TSLA",
        "MARA",
        "RIOT",
        "F",
        "BAC",
        "INTC",
        "AMZN",
        "MSFT",
        "GOOGL",
    ]
    print(f"Running daily scan on {len(sample_basket)} tickers...")
    found = run_daily_scan(sample_basket)
    print(f"Scan complete. Inserted {found} high-volume picks.")
<<<<<<< HEAD
    
@app.get("/")
def read_root():
    return {"status": "online", "message": "Stock Scanner API is running"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for all origins (or specify GitHub Pages)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://midasmonicker.github.io",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"  # Allows access from any domain (including Vercel/GitHub Pages)
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # Allows all headers
)

@app.get("/api/picks")
def get_picks():
    # Your existing route handler code here
    return {"picks": [...]}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows GitHub Pages, Vercel, and local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint (Fixes the 404 health check in Render logs)
@app.get("/")
def read_root():
    return {"status": "online", "message": "Portfolio Tracker API is running"}

# Your existing picks endpoint
@app.get("/api/picks")
def get_picks():
    # Return your stock scanner picks
    return {"picks": []}
=======
>>>>>>> 213526b (Full Code Adjustment)
