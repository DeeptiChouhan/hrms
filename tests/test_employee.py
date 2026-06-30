import time

import pytest

from api.reset_api import (
    delete_employee_by_work_email_if_exists,
    normalize_work_email,
)
from pages.employee_page import EmployeePage
from pages.invitation_accept_page import InvitationAcceptPage
from pages.login_page import LoginPage
from utils.config import BASE_URL
from utils.data_reader import load_employee_data
from utils.env_config import EMAIL, NEW_EMPLOYEE_LOGIN_EMAIL, NEW_EMPLOYEE_PASSWORD, PASSWORD
from utils.invitation_link import invite_resolution_configured, resolve_invitation_accept_url

_INVITE_VIEWPORT = {"width": 1366, "height": 900}


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
    # API login in cleanup invalidates the browser session if run after UI login.
    delete_employee_by_work_email_if_exists(
        emp_data["work_email"],
        admin_email=EMAIL,
        admin_password=PASSWORD,
    )
    login_page.login(EMAIL, PASSWORD)
    employee_page.navigate_to_employees()
    employee_page.click_add_employee()
    employee_page.verify_add_employee_page()
    employee_page.add_employee(emp_data)
    employee_page.assert_employee_save_navigated_away_from_create()


@pytest.mark.employee_invite
def test_add_employee_accept_invite_set_password_and_login(page):
    """Create employee → open invite (Gmail/Mailinator/env URL) → set password → sign in as employee."""
    if not invite_resolution_configured():
        pytest.skip(
            "Need invitation link resolution: place credentials.json + gmail_token.json at repo root "
            "(run once: python utils/google_api_helper.py --authorize credentials.json gmail_token.json), "
            "or set INVITATION_ACCEPT_URL / invitation_accept_url in config.json, "
            "or MAILINATOR_INBOX_LOCAL."
        )

    login_page = LoginPage(page)
    employee_page = EmployeePage(page)
    emp_data = load_employee_data()
    emp_data["work_email"] = normalize_work_email(emp_data["work_email"])
    emp_data["personal_email"] = normalize_work_email(str(emp_data["personal_email"]))

    delete_employee_by_work_email_if_exists(
        emp_data["work_email"],
        admin_email=EMAIL,
        admin_password=PASSWORD,
    )
    login_page.login(EMAIL, PASSWORD)
    employee_page.navigate_to_employees()
    employee_page.click_add_employee()
    employee_page.verify_add_employee_page()
    invite_sent_after_ms = int(time.time() * 1000)
    employee_page.add_employee(emp_data)
    employee_page.assert_employee_save_navigated_away_from_create()

    # Fresh browser context = no admin cookies (like opening the link in Incognito).
    browser = page.context.browser
    invite_context = browser.new_context(viewport=_INVITE_VIEWPORT)
    invite_page = invite_context.new_page()
    try:
        invite_url = resolve_invitation_accept_url(
            invite_page,
            app_base_url=BASE_URL,
            timeout_s=120,
            invite_link_hints=(emp_data["work_email"], emp_data["personal_email"]),
            not_before_ms=invite_sent_after_ms,
        )
        invite_page.goto(invite_url, wait_until="load")
        InvitationAcceptPage(invite_page).set_password_and_submit(NEW_EMPLOYEE_PASSWORD)
    finally:
        invite_page.close()
        invite_context.close()

    page.context.clear_cookies()

    # Same work email as registration (e.g. deepti.chouhan+1a@encoresky.com) + invite password.
    employee_login_email = NEW_EMPLOYEE_LOGIN_EMAIL or emp_data["work_email"]
    login_page.navigate_to_sign_in()
    login_page.login(employee_login_email, NEW_EMPLOYEE_PASSWORD)