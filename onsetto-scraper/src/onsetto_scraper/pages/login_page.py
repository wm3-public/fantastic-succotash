"""Login page object."""

import logging

from onsetto_scraper.exceptions import LoginError

from .base_page import BasePage

logger = logging.getLogger("onsetto_scraper.pages.login")


class LoginPage(BasePage):
    PATH = "/login"

    async def navigate(self) -> None:
        await self._navigate(self.PATH)

    async def login(self, username: str, password: str) -> None:
        """Fill credentials and submit the login form.

        Uses plain HTML ids (#email, #password) because the login page has no
        data-testid. After submission, waits for the MFA form to popup.
        """
        logger.info("Logging in as %s", username)
        await self._fill("#email", username)
        await self._fill("#password", password)
        await self._page.locator("button[type='submit']").click()

        # The MFA form renders at the same /login URL (no navigation), so we wait
        # for the OTP input to appear rather than a URL change.
        try:
            await self._page.locator("input[data-input-otp='true']").wait_for(
                state="visible", timeout=self._config.timeout
            )
        except Exception as exc:
            raise LoginError("Login failed: MFA form did not appear") from exc

        logger.info("Login submitted successfully")
