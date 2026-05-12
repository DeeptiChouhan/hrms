"""
Page object for Department add/list flows.
Locators align with `source_code/est-hrms-web/src/components/department`:
- `department-form.tsx` — CustomInput name/name, departmentCode, description; FormActionButtons Save.
- `department-list.tsx` — CustomTable + CustomActionMenu (IconButton + delete + DeleteModel).
- `table-filter.tsx` — list search OutlinedInput placeholder `Search...` (i18n key).
"""

import re

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect


class AddDepartmentPage:
    """POM for creating a department (and optional list cleanup). All locators live in __init__."""

    def __init__(self, page: Page):
        self.page = page

        # Navigation — sidebar link to departments list (same pattern as designations)
        self.departments_menu = page.get_by_role("link", name=re.compile(r"departments?", re.I))

        # `app/(protected)/departments/page.tsx` — PageHeader uses Next <Link href={paths.department.create}> + Button
        # with `t(label ?? 'add')` (no custom label) → CTA is usually a link "Add", not a bare "Add department" button.
        self.add_department_cta = page.locator('a[href*="departments/create"]')
        self.add_department_button = page.get_by_role(
            "button",
            name=re.compile(r"(^\s*\+?\s*add\b)|(\badd\s+department\b)", re.I),
        )
        self.list_search_input = page.get_by_placeholder(re.compile(r"Search\.+", re.I))

        # DepartmentForm — `department-form.tsx`: <form> + Card + CustomInput fields (RHF `name` on inputs)
        self.department_form = page.locator("form").filter(has=page.locator('input[name="departmentCode"]')).first
        self.name_input = self.department_form.locator('input[name="name"]')
        self.department_code_input = self.department_form.locator('input[name="departmentCode"]')
        self.description_input = self.department_form.locator(
            'textarea[name="description"], input[name="description"]'
        )

        # `department-form.tsx` Typography variant="h6" — t('addNewDepartment') | t('updateDepartment')
        self.add_or_update_department_title = page.get_by_text(
            re.compile(r"add\s+new\s+department|update\s+department", re.I)
        )

        # `department-form.tsx` FormHeader title="departmentDetails" (translated)
        self.department_details_section = self.department_form.get_by_text(
            re.compile(r"department\s*details", re.I)
        )

        # FormActionButtons — fixed footer Save/Cancel (`FormActionButtons.tsx`, same pattern as designation)
        self.cancel_button = page.get_by_role("button", name=re.compile(r"^cancel$", re.I)).first
        self.save_button = self.cancel_button.locator(
            "xpath=ancestor::*[.//button[normalize-space()='Save']][1]//button[normalize-space()='Save']"
        ).or_(page.get_by_role("button", name=re.compile(r"^save$", re.I)))

        # DepartmentList empty state — `department-list.tsx` message="No Departments found"
        self.no_departments_message = page.get_by_text(re.compile(r"no\s+departments?\s+found", re.I))

        # Feedback
        self.alert_messages = page.locator("[role='alert'], .MuiAlert-message")
        self.field_errors = page.locator(".MuiFormHelperText-root.Mui-error")

    # `src/paths.ts` — department.create: '/departments/create', views: '/departments'
    _url_create = re.compile(r".*\/departments\/create\/?(\?.*)?$", re.I)
    _url_list = re.compile(r".*\/departments\/?(\?.*)?$", re.I)

    def navigate_to_departments_list(self) -> None:
        self.departments_menu.first.click()
        expect(self.add_department_cta).to_be_visible(timeout=20_000)

    def _department_row(self, name: str):
        """`department-list.tsx` NameCell: primary line is `row.name` (and code on second line)."""
        pat = re.compile(re.escape(name), re.I)
        table_row = self.page.locator("tbody tr").filter(has_text=pat)
        grid_row = self.page.locator('[role="row"]').filter(has=self.page.locator('[role="gridcell"]')).filter(
            has_text=pat
        )
        return table_row.or_(grid_row).first

    def _open_row_actions_and_delete(self, row) -> None:
        """`CustomActionMenu.tsx`: IconButton (DotsThreeVertical) opens Menu → Delete → `DeleteModel` dialog."""
        menu_trigger = row.locator('button[aria-haspopup="true"]')
        if menu_trigger.count() > 0:
            menu_trigger.last.click()
        else:
            row.locator("button:has(svg)").last.click()
        # MenuItem wraps Typography with `t('delete')` — locale may use different casing
        self.page.get_by_role("menuitem", name=re.compile(r"delete", re.I)).first.click()
        dialog_delete = self.page.get_by_role("dialog").get_by_role(
            "button", name=re.compile(r"delete", re.I)
        )
        try:
            dialog_delete.click(timeout=5_000)
        except PlaywrightTimeoutError:
            pass

    def _delete_row_if_search_matches(self, search_term: str) -> None:
        """Search list (`TableDataFilters` debounce ~500ms); delete first visible data row if any."""
        expect(self.list_search_input).to_be_visible(timeout=15_000)
        self.list_search_input.click()
        self.list_search_input.fill("")
        self.list_search_input.fill(search_term)
        self.page.wait_for_timeout(700)

        row = self._department_row(search_term)
        try:
            row.wait_for(state="visible", timeout=8_000)
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

    def delete_department_if_exists(self, name: str, department_code: str) -> None:
        """
        Remove clashes before create: `department-list.tsx` NameCell shows name + code on two lines —
        search by **code** first (avoids duplicate D010 with a different name), then by **name**.
        """
        self._delete_row_if_search_matches(department_code)
        self._delete_row_if_search_matches(name)

    def open_add_department_form(self) -> None:
        try:
            self.add_department_cta.first.click(timeout=10_000)
        except PlaywrightTimeoutError:
            self.add_department_button.first.click(timeout=20_000)
        self.page.wait_for_url(self._url_create, timeout=20_000)
        expect(self.page).to_have_url(self._url_create)

    def fill_department_form(self, name: str, department_code: str, description: str) -> None:
        """`department-form.tsx` fields: name, departmentCode (uppercased in app), description."""
        expect(self.add_or_update_department_title).to_be_visible(timeout=15_000)
        self.name_input.click()
        self.name_input.fill(name)
        self.department_code_input.click()
        self.department_code_input.fill(department_code)
        self.description_input.click()
        self.description_input.fill(description)

    def submit_department_form(self) -> None:
        """`FormActionButtons` Save → `router.push(paths.department.views)` i.e. `/departments`."""
        save_btn = self.save_button.first
        save_btn.scroll_into_view_if_needed()
        expect(save_btn).to_be_visible(timeout=20_000)
        expect(save_btn).to_be_enabled(timeout=20_000)
        save_btn.click()
        try:
            expect(self.page).to_have_url(self._url_list, timeout=45_000)
        except AssertionError as exc:
            snack = self.page.locator(".MuiSnackbarContent-message")
            try:
                parts = []
                for i in range(min(snack.count(), 5)):
                    t = snack.nth(i).inner_text().strip()
                    if t:
                        parts.append(t)
                hint = " | ".join(parts)[:600]
            except Exception:
                hint = ""
            extra = f" Snackbar: {hint!r}" if hint else ""
            raise AssertionError(
                f"Expected redirect to departments list after Save; URL is {self.page.url!r}.{extra}"
            ) from exc
        expect(self.page).not_to_have_url(self._url_create)

    def add_department(self, name: str, department_code: str, description: str) -> None:
        """Full create: list → optional cleanup → create form → fill → save → list (`paths.department.views`)."""
        self.navigate_to_departments_list()
        self.delete_department_if_exists(name, department_code)
        self.open_add_department_form()
        self.fill_department_form(name, department_code, description)
        self.submit_department_form()
