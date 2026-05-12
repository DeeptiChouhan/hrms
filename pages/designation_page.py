import re
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect
from utils.playwright_patterns import (
    SEARCH_DEBOUNCE_MS,
    data_row_with_text,
    delete_row_via_action_menu,
    list_search_locator,
    mui_footer_save_locator,
)

# Single source for designation used in this suite (list + form).
DESIGNATION_NAME = "Test_Developer"
class DesignationPage:
    """Designations list + create form."""
    def __init__(self, page: Page) -> None:
        self.page = page
        self.designations_menu = page.get_by_role("link", name=re.compile(r"designations?", re.I))
        self.add_designation_btn = page.get_by_role(
            "button",
            name=re.compile(r"(^\s*\+?\s*add\b)|(\badd\s+designation\b)", re.I),
        )
        self.designation_form = page.locator("form").filter(has=page.locator('input[name="name"]')).first
        self.name_input = self.designation_form.locator('input[name="name"]')
        self.description_input = self.designation_form.locator(
            'textarea[name="description"], input[name="description"]'
        )
        self.save_button = mui_footer_save_locator(page)
    _url_create = re.compile(r".*/designations?/create/?(\?.*)?$", re.I)

    def navigate_to_designations_list(self) -> None:
        self.designations_menu.first.click()
        expect(self.add_designation_btn.first).to_be_visible(timeout=20_000)

    def delete_designation_if_exists(self, name: str = DESIGNATION_NAME) -> None:
        search = list_search_locator(self.page)
        expect(search).to_be_visible(timeout=15_000)
        search.click()
        search.fill("")
        search.fill(name)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(SEARCH_DEBOUNCE_MS)

        row = data_row_with_text(self.page, name)
        try:
            row.wait_for(state="visible", timeout=5_000)
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

    def add_designation(self) -> None:
        self.navigate_to_designations_list()
        self.delete_designation_if_exists(DESIGNATION_NAME)
        self.add_designation_btn.first.click()
        self.page.wait_for_url(self._url_create, timeout=20_000)
        expect(self.page).to_have_url(self._url_create)

        self.name_input.click()
        self.name_input.fill(DESIGNATION_NAME)
        self.description_input.click()
        self.description_input.fill("Develops and maintains software applications")
        self.save_button.first.click()
        expect(self.page).not_to_have_url(self._url_create, timeout=20_000)
