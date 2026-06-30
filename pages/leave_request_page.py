"""Leave requests — locators mirror `est-hrms-web` leave components.

Source references:
- ``src/paths.ts`` — ``/leave-requests/my-requests``, ``/leave-requests/create``
- ``src/app/(protected)/leave-requests/layout.tsx`` — My Requests tab
- ``src/app/(protected)/leave-requests/my-requests/page.tsx`` — PageHeader ``addRequest``
- ``src/components/leave/leave-request-form.tsx`` — form fields + submit
- ``src/components/leave/leave-type-select.tsx`` — leave type cards
- ``src/components/leave/leave-session-selector.tsx`` — half-day session buttons
"""
from __future__ import annotations

import re
from datetime import date, timedelta

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect


class LeaveRequestPage:
    """Leave Requests → My Requests → create leave application."""

    _URL_MY_REQUESTS = re.compile(r".*/leave-requests/my-requests/?(\?.*)?$", re.I)
    _URL_CREATE = re.compile(r".*/leave-requests/create/?(\?.*)?$", re.I)

    def __init__(self, page: Page) -> None:
        self.page = page
        # Sidebar (`config.ts` → title `leaveRequests`).
        self.leave_requests_menu = page.get_by_role(
            "link", name=re.compile(r"leave requests?", re.I)
        )
        # Horizontal tabs (`leave-requests/layout.tsx` → label `myRequests`).
        self.my_requests_tab = page.get_by_role(
            "link", name=re.compile(r"my requests?", re.I)
        )
        # PageHeader (`my-requests/page.tsx` → label `addRequest`).
        self.add_request_cta = page.locator('a[href*="leave-requests/create"]')
        self.add_request_button = page.get_by_role(
            "button", name=re.compile(r"add request", re.I)
        )

        # LeaveRequestForm — react-hook-form field names.
        self.reason_input = page.locator('textarea[name="reason"], input[name="reason"]')
        self.start_date_input = page.get_by_label(re.compile(r"start date", re.I))
        self.end_date_input = page.get_by_label(re.compile(r"end date", re.I))

        # LeaveSessionSelector + footer actions (`leave-request-form.tsx`).
        self.submit_request_button = page.get_by_role(
            "button", name=re.compile(r"submit request", re.I)
        )

    def navigate_to_my_requests(self) -> None:
        self.leave_requests_menu.first.click()
        expect(self.page).to_have_url(
            re.compile(r".*/leave-requests/(my-requests|)$", re.I),
            timeout=20_000,
        )
        if not self._URL_MY_REQUESTS.search(self.page.url or ""):
            self.my_requests_tab.first.click()
            expect(self.page).to_have_url(self._URL_MY_REQUESTS, timeout=20_000)

    def open_add_request_form(self) -> None:
        try:
            self.add_request_cta.first.click(timeout=10_000)
        except PlaywrightTimeoutError:
            self.add_request_button.first.click(timeout=20_000)
        self.page.wait_for_url(self._URL_CREATE, timeout=20_000)
        expect(self.page).to_have_url(self._URL_CREATE)

    def _leave_type_option_cards(self):
        """``LeaveTypeSelect`` option cards only — not the section wrapper ``Card``.

        Page-wide ``.MuiCard-root`` matches the outer leave-type section card, which
        contains every option's text as descendants. That makes filters match the
        wrapper instead of the clickable card (e.g. Casual Leave stays selected).
        """
        section = self.page.locator(".MuiCard-root").filter(
            has=self.page.get_by_text(re.compile(r"leave type", re.I))
        ).first
        expect(section).to_be_visible(timeout=20_000)
        return section.locator(".MuiGrid2-root > .MuiCard-root")

    def select_leave_type(self, leave_type_name: str, leave_type_code: str) -> None:
        """Click the leave-type card (``LeaveTypeSelect``)."""
        card = self._leave_type_option_cards().filter(
            has_text=re.compile(re.escape(leave_type_name), re.I)
        ).filter(
            has_text=re.compile(re.escape(leave_type_code), re.I)
        )
        expect(card).to_have_count(1, timeout=20_000)
        target = card.first
        expect(target).to_be_visible(timeout=20_000)
        target.click()
        expect(target).to_have_css("border-width", "2px", timeout=10_000)

    def _fill_date_input(self, locator, value: str) -> None:
        locator.click(timeout=10_000)
        locator.fill(value)
        locator.press("Tab")

    def fill_leave_dates(self, leave_date: date) -> None:
        """MUI DatePicker format is DD-MM-YYYY (``CustomDatePicker``)."""
        formatted = leave_date.strftime("%d-%m-%Y")
        self._fill_date_input(self.start_date_input, formatted)
        self._fill_date_input(self.end_date_input, formatted)

    def _session_section(self, heading: str):
        """Scope to ``LeaveSessionSelector`` column (``leave-session-selector.tsx``)."""
        label = self.page.get_by_text(re.compile(rf"^{heading}$", re.I))
        return label.locator(
            "xpath=ancestor::div[contains(@class,'MuiGrid2-root')][1]"
        )

    def select_start_session(self, session_label: str) -> None:
        section = self._session_section("leave start from")
        section.get_by_text(re.compile(session_label, re.I)).first.click()

    def select_end_session(self, session_label: str) -> None:
        section = self._session_section("leave end to")
        section.get_by_text(re.compile(session_label, re.I)).first.click()

    def fill_reason(self, reason: str) -> None:
        self.reason_input.click(timeout=10_000)
        self.reason_input.fill(reason)

    def submit_request(self) -> None:
        btn = self.submit_request_button.first
        btn.scroll_into_view_if_needed()
        expect(btn).to_be_visible(timeout=20_000)
        expect(btn).to_be_enabled(timeout=20_000)
        btn.click()
        expect(self.page).not_to_have_url(self._URL_CREATE, timeout=45_000)

    def create_leave_request(
        self,
        *,
        leave_type_name: str,
        leave_type_code: str,
        reason: str,
        leave_date: date | None = None,
        start_session: str = r"first half",
        end_session: str = r"second half",
    ) -> None:
        target_date = leave_date or (date.today() + timedelta(days=1))
        self.navigate_to_my_requests()
        self.open_add_request_form()
        self.select_leave_type(leave_type_name, leave_type_code)
        self.fill_leave_dates(target_date)
        self.select_start_session(start_session)
        self.select_end_session(end_session)
        self.fill_reason(reason)
        self.submit_request()

    # --- Sandwich leave scenarios (separate from ``create_leave_request``) ---

    def fill_leave_date_range(self, start_date: date, end_date: date) -> None:
        """Set start and end date on the leave request form."""
        self._fill_date_input(self.start_date_input, start_date.strftime("%d-%m-%Y"))
        self._fill_date_input(self.end_date_input, end_date.strftime("%d-%m-%Y"))

    def assert_sandwich_preview_visible(self) -> None:
        """Wait for sandwich calculation UI (``LeaveSandwichCalculationPreview``)."""
        expect(
            self.page.get_by_text(re.compile(r"sandwich\s*days", re.I)).first
        ).to_be_visible(timeout=45_000)

    def _submit_sandwich_leave_request(
        self,
        *,
        leave_type_name: str,
        leave_type_code: str,
        reason: str,
        start_date: date,
        end_date: date,
        start_session: str,
        end_session: str,
        expect_sandwich: bool = False,
    ) -> None:
        self.navigate_to_my_requests()
        self.open_add_request_form()
        self.select_leave_type(leave_type_name, leave_type_code)
        self.fill_leave_date_range(start_date, end_date)
        self.select_start_session(start_session)
        self.select_end_session(end_session)
        self.fill_reason(reason)
        if expect_sandwich:
            self.assert_sandwich_preview_visible()
        self.submit_request()

    def create_weekend_sandwich_leaves(
        self,
        *,
        friday: date,
        monday: date,
        leave_type_name: str,
        leave_type_code: str,
        reason_before_weekend: str,
        reason_after_weekend: str,
        start_session: str = "First half",
        end_session: str = "Second half",
    ) -> None:
        """
        Create two full-day leaves: Friday then Monday with weekend in between.

        The Monday request should show sandwich days for Sat–Sun when the leave
        policy has ``applySandwichOnWeekends`` enabled.
        """
        self._submit_sandwich_leave_request(
            leave_type_name=leave_type_name,
            leave_type_code=leave_type_code,
            reason=reason_before_weekend,
            start_date=friday,
            end_date=friday,
            start_session=start_session,
            end_session=end_session,
        )
        self._submit_sandwich_leave_request(
            leave_type_name=leave_type_name,
            leave_type_code=leave_type_code,
            reason=reason_after_weekend,
            start_date=monday,
            end_date=monday,
            start_session=start_session,
            end_session=end_session,
            expect_sandwich=True,
        )
