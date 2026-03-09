"""Rate limiter for API endpoints."""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def get_rate_limit_string() -> str:
    """Return rate limit string from config, e.g. '60/minute'."""
    return f"{settings.rate_limit_per_minute}/minute"


limiter = Limiter(key_func=get_remote_address)
