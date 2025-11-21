import grpc
import pytest
from weather_service.interceptors import ApiKeyInterceptor


class DummyHandlerCallDetails:
    def __init__(self, metadata):
        self.invocation_metadata = metadata


def test_interceptor_rejects_bad_key():
    interceptor = ApiKeyInterceptor(expected_key="good")
    def cont(details):
        return "ok"
    details = DummyHandlerCallDetails([("x-api-key", "bad")])
    handler = interceptor.intercept_service(cont, details)
    # Returns a handler that will abort; simulate call
    class DummyContext:
        def __init__(self):
            self.aborted = False
        def abort(self, code, message):
            self.aborted = True
            raise RuntimeError("aborted")
    with pytest.raises(RuntimeError):
        handler.unary_unary(None, DummyContext())  # type: ignore[attr-defined]


def test_interceptor_allows_good_key():
    interceptor = ApiKeyInterceptor(expected_key="good")
    def cont(details):
        return "ok"
    details = DummyHandlerCallDetails([("x-api-key", "good")])
    out = interceptor.intercept_service(cont, details)
    assert out == "ok"
