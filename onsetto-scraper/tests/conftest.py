from typing import AsyncGenerator

import pytest
from playwright.async_api import Browser, Page, async_playwright

from onsetto_scraper.config import ScraperConfig
from onsetto_scraper.luhn import luhn_generate
from onsetto_scraper.models.banking import BankingDetails
from onsetto_scraper.models.payment import PaymentMethod


@pytest.fixture(scope="session")
def scraper_config() -> ScraperConfig:
    return ScraperConfig()


@pytest.fixture(scope="session")
async def browser(scraper_config: ScraperConfig) -> AsyncGenerator[Browser, None]:
    pw = await async_playwright().start()
    b = await pw.chromium.launch(
        headless=scraper_config.headless,
        slow_mo=scraper_config.slow_mo,
    )
    yield b
    await b.close()
    await pw.stop()


@pytest.fixture
async def page(browser: Browser) -> AsyncGenerator[Page, None]:
    ctx = await browser.new_context()
    pg = await ctx.new_page()
    yield pg
    await ctx.close()


@pytest.fixture
def banking_details() -> BankingDetails:
    return BankingDetails(routing_number="021000021", account_number="123456789")


@pytest.fixture
def payment_method() -> PaymentMethod:
    return PaymentMethod(
        cardholder_name="Test User",
        card_number=luhn_generate(prefix="4", length=16),
        exp_month=12,
        exp_year=2030,
        cvc="123",
    )
