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


def _stub_expect(monkeypatch: pytest.MonkeyPatch, *, raises: bool) -> None:
    """Patch playwright.expect in account_page to succeed or fail without a real browser."""
    mock_assertions = MagicMock()
    if raises:
        mock_assertions.to_contain_text = AsyncMock(side_effect=Exception("not found"))
    else:
        mock_assertions.to_contain_text = AsyncMock()
    monkeypatch.setattr("onsetto_scraper.pages.account_page.expect", lambda _: mock_assertions)


def _stub_locator_inner_text(account_page: AccountPage, text: str) -> None:
    """Make _page.locator().inner_text() return *text* (needed for error-path messages)."""
    account_page._page.locator.return_value.inner_text = AsyncMock(return_value=text)


# ── verify_banking_saved ────────────────────────────────────────────────────

async def test_verify_banking_saved_passes_when_last4_in_summary(
    account_page: AccountPage, banking_details: BankingDetails, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_expect(monkeypatch, raises=False)
    await account_page.verify_banking_saved(banking_details)  # should not raise


async def test_verify_banking_saved_raises_on_empty_summary(
    account_page: AccountPage, banking_details: BankingDetails, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_expect(monkeypatch, raises=True)
    _stub_locator_inner_text(account_page, "")
    with pytest.raises(VerificationError):
        await account_page.verify_banking_saved(banking_details)


async def test_verify_banking_saved_raises_when_last4_absent(
    account_page: AccountPage, banking_details: BankingDetails, monkeypatch: pytest.MonkeyPatch
) -> None:
    last4 = banking_details.account_number[-4:]
    _stub_expect(monkeypatch, raises=True)
    _stub_locator_inner_text(account_page, "Account ending 0000 updated")
    with pytest.raises(VerificationError, match=last4):
        await account_page.verify_banking_saved(banking_details)


# ── verify_payment_saved ────────────────────────────────────────────────────

async def test_verify_payment_saved_passes_when_last4_in_summary(
    account_page: AccountPage, payment_method: PaymentMethod, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_expect(monkeypatch, raises=False)
    await account_page.verify_payment_saved(payment_method)  # should not raise


async def test_verify_payment_saved_raises_on_empty_summary(
    account_page: AccountPage, payment_method: PaymentMethod, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_expect(monkeypatch, raises=True)
    _stub_locator_inner_text(account_page, "")
    with pytest.raises(VerificationError):
        await account_page.verify_payment_saved(payment_method)


async def test_verify_payment_saved_raises_when_last4_absent(
    account_page: AccountPage, payment_method: PaymentMethod, monkeypatch: pytest.MonkeyPatch
) -> None:
    last4 = payment_method.card_number[-4:]
    _stub_expect(monkeypatch, raises=True)
    _stub_locator_inner_text(account_page, "Card ending 0000 saved")
    with pytest.raises(VerificationError, match=last4):
        await account_page.verify_payment_saved(payment_method)


# ── fill_banking_details ────────────────────────────────────────────────────

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


# ── fill_payment_method ─────────────────────────────────────────────────────

@pytest.fixture
def mock_card_locator() -> MagicMock:
    loc = MagicMock()
    loc.click = AsyncMock()
    loc.press_sequentially = AsyncMock()
    return loc


async def test_fill_payment_method_uses_correct_selectors(
    account_page: AccountPage, payment_method: PaymentMethod, mock_card_locator: MagicMock
) -> None:
    account_page._fill = AsyncMock()  # type: ignore[method-assign]
    account_page._page.locator.return_value = mock_card_locator

    await account_page.fill_payment_method(payment_method)

    # cardholder filled via _fill
    account_page._fill.assert_any_call('[data-testid="card-holder"]', payment_method.cardholder_name)  # type: ignore[attr-defined]

    # card fields interacted via locator
    locator_selectors = [call.args[0] for call in account_page._page.locator.call_args_list]
    assert '[data-testid="card-number"]' in locator_selectors
    assert '[data-testid="card-exp-month"]' in locator_selectors
    assert '[data-testid="card-exp-year"]' in locator_selectors
    assert '[data-testid="card-cvc"]' in locator_selectors


async def test_fill_payment_method_types_raw_card_digits(
    account_page: AccountPage, payment_method: PaymentMethod, mock_card_locator: MagicMock
) -> None:
    """Card number is passed as raw digits (no spaces); the UI component formats them."""
    typed: list[str] = []

    async def capture_sequential(value: str, **_kwargs: object) -> None:
        typed.append(value)

    mock_card_locator.press_sequentially = capture_sequential
    account_page._fill = AsyncMock()  # type: ignore[method-assign]
    account_page._page.locator.return_value = mock_card_locator

    await account_page.fill_payment_method(payment_method)

    assert payment_method.card_number in typed
    # Raw digits only — no space-formatted groups
    assert not any(" " in v for v in typed)
