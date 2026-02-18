from fastapi import Request

from src.config import settings

HSTS_MAX_AGE = 31536000


async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = f"max-age={HSTS_MAX_AGE}; includeSubDomains"
    return response
