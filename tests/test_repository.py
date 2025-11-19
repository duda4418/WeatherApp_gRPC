from datetime import datetime, timedelta

from db.mongo_repository import MongoRepository
from core.settings import settings

# Assumes local Mongo running via compose on default port.
# Mark test to skip if connection fails quickly.

def test_insert_and_query_observation():
    repo = MongoRepository(settings.MONGO_URI)
    now = datetime.utcnow().replace(microsecond=0)
    _id = repo.insert_observation({
        'city': 'TestCity',
        'provider': 'openweathermap',
        'observation_time': now,
        'fetched_at': now,
        'temp_c': 20.5
    })
    assert _id
    docs = repo.get_observations('TestCity', now - timedelta(minutes=1), now + timedelta(minutes=1))
    assert len(docs) >= 1
    assert any(d['temp_c'] == 20.5 for d in docs)


def test_temperature_series_bucket():
    repo = MongoRepository(settings.MONGO_URI)
    base = datetime.utcnow().replace(second=0, microsecond=0) - timedelta(minutes=30)
    # Insert some synthetic data across 10 minutes
    for i in range(10):
        ts = base + timedelta(minutes=i)
        repo.insert_observation({
            'city': 'SeriesCity',
            'provider': 'openweathermap',
            'observation_time': ts,
            'fetched_at': ts,
            'temp_c': 15 + i
        })
    series = repo.get_temperature_series('SeriesCity', base, base + timedelta(minutes=9), bucket_minutes=5)
    # Expect roughly 2 buckets (0-4,5-9)
    assert len(series) >= 2
    # Ensure timestamps sorted
    stamps = [p['timestamp'] for p in series]
    assert stamps == sorted(stamps)
