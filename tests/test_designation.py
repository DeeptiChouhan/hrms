import uuid

from pages.login_page import LoginPage
from pages.designation_page import DesignationPage
from utils.env_config import EMAIL, PASSWORD


def test_add_designation_navigation(page):
    login_page = LoginPage(page)
    designation_page = DesignationPage(page)

    login_page.login(EMAIL, PASSWORD)
    designation_page.add_designation()
