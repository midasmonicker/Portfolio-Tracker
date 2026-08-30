import os
from datetime import datetime
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

print(f"URL Present: {bool(SUPABASE_URL)}")
print(f"KEY Present: {bool(SUPABASE_KEY)}")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None

if __name__ == "__main__":
    if not supabase:
        print("CRITICAL ERROR: Secrets are missing in GitHub!")
    else:
        test_record = [{
            "symbol": "TEST",
            "price": 100.00,
            "volume": 5000000,
            "avg_volume": 1000000,
            "vol_multiple": 5.0,
            "pct_change": 10.5,
            "scan_date": datetime.now().strftime("%Y-%m-%d")
        }]
        print("Attempting to insert test record into Supabase...")
        res = supabase.table("stock_picks").upsert(test_record).execute()
        print(f"Supabase Output: {res}")
