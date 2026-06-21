"""MFA page object."""

import logging

from onsetto_scraper.exceptions import LoginError

from .base_page import BasePage

logger = logging.getLogger("onsetto_scraper.pages.mfa")

# The MFA page uses a custom OTP input component (input-otp library).
# The visible input has data-input-otp="true" and pointer-events: all,
# even though its wrapper container has pointer-events: none.
_OTP_INPUT = "input[data-input-otp='true']"
_SUBMIT_BUTTON = "button[type='submit']"


class MfaPage(BasePage):
    async def submit_mfa(self, code: str) -> None:
        """Fill the 4-digit OTP and submit.

        The submit button starts disabled and enables once all digits are typed.
        After submission, waits for navigation away from /mfa.
        """
        logger.info("Submitting MFA code")

        otp_input = self._page.locator(_OTP_INPUT)
        await otp_input.wait_for(state="visible", timeout=self._config.timeout)
        await otp_input.click(force=True)
        await self._page.keyboard.type(code, delay=100)

        # Wait for the submit button to become enabled (all digits filled).
        # :not([disabled]) narrows the locator so state="visible" implies enabled.
        submit = self._page.locator(f"{_SUBMIT_BUTTON}:not([disabled])")
        await submit.wait_for(state="visible", timeout=self._config.timeout)
        await submit.click()

        try:
            await self._page.wait_for_url(
                lambda url: "/app" in url,
                timeout=self._config.timeout,
            )
        except Exception as exc:
            raise LoginError("MFA failed: did not navigate to /app after submit") from exc

        logger.info("MFA submitted successfully")
