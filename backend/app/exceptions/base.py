class PlanshipException(Exception):
    """Base exception for the Planship application."""

    def __init__(self, status_code: int = 500, detail: str = "An error occurred") -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class NotFoundException(PlanshipException):
    """Resource not found (404)."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(status_code=404, detail=detail)


class ForbiddenException(PlanshipException):
    """Access forbidden (403)."""

    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(status_code=403, detail=detail)


class BadRequestException(PlanshipException):
    """Bad request (400)."""

    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(status_code=400, detail=detail)


class UnauthorizedException(PlanshipException):
    """Unauthorized access (401)."""

    def __init__(self, detail: str = "Unauthorized") -> None:
        super().__init__(status_code=401, detail=detail)


class ConflictException(PlanshipException):
    """Conflict (409)."""

    def __init__(self, detail: str = "Conflict") -> None:
        super().__init__(status_code=409, detail=detail)
