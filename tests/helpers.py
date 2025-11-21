import grpc
import requests

class DummyContext:
    def __init__(self):
        self.aborted = None
    def abort(self, code, message):
        self.aborted = (code, message)
        raise RuntimeError(f"aborted: {code} {message}")


class RepoOK:
    def __init__(self):
        self.inserted = []
    def insert_observation(self, doc):
        self.inserted.append(doc)
        return "id"

class FakeRepo:
    def __init__(self):
        self.inserted = []
    def insert_observation(self, doc):
        self.inserted.append(doc)
        return "id"

class RepoPersistFail:
    def insert_observation(self, doc):
        raise RuntimeError("db down")

class FakeProvider:
    def __init__(self, data=None, error=None):
        self._data = data
        self._error = error
    def get_current(self, city):
        if self._error:
            raise self._error
        return self._data or {
            "name": city,
            "main": {"temp": 11.1, "humidity": 50},
            "weather": [{"description": "few clouds"}],
            "wind": {"speed": 2.5},
        }

def make_provider(data=None, error=None):
    class P:
        def get_current(self, city):
            if error:
                raise error
            return data or {
                "name": city,
                "main": {"temp": 1.23, "humidity": 40},
                "weather": [{"description": "scattered clouds"}],
                "wind": {"speed": 1.1},
            }
    return P()

class DummyHandlerCallDetails:
    def __init__(self, metadata):
        self.invocation_metadata = metadata

class DummyResp:
    def __init__(self, status_code=200, json_data=None, json_error=False):
        self.status_code = status_code
        self._json_data = json_data or {"main": {"temp": 10}, "weather": [{}]}
        self._json_error = json_error
    def json(self):
        if self._json_error:
            raise ValueError("bad json")
        return self._json_data

class DummyResponse:
    def __init__(self, status_code=200, json_data=None, raise_json=False):
        self.status_code = status_code
        self._json = json_data or {}
        self._raise_json = raise_json
    def json(self):
        if self._raise_json:
            raise ValueError("bad json")
        return self._json
