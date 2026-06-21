from datetime import date

import pytest
from onsetto_scraper.luhn import luhn_generate
from onsetto_scraper.models.banking import BankingDetails
from onsetto_scraper.models.payment import PaymentMethod
from pydantic import ValidationError


def test_banking_valid() -> None:
    b = BankingDetails(routing_number="021000021", account_number="12345678")
    assert b.routing_number == "021000021"
    assert b.account_number == "12345678"


def test_banking_routing_min_boundary() -> None:
    BankingDetails(routing_number="000000000", account_number="1234")


def test_banking_routing_too_short() -> None:
    with pytest.raises(ValidationError, match="exactly 9 digits"):
        BankingDetails(routing_number="12345678", account_number="1234")


def test_banking_routing_too_long() -> None:
    with pytest.raises(ValidationError, match="exactly 9 digits"):
        BankingDetails(routing_number="1234567890", account_number="1234")


def test_banking_routing_non_digit() -> None:
    with pytest.raises(ValidationError, match="exactly 9 digits"):
        BankingDetails(routing_number="02100002a", account_number="1234")


def test_banking_account_min_length() -> None:
    BankingDetails(routing_number="021000021", account_number="1234")


def test_banking_account_max_length() -> None:
    BankingDetails(routing_number="021000021", account_number="12345678901234567")


def test_banking_account_too_short() -> None:
    with pytest.raises(ValidationError, match="4"):
        BankingDetails(routing_number="021000021", account_number="123")


def test_banking_account_too_long() -> None:
    with pytest.raises(ValidationError, match="4"):
        BankingDetails(routing_number="021000021", account_number="123456789012345678")


def test_banking_account_non_digit() -> None:
    with pytest.raises(ValidationError):
        BankingDetails(routing_number="021000021", account_number="1234abcd")


def _valid_payment(
    cardholder_name: str = "Test User",
    card_number: str | None = None,
    exp_month: int = 12,
    exp_year: int | None = None,
    cvc: str = "123",
) -> PaymentMethod:
    today = date.today()
    return PaymentMethod(
        cardholder_name=cardholder_name,
        card_number=card_number or luhn_generate(prefix="4", length=16),
        exp_month=exp_month,
        exp_year=exp_year if exp_year is not None else today.year + 1,
        cvc=cvc,
    )


def test_payment_valid() -> None:
    p = _valid_payment()
    assert p.cardholder_name == "Test User"
    assert p.cvc == "123"


def test_payment_invalid_luhn() -> None:
    with pytest.raises(ValidationError, match="Luhn"):
        _valid_payment(card_number="4242424242424243")


def test_payment_card_number_non_digit() -> None:
    with pytest.raises(ValidationError):
        _valid_payment(card_number="4242abcd42424242")


def test_payment_card_number_too_short() -> None:
    with pytest.raises(ValidationError):
        _valid_payment(card_number="424242424242")


def test_payment_card_number_too_long() -> None:
    with pytest.raises(ValidationError):
        _valid_payment(card_number="42424242424242424242")


def test_payment_expired_year() -> None:
    with pytest.raises(ValidationError, match="expired"):
        _valid_payment(exp_year=2020, exp_month=1)


def test_payment_expired_same_year_past_month() -> None:
    today = date.today()
    past_month = today.month - 1 if today.month > 1 else 12
    past_year = today.year if today.month > 1 else today.year - 1
    with pytest.raises(ValidationError, match="expired"):
        _valid_payment(exp_year=past_year, exp_month=past_month)


def test_payment_future_expiry_valid() -> None:
    today = date.today()
    _valid_payment(exp_year=today.year + 5, exp_month=6)


def test_payment_cvc_3_digits() -> None:
    _valid_payment(cvc="123")


def test_payment_cvc_4_digits() -> None:
    _valid_payment(cvc="1234")


def test_payment_cvc_2_digits() -> None:
    with pytest.raises(ValidationError, match="3 or 4"):
        _valid_payment(cvc="12")


def test_payment_cvc_5_digits() -> None:
    with pytest.raises(ValidationError, match="3 or 4"):
        _valid_payment(cvc="12345")


def test_payment_cvc_non_digit() -> None:
    with pytest.raises(ValidationError):
        _valid_payment(cvc="abc")


def test_payment_blank_cardholder_name() -> None:
    with pytest.raises(ValidationError, match="blank"):
        _valid_payment(cardholder_name="   ")


def test_payment_cardholder_name_stripped() -> None:
    p = _valid_payment(cardholder_name="  Jane Doe  ")
    assert p.cardholder_name == "Jane Doe"


def test_payment_invalid_exp_month_zero() -> None:
    with pytest.raises(ValidationError, match="1 and 12"):
        _valid_payment(exp_month=0)


def test_payment_invalid_exp_month_thirteen() -> None:
    with pytest.raises(ValidationError, match="1 and 12"):
        _valid_payment(exp_month=13)
