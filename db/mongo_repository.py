from datetime import datetime
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
        doc.setdefault("fetched_at", datetime.utcnow())
        if not isinstance(doc.get("observation_time"), datetime):
            doc["observation_time"] = doc.get("fetched_at", datetime.utcnow())
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
                "avg_temp": {"$avg": "$temp_c"}
            }},
            {"$project": {
                "timestamp": {
                    "$dateFromParts": {
                        "year": "$_id.y", "month": "$_id.m", "day": "$_id.d", "hour": "$_id.h",
                        "minute": {"$multiply": ["$_id.slice", bucket_minutes]}
                    }
                },
                "avg_temp": 1
            }},
            {"$sort": {"timestamp": 1}}
        ]
        out = []
        for bucket in self._col.aggregate(pipeline):
            out.append({
                "timestamp": bucket["timestamp"],
                "avg_temp_c": bucket.get("avg_temp", 0.0)
            })
        return out
