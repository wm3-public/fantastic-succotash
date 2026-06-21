"""Integration tests — require a running app. Skipped by default (-m 'not integration')."""

import re

import pytest
from onsetto_scraper.config import ScraperConfig
from onsetto_scraper.models.banking import BankingDetails
from onsetto_scraper.models.payment import PaymentMethod
from onsetto_scraper.pages.account_page import AccountPage
from onsetto_scraper.pages.login_page import LoginPage
from onsetto_scraper.pages.mfa_page import MfaPage
from onsetto_scraper.pages.orders_page import OrdersPage
from playwright.async_api import Page


@pytest.fixture(scope="session")
def scraper_config() -> ScraperConfig:
    return ScraperConfig()


async def _login(page: Page, config: ScraperConfig) -> None:
    login = LoginPage(page, config)
    mfa = MfaPage(page, config)
    await login.navigate()
    await login.login(config.test_username, config.test_password)
    await mfa.submit_mfa(config.test_mfa_code)


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.integration
async def test_full_account_flow(
    page: Page,
    scraper_config: ScraperConfig,
    banking_details: BankingDetails,
    payment_method: PaymentMethod,
) -> None:
    await _login(page, scraper_config)

    account = AccountPage(page, scraper_config)
    await account.navigate()

    await account.fill_banking_details(banking_details)
    await account.save_banking()
    await account.verify_banking_saved(banking_details)

    await account.fill_payment_method(payment_method)
    await account.save_payment()
    await account.verify_payment_saved(payment_method)


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.integration
async def test_banking_summary_contains_last_updated(
    page: Page,
    scraper_config: ScraperConfig,
    banking_details: BankingDetails,
) -> None:
    await _login(page, scraper_config)
    account = AccountPage(page, scraper_config)
    await account.navigate()
    await account.fill_banking_details(banking_details)
    await account.save_banking()

    summary = await account.get_banking_summary()
    assert summary.strip(), "bank-saved-info is empty after save"
    assert re.search(r"\b20\d{2}\b", summary), "No year found in banking summary"


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.integration
async def test_payment_summary_contains_last_updated(
    page: Page,
    scraper_config: ScraperConfig,
    banking_details: BankingDetails,
    payment_method: PaymentMethod,
) -> None:
    await _login(page, scraper_config)
    account = AccountPage(page, scraper_config)
    await account.navigate()
    # Banking must be saved first (session requirement)
    await account.fill_banking_details(banking_details)
    await account.save_banking()
    await account.fill_payment_method(payment_method)
    await account.save_payment()

    summary = await account.get_payment_summary()
    assert summary.strip(), "payment-saved-info is empty after save"
    assert re.search(r"\b20\d{2}\b", summary), "No year found in payment summary"


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.integration
async def test_orders_page_returns_rows(
    page: Page,
    scraper_config: ScraperConfig,
) -> None:
    await _login(page, scraper_config)
    orders_page = OrdersPage(page, scraper_config)
    await orders_page.navigate()
    orders = await orders_page.get_orders()
    assert isinstance(orders, list)
    if orders:
        assert "order_id" in orders[0]
        assert "item" in orders[0]
        assert "status" in orders[0]
