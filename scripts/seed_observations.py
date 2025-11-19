"""Seed synthetic temperature observations directly into Mongo for chart testing.
Does NOT call OpenWeather; purely generates a time series.

Usage:
  python scripts/seed_observations.py --city London --points 24 --step-minutes 5 --start '2025-11-17T10:00:00'

Each point temp is base + index * delta.
"""
import argparse
from datetime import datetime, timedelta
from db.mongo_repository import MongoRepository
from core.settings import settings

DEFAULT_URI = settings.MONGO_URI


def main():
    p = argparse.ArgumentParser(description="Seed synthetic weather observations")
    p.add_argument("--city", required=True)
    p.add_argument("--points", type=int, default=24)
    p.add_argument("--step-minutes", type=int, default=5)
    p.add_argument("--base-temp", type=float, default=10.0)
    p.add_argument("--delta", type=float, default=0.3, help="Increment per point")
    p.add_argument("--start", help="ISO start time (UTC). Defaults to now - points*step")
    p.add_argument("--uri", default=DEFAULT_URI)
    args = p.parse_args()

    repo = MongoRepository(args.uri)

    if args.start:
        start = datetime.fromisoformat(args.start)
    else:
        start = datetime.utcnow() - timedelta(minutes=args.points * args.step_minutes)

    for i in range(args.points):
        ts = start + timedelta(minutes=i * args.step_minutes)
        temp = args.base_temp + i * args.delta
        repo.insert_observation({
            'city': args.city,
            'provider': 'synthetic',
            'observation_time': ts,
            'fetched_at': ts,
            'temp_c': temp,
            'humidity_pct': 50,
            'conditions': 'synthetic',
            'wind_speed_ms': 2.0
        })
    print(f"Inserted {args.points} synthetic points for {args.city} starting {start.isoformat()}.")


if __name__ == '__main__':
    main()
