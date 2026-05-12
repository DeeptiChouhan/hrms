from pages.add_department_page import AddDepartmentPage
from pages.login_page import LoginPage
from utils.env_config import EMAIL, PASSWORD

def test_add_department(page):
    """Creates a department row (code isolated for test data)."""
    login_page = LoginPage(page)
    department_page = AddDepartmentPage(page)
    login_page.login(EMAIL, PASSWORD)
    department_page.add_department(
        name="Test_Department",
        department_code="DT010",
        description="Software Test_Department description.",
    )
