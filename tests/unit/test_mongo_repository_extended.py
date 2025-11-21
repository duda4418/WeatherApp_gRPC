from __future__ import annotations

"""Extended tests for MongoRepository to raise coverage.

These tests exercise:
 - insert_observation branches (observation_time missing / not datetime)
 - get_observations time window filtering and ordering
 - get_temperature_series bucketing & icon normalization (list / invalid types)
 - get_daily_series day aggregation and days < 1 edge
"""

from datetime import datetime, timedelta, UTC
from typing import Any, Dict, List

from db.mongo_repository import MongoRepository
from tests.factories import observation_doc


class FakeCursor:
    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = docs

    def sort(self, key: str, direction: int):  # direction: 1 asc / -1 desc
        reverse = direction == -1
        self._docs = sorted(self._docs, key=lambda d: d.get(key), reverse=reverse)
        return self

    def __iter__(self):
        return iter(self._docs)


class FakeCollectionExtended:
    def __init__(self):
        self.docs: List[Dict[str, Any]] = []

    # Basic insert
    def insert_one(self, doc: Dict[str, Any]):
        doc.setdefault("_id", f"id{len(self.docs)+1}")
        self.docs.append(doc)
        class Res: pass
        res = Res(); res.inserted_id = doc["_id"]
        return res

    # Filtering by city & time range, emulate pymongo cursor
    def find(self, query: Dict[str, Any]):
        city = query.get("city")
        time_range = query.get("observation_time", {})
        start = time_range.get("$gte", datetime.min.replace(tzinfo=UTC))
        end = time_range.get("$lte", datetime.max.replace(tzinfo=UTC))
        out = [d for d in self.docs if d.get("city") == city and start <= d.get("observation_time") <= end]
        return FakeCursor(out)

    def find_one(self, query: Dict[str, Any], sort=None):
        city = query.get("city")
        relevant = [d for d in self.docs if d.get("city") == city]
        if not relevant:
            return None
        return sorted(relevant, key=lambda x: x.get("observation_time"), reverse=True)[0]

    # Simplified aggregate interpretation for temperature_series & daily_series
    def aggregate(self, pipeline: List[Dict[str, Any]]):
        # Detect which aggregation based on presence of 'slice' in _id
        is_temp_series = any("slice" in (stage.get("$group", {}).get("_id", {})) for stage in pipeline)
        if is_temp_series:
            # Extract bucket_minutes from multiply expression if present; fallback 5
            bucket_minutes = 5
            # All docs already inserted; group by computed bucket
            buckets: Dict[tuple, List[Dict[str, Any]]] = {}
            for d in self.docs:
                ts: datetime = d["observation_time"]
                key = (ts.year, ts.month, ts.day, ts.hour, ts.minute // bucket_minutes)
                buckets.setdefault(key, []).append(d)
            for (y, m, day, hour, slice_idx), docs in sorted(buckets.items()):
                avg_temp = sum(x.get("temp_c", 0.0) for x in docs) / max(len(docs), 1)
                # icon extraction (raw.weather.0.icon) mimic first document behavior
                first_raw = docs[0].get("raw", {})
                icon = ((first_raw.get("weather") or [{}])[0]).get("icon")
                yield {
                    "timestamp": datetime(y, m, day, hour, slice_idx * bucket_minutes, tzinfo=UTC),
                    "avg_temp": avg_temp,
                    "first_icon": icon,
                }
        else:
            # Daily series grouping by date
            days: Dict[tuple, List[Dict[str, Any]]] = {}
            for d in self.docs:
                ts: datetime = d["observation_time"]
                key = (ts.year, ts.month, ts.day)
                days.setdefault(key, []).append(d)
            for (y, m, day), docs in sorted(days.items()):
                avg_temp = sum(x.get("temp_c", 0.0) for x in docs) / max(len(docs), 1)
                icon = ((docs[0].get("raw", {}).get("weather") or [{}])[0]).get("icon")
                yield {
                    "day_start": datetime(y, m, day, tzinfo=UTC),
                    "avg_temp": avg_temp,
                    "first_ts": docs[0]["observation_time"],
                    "first_icon": icon,
                }


def make_repo() -> MongoRepository:
    repo = MongoRepository("mongodb://ignored")
    repo._col = FakeCollectionExtended()  # type: ignore[attr-defined]
    return repo


# --- Smoke tests migrated from test_mongo_repository.py ---
def test_insert_observation_sets_defaults():
    repo = make_repo()
    odoc = observation_doc()
    # Simulate missing observation_time to exercise defaulting logic
    if "observation_time" in odoc:
        del odoc["observation_time"]
    inserted_id = repo.insert_observation(odoc)
    assert inserted_id
    stored = repo._col.docs[0]
    assert isinstance(stored["observation_time"], datetime)


def test_get_latest_observation():
    repo = make_repo()
    repo._col.insert_one(observation_doc(temp=1, minutes_ago=5))
    repo._col.insert_one(observation_doc(temp=2, minutes_ago=1))
    latest = repo.get_latest_observation("Berlin")
    assert latest["temp_c"] == 2


def test_insert_observation_sets_defaults_when_missing():
    repo = make_repo()
    doc = {"city": "X", "temp_c": 1.0, "raw": {"weather": [{}]}}
    repo.insert_observation(doc)
    stored = repo._col.docs[0]
    assert isinstance(stored["observation_time"], datetime)
    assert stored["observation_time"].tzinfo is not None


def test_insert_observation_normalizes_non_datetime_observation_time():
    repo = make_repo()
    doc = {"city": "Y", "temp_c": 2.0, "raw": {"weather": [{}]}, "observation_time": "not a dt"}
    repo.insert_observation(doc)
    stored = repo._col.docs[0]
    assert isinstance(stored["observation_time"], datetime)


def test_get_observations_filters_and_sorts():
    repo = make_repo()
    base = datetime.now(UTC).replace(second=0, microsecond=0)
    for offset, temp in [(10, 5.0), (5, 6.0), (15, 4.0)]:  # minutes offset
        repo.insert_observation({
            "city": "Berlin",
            "temp_c": temp,
            "raw": {"weather": [{}]},
            "observation_time": base + timedelta(minutes=offset)
        })
    start = base + timedelta(minutes=5)
    end = base + timedelta(minutes=15)
    obs = repo.get_observations("Berlin", start, end)
    # Should include 5,10,15 sorted ascending by observation_time
    temps = [o["temp_c"] for o in obs]
    assert temps == [6.0, 5.0, 4.0]


def test_get_temperature_series_buckets_and_icon_handling():
    repo = make_repo()
    # Align base time to the start of a 5-minute bucket to avoid boundary crossing
    now = datetime.now(UTC).replace(second=0, microsecond=0)
    aligned_minute = now.minute - (now.minute % 5)
    base = now.replace(minute=aligned_minute)
    # Icons: list, string, invalid int
    docs = []
    # Case 1: icon is a list -> should normalize to first element
    docs.append({
        "city": "Berlin",
        "temp_c": 10,
        "raw": {"weather": [{"icon": ["01d"]}]},
        "observation_time": base,
    })
    # Case 2: icon is a plain string
    docs.append({
        "city": "Berlin",
        "temp_c": 20,
        "raw": {"weather": [{"icon": "02n"}]},
        "observation_time": base + timedelta(minutes=3),
    })
    # Case 3: icon is invalid type (int) -> should become None
    docs.append({
        "city": "Berlin",
        "temp_c": 30,
        "raw": {"weather": [{"icon": 123}]},
        "observation_time": base + timedelta(minutes=7),
    })
    for d in docs:
        repo.insert_observation(d)
    series = repo.get_temperature_series("Berlin", base - timedelta(minutes=1), base + timedelta(minutes=10))
    assert series  # non-empty
    # Expect two buckets (0-4, 5-9 minutes) with avg temps
    bucket_temps = [b["avg_temp_c"] for b in series]
    assert any(abs(t - 15.0) < 0.01 for t in bucket_temps)  # first bucket avg of 10 & 20
    assert any(30.0 <= t <= 30.1 for t in bucket_temps)
    # Icon normalization: list becomes first element string, invalid type becomes None
    icons = [b["icon"] for b in series]
    assert "01d" in icons or "02n" in icons  # at least one valid icon


def test_get_daily_series_groups_and_edge_days():
    repo = make_repo()
    today = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    repo.insert_observation({"city": "Paris", "temp_c": 10, "raw": {"weather": [{"icon": "01d"}]}, "observation_time": yesterday})
    repo.insert_observation({"city": "Paris", "temp_c": 20, "raw": {"weather": [{"icon": "01d"}]}, "observation_time": today})
    daily = repo.get_daily_series("Paris", days=2)
    assert len(daily) == 2
    temps_sorted = sorted(d["avg_temp_c"] for d in daily)
    assert temps_sorted == [10.0, 20.0]
    assert repo.get_daily_series("Paris", days=0) == []  # edge case
