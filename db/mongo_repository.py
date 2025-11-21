from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any

from pymongo import MongoClient
from pymongo.collection import Collection
from core.settings import settings

MONGO_URI = settings.MONGO_URI
DB_NAME = settings.MONGO_APP_DB
COLLECTION_NAME = "weather_observations"

class MongoRepository:
    def __init__(self, uri: str = MONGO_URI, db_name: str | None = DB_NAME):
        self._client = MongoClient(uri)
        # Fallback if db_name is None
        self._db = self._client[(db_name or "weatherdb")]
        self._col: Collection = self._db[COLLECTION_NAME]

    def insert_observation(self, doc: Dict[str, Any]) -> str:
        # Ensure required fields
        doc.setdefault("fetched_at", datetime.now(UTC))
        if not isinstance(doc.get("observation_time"), datetime):
            doc["observation_time"] = doc.get("fetched_at", datetime.now(UTC))
        res = self._col.insert_one(doc)
        return str(res.inserted_id)

    def get_observations(self, city: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        cursor = self._col.find({
            "city": city,
            "observation_time": {"$gte": start, "$lte": end}
        }).sort("observation_time", 1)
        return list(cursor)

    def get_temperature_series(self, city: str, start: datetime, end: datetime, bucket_minutes: int = 5) -> List[Dict[str, Any]]:
        # Aggregation pipeline to bucket by N minutes and average temperature
        pipeline = [
            {"$match": {"city": city, "observation_time": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": {
                    "y": {"$year": "$observation_time"},
                    "m": {"$month": "$observation_time"},
                    "d": {"$dayOfMonth": "$observation_time"},
                    "h": {"$hour": "$observation_time"},
                    "slice": {"$floor": {"$divide": [{"$minute": "$observation_time"}, bucket_minutes]}}
                },
                "avg_temp": {"$avg": "$temp_c"},
                "first_icon": {"$first": "$raw.weather.0.icon"}
            }},
            {"$project": {
                "timestamp": {
                    "$dateFromParts": {
                        "year": "$_id.y", "month": "$_id.m", "day": "$_id.d", "hour": "$_id.h",
                        "minute": {"$multiply": ["$_id.slice", bucket_minutes]}
                    }
                },
                "avg_temp": 1,
                "first_icon": 1
            }},
            {"$sort": {"timestamp": 1}}
        ]
        out = []
        for bucket in self._col.aggregate(pipeline):
            icon_raw = bucket.get("first_icon")
            if isinstance(icon_raw, list):
                icon_raw = icon_raw[0] if icon_raw else None
            elif not isinstance(icon_raw, str):
                icon_raw = None
            out.append({
                "timestamp": bucket["timestamp"],
                "avg_temp_c": bucket.get("avg_temp", 0.0),
                "icon": icon_raw
            })
        return out

    def get_daily_series(self, city: str, days: int) -> List[Dict[str, Any]]:
        """Return average temperature per day for the last `days` days (inclusive of today).

        Groups observations by calendar day (UTC) and computes average `temp_c`.
        """
        if days < 1:
            return []
        end = datetime.now(UTC)
        start = end.replace(hour=0, minute=0, second=0, microsecond=0)  # today 00:00
        start = start - timedelta(days=days - 1)
        pipeline = [
            {"$match": {"city": city, "observation_time": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": {
                    "y": {"$year": "$observation_time"},
                    "m": {"$month": "$observation_time"},
                    "d": {"$dayOfMonth": "$observation_time"},
                },
                "avg_temp": {"$avg": "$temp_c"},
                "first_ts": {"$min": "$observation_time"},
                "first_icon": {"$first": "$raw.weather.0.icon"}
            }},
            {"$project": {
                "day_start": {"$dateFromParts": {"year": "$_id.y", "month": "$_id.m", "day": "$_id.d"}},
                "avg_temp": 1,
                "first_ts": 1,
                "first_icon": 1
            }},
            {"$sort": {"day_start": 1}}
        ]
        out: List[Dict[str, Any]] = []
        for doc in self._col.aggregate(pipeline):
            icon_raw = doc.get("first_icon")
            if isinstance(icon_raw, list):
                icon_raw = icon_raw[0] if icon_raw else None
            elif not isinstance(icon_raw, str):
                icon_raw = None
            out.append({
                "date": doc["day_start"].date().isoformat(),
                "avg_temp_c": doc.get("avg_temp", 0.0),
                "icon": icon_raw
            })
        return out

    def get_latest_observation(self, city: str) -> Dict[str, Any] | None:
        """Return the most recent raw observation document for a city.

        The server stores a `raw` field containing the upstream OpenWeather payload.
        This method surfaces the whole document so the API layer can extract
        extended metrics (pressure, humidity, wind, sunrise/sunset, etc.).
        """
        doc = self._col.find_one({"city": city}, sort=[("observation_time", -1)])
        return doc
