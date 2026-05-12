import os
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def get_headless_value() -> bool:
    """
    Browser headless mode.

    - Set ``HEADLESS=true|false`` (or ``1``/``0``, ``yes``/``no``) to override any default.
    - On GitHub Actions, ``GITHUB_ACTIONS`` is set → default ``headless=True`` (no display).
    - Locally (no override), default ``headless=False`` so you see the browser.
    """
    raw = os.getenv("HEADLESS")
    if raw is not None and str(raw).strip() != "":
        return str(raw).strip().lower() in ("true", "1", "yes")

    if os.getenv("GITHUB_ACTIONS", "").strip().lower() == "true":
        return True

    return False