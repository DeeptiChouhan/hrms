"""Shared MUI / DataGrid patterns used across list + form page objects."""

from __future__ import annotations
import re
from typing import Final
from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError
# TableDataFilters / toolbar search (`table-filter.tsx` uses i18n key `Search...`).
SEARCH_PLACEHOLDER: Final[re.Pattern[str]] = re.compile(r"Search\.+", re.I)
# CustomTable debounces search ~500ms before refetch.
SEARCH_DEBOUNCE_MS: Final[int] = 700

def list_search_locator(page: Page) -> Locator:
    return page.get_by_placeholder(SEARCH_PLACEHOLDER)

def data_row_with_text(page: Page, needle: str) -> Locator:
    """Prefer `tbody tr`; fall back to MUI DataGrid body rows."""
    pat = re.compile(re.escape(needle), re.I)
    table = page.locator("tbody tr").filter(has_text=pat)
    grid = page.locator('[role="row"]').filter(has=page.locator('[role="gridcell"]')).filter(has_text=pat)
    return table.or_(grid).first

def delete_row_via_action_menu(page: Page, row: Locator) -> None:
    """CustomActionMenu: kebab → Delete → optional DeleteModel confirm."""
    trigger = row.locator('button[aria-haspopup="true"]')
    if trigger.count() > 0:
        trigger.last.click()
    else:
        row.locator("button:has(svg)").last.click()

    page.get_by_role("menuitem", name=re.compile(r"delete", re.I)).first.click()

    confirm = page.get_by_role("dialog").get_by_role("button", name=re.compile(r"delete", re.I))
    try:
        confirm.click(timeout=5_000)
    except PlaywrightTimeoutError:
        pass

def mui_footer_save_locator(page: Page) -> Locator:
    """Save in fixed footer next to Cancel (`FormActionButtons` pattern)."""
    cancel = page.get_by_role("button", name=re.compile(r"^cancel$", re.I)).first
    return cancel.locator(
        "xpath=ancestor::*[.//button[normalize-space()='Save']][1]//button[normalize-space()='Save']"
    ).or_(page.get_by_role("button", name=re.compile(r"^save$", re.I)))
