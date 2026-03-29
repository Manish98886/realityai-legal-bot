import asyncio
import logging
import functools

import httpx
from telegram.error import TimedOut

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
BASE_BACKOFF = 1  # seconds; doubles each attempt: 1, 2, 4, 8, 16


def with_retry(func):
    """
    Async decorator that retries a coroutine on TimedOut / httpx.ReadTimeout
    using exponential backoff (1s, 2s, 4s, 8s, 16s). After MAX_RETRIES
    exhausted the exception is re-raised so the caller can decide what to do.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        delay = BASE_BACKOFF
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await func(*args, **kwargs)
            except (TimedOut, httpx.ReadTimeout, httpx.ConnectTimeout) as exc:
                if attempt == MAX_RETRIES:
                    logger.error(
                        "Max retries (%d) reached for %s. Last error: %s",
                        MAX_RETRIES,
                        func.__name__,
                        exc,
                    )
                    raise
                logger.warning(
                    "Timeout in %s (attempt %d/%d): %s — retrying in %ds…",
                    func.__name__,
                    attempt,
                    MAX_RETRIES,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
                delay *= 2
    return wrapper


async def run_with_retry(coro_factory, label: str = "task"):
    """
    Call ``coro_factory()`` (a zero-argument callable that returns a coroutine)
    and retry on timeout errors with exponential backoff.

    Example::

        await run_with_retry(lambda: app.run_polling(...), label="run_polling")
    """
    delay = BASE_BACKOFF
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await coro_factory()
        except (TimedOut, httpx.ReadTimeout, httpx.ConnectTimeout) as exc:
            if attempt == MAX_RETRIES:
                logger.error(
                    "Max retries (%d) reached for '%s'. Last error: %s",
                    MAX_RETRIES,
                    label,
                    exc,
                )
                raise
            logger.warning(
                "Timeout in '%s' (attempt %d/%d): %s — retrying in %ds…",
                label,
                attempt,
                MAX_RETRIES,
                exc,
                delay,
            )
            await asyncio.sleep(delay)
            delay *= 2
