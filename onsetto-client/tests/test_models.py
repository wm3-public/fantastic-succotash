import uuid

import pytest
from onsetto_client.models.enums import OrderStatus
from onsetto_client.models.input_models import (
    AuthRequest,
    BankAccountUpdate,
    MFARequest,
    OrderCreate,
    PaymentMethodUpdate,
)
from onsetto_client.models.output_models import (
    BankAccountUpdatedResponse,
    ListingResponse,
    MFAResponse,
    OrderResponse,
    PaymentMethodResponse,
    UserProfileResponse,
)
from onsetto_client.models.secret_fields import SecretStr, SecretStrExceptLast4
from pydantic import ValidationError


def test_secret_str_masked() -> None:
    s = SecretStr("mysecret")
    assert str(s) == "********"
    assert s.get_secret_value() == "mysecret"


def test_secret_str_empty_masked() -> None:
    s = SecretStr("")
    assert str(s) == ""


def test_secret_str_except_last4_masked() -> None:
    s = SecretStrExceptLast4("4242424242424242")
    assert str(s) == "************4242"
    assert s.get_secret_value() == "4242424242424242"


def test_secret_str_except_last4_short_value() -> None:
    # Exactly 4 chars: 0 mask chars + all 4 visible
    s = SecretStrExceptLast4("1234")
    assert str(s) == "1234"


def test_secret_str_except_last4_fewer_than_4_chars() -> None:
    # Fewer than 4 chars: negative mask count → empty string, full value visible
    s = SecretStrExceptLast4("abc")
    assert str(s) == "abc"


def test_order_status_paid_value() -> None:
    assert OrderStatus.PAID.value == "paid"


def test_order_status_pending_value() -> None:
    assert OrderStatus.PENDING.value == "pending"


def test_order_status_parses_from_string() -> None:
    assert OrderStatus("paid") == OrderStatus.PAID
    assert OrderStatus("pending") == OrderStatus.PENDING


def test_auth_request_stores_fields() -> None:
    req = AuthRequest(email="a@b.com", password="pass")
    assert req.email == "a@b.com"
    assert req.password == "pass"


def test_mfa_request_stores_fields() -> None:
    req = MFARequest(mfa_token="mfa_abc", code="1234")
    assert req.mfa_token == "mfa_abc"
    assert req.code == "1234"


def test_bank_account_update_stores_fields() -> None:
    req = BankAccountUpdate(routing_number="021000021", account_number="1234567890")
    assert req.routing_number == "021000021"
    assert req.account_number == "1234567890"


def test_order_create_stores_uuid() -> None:
    uid = uuid.uuid4()
    req = OrderCreate(listing_id=uid)
    assert req.listing_id == uid


def test_order_create_parses_uuid_string() -> None:
    uid_str = "00000000-0000-0000-0000-000000000001"
    req = OrderCreate(listing_id=uid_str)  # type: ignore[arg-type]
    assert str(req.listing_id) == uid_str


def test_payment_method_update_stores_all_fields() -> None:
    req = PaymentMethodUpdate(
        cardholder_name="Alice",
        card_number="4242424242424242",
        cvc="123",
        exp_month=12,
        exp_year=2027,
    )
    assert req.cardholder_name == "Alice"
    assert req.card_number == "4242424242424242"
    assert req.cvc == "123"
    assert req.exp_month == 12
    assert req.exp_year == 2027


def test_bank_account_update_invalid_routing_too_short() -> None:
    with pytest.raises(ValidationError):
        BankAccountUpdate(routing_number="12345678", account_number="1234")


def test_bank_account_update_invalid_routing_too_long() -> None:
    with pytest.raises(ValidationError):
        BankAccountUpdate(routing_number="1234567890", account_number="1234")


def test_bank_account_update_invalid_account_too_short() -> None:
    with pytest.raises(ValidationError):
        BankAccountUpdate(routing_number="021000021", account_number="123")


def test_bank_account_update_invalid_account_too_long() -> None:
    with pytest.raises(ValidationError):
        BankAccountUpdate(routing_number="021000021", account_number="1" * 18)


def test_payment_method_update_invalid_luhn() -> None:
    with pytest.raises(ValidationError):
        PaymentMethodUpdate(
            cardholder_name="Alice", card_number="4242424242424241", cvc="123", exp_month=12, exp_year=2030
        )


def test_payment_method_update_blank_cardholder() -> None:
    with pytest.raises(ValidationError):
        PaymentMethodUpdate(
            cardholder_name="   ", card_number="4242424242424242", cvc="123", exp_month=12, exp_year=2030
        )


def test_payment_method_update_invalid_cvc() -> None:
    with pytest.raises(ValidationError):
        PaymentMethodUpdate(
            cardholder_name="Alice", card_number="4242424242424242", cvc="12", exp_month=12, exp_year=2030
        )


def test_payment_method_update_expired_card() -> None:
    with pytest.raises(ValidationError):
        PaymentMethodUpdate(
            cardholder_name="Alice", card_number="4242424242424242", cvc="123", exp_month=1, exp_year=2020
        )


def test_payment_method_update_strips_spaces_from_card_number() -> None:
    req = PaymentMethodUpdate(
        cardholder_name="Alice",
        card_number="4242 4242 4242 4242",
        cvc="123",
        exp_month=12,
        exp_year=2030,
    )
    assert req.card_number == "4242424242424242"


def test_user_profile_response_parses() -> None:
    uid = "00000000-0000-0000-0000-000000000001"
    m = UserProfileResponse(id=uid, email="a@b.com", display_name="Alice")  # type: ignore[arg-type]
    assert str(m.id) == uid
    assert m.email == "a@b.com"
    assert m.display_name == "Alice"


def test_listing_response_parses() -> None:
    data = {
        "id": "listing-1",
        "category": "electronics",
        "seller_id": "00000000-0000-0000-0000-000000000002",
        "title": "Widget",
        "price": 9.99,
    }
    m = ListingResponse.model_validate(data)
    assert m.title == "Widget"
    assert m.price == 9.99


def test_order_response_parses_with_enum() -> None:
    data = {
        "id": "00000000-0000-0000-0000-000000000001",
        "listing_id": "00000000-0000-0000-0000-000000000002",
        "status": "paid",
        "total": 24.99,
    }
    m = OrderResponse.model_validate(data)
    assert m.status == OrderStatus.PAID
    assert m.total == 24.99


def test_order_response_defaults_to_pending() -> None:
    data = {
        "id": "00000000-0000-0000-0000-000000000001",
        "listing_id": "00000000-0000-0000-0000-000000000002",
        "total": 5.0,
    }
    m = OrderResponse.model_validate(data)
    assert m.status == OrderStatus.PENDING


def test_mfa_response_parses() -> None:
    data = {
        "access_token": "eyJ",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "ref",
    }
    m = MFAResponse.model_validate(data)
    assert m.access_token == "eyJ"
    assert m.expires_in == 3600


def test_bank_account_updated_response_parses() -> None:
    data = {"account_masked": "••••7890", "routing_masked": "•••0021", "token": "btok_x"}
    m = BankAccountUpdatedResponse.model_validate(data)
    assert m.account_masked == "••••7890"
    assert m.routing_masked == "•••0021"
    assert m.token == "btok_x"


def test_payment_method_response_parses() -> None:
    data = {"card_brand": "visa", "exp_month": 12, "exp_year": 2027, "last4": "4242", "token": "tok_x"}
    m = PaymentMethodResponse.model_validate(data)
    assert m.card_brand == "visa"
    assert m.last4 == "4242"


def test_order_create_invalid_uuid_raises() -> None:
    with pytest.raises(ValidationError):
        OrderCreate(listing_id="not-a-uuid")  # type: ignore[arg-type]


def test_order_response_invalid_status_raises() -> None:
    data = {
        "id": "00000000-0000-0000-0000-000000000001",
        "listing_id": "00000000-0000-0000-0000-000000000002",
        "status": "refunded",
        "total": 5.0,
    }
    with pytest.raises(ValidationError):
        OrderResponse.model_validate(data)


def test_user_profile_response_invalid_uuid_raises() -> None:
    with pytest.raises(ValidationError):
        UserProfileResponse.model_validate({"id": "bad-uuid", "email": "a@b.com", "display_name": "x"})
