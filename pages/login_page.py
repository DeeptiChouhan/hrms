from playwright.sync_api import Page, expect

class LoginPage:

    def __init__(self, page):
        self.page = page
        # Locators
        self.email_input = page.locator('input[type="Email"]')
        self.password_input = page.locator('input[type="password"]')
        self.sign_in_button = page.locator('button:has-text("Sign in")')
        self.error_message = page.locator('text=Invalid credentials')
        self.forgot_password_link = page.locator('text=Forgot password?')
        self.email_required_error = page.locator('text=Email is required')
        self.password_required_error = page.locator('text=Password is required')
        self.invalid_email_format_error = page.locator('text=Email is not valid')
        
    def login(self, email, password):
        self.email_input.fill(email)
        self.password_input.fill(password)

    def click_login(self):
        login_btn = self.page.locator("[type='submit']")
        login_btn.click()
        
    def validate_login(self):
        self.page.wait_for_timeout(2000)  # temporary (avoid in real)
        assert "dashboard" in self.page.url
        assert self.page.locator("text=Dashboard").is_visible()

    #User login timestamp updated
    def validate_login_timestamp(self):
        self.page.wait_for_timeout(2000)  # temporary (avoid in real)
        timestamp = self.page.locator("text=Last Login:").inner_text()
        print("Last Login Timestamp:", timestamp)   

    #Valid username + valid password → login success
    def valid_login(self):
        self.login("deepti.chouhan@encoresky.com", "Test@123")
        self.click_login()
        self.validate_login()

    #Valid username + invalid password → login failure
    def invalid_password(self):    
        self.login("deepti.chouhan@encoresky.com", "Invalid@123")
        self.click_login()
        #self.error_message.wait_for(state="visible")
        expect(self.error_message).to_be_visible()


    #Invalid username + valid password → login failure
    def invalid_email(self):
        self.login("invalid.email@encoresky.com", "Test@123")
        self.click_login()
        expect(self.error_message).to_be_visible()

    #Invalid username + invalid password → login failure
    def invalid_login(self):
        self.login("invalid.email@encoresky.com", "Invalid@123")
        self.click_login()
        expect(self.error_message).to_be_visible()

    def assert_email_required_error(self):
        self.email_input.fill("")
        self.password_input.fill("Test@123")
        self.click_login()
        expect(self.email_required_error).to_be_visible()

    def assert_password_required_error(self):
        self.email_input.fill("deepti.chouhan@encoresky.com")
        self.password_input.fill("")
        self.click_login()
        expect(self.password_required_error).to_be_visible()

    def invalid_email_format(self):
        self.login("deepti.chouhan@encoreskycom", "Test@123")
        self.click_login()
        expect(self.invalid_email_format_error).to_be_visible()