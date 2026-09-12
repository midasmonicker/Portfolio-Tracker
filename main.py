from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://portfolio-tracker-seven-beta.vercel.app", "http://localhost:8000",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None

app = FastAPI(title="Stock Screening Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["portfolio-tracker-6byh182nm-midas-monicker.vercel.app", "http://localhost:8000",],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

            latest_price = float(df['Close'].iloc[-1])
            latest_volume = int(df['Volume'].iloc[-1])
            avg_vol_20d = float(df['Volume'].iloc[:-1].mean())
            
            if avg_vol_20d == 0:
                continue

            vol_multiple = round(latest_volume / avg_vol_20d, 2)
            pct_change = round(((latest_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100, 2)

            if latest_price >= min_price and vol_multiple >= vol_threshold:
                record = {
                    "symbol": ticker,
                    "price": round(latest_price, 2),
                    "volume": latest_volume,
                    "avg_volume": int(avg_vol_20d),
                    "vol_multiple": vol_multiple,
                    "pct_change": pct_change,
                    "scan_date": today_str
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

@app.get("/api/picks")
def get_picks():
    # Fetch picks from Supabase
    response = supabase.table("picks").select("*").execute()
    # Return directly as a list instead of nesting in a dictionary
    return response.data
    
if __name__ == "__main__":
    sample_basket = ["AAPL", "AMD", "NVDA", "PLTR", "SOFI", "TSLA", "MARA", "RIOT", "F", "BAC", "INTC", "AMZN", "MSFT", "GOOGL"]
    print(f"Running daily scan on {len(sample_basket)} tickers...")
    found = run_daily_scan(sample_basket)
    print(f"Scan complete. Inserted {found} high-volume picks.")
    
@app.get("/")
def read_root():
    return {"status": "online", "message": "Stock Scanner API is running"}
