"""Resolve HRMS ``/invitation/accept/<token>`` from env, Gmail API, or Mailinator."""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import Page

_REPO_ROOT = Path(__file__).resolve().parent.parent

import utils.env_config  # noqa: F401 — load repo-root `.env` before invite `os.getenv` calls


def _invite_test_config() -> dict[str, Any]:
    try:
        from utils.data_reader import load_config

        raw = load_config()
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _merged_invitation_accept_url() -> str:
    v = os.getenv("INVITATION_ACCEPT_URL", "").strip()
    if v:
        return v
    return str(_invite_test_config().get("invitation_accept_url") or "").strip()


def merged_gmail_oauth_paths() -> tuple[str, str]:
    cfg = _invite_test_config()
    c = os.getenv("GOOGLE_GMAIL_CREDENTIALS", "").strip() or str(
        cfg.get("google_gmail_credentials") or ""
    ).strip()
    t = os.getenv("GOOGLE_GMAIL_TOKEN", "").strip() or str(cfg.get("google_gmail_token") or "").strip()
    if not c:
        default_c = _REPO_ROOT / "credentials.json"
        if default_c.is_file():
            c = str(default_c)
    if not t:
        default_t = _REPO_ROOT / "gmail_token.json"
        if default_t.is_file():
            t = str(default_t)
    return c, t


def _merged_mailinator_local() -> str:
    v = os.getenv("MAILINATOR_INBOX_LOCAL", "").strip()
    if v:
        return v
    return str(_invite_test_config().get("mailinator_inbox_local") or "").strip()


MAILINATOR_INBOX_URL = "https://www.mailinator.com/v4/public/inboxes.jsp"


def _invite_href_regex(app_base_url: str) -> re.Pattern[str]:
    host = urlparse(app_base_url).netloc
    return re.compile(
        rf"https://{re.escape(host)}/invitation/accept/[A-Za-z0-9._~=-]+",
        re.I,
    )


def find_invitation_accept_url_in_text(app_base_url: str, text: str) -> str | None:
    m = _invite_href_regex(app_base_url).search(text)
    return m.group(0) if m else None


def invite_resolution_configured() -> bool:
    """True when invite URL can be resolved (``.env``, ``config.json``, or Mailinator)."""
    if _merged_invitation_accept_url():
        return True
    gc, gt = merged_gmail_oauth_paths()
    if gc and gt:
        from utils.google_api_helper import gmail_oauth_paths_ok

        return gmail_oauth_paths_ok(gc, gt)
    return bool(_merged_mailinator_local())


def _invite_hints_tuple(hints: Sequence[str] | None) -> tuple[str, ...]:
    if not hints:
        return ()
    return tuple(s.strip() for s in hints if (s or "").strip())


def _html_matches_invite_hints(html: str, hints: tuple[str, ...]) -> bool:
    if not hints:
        return True
    low = html.lower()
    return any(h.lower() in low for h in hints)


def resolve_invitation_accept_url(
    page: Page,
    *,
    app_base_url: str,
    mailinator_inbox_local: str | None = None,
    timeout_s: int = 120,
    invite_link_hints: Sequence[str] | None = None,
) -> str:
    """Resolve URL: INVITATION_ACCEPT_URL, else Gmail OAuth files, else Mailinator."""
    hints_tuple = _invite_hints_tuple(invite_link_hints)
    explicit = _merged_invitation_accept_url()
    if explicit:
        return explicit

    _gc, _gt = merged_gmail_oauth_paths()
    if _gc and _gt:
        from utils.google_api_helper import (
            fetch_invitation_accept_url_from_gmail,
            gmail_oauth_paths_ok,
        )

        if gmail_oauth_paths_ok(_gc, _gt):
            return fetch_invitation_accept_url_from_gmail(
                app_base_url,
                credentials_path=_gc,
                token_path=_gt,
                timeout_s=timeout_s,
                invite_link_hints=hints_tuple if hints_tuple else None,
            )

    local = (mailinator_inbox_local or _merged_mailinator_local()).strip()
    if not local:
        raise RuntimeError(
            "Invitation link is required: set INVITATION_ACCEPT_URL (or "
            "invitation_accept_url in config.json), or Gmail paths in env/config, "
            "or MAILINATOR_INBOX_LOCAL / mailinator_inbox_local in config.json. "
            "See utils/google_api_helper.py for Gmail OAuth."
        )

    rx = _invite_href_regex(app_base_url)
    inbox_url = f"{MAILINATOR_INBOX_URL}?to={local}"
    deadline = time.monotonic() + timeout_s

    while time.monotonic() < deadline:
        page.goto(inbox_url, wait_until="domcontentloaded")
        page.wait_for_timeout(4_000)
        html = page.content()
        if not _html_matches_invite_hints(html, hints_tuple):
            page.wait_for_timeout(3_000)
            continue
        matches = list(rx.finditer(html))
        if matches:
            chosen = matches[-1] if hints_tuple else matches[0]
            return chosen.group(0)

        rows = page.locator("table tbody tr").filter(has=page.locator("td"))
        if rows.count() > 0:
            try:
                rows.first.click(timeout=5_000)
                page.wait_for_timeout(3_000)
                inner = page.content()
                if not _html_matches_invite_hints(inner, hints_tuple):
                    pass
                else:
                    row_matches = list(rx.finditer(inner))
                    if row_matches:
                        chosen = row_matches[-1] if hints_tuple else row_matches[0]
                        return chosen.group(0)
            except Exception:
                pass

        page.wait_for_timeout(3_000)

    raise TimeoutError(
        f"No invitation link found in Mailinator inbox {local!r} within {timeout_s}s. "
        "Use INVITATION_ACCEPT_URL, Gmail (GOOGLE_GMAIL_*), or check the inbox."
    )
