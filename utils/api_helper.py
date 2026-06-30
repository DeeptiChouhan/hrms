"""HTTP helpers for HRMS APIs used outside the browser."""

from __future__ import annotations

from typing import Any

import requests

from utils.config import API_URL, BASE_URL


def login_api(email: str, password: str, *, timeout_s: float = 60) -> requests.Response:
    """POST `/login` with tenant domain header (same as web app)."""
    headers = {"x-tenant-domain": BASE_URL}
    payload = {"email": email, "password": password}
    return requests.post(f"{API_URL}/login", json=payload, headers=headers, timeout=timeout_s)


def _login_response_body(resp: requests.Response) -> dict[str, Any]:
    body = resp.json()
    return body if isinstance(body, dict) else {}


def login_auth_headers(email: str, password: str, *, timeout_s: float = 60) -> dict[str, str]:
    """
    Auth headers for company/leave APIs after ``/login``.

    Leave service requires ``x-branch-id`` and ``x-company-id`` (see ``ApiClient.js``).
    """
    login_resp = login_api(email, password, timeout_s=timeout_s)
    login_resp.raise_for_status()
    response = _login_response_body(login_resp).get("response")
    if not isinstance(response, dict):
        raise RuntimeError("Login succeeded but response payload is missing.")

    token = response.get("token")
    if not token:
        raise RuntimeError("Login succeeded but no token in response.")

    user = response.get("data")
    user = user if isinstance(user, dict) else {}

    headers = {
        "Authorization": f"Bearer {token}",
        "x-tenant-domain": BASE_URL,
        "Content-Type": "application/json",
        "Accept": "application/json; charset=UTF-8",
    }

    company_id = (user.get("company") or {}).get("id")
    employment = user.get("userEmployment") or {}
    branch_id = (employment.get("branch") or {}).get("id")
    if not branch_id:
        branches = user.get("branches") or []
        if isinstance(branches, list) and branches:
            hq = next(
                (b for b in branches if isinstance(b, dict) and b.get("isHeadQuarter")),
                None,
            )
            branch_id = (hq or branches[0]).get("id")

    if company_id:
        headers["x-company-id"] = str(company_id)
    if branch_id:
        headers["x-branch-id"] = str(branch_id)

    return headers
