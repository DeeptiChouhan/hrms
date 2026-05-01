import re
from playwright.sync_api import Page, expect
from datetime import datetime, timedelta

class EmployeePage:

    def __init__(self, page: Page):
        self.page = page
        self.employees_menu = page.get_by_role("link", name="Employees").first # Sidebar
        self.add_employee_btn = page.get_by_role("link", name="Add Employee") # Add Employee button (robust locator)

    def navigate_to_employees(self):
        self.employees_menu.click()

    def click_add_employee(self):
        self.add_employee_btn.click()
        self.page.wait_for_url("**/employees/create")

    def verify_add_employee_page(self):
        expect(self.page).to_have_url(re.compile(r".*/employees/create$"))
        expect(self.page.get_by_role("heading", name="Add New Employee")).to_be_visible()

    def add_employee(self, DATA):
        self.page.fill('input[name="firstName"]', DATA["first_name"])
        self.page.fill('input[name="lastName"]', DATA["last_name"])
        self.page.fill('input[name="personalEmail"]', DATA["personal_email"])
        self.page.fill('input[name="jobTitle"]', DATA["job_title"])
        self.page.fill('input[name="email"]', DATA["work_email"])
        self.page.click('#mui-component-select-designationId')
        self.page.click('text=Software Engineer')
        self.page.click('#mui-component-select-departmentId')
        self.page.click('text=Development (D010)')
        self.page.click('#mui-component-select-directLeadId')
        self.page.click('text=Ravindra Singh Gautam - EMP-2')
        # Scroll until element is visible 
        self.page.click('#mui-component-select-hrManagerId')

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

        self.page.fill('input[name="dateOfJoining"]', today)
        self.page.fill('input[name="probationEndDate"]', probation_date)

        # 🔹 Save Button
        self.page.locator("//button[.//text()='Save']").click()
        save_btn = self.page.locator("//button[.//text()='Save']")
        # wait for 5 sec after clicking save (temporary, replace with better wait)
        self.page.wait_for_timeout(5000)
        save_btn.wait_for(timeout=5000)
        save_btn.scroll_into_view_if_needed()
        save_btn.click(force=True)