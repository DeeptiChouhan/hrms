from playwright.sync_api import expect, sync_playwright
import threading
from pages.login_page import LoginPage
from utils.env_config import EMAIL, PASSWORD

def test_valid_login(page):
    login_page = LoginPage(page)
    login_page.login(EMAIL, PASSWORD)

def test_wrong_email(page):
    login_page = LoginPage(page)
    login_page.invalid_email()

def test_wrong_password(page):
    login_page = LoginPage(page)
    login_page.invalid_password()  

def test_wrong_creds(page):
    login_page = LoginPage(page)
    login_page.wrong_creds()

def test_empty_email(page):
    login_page = LoginPage(page)
    login_page.assert_email_required_error()

def test_empty_password(page):
    login_page = LoginPage(page)
    login_page.assert_password_required_error()

def test_invalid_email_format(page):
    login_page = LoginPage(page)
    login_page.invalid_email_format()

