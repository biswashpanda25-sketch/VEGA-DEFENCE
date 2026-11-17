"""Failed-authentication throttling.

Only *failed* attempts are counted: a brute-force limiter that also punishes successful logins would
lock out legitimate operators during busy periods. State is in-process, which is correct for a single
node; a multi-node deployment must use Redis (documented in KNOWN_ISSUES).
"""
import os
import time

WINDOW_S = 60
MAX_FAILURES = int(os.getenv("LOGIN_MAX_FAILURES_PER_MIN", "20"))

_failures: dict[str, list[float]] = {}


def is_throttled(key: str) -> bool:
    now = time.time()
    stamps = [t for t in _failures.get(key, []) if now - t < WINDOW_S]
    _failures[key] = stamps
    return len(stamps) >= MAX_FAILURES


def record_failure(key: str) -> None:
    _failures.setdefault(key, []).append(time.time())


def clear(key: str) -> None:
    _failures.pop(key, None)
