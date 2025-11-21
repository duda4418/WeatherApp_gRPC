"""gRPC server interceptors for Weather service."""

import grpc
from core.settings import settings


class ApiKeyInterceptor(grpc.ServerInterceptor):
    """Simple metadata-based API key authentication interceptor."""

    def __init__(self, *, expected_key: str | None = None):
        self._expected = expected_key or settings.GRPC_API_KEY

    def intercept_service(self, continuation, handler_call_details):  # noqa: D401
        meta = dict(handler_call_details.invocation_metadata)
        if meta.get("x-api-key") != self._expected:
            def unary_unauthed(request, context):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid API key")
            return grpc.unary_unary_rpc_method_handler(unary_unauthed)
        return continuation(handler_call_details)
