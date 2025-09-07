"""
Simple dynamic settings helpers.
Read environment variables at call time to support tests that toggle flags.
"""

from __future__ import annotations

import os
from typing import Any, Optional


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(key, default)


def get_flag(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return bool(default)
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except Exception:
        return default


def get_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except Exception:
        return default


def get_list(key: str, default: list[str] | None = None, sep: str = ",") -> list[str]:
    raw = os.getenv(key)
    if not raw:
        return default or []
    return [item.strip() for item in raw.split(sep) if item.strip()]
