"""Pytest configuration: environment setup and common fixtures.

Note: File intentionally named `confest.py` originally; kept but now populated.
Recommended to rename to `conftest.py` for Pytest auto-discovery. Keeping name
as-is to avoid unintended user workflow impact. If coverage collection misses
fixtures, rename this file.
"""

import os
import sys
import types
import grpc
import threading
from pathlib import Path
from concurrent import futures


def pytest_configure():  # executed before tests collected
	# Provide required environment variables for settings initialization.
	os.environ.setdefault("OPENWEATHER_API_KEY", "test-key")
	os.environ.setdefault("GRPC_API_KEY", "test-grpc")
	os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
	os.environ.setdefault("MONGO_APP_DB", "weatherdb_test")
	os.environ.setdefault("GRPC_PORT", "50051")
	os.environ.setdefault("GRPC_ADDRESS", "localhost")
	os.environ.setdefault("OPENWEATHER_URL", "https://api.example.com/weather")

	# Ensure project root is on sys.path for direct package imports (db, proto, weather_service)
	root = Path(__file__).resolve().parent.parent
	if str(root) not in sys.path:
		sys.path.insert(0, str(root))


class FakeCollection:
	def __init__(self):
		self.docs = []

	# Mongo insert_one simulation
	def insert_one(self, doc):
		doc = dict(doc)
		doc.setdefault("_id", f"id{len(self.docs)+1}")
		self.docs.append(doc)
		return types.SimpleNamespace(inserted_id=doc["_id"])

	def find(self, query):
		city = query.get("city")
		start = query.get("observation_time", {}).get("$gte")
		end = query.get("observation_time", {}).get("$lte")
		result = [d for d in self.docs if d.get("city") == city and start <= d.get("observation_time") <= end]
		class Cursor(list):
			def sort(self, key, direction):
				return Cursor(sorted(self, key=lambda x: x.get(key)))
		return Cursor(result)

	def aggregate(self, pipeline):  # very simplified: return precomputed buckets
		# Recognize temperature series pipeline by presence of $group slice
		if any("slice" in (stage.get("$group", {}).get("_id", {})) for stage in pipeline):
			# Return one bucket with timestamp field mimic
			return [
				{
					"timestamp": self.docs[0]["observation_time"],
					"avg_temp": self.docs[0].get("temp_c", 0),
					"first_icon": "01d",
				}
			] if self.docs else []
		# Daily series: produce a doc per unique date
		days = {}
		for d in self.docs:
			key = d["observation_time"].date()
			days.setdefault(key, []).append(d.get("temp_c", 0))
		out = []
		for day, temps in sorted(days.items()):
			out.append({
				"day_start": day,  # will be processed into iso in repo
				"avg_temp": sum(temps) / len(temps) if temps else 0,
				"first_icon": "01d",
			})
		return out

	def find_one(self, query, sort=None):
		city = query.get("city")
		relevant = [d for d in self.docs if d.get("city") == city]
		if not relevant:
			return None
		# Sort descending by observation_time if requested
		return sorted(relevant, key=lambda x: x.get("observation_time"), reverse=True)[0]


def fake_repo_with_collection(repo_cls):
	repo = repo_cls("mongodb://ignored")
	repo._col = FakeCollection()  # type: ignore[attr-defined]
	return repo


def start_test_grpc_server(servicer, add_fn, api_key: str):
	server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
	add_fn(servicer, server)
	port = server.add_insecure_port("[::]:0")
	server.start()
	return server, port

