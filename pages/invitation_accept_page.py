"""`/invitation/accept/[token]` — set password.

Targets HRMS ``CustomPasswordInput`` + react-hook-form field names (see
``source_code/est-hrms-web/src/components/auth/invitation-accept-form.tsx``).
MUI toggles ``type`` between ``password`` and ``text`` when the visibility icon
is used, so ``input[type="password"]`` alone is unreliable.
"""

from __future__ import annotations

import re
import time

from playwright.sync_api import Page, expect

_TYPING_DELAY_MS = 30
_INVITE_URL = re.compile(r".*/invitation/accept/", re.I)


class InvitationAcceptPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def _still_on_invite(self, page: Page) -> bool:
        return bool(_INVITE_URL.search(page.url or ""))

    def _raise_if_left_invite(self, page: Page, detail: str) -> None:
        if not self._still_on_invite(page):
            raise AssertionError(
                f"{detail} Current URL: {page.url!r}. "
                "If this happens before typing, the invite token may be invalid/expired "
                "(getInvitationInfo redirects to sign-in). Use a fresh invite link from the latest email."
            )

    @staticmethod
    def _fill_rhf_password_input(locator, password: str) -> None:
        """Focus inner MUI input; avoid clicking adornment (eye) area."""
        locator.scroll_into_view_if_needed()
        locator.click(timeout=10_000)
        locator.press("Control+a")
        locator.press_sequentially(password, delay=_TYPING_DELAY_MS)

    def set_password_and_submit(self, password: str) -> None:
        page = self.page
        expect(page).to_have_url(_INVITE_URL, timeout=30_000)

        pw = page.locator('input[name="password"]')
        cw = page.locator('input[name="confirmPassword"]')

        # Wait for both RHF fields (stable regardless of password vs text type).
        deadline = time.monotonic() + 60.0
        while time.monotonic() < deadline:
            self._raise_if_left_invite(page, "Left invitation page while waiting for form.")
            if pw.count() > 0 and cw.count() > 0:
                try:
                    expect(pw).to_be_visible(timeout=3_000)
                    expect(cw).to_be_visible(timeout=3_000)
                    break
                except AssertionError:
                    pass
            page.wait_for_timeout(200)
        else:
            self._raise_if_left_invite(page, "Timed out waiting for invite form.")
            raise AssertionError(
                "Could not find input[name=\"password\"] and input[name=\"confirmPassword\"]. "
                "Page may not be the HRMS invite form or selectors changed."
            )

        self._fill_rhf_password_input(pw, password)
        page.wait_for_timeout(400)
        self._raise_if_left_invite(page, "Redirected after filling password.")

        self._fill_rhf_password_input(cw, password)
        page.wait_for_timeout(400)
        self._raise_if_left_invite(page, "Redirected after filling confirm password.")

        if pw.input_value(timeout=5_000) != password or cw.input_value(timeout=5_000) != password:
            raise AssertionError(
                f"Values mismatch after fill: password={pw.input_value()!r}, "
                f"confirmPassword={cw.input_value()!r}, expected {password!r}."
            )

        submit = page.locator("form").locator('button[type="submit"]')
        if submit.count() == 0:
            submit = page.locator("form").get_by_role("button", name=re.compile(r"submit", re.I))
        if submit.count() == 0:
            submit = page.get_by_role("button", name=re.compile(r"submit", re.I))
        btn = submit.first
        expect(btn).to_be_visible(timeout=15_000)
        btn.scroll_into_view_if_needed()
        expect(btn).to_be_enabled(timeout=20_000)
        btn.click()

        try:
            page.wait_for_load_state("networkidle", timeout=45_000)
        except Exception:
            pass

        expect(page).to_have_url(re.compile(r".*/sign-in"), timeout=45_000)
