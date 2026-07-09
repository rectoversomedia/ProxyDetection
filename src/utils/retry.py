"""Retry logic with exponential backoff."""

from __future__ import annotations

import asyncio
import functools
from typing import Any, Callable, Optional, Type, TypeVar, Union

from tenacity import (
    AsyncRetrying,
    RetryCallState,
    Retrying,
    RetryError,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from .logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    multiplier: float = 2.0,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
    on_retry: Optional[Callable[[Exception], None]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying synchronous functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
        multiplier: Exponential multiplier for wait time
        exceptions: Exception types to catch and retry
        on_retry: Optional callback function called on each retry

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            retryer = Retrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(
                    min=min_wait,
                    max=max_wait,
                    multiplier=multiplier,
                ),
                reraise=True,
                before_sleep=before_sleep_log(logger, logging.WARNING),
            )

            for attempt in retryer:
                try:
                    return attempt(func, *args, **kwargs)
                except exceptions as e:
                    if on_retry:
                        on_retry(e)
                    raise

        return wrapper
    return decorator


async def async_retry_with_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    multiplier: float = 2.0,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
    on_retry: Optional[Callable[[Exception], None]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
        multiplier: Exponential multiplier for wait time
        exceptions: Exception types to catch and retry
        on_retry: Optional callback function called on each retry

    Returns:
        Decorated async function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(
                    min=min_wait,
                    max=max_wait,
                    multiplier=multiplier,
                ),
                reraise=True,
                before_sleep=before_sleep_log(logger, logging.WARNING),
            ):
                with attempt:
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        if on_retry:
                            on_retry(e)
                        raise

        return wrapper
    return decorator


def log_retry(retry_state: RetryCallState) -> None:
    """Log retry attempts."""
    if retry_state.outcome and retry_state.outcome.failed:
        exc = retry_state.outcome.exception()
        attempt = retry_state.attempt_number
        logger.warning(
            f"Retry attempt {attempt} failed: {exc}",
            exc_info=True,
        )
