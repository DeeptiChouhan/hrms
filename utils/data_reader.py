"""Load JSON fixtures and config from disk (paths resolved from repo root)."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent

def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def load_config() -> dict[str, Any]:
    return _read_json(_REPO_ROOT / "config.json")

def load_employee_data() -> dict[str, Any]:
    return _read_json(_REPO_ROOT / "test_data" / "new_emp_details.json")

def load_test_data() -> dict[str, Any]:
    return _read_json(_REPO_ROOT / "test_data" / "test_data.json")
