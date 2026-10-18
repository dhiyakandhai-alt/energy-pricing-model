"""
Download GB wholesale electricity prices from Elexon.
Run from the project folder with:  python src/fetch_prices.py
"""

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index"
START = date(2024, 1, 1)
END = date.today()
CHUNK_DAYS = 7
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "market_index_prices.csv"


def fetch_chunk(start, end):
    """Fetch all prices between two dates from the Elexon API."""
    params = {"from": f"{start.isoformat()}T00:00Z", "to": f"{end.isoformat()}T00:00Z"}
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()["data"]


def main():
    rows = []
    chunk_start = START
    while chunk_start < END:
        chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS), END)
        print(f"Fetching {chunk_start} to {chunk_end}...")
        rows.extend(fetch_chunk(chunk_start, chunk_end))
        chunk_start = chunk_end

    df = pd.DataFrame(rows)
    df = df[df["dataProvider"] == "APXMIDP"]
    df = df[["startTime", "settlementDate", "settlementPeriod", "price", "volume"]]
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df = df.drop_duplicates("startTime").sort_values("startTime")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False)

    print(f"\nSaved {len(df):,} half-hourly prices to {OUTPUT}")
    print(df["price"].describe().round(2))


if __name__ == "__main__":
    main()