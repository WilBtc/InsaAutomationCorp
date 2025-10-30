"""
Rate Limiting for INSA CRM API
Prevents brute-force attacks and API abuse
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Custom rate limit exceeded handler
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit errors
    Returns 429 with retry-after header
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.detail
        },
        headers={"Retry-After": str(exc.detail)}
    )
