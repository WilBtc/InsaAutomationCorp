"""
Admin API routes for rate limit management.

This module provides endpoints for monitoring and managing rate limits,
including viewing status, resetting limits, and identifying abusers.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.core.rate_limiter import RateLimiter, TimeWindow, DEFAULT_RATE_LIMITS
from app.core.auth import require_role, UserRole, get_current_user
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/admin/rate-limits", tags=["Rate Limits - Admin"])


# Pydantic models
class RateLimitStatus(BaseModel):
    """Rate limit status for a single window."""

    window: str = Field(..., description="Time window (second, minute, hour, day)")
    limit: int = Field(..., description="Maximum requests allowed")
    remaining: int = Field(..., description="Remaining requests")
    reset_at: int = Field(..., description="Unix timestamp when limit resets")
    usage_percent: float = Field(..., description="Percentage of limit used")


class UserRateLimitStatus(BaseModel):
    """Complete rate limit status for a user."""

    user_id: str = Field(..., description="User identifier")
    role: str = Field(..., description="User role")
    limits: Dict[str, RateLimitStatus] = Field(..., description="Status per time window")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RateLimitAbuser(BaseModel):
    """User with excessive rate limit violations."""

    user_id: str = Field(..., description="User identifier")
    tokens_remaining: float = Field(..., description="Remaining tokens")
    usage_percent: float = Field(..., description="Usage percentage")
    window: str = Field(..., description="Time window analyzed")


class RateLimitConfiguration(BaseModel):
    """Rate limit configuration."""

    role: str = Field(..., description="Role to configure")
    window: str = Field(..., description="Time window")
    limit: int = Field(..., ge=1, description="New rate limit")


class RateLimitConfigurationResponse(BaseModel):
    """Response for configuration update."""

    success: bool = Field(..., description="Whether update was successful")
    message: str = Field(..., description="Result message")
    configuration: Dict[str, Any] = Field(..., description="Updated configuration")


class ResetLimitRequest(BaseModel):
    """Request to reset user rate limits."""

    user_id: str = Field(..., description="User ID to reset")
    windows: Optional[List[str]] = Field(None, description="Specific windows to reset (default: all)")


class ResetLimitResponse(BaseModel):
    """Response for rate limit reset."""

    success: bool = Field(..., description="Whether reset was successful")
    user_id: str = Field(..., description="User ID")
    keys_deleted: int = Field(..., description="Number of Redis keys deleted")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GlobalRateLimitStats(BaseModel):
    """Global rate limit statistics."""

    total_users_tracked: int = Field(..., description="Total users being tracked")
    global_limit: Dict[str, Any] = Field(..., description="Global rate limit configuration")
    top_consumers: List[RateLimitAbuser] = Field(..., description="Top rate limit consumers")
    role_configurations: Dict[str, Dict[str, int]] = Field(..., description="Rate limits per role")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Dependency to get rate limiter (will be injected by app)
async def get_rate_limiter() -> RateLimiter:
    """
    Get RateLimiter instance from app state.

    This should be overridden in the main app to inject the actual limiter.
    """
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Rate limiter not initialized"
    )


@router.get(
    "/status",
    response_model=GlobalRateLimitStats,
    summary="Get global rate limit statistics",
    description="Get comprehensive rate limit statistics including top consumers and configurations"
)
async def get_rate_limit_stats(
    current_user: dict = Depends(get_current_user),
    limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Get global rate limit statistics.

    Requires admin role.
    """
    # Verify admin role
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )

    try:
        # Get top consumers
        top_consumers = await limiter.get_top_consumers(limit=10)

        # Convert to response model
        abusers = [
            RateLimitAbuser(
                user_id=consumer["user_id"],
                tokens_remaining=consumer["tokens_remaining"],
                usage_percent=0.0,  # Calculate if limit known
                window="minute"
            )
            for consumer in top_consumers
        ]

        # Count total tracked users (approximate)
        # In production, might want to maintain a separate counter
        total_users = len(top_consumers)

        # Build response
        return GlobalRateLimitStats(
            total_users_tracked=total_users,
            global_limit={
                "limit": 10000,
                "window": "minute",
                "burst_multiplier": 1.5
            },
            top_consumers=abusers,
            role_configurations={
                role: {window.value: limit for window, limit in limits.items()}
                for role, limits in DEFAULT_RATE_LIMITS.items()
            }
        )

    except Exception as e:
        logger.error(f"Failed to get rate limit stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.get(
    "/status/{user_id}",
    response_model=UserRateLimitStatus,
    summary="Get rate limit status for specific user",
    description="Get detailed rate limit status for a specific user across all time windows"
)
async def get_user_rate_limit_status(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Get rate limit status for a specific user.

    Requires admin role or self (users can check their own status).
    """
    # Verify authorization
    if (current_user.get("role") != UserRole.ADMIN.value and
        str(current_user.get("user_id")) != user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    try:
        # Get user's role (in production, query from database)
        # For now, use the current user's role if checking self
        role = current_user.get("role", "viewer")

        # Get status from rate limiter
        status_dict = await limiter.get_user_status(user_id, role)

        # Convert to response model
        limits = {
            window: RateLimitStatus(
                window=window,
                limit=data["limit"],
                remaining=data["remaining"],
                reset_at=data["reset_at"],
                usage_percent=data["usage_percent"]
            )
            for window, data in status_dict.items()
        }

        return UserRateLimitStatus(
            user_id=user_id,
            role=role,
            limits=limits
        )

    except Exception as e:
        logger.error(f"Failed to get user rate limit status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user status: {str(e)}"
        )


@router.get(
    "/abusers",
    response_model=List[RateLimitAbuser],
    summary="Get top rate limit violators",
    description="Identify users with highest rate limit usage (potential abusers)"
)
async def get_rate_limit_abusers(
    limit: int = Query(10, ge=1, le=100, description="Number of top abusers to return"),
    window: str = Query("minute", description="Time window to analyze"),
    current_user: dict = Depends(get_current_user),
    limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Get top rate limit abusers.

    Requires admin role.
    """
    # Verify admin role
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )

    try:
        # Validate window
        try:
            time_window = TimeWindow(window.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid window: {window}. Must be one of: second, minute, hour, day"
            )

        # Get top consumers
        consumers = await limiter.get_top_consumers(limit=limit, window=time_window)

        # Convert to response model
        abusers = [
            RateLimitAbuser(
                user_id=consumer["user_id"],
                tokens_remaining=consumer["tokens_remaining"],
                usage_percent=0.0,  # Calculate if limit known
                window=window
            )
            for consumer in consumers
        ]

        logger.info(
            f"Retrieved {len(abusers)} rate limit abusers",
            extra={"window": window, "limit": limit}
        )

        return abusers

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rate limit abusers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve abusers: {str(e)}"
        )


@router.post(
    "/reset/{user_id}",
    response_model=ResetLimitResponse,
    summary="Reset rate limits for a user",
    description="Reset all rate limits for a specific user (admin only)"
)
async def reset_user_rate_limits(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Reset all rate limits for a user.

    Requires admin role.
    """
    # Verify admin role
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )

    try:
        # Reset limits
        keys_deleted = await limiter.reset_user_limits(user_id)

        logger.info(
            f"Reset rate limits for user {user_id}",
            extra={
                "user_id": user_id,
                "keys_deleted": keys_deleted,
                "admin_user": current_user.get("user_id")
            }
        )

        return ResetLimitResponse(
            success=True,
            user_id=user_id,
            keys_deleted=keys_deleted
        )

    except Exception as e:
        logger.error(f"Failed to reset user rate limits: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset limits: {str(e)}"
        )


@router.put(
    "/configure",
    response_model=RateLimitConfigurationResponse,
    summary="Update rate limit configuration",
    description="Update rate limit configuration for a specific role and window (super-admin only)"
)
async def update_rate_limit_configuration(
    config: RateLimitConfiguration,
    current_user: dict = Depends(get_current_user),
    limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Update rate limit configuration.

    Requires super-admin role (admin + special permission).
    In production, this would modify the configuration and reload the limiter.
    """
    # Verify super-admin role
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )

    # Additional super-admin check
    if not current_user.get("is_super_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super-admin privileges required to modify rate limit configuration"
        )

    try:
        # Validate role
        if config.role not in DEFAULT_RATE_LIMITS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {config.role}. Must be one of: {list(DEFAULT_RATE_LIMITS.keys())}"
            )

        # Validate window
        try:
            time_window = TimeWindow(config.window.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid window: {config.window}. Must be one of: second, minute, hour, day"
            )

        # In production, this would:
        # 1. Update configuration in database
        # 2. Reload rate limiter with new configuration
        # 3. Broadcast update to all workers (if distributed)

        # For now, just update in-memory configuration
        limiter.default_limits[config.role][time_window] = config.limit

        logger.warning(
            f"Rate limit configuration updated",
            extra={
                "role": config.role,
                "window": config.window,
                "new_limit": config.limit,
                "admin_user": current_user.get("user_id")
            }
        )

        return RateLimitConfigurationResponse(
            success=True,
            message=f"Updated {config.role} rate limit for {config.window} to {config.limit}",
            configuration={
                "role": config.role,
                "window": config.window,
                "limit": config.limit,
                "updated_at": datetime.utcnow().isoformat(),
                "updated_by": current_user.get("username")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update rate limit configuration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.get(
    "/configuration",
    response_model=Dict[str, Dict[str, int]],
    summary="Get current rate limit configuration",
    description="Get current rate limit configuration for all roles"
)
async def get_rate_limit_configuration(
    current_user: dict = Depends(get_current_user),
    limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Get current rate limit configuration.

    Requires admin role.
    """
    # Verify admin role
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )

    try:
        # Build configuration response
        config = {
            role: {window.value: limit for window, limit in limits.items()}
            for role, limits in limiter.default_limits.items()
        }

        return config

    except Exception as e:
        logger.error(f"Failed to get rate limit configuration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configuration: {str(e)}"
        )
