import re
from playwright.sync_api import Page, expect
from datetime import datetime, timedelta

class EmployeePage:

    def __init__(self, page: Page):
        self.page = page
        self.employees_menu = page.get_by_role("link", name="Employees").first # Sidebar
        self.add_employee_btn = page.get_by_role("link", name="Add Employee") # Add Employee button (robust locator)
        self.first_name_input = page.locator('input[name="firstName"]') # First Name input field
        self.last_name_input = page.locator('input[name="lastName"]') # Last Name input field
        self.personal_email_input = page.locator('input[name="personalEmail"]') # Personal Email input field    
        self.job_title_input = page.locator('input[name="jobTitle"]') # Job Title input field
        self.work_email_input = page.locator('input[name="email"]') # Work Email
        self.date_of_birth_input = page.get_by_label(re.compile(r"date\s*of\s*birth", re.I)).or_(
            page.locator('input[name="dateOfBirth"]')
        )
        self.designation_dropdown = page.locator('#mui-component-select-designationId') # Designation dropdown
        self.department_dropdown = page.locator('#mui-component-select-departmentId') # Department dropdown
        self.direct_lead_dropdown = page.locator('#mui-component-select-directLeadId') # Direct Lead dropdown
        self.hr_manager_dropdown = page.locator('#mui-component-select-hrManagerId') # HR Manager dropdown
        self.date_of_joining_input = page.locator('input[name="dateOfJoining"]') # Date of Joining input field
        self.probation_end_date_input = page.locator('input[name="probationEndDate"]') # Probation End Date input field     

    def _locate_save_button(self):
        """Save next to Cancel at the bottom — avoids unrelated 'Save' in header/modals."""
        cancel = self.page.get_by_role("button", name=re.compile(r"^Cancel$", re.I))
        return cancel.locator(
            "xpath=ancestor::*[.//button[normalize-space()='Save']][1]"
            "//button[normalize-space()='Save']"
        )

    def _prepare_footer_for_save(self):
        """Close MUI datepicker/listbox layers; scroll so footer actions are in view."""
        self.page.keyboard.press("Escape")
        self.page.keyboard.press("Escape")
        try:
            self.page.get_by_role("heading", name="Add New Employee").click(timeout=3_000)
        except Exception:
            pass
        self.page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
        cancel = self.page.get_by_role("button", name=re.compile(r"^Cancel$", re.I))
        cancel.scroll_into_view_if_needed()
        cancel.evaluate("el => el.scrollIntoView({ block: 'center', inline: 'nearest' })")

    def navigate_to_employees(self):
        self.employees_menu.click()

    def click_add_employee(self):
        self.add_employee_btn.click()
        self.page.wait_for_url("**/employees/create")

    def verify_add_employee_page(self):
        expect(self.page).to_have_url(re.compile(r".*/employees/create$"))
        expect(self.page.get_by_role("heading", name="Add New Employee")).to_be_visible()

    def add_employee(self, DATA):
        self.first_name_input.fill(DATA["first_name"])
        self.last_name_input.fill(DATA["last_name"])
        self.personal_email_input.fill(DATA["personal_email"])
        self.job_title_input.fill(DATA["job_title"])
        self.work_email_input.fill(DATA["work_email"])
        dob = DATA.get("dob")
        if dob:
            self.date_of_birth_input.fill(dob)
            self.date_of_birth_input.press("Tab")
        self.designation_dropdown.click()
        self.page.get_by_role("option", name=re.compile(r"Junior\s+software\s+engineer", re.I)).first.click()
        self.department_dropdown.click()
        self.page.click('text=Development (D010)')
        self.direct_lead_dropdown.click()
        self.page.click('text=Ravindra Singh Gautam - EMP-2')
        # Scroll until element is visible 
        self.hr_manager_dropdown.click()
        dropdown = self.page.locator('ul[role="listbox"]')
        dropdown.wait_for()

        # 🔥 Find search input inside dropdown
        search_input = self.page.locator('input[placeholder="Search.."]')

        if search_input.count() > 0:
            search_input.fill("FC Patidar")
        else:
            # fallback: type directly
            self.page.keyboard.type("FC Patidar")

        # Click filtered result
        self.page.locator('li', has_text="FC Patidar - EMP-1").click()
        # 🔹 Date Handling
        today = datetime.today().strftime("%d-%m-%Y")
        probation_date = (datetime.today() + timedelta(days=180)).strftime("%d-%m-%Y")

        self.date_of_joining_input.fill(today)
        self.probation_end_date_input.fill(probation_date)
        self.probation_end_date_input.press("Tab")

        self._prepare_footer_for_save()
        save_btn = self._locate_save_button()
        save_btn.scroll_into_view_if_needed()
        save_btn.evaluate("el => el.scrollIntoView({ block: 'center', inline: 'nearest' })")
        expect(save_btn).to_be_visible(timeout=20_000)
        expect(save_btn).to_be_enabled(timeout=20_000)
        save_btn.click()

    def _snapshot_inline_errors(self) -> str:
        chunks = []
        for sel in (
            '[role="alert"]',
            ".MuiAlert-message",
            ".MuiSnackbarContent-root",
            ".MuiSnackbarContent-message",
            ".MuiFormHelperText-root.Mui-error",
        ):
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

    def assert_employee_save_navigated_away_from_create(self, timeout_ms: float = 30_000):
        """Fails if save did not navigate away from the create screen (typical HRMS flow)."""
        try:
            expect(self.page).not_to_have_url(
                re.compile(r".*/employees/create/?(\?.*)?$"),
                timeout=timeout_ms,
            )
        except AssertionError as exc:
            hints = self._snapshot_inline_errors()
            extra = f" Visible messages: {hints!r}" if hints else ""
            raise AssertionError(
                f"Still on create employee URL after Save.{extra} "
                f"Check required fields (e.g. date of birth), validation messages, and unique emails."
            ) from exc