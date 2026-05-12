import re
from playwright.sync_api import Page, expect
class LoginPage:
    """Login screen and negative-path checks."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.email_input = page.locator('input[type="Email"]')
        self.password_input = page.locator('input[type="password"]')
        self.sign_in_button = page.locator('button:has-text("Sign in")')
        self.error_message = page.locator("text=Invalid credentials")
        self.forgot_password_link = page.locator("text=Forgot password?")
        self.email_required_error = page.locator("text=Email is required")
        self.password_required_error = page.locator("text=Password is required")
        self.invalid_email_format_error = page.locator("text=Email is not valid")

    def login_input(self, email: str, password: str) -> None:
        self.email_input.fill(email)
        self.password_input.fill(password)

    def click_login(self) -> None:
        self.page.locator("[type='submit']").click()

    def validate_login(self) -> None:
        expect(self.page).to_have_url(re.compile(r"dashboard", re.I), timeout=20_000)
        expect(self.page.get_by_role("link", name="Dashboard")).to_be_visible()

    def login(self, email: str, password: str) -> None:
        self.login_input(email, password)
        self.click_login()
        self.validate_login()

    def invalid_password(self) -> None:
        self.login_input("deepti.chouhan@encoresky.com", "Invalid@123")
        self.click_login()
        expect(self.error_message).to_be_visible()

    def invalid_email(self) -> None:
        self.login_input("invalid.email@encoresky.com", "Test@123")
        self.click_login()
        expect(self.error_message).to_be_visible()

    def assert_email_required_error(self) -> None:
        self.email_input.fill("")
        self.password_input.fill("Test@123")
        self.click_login()
        expect(self.email_required_error).to_be_visible()

    def assert_password_required_error(self) -> None:
        self.email_input.fill("deepti.chouhan@encoresky.com")
        self.password_input.fill("")
        self.click_login()
        expect(self.password_required_error).to_be_visible()

    def invalid_email_format(self) -> None:
        self.login_input("deepti.chouhan@encoreskycom", "Test@123")
        self.click_login()
        expect(self.invalid_email_format_error).to_be_visible()

    def wrong_creds(self) -> None:
        self.login_input("deepti.chouihan+9ei3@encoresky.com", "Test@12334")
        self.click_login()
        expect(self.error_message).to_be_visible()
