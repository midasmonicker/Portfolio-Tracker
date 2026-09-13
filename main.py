import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import requests
from supabase import Client, create_client
import yfinance as yf

# Initialize FastAPI Application
app = FastAPI(title="Stock Screening Engine")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

supabase: Client = (
    create_client(SUPABASE_URL, SUPABASE_KEY)
    if (SUPABASE_URL and SUPABASE_KEY)
    else None
)


def send_telegram_alert(picks: list):
    """Formats and sends stock picks to a Telegram channel/chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram configuration missing. Skipping notification.")
        return

    message = f"🚀 *High-Volume Stock Picks ({datetime.now().strftime('%Y-%m-%d')})*\n\n"

    for p in picks:
        message += (
            f"• *{p['symbol']}*\n"
            f"  💰 Price: ${p['price']}\n"
            f"  📊 Volume Multiple: {p['vol_multiple']}x\n"
            f"  📈 Change: {p['pct_change']}%\n\n"
        )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("Telegram alert sent successfully!")
        else:
            print(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")


def run_daily_scan(tickers: list, vol_threshold=1.2, min_price=5.0):
    """Scans tickers for volume spikes, writes to Supabase, and triggers alerts."""
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

    if results:
        if supabase:
            supabase.table("stock_picks").upsert(results).execute()
            print(f"Successfully upserted {len(results)} records to Supabase.")

        # Send Telegram Notification
        send_telegram_alert(results)

    return len(results)


@app.get("/")
def read_root():
    return {"status": "online", "message": "Stock Scanner API is running"}


@app.get("/api/picks")
def get_picks():
    if not supabase:
        return {"error": "Supabase client uninitialized", "picks": []}

    try:
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

        picks_res = (
            supabase.table("stock_picks")
            .select("*")
            .eq("scan_date", latest_date)
            .execute()
        )

        return {"date": latest_date, "picks": picks_res.data}
    except Exception as e:
        return {"error": str(e), "picks": []}


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
