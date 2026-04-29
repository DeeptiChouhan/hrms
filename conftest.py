import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Launch browser in non-headless mode (visible)
        page = browser.new_page()  # Create new page
        page.goto("https://hrms.eznity.ai")
        yield page
        browser.close()