"""Company API helpers for test data reset (e.g. remove stale employees)."""

import os
from typing import Optional

import requests

from utils.api_helper import login_api
from utils.config import BASE_URL

EMPLOYEE_DELETE_URL = "https://hrms-api.encoreskydev.com/company/api/v1/employees/delete"


def normalize_work_email(work_email: str) -> str:
    """Work emails are matched case-insensitively in HRMS; API expects lowercase for delete."""
    return work_email.strip().lower()


def _bearer_token(admin_email: str, admin_password: str) -> str:
    login_resp = login_api(admin_email, admin_password)
    login_resp.raise_for_status()
    body = login_resp.json()
    return body["response"]["token"]


def delete_employee_by_work_email_if_exists(
    work_email: str,
    *,
    admin_email: Optional[str] = None,
    admin_password: Optional[str] = None,
) -> None:
    """
    1) Resolve work email the same way HRMS stores it (lowercase).
    2) Call delete API: if an employee exists, they are removed; if not, no-op.
    3) On failure (e.g. cannot delete because assigned as lead), print response and raise.

    There is no separate stable "lookup" endpoint in this environment; existence is
    determined from the delete response (200 = was registered, 404 + message = not).
    """
    normalized = normalize_work_email(work_email)
    if normalized != work_email.strip():
        print(
            f"[HRMS cleanup] Work email normalized for API match: {work_email!r} -> {normalized!r}",
            flush=True,
        )

    email = (admin_email or os.getenv("EMAIL") or "").strip()
    password = (admin_password or os.getenv("PASSWORD") or "").strip()
    if not email or not password:
        raise RuntimeError("EMAIL and PASSWORD must be set (env or arguments) to call delete API.")

    print(f"[HRMS cleanup] Checking for existing employee with work email: {normalized!r}", flush=True)

    token = _bearer_token(email, password)
    headers = {
        "Authorization": f"Bearer {token}",
        "x-tenant-domain": BASE_URL,
        "Content-Type": "application/json",
    }
    resp = requests.delete(
        EMPLOYEE_DELETE_URL,
        headers=headers,
        json={"email": normalized},
        timeout=60,
    )

    try:
        payload = resp.json()
    except ValueError:
        payload = {}

    if resp.status_code in (200, 201, 204):
        if payload.get("success") is False:
            err = payload.get("message") or resp.text or resp.reason
            print(f"[HRMS cleanup] Delete API returned {resp.status_code} but success=false: {err}", flush=True)
            raise RuntimeError(
                f"Employee delete did not succeed for {normalized!r} ({resp.status_code}): {err}"
            )
        print(
            f"[HRMS cleanup] Employee existed and was deleted: {normalized!r} — {payload.get('message', 'ok')}",
            flush=True,
        )
        return

    if resp.status_code == 404 and payload.get("message") == "Employee not found.":
        print(
            f"[HRMS cleanup] No employee registered with work email {normalized!r}; proceeding with create.",
            flush=True,
        )
        return

    msg = payload.get("message") or resp.text or resp.reason
    print(
        f"[HRMS cleanup] ERROR delete employee {normalized!r}: HTTP {resp.status_code} — {msg}",
        flush=True,
    )
    raise RuntimeError(
        f"Employee delete API failed ({resp.status_code}) for {normalized!r}: {msg}"
    )
