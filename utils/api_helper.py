"""HTTP helpers for HRMS APIs used outside the browser."""

from __future__ import annotations
import requests
from utils.config import API_URL, BASE_URL

def login_api(email: str, password: str, *, timeout_s: float = 60) -> requests.Response:
    """POST `/login` with tenant domain header (same as web app)."""
    headers = {"x-tenant-domain": BASE_URL}
    payload = {"email": email, "password": password}
    return requests.post(f"{API_URL}/login", json=payload, headers=headers, timeout=timeout_s)
