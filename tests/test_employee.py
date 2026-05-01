from pages.login_page import LoginPage
from pages.employee_page import EmployeePage
from utils.env_config import EMAIL, PASSWORD
from datetime import datetime
from utils.data_reader import load_employee_data

def test_add_employee_navigation(page):
    login_page = LoginPage(page)
    employee_page = EmployeePage(page)

    login_page.login(EMAIL, PASSWORD)
    employee_page.navigate_to_employees()
    employee_page.click_add_employee()
    employee_page.verify_add_employee_page()


def test_add_employee(page):
    login_page = LoginPage(page)
    employee_page = EmployeePage(page)
    login_page.login(EMAIL, PASSWORD)
    employee_page.navigate_to_employees()
    employee_page.click_add_employee()
    employee_page.verify_add_employee_page()
    emp_data = load_employee_data()# Load JSON data
    employee_page.add_employee(emp_data)
    