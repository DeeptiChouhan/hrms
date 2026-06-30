"""Leave request cleanup helpers before UI create (same-day duplicate guard)."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import requests

from utils.api_helper import login_auth_headers
from utils.config import LEAVE_MY_REQUESTS_URL, LEAVE_REQUESTS_URL

logger = logging.getLogger(__name__)

_SKIP_STATUSES = frozenset({"cancelled", "rejected"})


def _response_json(resp: requests.Response) -> dict[str, Any]:
    try:
        body = resp.json()
        return body if isinstance(body, dict) else {}
    except ValueError:
        return {}


def _parse_iso_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def _leave_covers_date(leave: dict[str, Any], target: date) -> bool:
    start_raw = leave.get("startDate")
    end_raw = leave.get("endDate")
    if not start_raw or not end_raw:
        return False
    start = _parse_iso_date(str(start_raw))
    end = _parse_iso_date(str(end_raw))
    return start <= target <= end


def _list_my_leave_requests(headers: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    page = 1
    limit = 100
    while True:
        resp = requests.get(
            LEAVE_MY_REQUESTS_URL,
            headers=headers,
            params={"page": page, "limit": limit},
            timeout=60,
        )
        resp.raise_for_status()
        payload = _response_json(resp)
        if not payload.get("success"):
            break
        response = payload.get("response")
        if not isinstance(response, dict):
            break
        batch = response.get("data")
        if not isinstance(batch, list):
            break
        rows.extend(item for item in batch if isinstance(item, dict))
        pagination = response.get("pagination")
        total_pages = 1
        if isinstance(pagination, dict):
            total_pages = int(pagination.get("totalPages") or 1)
        if page >= total_pages:
            break
        page += 1
    return rows


def cancel_leave_for_date_if_exists(
    target: date,
    *,
    email: str,
    password: str,
) -> bool:
    """
    If my-requests already cover ``target``, cancel/delete them and return True.

    Returns False when no matching leave exists (caller can proceed to create).
    """
    headers = login_auth_headers(email, password)
    leaves = _list_my_leave_requests(headers)
    matching = [row for row in leaves if _leave_covers_date(row, target)]
    actionable = [
        row
        for row in matching
        if str(row.get("status") or "").strip().lower() not in _SKIP_STATUSES
    ]
    if not actionable:
        logger.info("No active leave for %s; proceeding to create.", target.isoformat())
        return False

    for leave in actionable:
        leave_id = str(leave.get("id") or "").strip()
        if not leave_id:
            continue
        status = str(leave.get("status") or "").strip().lower()
        if status in _SKIP_STATUSES:
            logger.info("Skipping leave %s (%s).", leave_id, status)
            continue

        if status == "draft":
            resp = requests.delete(
                f"{LEAVE_REQUESTS_URL}/{leave_id}",
                headers=headers,
                timeout=60,
            )
        elif status in {"pending", "approved", "applied"}:
            resp = requests.patch(
                f"{LEAVE_REQUESTS_URL}/{leave_id}/cancel",
                headers=headers,
                json={"cancellationReason": "Automation cleanup before recreate"},
                timeout=60,
            )
        else:
            logger.warning("Unsupported leave status %r for %s; skipping.", status, leave_id)
            continue

        payload = _response_json(resp)
        if resp.status_code in (200, 201, 204) and payload.get("success", True):
            logger.info("Cancelled leave %s (%s) for %s.", leave_id, status, target.isoformat())
            continue

        msg = payload.get("message") or resp.text or resp.reason
        raise RuntimeError(
            f"Failed to cancel leave request {leave_id!r} ({status}) for "
            f"{target.isoformat()}: {msg}"
        )

    return True


def delete_my_leave_requests_for_date_if_exists(
    target: date,
    *,
    email: str,
    password: str,
) -> None:
    """Backward-compatible alias for :func:`cancel_leave_for_date_if_exists`."""
    cancel_leave_for_date_if_exists(target, email=email, password=password)
