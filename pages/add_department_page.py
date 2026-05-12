"""Department list + create — locators mirror `est-hrms-web` department components."""
import re
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect
from utils.playwright_patterns import (
    SEARCH_DEBOUNCE_MS,
    data_row_with_text,
    delete_row_via_action_menu,
    list_search_locator,
    mui_footer_save_locator,
)
class AddDepartmentPage:
    """Departments: optional list cleanup, then create (`/departments/create` → `/departments`)."""

    _URL_CREATE = re.compile(r".*/departments/create/?(\?.*)?$", re.I)
    _URL_LIST = re.compile(r".*/departments/?(\?.*)?$", re.I)

    def __init__(self, page: Page) -> None:
        self.page = page
        self.departments_menu = page.get_by_role("link", name=re.compile(r"departments?", re.I))
        # PageHeader: Next Link to create + Button label `t('add')` (see `PageHeader.tsx`).
        self.add_department_cta = page.locator('a[href*="departments/create"]')
        self.add_department_button = page.get_by_role(
            "button",
            name=re.compile(r"(^\s*\+?\s*add\b)|(\badd\s+department\b)", re.I),
        )
        self.list_search_input = list_search_locator(page)

        self.department_form = page.locator("form").filter(has=page.locator('input[name="departmentCode"]')).first
        self.name_input = self.department_form.locator('input[name="name"]')
        self.department_code_input = self.department_form.locator('input[name="departmentCode"]')
        self.description_input = self.department_form.locator(
            'textarea[name="description"], input[name="description"]'
        )
        self.add_or_update_department_title = page.get_by_text(
            re.compile(r"add\s+new\s+department|update\s+department", re.I)
        )
        self.save_button = mui_footer_save_locator(page)

    def navigate_to_departments_list(self) -> None:
        self.departments_menu.first.click()
        expect(self.add_department_cta).to_be_visible(timeout=20_000)

    def _delete_row_if_search_matches(self, search_term: str) -> None:
        expect(self.list_search_input).to_be_visible(timeout=15_000)
        self.list_search_input.click()
        self.list_search_input.fill("")
        self.list_search_input.fill(search_term)
        self.page.wait_for_timeout(SEARCH_DEBOUNCE_MS)

        row = data_row_with_text(self.page, search_term)
        try:
            row.wait_for(state="visible", timeout=8_000)
        except PlaywrightTimeoutError:
            return

        delete_row_via_action_menu(self.page, row)
        try:
            expect(row).not_to_be_visible(timeout=15_000)
        except AssertionError:
            try:
                row.wait_for(state="detached", timeout=5_000)
            except PlaywrightTimeoutError:
                pass

    def delete_department_if_exists(self, name: str, department_code: str) -> None:
        """Remove rows matching code then name (code can collide across different names)."""
        self._delete_row_if_search_matches(department_code)
        self._delete_row_if_search_matches(name)

    def open_add_department_form(self) -> None:
        try:
            self.add_department_cta.first.click(timeout=10_000)
        except PlaywrightTimeoutError:
            self.add_department_button.first.click(timeout=20_000)
        self.page.wait_for_url(self._URL_CREATE, timeout=20_000)
        expect(self.page).to_have_url(self._URL_CREATE)

    def fill_department_form(self, name: str, department_code: str, description: str) -> None:
        expect(self.add_or_update_department_title).to_be_visible(timeout=15_000)
        self.name_input.click()
        self.name_input.fill(name)
        self.department_code_input.click()
        self.department_code_input.fill(department_code)
        self.description_input.click()
        self.description_input.fill(description)

    def submit_department_form(self) -> None:
        save_btn = self.save_button.first
        save_btn.scroll_into_view_if_needed()
        expect(save_btn).to_be_visible(timeout=20_000)
        expect(save_btn).to_be_enabled(timeout=20_000)
        save_btn.click()

        try:
            expect(self.page).to_have_url(self._URL_LIST, timeout=45_000)
        except AssertionError as exc:
            snack = self.page.locator(".MuiSnackbarContent-message")
            try:
                parts = [snack.nth(i).inner_text().strip() for i in range(min(snack.count(), 5))]
                hint = " | ".join(p for p in parts if p)[:600]
            except Exception:
                hint = ""
            extra = f" Snackbar: {hint!r}" if hint else ""
            raise AssertionError(
                f"Expected redirect to /departments after Save; URL is {self.page.url!r}.{extra}"
            ) from exc
        expect(self.page).not_to_have_url(self._URL_CREATE)

    def add_department(self, name: str, department_code: str, description: str) -> None:
        self.navigate_to_departments_list()
        self.delete_department_if_exists(name, department_code)
        self.open_add_department_form()
        self.fill_department_form(name, department_code, description)
        self.submit_department_form()
