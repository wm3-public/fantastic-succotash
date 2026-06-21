"""Orchestrates the full login, account update, and verification flow."""

import logging
from types import TracebackType

from playwright.async_api import Browser, Page, Playwright, async_playwright

from onsetto_scraper.config import ScraperConfig
from onsetto_scraper.models.banking import BankingDetails
from onsetto_scraper.models.payment import PaymentMethod
from onsetto_scraper.pages.account_page import AccountPage
from onsetto_scraper.pages.login_page import LoginPage
from onsetto_scraper.pages.mfa_page import MfaPage

logger = logging.getLogger("onsetto_scraper.scraper")


class AccountScraper:
    """Async context manager that owns the Playwright browser lifecycle."""

    def __init__(self, config: ScraperConfig | None = None) -> None:
        self._config = config or ScraperConfig()  # type: ignore[call-arg]  # fields loaded from env
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    async def __aenter__(self) -> "AccountScraper":
        """Async entry for the context manager.

        Return:
            this AccountScraper instance
        """
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._config.headless,
            slow_mo=self._config.slow_mo,
        )
        self._page = await self._browser.new_page()
        logger.info("Browser launched (headless=%s)", self._config.headless)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async exit for the context manager.

        Args:
            exc_type (type[BaseException]): The exception type if there was one
            exc_val (BaseException): The exception itself if there was one
            exc_tb (TracebackType): The exception traceback if there was one
        """
        try:
            # Try to close the browser if it's open
            if self._browser:
                await self._browser.close()
        finally:
            # Always stop playwright
            if self._playwright:
                await self._playwright.stop()
        logger.info("Browser closed")

    async def run(
        self,
        banking: BankingDetails,
        payment: PaymentMethod,
        *,
        username: str,
        password: str,
        mfa_code: str,
    ) -> None:
        """Run the scraper.

        Args:
            banking (BankingDetails): The banking details to use
            payment (PaymentMethod): The credit card info to use
            username (str): The username to authenticate with
            password (str): The password to authenticate with
            mfa_code (str): The multi-factor auth code to use
        """
        page = self._page
        if page is None:
            raise RuntimeError("AccountScraper must be used as an async context manager")

        login = LoginPage(page, self._config)
        mfa = MfaPage(page, self._config)
        account = AccountPage(page, self._config)

        logger.info("Starting account update flow")

        await login.navigate()
        await login.login(username, password)
        await mfa.submit_mfa(mfa_code)

        await account.navigate()

        await account.fill_banking_details(banking)
        await account.save_banking()
        await account.verify_banking_saved(banking)

        await account.fill_payment_method(payment)
        await account.save_payment()
        await account.verify_payment_saved(payment)

        logger.info("Account update flow completed successfully")
