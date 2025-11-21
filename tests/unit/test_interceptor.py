
import pytest
from weather_service.interceptors import ApiKeyInterceptor
from tests.helpers import DummyHandlerCallDetails, DummyContext


def test_interceptor_rejects_bad_key():
    interceptor = ApiKeyInterceptor(expected_key="good")
    def cont(details):
        return "ok"
    details = DummyHandlerCallDetails([("x-api-key", "bad")])
    handler = interceptor.intercept_service(cont, details)
    with pytest.raises(RuntimeError):
        handler.unary_unary(None, DummyContext())  # type: ignore[attr-defined]


def test_interceptor_allows_good_key():
    interceptor = ApiKeyInterceptor(expected_key="good")
    def cont(details):
        return "ok"
    details = DummyHandlerCallDetails([("x-api-key", "good")])
    out = interceptor.intercept_service(cont, details)
    assert out == "ok"
