"""Account settings page object — banking details and payment method."""

import logging

from playwright.async_api import expect

from onsetto_scraper.exceptions import VerificationError
from onsetto_scraper.models.banking import BankingDetails
from onsetto_scraper.models.payment import PaymentMethod

from .base_page import BasePage

logger = logging.getLogger("onsetto_scraper.pages.account")


class AccountPage(BasePage):
    PATH = "/app/account"

    async def navigate(self) -> None:
        await self._navigate(self.PATH)

    async def fill_banking_details(self, details: BankingDetails) -> None:
        logger.info("Filling banking details")
        await self._fill('[data-testid="bank-routing"]', details.routing_number)
        await self._fill('[data-testid="bank-account"]', details.account_number)

    async def save_banking(self) -> None:
        logger.info("Saving banking details")
        await self._click('[data-testid="bank-save"]')

    async def get_banking_summary(self) -> str:
        return await self._get_text('[data-testid="bank-saved-info"]')

    async def verify_banking_saved(self, details: BankingDetails) -> None:
        """Confirm the masked summary reflects the saved account number."""
        last4 = details.account_number[-4:]
        locator = self._page.locator('[data-testid="bank-saved-info"]')
        try:
            await expect(locator).to_contain_text(last4, timeout=self._config.timeout)
        except Exception as exc:
            summary = (await locator.inner_text()).strip()
            raise VerificationError(
                f"Expected masked account ending {last4!r} in banking summary, got: {summary!r}"
            ) from exc
        logger.info("Banking details verified in summary")

    async def fill_payment_method(self, method: PaymentMethod) -> None:
        logger.info("Filling payment method")
        await self._fill('[data-testid="card-holder"]', method.cardholder_name)
        # Card inputs use a masked component (like the OTP input) that needs
        # keydown/keypress events to update internal state — fill() bypasses these.
        for selector, value in [
            ('[data-testid="card-number"]', method.card_number),
            ('[data-testid="card-exp-month"]', str(method.exp_month).zfill(2)),
            ('[data-testid="card-exp-year"]', str(method.exp_year)),
            ('[data-testid="card-cvc"]', method.cvc),
        ]:
            loc = self._page.locator(selector)
            await loc.click(click_count=3)
            await loc.press_sequentially(value, delay=50)

    async def save_payment(self) -> None:
        logger.info("Saving payment method")
        await self._click('[data-testid="card-save"]')

    async def get_payment_summary(self) -> str:
        return await self._get_text('[data-testid="payment-saved-info"]')

    async def verify_payment_saved(self, method: PaymentMethod) -> None:
        """Confirm the masked summary reflects the saved card number."""
        last4 = method.card_number[-4:]
        locator = self._page.locator('[data-testid="payment-saved-info"]')
        try:
            await expect(locator).to_contain_text(last4, timeout=self._config.timeout)
        except Exception as exc:
            summary = (await locator.inner_text()).strip()
            raise VerificationError(
                f"Expected masked card ending {last4!r} in payment summary, got: {summary!r}"
            ) from exc
        logger.info("Payment method verified in summary")
