from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


async def with_retries[T](
    operation: Callable[[], Awaitable[T]],
    *,
    retries: int = 3,
    timeout_seconds: float = 30.0,
) -> T:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            return await asyncio.wait_for(operation(), timeout=timeout_seconds)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == retries - 1:
                break
            await asyncio.sleep(2**attempt)
    assert last_error is not None
    raise last_error
