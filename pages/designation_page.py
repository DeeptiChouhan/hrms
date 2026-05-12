import re
import time

from playwright.sync_api import Page, expect


class DesignationPage:

    def __init__(self, page: Page):
        self.page = page
        self.designations_menu = page.get_by_role("link", name=re.compile(r"designations?", re.I))
        self.add_designation_btn =page.get_by_role("button", name=re.compile(r"(^\s*\+?\s*add\b)|(\badd\s+designation\b)", re.I))
        self.designation_form = page.locator("form").filter(has=page.locator('input[name="name"]')).first
        self.name_input = self.designation_form.locator('input[name="name"]')
        self.description_input = self.designation_form.locator(
            'textarea[name="description"], input[name="description"]'
        )
        self.cancel_button = page.get_by_role("button", name=re.compile(r"^cancel$", re.I)).first
        self.save_button = self.cancel_button.locator(
            "xpath=ancestor::*[.//button[normalize-space()='Save']][1]//button[normalize-space()='Save']"
        ).or_(page.get_by_role("button", name=re.compile(r"^save$", re.I)))

        # Validation/success surfaces (common MUI)
        self.alert_messages = page.locator("[role='alert'], .MuiAlert-message")
        self.field_errors = page.locator(".MuiFormHelperText-root.Mui-error, [role='alert']")

        # Designation list (table or MUI DataGrid rows)
        self.designation_list_rows = page.locator("table tbody tr, [role='row']")

    def add_designation(self):
        self.designations_menu.first.click()
        self.add_designation_btn.first.click()
        self.page.wait_for_url(re.compile(r".*/designations?/create/?(\?.*)?$", re.I), timeout=20_000)
        expect(self.page).to_have_url(
            re.compile(r".*/designations?/create/?(\?.*)?$", re.I)
        )
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

   