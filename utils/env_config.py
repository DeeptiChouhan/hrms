"""Environment-backed settings for tests."""

from __future__ import annotations
import os
from dotenv import load_dotenv
load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def _parse_optional_bool(raw: str | None) -> bool | None:
    """Return True/False when the env var is set to a known token; None if unset or blank."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    low = s.lower()
    if low in ("true", "1", "yes"):
        return True
    if low in ("false", "0", "no"):
        return False
    return None


def get_headless_value() -> bool:
    """
    Chromium headless flag for Playwright.

    - ``HEADLESS`` when set: explicit true/false (also ``1``/``0``, ``yes``/``no``).
    - GitHub Actions: ``GITHUB_ACTIONS=true`` → headless (no display on runners).
    - Local default: headed (``False``) for easier debugging.
    """
    override = _parse_optional_bool(os.getenv("HEADLESS"))
    if override is not None:
        return override
    if os.getenv("GITHUB_ACTIONS", "").strip().lower() == "true":
        return True
    return False
