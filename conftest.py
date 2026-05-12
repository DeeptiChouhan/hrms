from pathlib import Path
import allure
import pytest
from playwright.sync_api import sync_playwright
from utils.data_reader import load_config
from utils.env_config import get_headless_value
VIEWPORT = {"width": 1366, "height": 900}
SCREENSHOT_DIR = Path("screenshots")

@pytest.fixture
def page():
    """Chromium page: headed locally, headless on CI (see ``get_headless_value``)."""
    headless = get_headless_value()
    config = load_config()
    base_url = config["base_url"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(viewport=VIEWPORT)
        pg = context.new_page()
        pg.goto(base_url)
        yield pg
        browser.close()

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    pg = item.funcargs.get("page")
    if not pg:
        return

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / f"{item.name}.png"
    pg.screenshot(path=str(path))
    allure.attach.file(
        str(path),
        name="Failure Screenshot",
        attachment_type=allure.attachment_type.PNG,
    )
