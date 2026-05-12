from pages.login_page import LoginPage
from pages.employee_page import EmployeePage
from utils.env_config import EMAIL, PASSWORD
from api.reset_api import delete_employee_by_work_email_if_exists, normalize_work_email
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
    emp_data = load_employee_data()
    emp_data["work_email"] = normalize_work_email(emp_data["work_email"])
    # Cleanup uses the login API; doing that after browser login can invalidate the Playwright session.
    delete_employee_by_work_email_if_exists(
        emp_data["work_email"], admin_email=EMAIL, admin_password=PASSWORD
    )
    login_page.login(EMAIL, PASSWORD)
    employee_page.navigate_to_employees()
    employee_page.click_add_employee()
    employee_page.verify_add_employee_page()
    employee_page.add_employee(emp_data)
    employee_page.assert_employee_save_navigated_away_from_create()
