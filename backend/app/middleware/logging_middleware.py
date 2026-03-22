import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.utils.datetime_utils import now_kst

logger = logging.getLogger("crewspace.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs each request with method, path, status code, and duration."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()
        timestamp = now_kst().strftime("%Y-%m-%d %H:%M:%S %Z")

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        logger.info(
            "[%s] %s %s -> %d (%.2f ms)",
            timestamp,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response
