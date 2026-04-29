from playwright.sync_api import expect, sync_playwright
import threading
from pages.login_page import LoginPage

def test_valid_login(page):
    login_page = LoginPage(page)
    login_page.login("deepti.chouhan@encoresky.com", "Test@123")
    login_page.click_login()
    login_page.validate_login()

def test_wrong_email(page):
    login_page = LoginPage(page)
    login_page.login("invalid.email@encoresky.com", "Test@123")
    login_page.click_login()
    login_page.invalid_email()

def test_wrong_password(page):
    login_page = LoginPage(page)
    login_page.login("deepti.chouhan@encoresky.com", "InvalidPassword")
    login_page.click_login()
    login_page.invalid_password()  

def test_wrong_creds(page):
    login_page = LoginPage(page)
    login_page.login("deepti.chouhan+11234@encoresky.com", "Test@123#")
    login_page.click_login()
    login_page.invalid_login()

def test_empty_email(page):
    login_page = LoginPage(page)
    login_page.login("", "Test@123")
    login_page.click_login()
    login_page.assert_email_required_error()

def test_empty_password(page):
    login_page = LoginPage(page)
    login_page.login("deepti.chouhan+1123435@encoresky.com", "")
    login_page.click_login()
    login_page.assert_password_required_error()

def test_invalid_email_format(page):
    login_page = LoginPage(page)
    login_page.login("deepti.chouhan@encoreskycom", "Test@123")
    login_page.click_login()
    login_page.invalid_email_format()

