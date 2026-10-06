"""
limiter.py - Shared rate limiting configuration using slowapi.
"""

import os

from fastapi import Request
from slowapi import Limiter


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address.
    Honors X-Forwarded-For ONLY when TRUSTED_PROXY=true to prevent IP spoofing.
    """
    trusted_proxy = os.getenv("TRUSTED_PROXY", "false").lower() in ("true", "1", "yes")
    if trusted_proxy:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else "127.0.0.1"


limiter = Limiter(key_func=get_client_ip, default_limits=["30/minute"])
