import pytest
import os
import allure
from playwright.sync_api import sync_playwright


# 🔹 Page Fixture
@pytest.fixture
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # CI-safe
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://hrms.eznity.ai")

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