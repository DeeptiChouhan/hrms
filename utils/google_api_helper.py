"""Gmail API: read-only inbox access to find HRMS invitation accept URLs."""

from __future__ import annotations

import argparse
import base64
import os
import sys
import time
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from utils.invitation_link import find_invitation_accept_url_in_text

GMAIL_SCOPES = ("https://www.googleapis.com/auth/gmail.readonly",)


def gmail_oauth_paths_ok(credentials_path: str, token_path: str) -> bool:
    c, t = credentials_path.strip(), token_path.strip()
    if not c or not t:
        return False
    return Path(c).is_file() and Path(t).is_file()


def gmail_oauth_paths_configured() -> bool:
    from utils.invitation_link import merged_gmail_oauth_paths

    return gmail_oauth_paths_ok(*merged_gmail_oauth_paths())


def _pad_b64(data: str) -> str:
    pad = len(data) % 4
    return data + ("=" * (4 - pad) if pad else "")


def _decode_body_data(data: str) -> str:
    return base64.urlsafe_b64decode(_pad_b64(data)).decode("utf-8", errors="replace")


def _collect_text_from_payload(payload: dict[str, Any], out: list[str]) -> None:
    mime = payload.get("mimeType", "")
    body = payload.get("body") or {}
    data = body.get("data")
    if data and mime in ("text/plain", "text/html"):
        out.append(_decode_body_data(data))
    for part in payload.get("parts") or ():
        _collect_text_from_payload(part, out)


def _message_body_text(message: dict[str, Any]) -> str:
    payload = message.get("payload") or {}
    chunks: list[str] = []
    _collect_text_from_payload(payload, chunks)
    snippet = (message.get("snippet") or "").strip()
    if snippet:
        chunks.append(snippet)
    return "\n".join(chunks)


def _invite_body_matches_hints(text: str, hints: tuple[str, ...]) -> bool:
    if not hints:
        return True
    lower = text.lower()
    return any(h.lower() in lower for h in hints)


def _load_gmail_credentials(credentials_path: str, token_path: str) -> Any:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        raise RuntimeError(
            "Gmail support requires: pip install google-api-python-client "
            "google-auth-httplib2 google-auth-oauthlib"
        ) from exc

    creds: Credentials | None = None
    if os.path.isfile(token_path):
        creds = Credentials.from_authorized_user_file(token_path, GMAIL_SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        Path(token_path).parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        return creds

    raise RuntimeError(
        "Gmail OAuth token missing or cannot refresh. Run once:\n"
        f'  python utils/google_api_helper.py --authorize "{credentials_path}" "{token_path}"\n'
        "Use a Desktop OAuth client JSON (Gmail API enabled)."
    )


def build_gmail_service(credentials_path: str | None = None, token_path: str | None = None) -> Any:
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Gmail support requires: pip install google-api-python-client "
            "google-auth-httplib2 google-auth-oauthlib"
        ) from exc

    c = (credentials_path or os.getenv("GOOGLE_GMAIL_CREDENTIALS", "")).strip()
    t = (token_path or os.getenv("GOOGLE_GMAIL_TOKEN", "")).strip()
    if not c or not t:
        raise RuntimeError("Set GOOGLE_GMAIL_CREDENTIALS and GOOGLE_GMAIL_TOKEN to file paths.")
    creds = _load_gmail_credentials(c, t)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def fetch_invitation_accept_url_from_gmail(
    app_base_url: str,
    *,
    credentials_path: str | None = None,
    token_path: str | None = None,
    list_query: str | None = None,
    poll_interval_s: float = 5.0,
    timeout_s: float = 120.0,
    max_messages_per_poll: int = 20,
    invite_link_hints: tuple[str, ...] | None = None,
) -> str:
    """Poll Gmail for an invite URL.

    When ``invite_link_hints`` is set (e.g. work + personal email), only messages whose
    body/snippet contain at least one hint are considered, and the **newest** match by
    ``internalDate`` is returned. That avoids reusing an old invite token from an earlier
    employee or test run.
    """
    service = build_gmail_service(credentials_path=credentials_path, token_path=token_path)
    q = (list_query or os.getenv("GMAIL_INVITE_LIST_QUERY", "").strip() or "newer_than:1d").strip()
    deadline = time.monotonic() + timeout_s
    hints = tuple(h.strip() for h in (invite_link_hints or ()) if (h or "").strip())

    while time.monotonic() < deadline:
        resp = (
            service.users()
            .messages()
            .list(userId="me", q=q, maxResults=max_messages_per_poll)
            .execute()
        )
        ids = [m["id"] for m in resp.get("messages", []) if m.get("id")]
        best_internal = -1
        best_url: str | None = None
        for mid in ids:
            full = (
                service.users()
                .messages()
                .get(userId="me", id=mid, format="full")
                .execute()
            )
            text = _message_body_text(full)
            if not _invite_body_matches_hints(text, hints):
                continue
            url = find_invitation_accept_url_in_text(app_base_url, text)
            if not url:
                continue
            internal = int(full.get("internalDate") or "0")
            if internal > best_internal:
                best_internal = internal
                best_url = url
        if best_url:
            return best_url
        time.sleep(poll_interval_s)

    raise TimeoutError(
        f"No invitation accept URL in Gmail (query={q!r}) within {timeout_s}s. "
        "Adjust GMAIL_INVITE_LIST_QUERY or confirm the invite is in this mailbox."
    )


def _authorize_cli(credentials_path: str, token_path: str) -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, GMAIL_SCOPES)
    creds = flow.run_local_server(port=0)
    Path(token_path).parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    print(f"Wrote token to {token_path}")


def main() -> None:
    p = argparse.ArgumentParser(description="Gmail OAuth for HRMS tests (readonly).")
    p.add_argument(
        "--authorize",
        nargs=2,
        metavar=("CREDENTIALS_JSON", "TOKEN_JSON"),
        help="One-time browser login; saves refresh token.",
    )
    args = p.parse_args()
    if args.authorize:
        _authorize_cli(args.authorize[0], args.authorize[1])
    else:
        p.print_help()


if __name__ == "__main__":
    main()
