import pytest
import os
import allure
from playwright.sync_api import sync_playwright
from utils.env_config import get_headless_value
from utils.data_reader import load_config

# 🔹 Page Fixture
@pytest.fixture
def page():
    headless = get_headless_value()
    config = load_config()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        #fullscreen for better visibility and to avoid viewport issues
        # Taller viewport so long MUI forms (dates + document block + footer) stay reachable.
        context = browser.new_context(viewport={"width": 1366, "height": 900})
        page = context.new_page()

        page.goto(config["base_url"])

        yield page

        browser.close()

# 🔹 Screenshot on Failure + Allure Attachment
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    # Take screenshot only if test FAILED
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page", None)

        if page:
            screenshot_dir = "screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)

            file_name = f"{item.name}.png"
            file_path = os.path.join(screenshot_dir, file_name)

            page.screenshot(path=file_path)

            # Attach screenshot to Allure report
            allure.attach.file(
                file_path,
                name="Failure Screenshot",
                attachment_type=allure.attachment_type.PNG
            )