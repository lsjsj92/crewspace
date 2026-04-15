# backend/app/middleware/cache_control.py
# API 응답 브라우저 캐싱 방지 미들웨어

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """모든 API 응답에 Cache-Control: no-store 헤더를 추가한다."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response
