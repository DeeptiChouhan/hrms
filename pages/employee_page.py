import re
from datetime import datetime, timedelta
from typing import Any, Mapping
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect
from utils.playwright_patterns import SEARCH_PLACEHOLDER, mui_footer_save_locator

class EmployeePage:
    """Employees → Add Employee flow (MUI form).

    Document Details locators mirror ``est-hrms-web/src/components/employee/employee-form.tsx``
    (``documentDetails`` card: ``panNumber``, ``esicNumber``, ``uanNumber``; ``aadhaarNumber`` on live app).
    """

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
        # ``employee-form.tsx`` → ``name="dob"`` (label: Date of Birth).
        self.date_of_birth_input = (
            page.locator('input[name="dob"]')
            .or_(page.get_by_label(re.compile(r"^date of birth$", re.I)))
        )
        # ``employee-form.tsx`` → ``name="preferredDob"`` (label: DOB (to greet)).
        self.greeting_preferences_dob_input = (
            page.locator('input[name="preferredDob"]')
            .or_(page.get_by_label(re.compile(r"DOB\s*\(\s*to greet\s*\)", re.I)))
        )
        self.designation_dropdown = page.locator("#mui-component-select-designationId")
        self.department_dropdown = page.locator("#mui-component-select-departmentId")
        self.direct_lead_dropdown = page.locator("#mui-component-select-directLeadId")
        self.hr_manager_dropdown = page.locator("#mui-component-select-hrManagerId")
        self.date_of_joining_input = page.locator('input[name="dateOfJoining"]')
        self.probation_end_date_input = page.locator('input[name="probationEndDate"]')

        # Document Details (`employee-form.tsx` → FormHeader title `documentDetails`).
        self.document_details_card = page.locator(".MuiCard-root").filter(
            has_text=re.compile(r"document details", re.I)
        )

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

    def _fill_date_input(self, locator, value: str) -> None:
        """MUI DatePicker format is DD-MM-YYYY (``CustomDatePicker``)."""
        field = locator.first
        field.scroll_into_view_if_needed()
        expect(field).to_be_visible(timeout=15_000)
        field.click(timeout=10_000)
        field.fill(value)
        field.press("Tab")

    def fill_date_of_birth(self, dob: str) -> None:
        """Required ``dob`` field (UI: Date of Birth)."""
        self._fill_date_input(self.date_of_birth_input, dob)

    def fill_greeting_preferences_dob(self, preferred_dob: str) -> None:
        """Required ``preferredDob`` field (UI: DOB (to greet))."""
        self._fill_date_input(self.greeting_preferences_dob_input, preferred_dob)

    def add_employee(self, data: Mapping[str, Any]) -> None:
        self.first_name_input.fill(data["first_name"])
        self.last_name_input.fill(data["last_name"])
        self.personal_email_input.fill(data["personal_email"])
        self.job_title_input.fill(data["job_title"])
        self.work_email_input.fill(data["work_email"])

        dob = str(data.get("dob", "")).strip()
        if not dob:
            raise ValueError('Employee test data must include "dob" (Date of Birth).')
        self.fill_date_of_birth(dob)

        greeting_dob = str(
            data.get("greeting_preferences_dob")
            or data.get("preferred_dob")
            or ""
        ).strip()
        if not greeting_dob:
            raise ValueError(
                'Employee test data must include "greeting_preferences_dob" '
                '(DOB to greet / preferredDob).'
            )
        self.fill_greeting_preferences_dob(greeting_dob)

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
        self._fill_date_input(self.date_of_joining_input, today)
        self._fill_date_input(self.probation_end_date_input, probation)

        self.fill_document_details(data)

        self._dismiss_overlays_and_scroll_to_footer()
        save_btn = self._footer_save()
        save_btn.scroll_into_view_if_needed()
        save_btn.evaluate("el => el.scrollIntoView({ block: 'center', inline: 'nearest' })")
        expect(save_btn).to_be_visible(timeout=20_000)
        expect(save_btn).to_be_enabled(timeout=20_000)
        save_btn.click()

    def _document_field(self, name: str):
        """Input inside Document Details card (`name` from react-hook-form)."""
        return self.document_details_card.locator(f'input[name="{name}"]')

    @staticmethod
    def _aadhaar_digits(raw: str) -> str:
        """Live schema expects 12 digits (`/^\d{12}$/` in `schema.ts`)."""
        return re.sub(r"\D", "", raw)[:12]

    def _fill_document_input(
        self,
        locator,
        value: str,
        *,
        type_slowly: bool = False,
    ) -> None:
        field = locator.first
        field.scroll_into_view_if_needed()
        expect(field).to_be_visible(timeout=15_000)
        field.click(timeout=10_000)
        field.press("Control+a")
        if type_slowly:
            field.press_sequentially(value, delay=30)
        else:
            field.fill(value)
        field.press("Tab")
        expect(field).not_to_have_value("", timeout=5_000)

    def fill_document_details(self, data: Mapping[str, Any]) -> None:
        """Fill Aadhaar, PAN, ESIC, and UAN in the Document Details card."""
        card = self.document_details_card.first
        card.scroll_into_view_if_needed()
        expect(card).to_be_visible(timeout=15_000)

        aadhaar_digits = self._aadhaar_digits(str(data.get("aadhaar_number", "")))
        if aadhaar_digits:
            aadhaar_input = self._document_field("aadhaarNumber")
            if aadhaar_input.count() == 0:
                aadhaar_input = self.page.locator('input[name="aadhaarNumber"]')
            if aadhaar_input.count() == 0:
                aadhaar_input = card.get_by_role(
                    "textbox", name=re.compile(r"aadhaar", re.I)
                )
            self._fill_document_input(aadhaar_input, aadhaar_digits, type_slowly=True)

        pan = str(data.get("pan_number", ""))
        if pan:
            self._fill_document_input(self._document_field("panNumber"), pan.upper())

        esic = str(data.get("esic_number", ""))
        if esic:
            self._fill_document_input(self._document_field("esicNumber"), esic)

        uan = str(data.get("uan_number", ""))
        if uan:
            self._fill_document_input(self._document_field("uanNumber"), uan)

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
