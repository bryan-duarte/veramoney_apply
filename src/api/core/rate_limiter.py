from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import settings


def get_rate_limit_key(request: Request) -> str:
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)
