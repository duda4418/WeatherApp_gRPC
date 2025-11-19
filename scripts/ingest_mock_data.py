"""Mock data ingestor for weather observations.

Generates synthetic observation documents compatible with `MongoRepository` expectations:
Each document fields:
  - city (str)
  - conditions (str)
  - fetched_at (datetime UTC)
  - observation_time (datetime UTC)
  - provider (str)
  - temp_c (float)
  - humidity_pct (int)
  - wind_speed_ms (float)
  - raw (dict) containing minimal OpenWeather-like payload with `weather[0].icon`

Usage examples (PowerShell):
  # Insert 3 days of 5-minute interval data for two cities
  python scripts/ingest_mock_data.py --cities Cluj,Bucharest --days 3 --interval-minutes 5

  # Daily-only sparse data (2 samples per day)
  python scripts/ingest_mock_data.py --cities Cluj --days 7 --interval-minutes 720 --mode daily

  # Dry-run (no DB writes)
  python scripts/ingest_mock_data.py --cities Cluj --days 2 --dry-run

Design considerations to avoid blocking MongoDB:
  - Inserts performed in small batches (`--batch-size`) using `insert_many(..., ordered=False)`.
  - Optional throttling between batches (`--throttle-ms`).
  - Document generation performed in memory prior to each batch write only.

The script targets the collection name defined in `mongo_repository.COLLECTION_NAME`.
"""

from __future__ import annotations

import argparse
import math
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from pymongo import MongoClient

try:
    from core.settings import settings  # type: ignore
    from db.mongo_repository import COLLECTION_NAME  # type: ignore
except Exception:  # pragma: no cover - fallback if imports fail
    settings = None
    COLLECTION_NAME = "weather_observations"


ICON_CHOICES_DAY = ["01d", "02d", "03d", "04d", "09d", "10d", "11d", "13d", "50d"]
ICON_CHOICES_NIGHT = [i.replace("d", "n") for i in ICON_CHOICES_DAY]
CONDITION_MAP = {
    "01": "clear sky",
    "02": "few clouds",
    "03": "scattered clouds",
    "04": "overcast clouds",
    "09": "shower rain",
    "10": "rain",
    "11": "thunderstorm",
    "13": "snow",
    "50": "mist",
}


def pick_icon(ts: datetime) -> str:
    """Return a plausible OpenWeather icon code based on time of day."""
    is_day = 6 <= ts.hour < 20
    choices = ICON_CHOICES_DAY if is_day else ICON_CHOICES_NIGHT
    return random.choice(choices)


def condition_for_icon(icon: str) -> str:
    return CONDITION_MAP.get(icon[:2], "variable conditions")


def generate_city_base_temp(city: str) -> float:
    """Assign a deterministic base temperature per city for repeatability."""
    seed = sum(ord(c) for c in city)
    random.seed(seed)
    # Continental climate baseline between -2 and 22 C
    return random.uniform(-2, 22)


def generate_observations(
    cities: List[str],
    days: int,
    interval_minutes: int,
    mode: str,
) -> List[Dict[str, Any]]:
    """Generate synthetic observation documents.

    mode:
      - "all": full time series across interval for given days
      - "daily": sparse (2 samples per day)
      - "series": ignore daily spread; only last day at interval
    """
    # Use timezone-aware UTC then drop tzinfo for storage consistency with existing code
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0).replace(tzinfo=None)
    docs: List[Dict[str, Any]] = []

    for city in cities:
        base_temp = generate_city_base_temp(city)
        if mode == "series":
            start = now - timedelta(days=1)
            total_minutes = (24 * 60)
            step = interval_minutes
            timestamps = [start + timedelta(minutes=m) for m in range(0, total_minutes, step)]
        elif mode == "daily":
            # Two samples per day: morning & evening
            start = now - timedelta(days=days - 1)
            timestamps = []
            for d in range(days):
                day_start = (start + timedelta(days=d)).replace(hour=8, minute=0)
                eve = (start + timedelta(days=d)).replace(hour=18, minute=0)
                timestamps.extend([day_start, eve])
        else:  # all
            start = now - timedelta(days=days - 1)
            total_minutes = days * 24 * 60
            step = interval_minutes
            timestamps = [start + timedelta(minutes=m) for m in range(0, total_minutes, step)]

        for ts in timestamps:
            # Diurnal component: sine wave with amplitude 6C
            diurnal = 6 * math.sin((ts.hour + ts.minute / 60) / 24 * 2 * math.pi)
            # Seasonal noise across days
            day_offset = (ts.date().toordinal() % 30) / 30.0
            seasonal = 4 * math.sin(day_offset * 2 * math.pi)
            noise = random.uniform(-1.5, 1.5)
            temp_c = base_temp + diurnal + seasonal + noise
            humidity = max(25, min(100, int(65 + random.gauss(0, 15))))
            wind = round(random.uniform(0.2, 8.5), 2)
            icon = pick_icon(ts)
            conditions = condition_for_icon(icon)
            raw_payload = {
                "weather": [{"id": 800, "main": conditions.split()[0].title(), "description": conditions, "icon": icon}],
                "main": {
                    "temp": temp_c,
                    "feels_like": temp_c - random.uniform(0, 2),
                    "pressure": random.randint(990, 1035),
                    "humidity": humidity,
                },
                "wind": {"speed": wind, "deg": random.randint(0, 359)},
                "dt": int(ts.timestamp()),
                "name": city,
            }
            docs.append({
                "city": city,
                "conditions": conditions,
                "fetched_at": ts,
                "observation_time": ts,
                "provider": "synthetic",
                "raw": raw_payload,
                "temp_c": round(temp_c, 2),
                "humidity_pct": humidity,
                "wind_speed_ms": wind,
            })
    return docs


def chunked(seq: List[Any], size: int) -> List[List[Any]]:
    return [seq[i:i + size] for i in range(0, len(seq), size)]


def ingest(
    docs: List[Dict[str, Any]],
    mongo_uri: str,
    db_name: str,
    batch_size: int,
    throttle_ms: int,
    dry_run: bool,
) -> int:
    if dry_run:
        print(f"[DRY-RUN] Would insert {len(docs)} documents into database '{db_name}' collection '{COLLECTION_NAME}'.")
        return 0
    client = MongoClient(mongo_uri)
    col = client[db_name][COLLECTION_NAME]
    inserted = 0
    for batch in chunked(docs, batch_size):
        if not batch:
            continue
        res = col.insert_many(batch, ordered=False)
        inserted += len(res.inserted_ids)
        if throttle_ms > 0:
            # Lightweight sleep without importing time earlier if unused
            import time
            time.sleep(throttle_ms / 1000.0)
    return inserted


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate and insert synthetic weather observations.")
    p.add_argument("--cities", required=True, help="Comma-separated list of city names.")
    p.add_argument("--days", type=int, default=3, help="Number of days of data to generate (ignored for mode=series where 1 day is used).")
    p.add_argument("--interval-minutes", type=int, default=10, help="Interval between observations in minutes (mode=daily uses 2 points/day; mode=series uses last day).")
    p.add_argument("--mode", choices=["all", "daily", "series"], default="all", help="Generation mode.")
    p.add_argument("--batch-size", type=int, default=500, help="Insert batch size to reduce locking impact.")
    p.add_argument("--throttle-ms", type=int, default=0, help="Sleep milliseconds between batches (0 = no throttle).")
    p.add_argument("--mongo-uri", default=getattr(settings, "MONGO_URI", "mongodb://localhost:27017"), help="Mongo connection URI (overrides username/password if provided).")
    p.add_argument("--host", default="localhost:27017", help="Mongo host:port used when building URI from credentials.")
    p.add_argument("--db-name", default=getattr(settings, "MONGO_APP_DB", "weatherdb"), help="Target database name.")
    p.add_argument("--auth-db", default=getattr(settings, "MONGO_APP_DB", "weatherdb"), help="Authentication database (authSource).")
    p.add_argument("--username", help="MongoDB username (optional; if provided with password will build URI).")
    p.add_argument("--password", help="MongoDB password (optional).")
    p.add_argument("--dry-run", action="store_true", help="Generate and report only; no database writes.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cities = [c.strip() for c in args.cities.split(",") if c.strip()]
    if not cities:
        raise SystemExit("No valid cities provided.")
    if args.days < 1:
        raise SystemExit("--days must be >= 1")
    # Build URI from provided credentials unless explicit --mongo-uri used differently
    mongo_uri = args.mongo_uri
    if args.username and args.password and "@" not in mongo_uri:
        mongo_uri = f"mongodb://{args.username}:{args.password}@{args.host}/{args.db_name}?authSource={args.auth_db}"
    docs = generate_observations(cities, args.days, args.interval_minutes, args.mode)
    print(f"Generated {len(docs)} documents for cities={cities} mode={args.mode}")
    try:
        inserted = ingest(
            docs,
            mongo_uri=mongo_uri,
            db_name=args.db_name,
            batch_size=args.batch_size,
            throttle_ms=args.throttle_ms,
            dry_run=args.dry_run,
        )
    except Exception as e:  # Broad catch to surface helpful hints, but keep traceback for debugging
        import pymongo.errors as pymerr
        if isinstance(e, pymerr.OperationFailure):
            print("Mongo OperationFailure:", e)
            if "requires authentication" in str(e):
                print("Hint: Provide credentials via --username/--password or a full --mongo-uri including authSource.")
                print("Example: --username weatherapp --password weatherpass --db-name weatherdb --auth-db weatherdb")
        raise
    else:
        if not args.dry_run:
            print(f"Inserted {inserted} documents into '{args.db_name}.{COLLECTION_NAME}'.")
        print("Done.")


if __name__ == "__main__":  # pragma: no cover
    main()
