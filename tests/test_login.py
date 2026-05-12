from pages.login_page import LoginPage
from utils.env_config import EMAIL, PASSWORD

def test_valid_login(page):
    LoginPage(page).login(EMAIL, PASSWORD)

def test_wrong_email(page):
    LoginPage(page).invalid_email()

def test_wrong_password(page):
    LoginPage(page).invalid_password()

def test_wrong_creds(page):
    LoginPage(page).wrong_creds()

def test_empty_email(page):
    LoginPage(page).assert_email_required_error()

def test_empty_password(page):
    LoginPage(page).assert_password_required_error()


def test_invalid_email_format(page):
    LoginPage(page).invalid_email_format()
