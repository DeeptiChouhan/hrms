"""Environment-backed settings for tests."""

from __future__ import annotations
import os
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_REPO_ROOT / ".env")
load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
# Password set on first login via invitation accept (new employee).
_pe = os.getenv("NEW_EMPLOYEE_PASSWORD")
NEW_EMPLOYEE_PASSWORD = (_pe.strip() if _pe else "") or "Test@123"
# Optional: force login email if HRMS expects personal_email or a specific alias.
_ne = os.getenv("NEW_EMPLOYEE_LOGIN_EMAIL")
NEW_EMPLOYEE_LOGIN_EMAIL = _ne.strip() if _ne else ""

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
