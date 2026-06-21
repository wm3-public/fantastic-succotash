"""Unit tests for page object logic that does not require a live browser."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from onsetto_scraper.config import ScraperConfig
from onsetto_scraper.exceptions import VerificationError
from onsetto_scraper.models.banking import BankingDetails
from onsetto_scraper.models.payment import PaymentMethod
from onsetto_scraper.pages.account_page import AccountPage


@pytest.fixture
def config(monkeypatch: pytest.MonkeyPatch) -> ScraperConfig:
    monkeypatch.setenv("ONSETTO_BASE_URL", "https://example.com")
    monkeypatch.setenv("ONSETTO_TEST_USERNAME", "u")
    monkeypatch.setenv("ONSETTO_TEST_PASSWORD", "p")
    monkeypatch.setenv("ONSETTO_TEST_MFA_CODE", "c")
    return ScraperConfig()


@pytest.fixture
def account_page(config: ScraperConfig) -> AccountPage:
    mock_page = MagicMock()
    mock_page.set_default_timeout = MagicMock()
    return AccountPage(mock_page, config)


async def test_verify_banking_saved_passes_when_last4_in_summary(
    account_page: AccountPage, banking_details: BankingDetails
) -> None:
    last4 = banking_details.account_number[-4:]
    account_page._get_text = AsyncMock(return_value=f"Account ending {last4} updated 2024-01-01")
    await account_page.verify_banking_saved(banking_details)  # should not raise


async def test_verify_banking_saved_raises_on_empty_summary(
    account_page: AccountPage, banking_details: BankingDetails
) -> None:
    account_page._get_text = AsyncMock(return_value="   ")
    with pytest.raises(VerificationError, match="empty"):
        await account_page.verify_banking_saved(banking_details)


async def test_verify_banking_saved_raises_when_last4_absent(
    account_page: AccountPage, banking_details: BankingDetails
) -> None:
    account_page._get_text = AsyncMock(return_value="Account ending 0000 updated")
    last4 = banking_details.account_number[-4:]
    with pytest.raises(VerificationError, match=last4):
        await account_page.verify_banking_saved(banking_details)


async def test_verify_payment_saved_passes_when_last4_in_summary(
    account_page: AccountPage, payment_method: PaymentMethod
) -> None:
    last4 = payment_method.card_number[-4:]
    account_page._get_text = AsyncMock(return_value=f"Card ending {last4} saved")
    await account_page.verify_payment_saved(payment_method)  # should not raise


async def test_verify_payment_saved_raises_on_empty_summary(
    account_page: AccountPage, payment_method: PaymentMethod
) -> None:
    account_page._get_text = AsyncMock(return_value="")
    with pytest.raises(VerificationError, match="empty"):
        await account_page.verify_payment_saved(payment_method)


async def test_verify_payment_saved_raises_when_last4_absent(
    account_page: AccountPage, payment_method: PaymentMethod
) -> None:
    account_page._get_text = AsyncMock(return_value="Card ending 0000 saved")
    with pytest.raises(VerificationError):
        await account_page.verify_payment_saved(payment_method)


async def test_fill_banking_details_uses_correct_selectors(
    account_page: AccountPage, banking_details: BankingDetails
) -> None:
    fills: list[tuple[str, str]] = []

    async def capture(selector: str, value: str) -> None:
        fills.append((selector, value))

    account_page._fill = capture  # type: ignore[method-assign]
    await account_page.fill_banking_details(banking_details)

    selectors = [s for s, _ in fills]
    assert '[data-testid="bank-routing"]' in selectors
    assert '[data-testid="bank-account"]' in selectors


async def test_fill_banking_details_passes_correct_values(
    account_page: AccountPage, banking_details: BankingDetails
) -> None:
    fills: list[tuple[str, str]] = []

    async def capture(selector: str, value: str) -> None:
        fills.append((selector, value))

    account_page._fill = capture  # type: ignore[method-assign]
    await account_page.fill_banking_details(banking_details)

    assert ('[data-testid="bank-routing"]', banking_details.routing_number) in fills
    assert ('[data-testid="bank-account"]', banking_details.account_number) in fills


async def test_fill_payment_method_uses_correct_selectors(
    account_page: AccountPage, payment_method: PaymentMethod
) -> None:
    fills: list[tuple[str, str]] = []

    async def capture(selector: str, value: str) -> None:
        fills.append((selector, value))

    account_page._fill = capture  # type: ignore[method-assign]
    await account_page.fill_payment_method(payment_method)

    selectors = [s for s, _ in fills]
    assert '[data-testid="card-holder"]' in selectors
    assert '[data-testid="card-number"]' in selectors
    assert '[data-testid="card-exp-month"]' in selectors
    assert '[data-testid="card-exp-year"]' in selectors
    assert '[data-testid="card-cvc"]' in selectors


async def test_fill_payment_method_formats_card_in_groups_of_4(
    account_page: AccountPage, payment_method: PaymentMethod
) -> None:
    fills: dict[str, str] = {}

    async def capture(selector: str, value: str) -> None:
        fills[selector] = value

    account_page._fill = capture  # type: ignore[method-assign]
    await account_page.fill_payment_method(payment_method)

    card_value = fills['[data-testid="card-number"]']
    # Digits should be space-separated in groups of 4
    assert " " in card_value
    digits_only = card_value.replace(" ", "")
    assert digits_only == payment_method.card_number
