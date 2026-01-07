from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

from rich.console import Console

console = Console()

T = TypeVar("T")


class GhAutomationError(RuntimeError):
    """Base exception for this tool."""


class ConfigError(GhAutomationError):
    pass


class ValidationError(GhAutomationError):
    pass


class ApiError(GhAutomationError):
    pass


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 4
    base_delay_s: float = 0.8
    max_delay_s: float = 8.0


def backoff_sleep(attempt: int, cfg: RetryConfig) -> None:
    delay = min(cfg.max_delay_s, cfg.base_delay_s * (2 ** (attempt - 1)))
    time.sleep(delay)


def retry(
    fn: Callable[[], T],
    *,
    retry_on: tuple[type[Exception], ...],
    cfg: RetryConfig = RetryConfig(),
) -> T:
    last_exc: Exception | None = None
    for attempt in range(1, cfg.max_attempts + 1):
        try:
            return fn()
        except retry_on as e:  # type: ignore[misc]
            last_exc = e
            if attempt == cfg.max_attempts:
                raise
            backoff_sleep(attempt, cfg)
    assert last_exc is not None
    raise last_exc
