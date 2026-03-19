"""Custom middleware: idempotency keys and rate limiting."""
import logging
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

_IDEMPOTENCY_HEADER = "Idempotency-Key"


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    If the client sends an Idempotency-Key header on a mutating request,
    echo it back so the client can detect replayed responses.

    A full implementation would cache and replay responses; this is the
    minimum viable version that passes the header through.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        idem_key = request.headers.get(_IDEMPOTENCY_HEADER)
        if idem_key and request.method in ("POST", "PATCH", "PUT", "DELETE"):
            response.headers[_IDEMPOTENCY_HEADER] = idem_key
        return response


def get_limiter():
    """Return a slowapi Limiter if the library is installed, else None."""
    try:
        from slowapi import Limiter
        from slowapi.util import get_remote_address

        default_limit = os.environ.get("AIBAA_RATE_LIMIT", "60/minute")
        return Limiter(key_func=get_remote_address, default_limits=[default_limit])
    except ImportError:
        logger.info("slowapi not installed — rate limiting disabled")
        return None
