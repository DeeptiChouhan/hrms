"""Company API helpers for test data reset (e.g. remove a stale employee before UI create)."""

from __future__ import annotations
import logging
import os
from typing import Any, Optional
import requests
from utils.api_helper import login_api
from utils.config import BASE_URL, EMPLOYEE_DELETE_URL

logger = logging.getLogger(__name__)

def normalize_work_email(work_email: str) -> str:
    """HRMS stores work emails lowercased; delete lookup must match."""
    return work_email.strip().lower()


def employee_login_email_variants(email: str) -> list[str]:
    """
    Login attempts to try in order: normalized address, then local-part without +alias.

    Some auth stacks treat ``user+tag@domain`` differently at login vs invite provisioning.
    """
    n = normalize_work_email(email)
    out: list[str] = [n]
    if "@" not in n:
        return out
    local, domain = n.split("@", 1)
    if "+" in local:
        base = f"{local.split('+', 1)[0]}@{domain}"
        if base not in out:
            out.append(base)
    return out

def _response_json(resp: requests.Response) -> dict[str, Any]:
    try:
        body = resp.json()
        return body if isinstance(body, dict) else {}
    except ValueError:
        return {}

def _bearer_token(admin_email: str, admin_password: str) -> str:
    login_resp = login_api(admin_email, admin_password)
    login_resp.raise_for_status()
    return login_resp.json()["response"]["token"]

def delete_employee_by_work_email_if_exists(
    work_email: str,
    *,
    admin_email: Optional[str] = None,
    admin_password: Optional[str] = None,
) -> None:
    """
    DELETE employee by work email if present (404 + "Employee not found." → no-op).

    Uses the same tenant header as web login. No separate "exists" API: outcome is inferred
    from the delete response. Raises on non-recoverable API errors (e.g. cannot delete lead).
    """
    normalized = normalize_work_email(work_email)
    if normalized != work_email.strip():
        logger.info("Normalized work email for API: %r → %r", work_email, normalized)

    email = (admin_email or os.getenv("EMAIL") or "").strip()
    password = (admin_password or os.getenv("PASSWORD") or "").strip()
    if not email or not password:
        raise RuntimeError("Set EMAIL and PASSWORD (env or arguments) to call the delete API.")

    logger.info("Checking employee by work email: %r", normalized)

    headers = {
        "Authorization": f"Bearer {_bearer_token(email, password)}",
        "x-tenant-domain": BASE_URL,
        "Content-Type": "application/json",
    }
    resp = requests.delete(
        EMPLOYEE_DELETE_URL,
        headers=headers,
        json={"email": normalized},
        timeout=60,
    )
    payload = _response_json(resp)

    if resp.status_code in (200, 201, 204):
        if payload.get("success") is False:
            msg = payload.get("message") or resp.text or resp.reason
            logger.error("Delete returned %s but success=false: %s", resp.status_code, msg)
            raise RuntimeError(f"Employee delete failed for {normalized!r} ({resp.status_code}): {msg}")
        logger.info("Deleted existing employee: %r (%s)", normalized, payload.get("message", "ok"))
        return

    if resp.status_code == 404 and payload.get("message") == "Employee not found.":
        logger.info("No employee for work email %r; continuing.", normalized)
        return

    msg = payload.get("message") or resp.text or resp.reason
    logger.error("Delete failed %s for %r: %s", resp.status_code, normalized, msg)
    raise RuntimeError(f"Employee delete API failed ({resp.status_code}) for {normalized!r}: {msg}")
