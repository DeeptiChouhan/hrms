import re

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect


class DesignationPage:

    def __init__(self, page: Page):
        self.page = page
        self.designations_menu = page.get_by_role("link", name=re.compile(r"designations?", re.I))
        self.add_designation_btn = page.get_by_role(
            "button", name=re.compile(r"(^\s*\+?\s*add\b)|(\badd\s+designation\b)", re.I)
        )
        self.designation_form = page.locator("form").filter(has=page.locator('input[name="name"]')).first
        self.name_input = self.designation_form.locator('input[name="name"]')
        self.description_input = self.designation_form.locator(
            'textarea[name="description"], input[name="description"]'
        )
        self.cancel_button = page.get_by_role("button", name=re.compile(r"^cancel$", re.I)).first
        self.save_button = self.cancel_button.locator(
            "xpath=ancestor::*[.//button[normalize-space()='Save']][1]//button[normalize-space()='Save']"
        ).or_(page.get_by_role("button", name=re.compile(r"^save$", re.I)))

        self.alert_messages = page.locator("[role='alert'], .MuiAlert-message")
        self.field_errors = page.locator(".MuiFormHelperText-root.Mui-error, [role='alert']")

        self.designation_list_rows = page.locator("table tbody tr, [role='row']")

    def _list_search_input(self):
        """Toolbar search (placeholder Search... / Search..)."""
        return self.page.get_by_placeholder(re.compile(r"Search\.+", re.I))

    def _designation_row(self, name: str):
        """Body row that shows this designation name (table or MUI DataGrid)."""
        pat = re.compile(re.escape(name), re.I)
        table_row = self.page.locator("tbody tr").filter(has_text=pat)
        grid_row = self.page.locator('[role="row"]').filter(has=self.page.locator('[role="gridcell"]')).filter(
            has_text=pat
        )
        return table_row.or_(grid_row).first

    def _open_row_actions_and_delete(self, row):
        """Row kebab / icon button (often aria-haspopup) then Delete menu item."""
        menu_trigger = row.locator('button[aria-haspopup="true"]')
        if menu_trigger.count() > 0:
            menu_trigger.last.click()
        else:
            row.locator("button:has(svg)").last.click()
        self.page.get_by_role("menuitem", name=re.compile(r"delete", re.I)).first.click()
        # Optional confirmation dialog
        dialog_delete = self.page.get_by_role("dialog").get_by_role(
            "button", name=re.compile(r"delete", re.I)
        )
        try:
            dialog_delete.click(timeout=3_000)
        except PlaywrightTimeoutError:
            pass

    def delete_designation_if_exists(self, name: str = "Developer") -> None:
        """
        On the designations list: search by name; if a row is shown, open row actions and delete.
        """
        search = self._list_search_input()
        expect(search).to_be_visible(timeout=15_000)
        search.click()
        search.fill("")
        search.fill(name)
        self.page.keyboard.press("Enter")

        row = self._designation_row(name)
        try:
            row.wait_for(state="visible", timeout=5_000)
        except PlaywrightTimeoutError:
            return

        self._open_row_actions_and_delete(row)
        try:
            expect(row).not_to_be_visible(timeout=15_000)
        except AssertionError:
            try:
                row.wait_for(state="detached", timeout=5_000)
            except PlaywrightTimeoutError:
                pass

    def add_designation(self):
        self.designations_menu.first.click()
        expect(self.add_designation_btn.first).to_be_visible(timeout=20_000)

        self.delete_designation_if_exists("Developer")

        self.add_designation_btn.first.click()
        self.page.wait_for_url(re.compile(r".*/designations?/create/?(\?.*)?$", re.I), timeout=20_000)
        expect(self.page).to_have_url(re.compile(r".*/designations?/create/?(\?.*)?$", re.I))
        self.name_input.click()
        self.name_input.fill("Developer")
        self.description_input.click()
        self.description_input.fill("Develops and maintains software applications")
        save_btn = self.save_button.first
        save_btn.click()
        expect(self.page).not_to_have_url(
            re.compile(r".*/designations?/create/?(\?.*)?$", re.I),
            timeout=20_000,
        )
