import re
from datetime import datetime, timedelta
from typing import Any, Mapping
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect
from utils.playwright_patterns import SEARCH_PLACEHOLDER, mui_footer_save_locator

class EmployeePage:
    """Employees → Add Employee flow (MUI form)."""

    _ERROR_SNAPSHOT_SELECTORS = (
        '[role="alert"]',
        ".MuiAlert-message",
        ".MuiSnackbarContent-root",
        ".MuiSnackbarContent-message",
        ".MuiFormHelperText-root.Mui-error",
    )

    def __init__(self, page: Page) -> None:
        self.page = page
        self.employees_menu = page.get_by_role("link", name="Employees").first
        self.add_employee_btn = page.get_by_role("link", name="Add Employee")
        self.first_name_input = page.locator('input[name="firstName"]')
        self.last_name_input = page.locator('input[name="lastName"]')
        self.personal_email_input = page.locator('input[name="personalEmail"]')
        self.job_title_input = page.locator('input[name="jobTitle"]')
        self.work_email_input = page.locator('input[name="email"]')
        self.date_of_birth_input = page.get_by_label(re.compile(r"date\s*of\s*birth", re.I)).or_(
            page.locator('input[name="dateOfBirth"]')
        )
        self.designation_dropdown = page.locator("#mui-component-select-designationId")
        self.department_dropdown = page.locator("#mui-component-select-departmentId")
        self.direct_lead_dropdown = page.locator("#mui-component-select-directLeadId")
        self.hr_manager_dropdown = page.locator("#mui-component-select-hrManagerId")
        self.date_of_joining_input = page.locator('input[name="dateOfJoining"]')
        self.probation_end_date_input = page.locator('input[name="probationEndDate"]')

    def _footer_save(self):
        return mui_footer_save_locator(self.page).first

    def _dismiss_overlays_and_scroll_to_footer(self) -> None:
        self.page.keyboard.press("Escape")
        self.page.keyboard.press("Escape")
        try:
            self.page.get_by_role("heading", name="Add New Employee").click(timeout=3_000)
        except PlaywrightTimeoutError:
            pass
        self.page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
        cancel = self.page.get_by_role("button", name=re.compile(r"^Cancel$", re.I))
        cancel.scroll_into_view_if_needed()
        cancel.evaluate("el => el.scrollIntoView({ block: 'center', inline: 'nearest' })")

    def navigate_to_employees(self) -> None:
        self.employees_menu.click()

    def click_add_employee(self) -> None:
        self.add_employee_btn.click()
        self.page.wait_for_url("**/employees/create")

    def verify_add_employee_page(self) -> None:
        expect(self.page).to_have_url(re.compile(r".*/employees/create$"))
        expect(self.page.get_by_role("heading", name="Add New Employee")).to_be_visible()

    def add_employee(self, data: Mapping[str, Any]) -> None:
        self.first_name_input.fill(data["first_name"])
        self.last_name_input.fill(data["last_name"])
        self.personal_email_input.fill(data["personal_email"])
        self.job_title_input.fill(data["job_title"])
        self.work_email_input.fill(data["work_email"])
        dob = data.get("dob")
        if dob:
            self.date_of_birth_input.fill(str(dob))
            self.date_of_birth_input.press("Tab")

        self.designation_dropdown.click()
        self.page.get_by_role("option", name=re.compile(r"Junior\s+software\s+engineer", re.I)).first.click()
        self.department_dropdown.click()
        self.page.click("text=Development (D010)")
        self.direct_lead_dropdown.click()
        self.page.click("text=Ravindra Singh Gautam - EMP-2")
        self.hr_manager_dropdown.click()
        self.page.locator('ul[role="listbox"]').wait_for()
        search = self.page.locator('input[placeholder="Search.."]').or_(self.page.get_by_placeholder(SEARCH_PLACEHOLDER))
        if search.count() > 0:
            search.first.fill("FC Patidar")
        else:
            self.page.keyboard.type("FC Patidar")
        self.page.locator("li", has_text="FC Patidar - EMP-1").click()

        today = datetime.today().strftime("%d-%m-%Y")
        probation = (datetime.today() + timedelta(days=180)).strftime("%d-%m-%Y")
        self.date_of_joining_input.fill(today)
        self.probation_end_date_input.fill(probation)
        self.probation_end_date_input.press("Tab")

        self._dismiss_overlays_and_scroll_to_footer()
        save_btn = self._footer_save()
        save_btn.scroll_into_view_if_needed()
        save_btn.evaluate("el => el.scrollIntoView({ block: 'center', inline: 'nearest' })")
        expect(save_btn).to_be_visible(timeout=20_000)
        expect(save_btn).to_be_enabled(timeout=20_000)
        save_btn.click()

    def _snapshot_inline_errors(self) -> str:
        chunks: list[str] = []
        for sel in self._ERROR_SNAPSHOT_SELECTORS:
            loc = self.page.locator(sel)
            try:
                n = loc.count()
            except Exception:
                continue
            for i in range(min(n, 8)):
                try:
                    t = loc.nth(i).inner_text(timeout=500).strip()
                    if t:
                        chunks.append(t)
                except Exception:
                    continue
        return " | ".join(dict.fromkeys(chunks))[:800]

    def assert_employee_save_navigated_away_from_create(self, timeout_ms: float = 30_000) -> None:
        try:
            expect(self.page).not_to_have_url(
                re.compile(r".*/employees/create/?(\?.*)?$"),
                timeout=timeout_ms,
            )
        except AssertionError as exc:
            hints = self._snapshot_inline_errors()
            extra = f" Visible messages: {hints!r}" if hints else ""
            raise AssertionError(
                "Still on create employee URL after Save." + extra + " "
                "Check required fields, validation messages, and unique emails."
            ) from exc
