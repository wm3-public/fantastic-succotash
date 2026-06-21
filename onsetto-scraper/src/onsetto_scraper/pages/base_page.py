"""Base page object with shared navigation and interaction helpers."""

import logging

from playwright.async_api import Locator, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from onsetto_scraper.config import ScraperConfig
from onsetto_scraper.exceptions import ElementNotFoundError, NavigationError

logger = logging.getLogger("onsetto_scraper.pages")


class BasePage:
    def __init__(self, page: Page, config: ScraperConfig) -> None:
        self._page = page
        self._config = config
        self._page.set_default_timeout(config.timeout)

    @retry(
        retry=retry_if_exception_type(NavigationError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def _navigate(self, path: str) -> None:
        url = self._config.base_url.rstrip("/") + path
        logger.info("Navigating to %s", url)
        try:
            await self._page.goto(url, wait_until="domcontentloaded")
        except Exception as exc:
            raise NavigationError(url, str(exc)) from exc

    async def _fill(self, selector: str, value: str) -> None:
        await self._page.locator(selector).fill(value)

    async def _click(self, selector: str) -> None:
        await self._page.locator(selector).click()
        # Callers wait for the expected post-click state explicitly (e.g. via
        # _wait_visible on a confirmation element) rather than relying on
        # "networkidle", which is unreliable on SPAs with background polling.

    async def _wait_visible(self, selector: str, *, timeout: float | None = None) -> Locator:
        locator = self._page.locator(selector)
        try:
            await locator.wait_for(
                state="visible",
                timeout=timeout if timeout is not None else self._config.timeout,
            )
        except PlaywrightTimeoutError as exc:
            raise ElementNotFoundError(selector) from exc
        return locator

    async def _get_text(self, selector: str) -> str:
        locator = await self._wait_visible(selector)
        return (await locator.inner_text()).strip()
