import json
import uuid

import pytest
from onsetto_client import (
    APIError,
    AuthenticationError,
    NotAuthenticatedError,
    OnsettoClient,
    RateLimitError,
)
from onsetto_client.models.enums import OrderStatus
from onsetto_client.models.output_models import (
    BankAccountUpdatedResponse,
    ListingResponse,
    OrderResponse,
    PaymentMethodResponse,
    UserProfileResponse,
)
from pytest_httpx import HTTPXMock

BASE_URL = "http://test"

USER_ID = "00000000-0000-0000-0000-000000000001"
LISTING_ID = "00000000-0000-0000-0000-000000000002"
SELLER_ID = "00000000-0000-0000-0000-000000000003"
ORDER_ID = "00000000-0000-0000-0000-000000000004"


def test_get_me_returns_profile(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/me",
        json={"id": USER_ID, "email": "user@example.com", "display_name": "Alice"},
    )

    result = client.get_me()

    assert isinstance(result, UserProfileResponse)
    assert result.email == "user@example.com"
    assert result.display_name == "Alice"
    assert str(result.id) == USER_ID


def test_get_me_sends_bearer_token(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/me",
        json={"id": USER_ID, "email": "user@example.com", "display_name": "Alice"},
    )

    client.get_me()

    request = httpx_mock.get_requests()[0]
    assert request.headers["Authorization"] == "Bearer test-access-token"


def test_get_listings_returns_list(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/listings",
        json=[
            {"id": LISTING_ID, "category": "electronics", "seller_id": SELLER_ID, "title": "Widget", "price": 9.99},
        ],
    )

    result = client.get_listings()

    assert len(result) == 1
    assert isinstance(result[0], ListingResponse)
    assert result[0].title == "Widget"
    assert result[0].price == 9.99


def test_get_listings_empty(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(method="GET", url=f"{BASE_URL}/listings", json=[])
    assert client.get_listings() == []


def test_get_orders_returns_list(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/orders",
        json=[
            {"id": ORDER_ID, "listing_id": LISTING_ID, "status": "paid", "total": 9.99},
        ],
    )

    result = client.get_orders()

    assert len(result) == 1
    assert isinstance(result[0], OrderResponse)
    assert result[0].status == OrderStatus.PAID
    assert result[0].total == 9.99


def test_get_orders_pending_status(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/orders",
        json=[{"id": ORDER_ID, "listing_id": LISTING_ID, "status": "pending", "total": 5.0}],
    )

    result = client.get_orders()

    assert result[0].status == OrderStatus.PENDING


def test_create_order_returns_response(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/orders",
        json={"id": ORDER_ID, "listing_id": LISTING_ID, "status": "pending", "total": 24.99},
    )

    result = client.create_order(LISTING_ID)

    assert isinstance(result, OrderResponse)
    assert result.total == 24.99
    assert str(result.listing_id) == LISTING_ID


def test_create_order_sends_listing_id(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/orders",
        json={"id": ORDER_ID, "listing_id": LISTING_ID, "status": "pending", "total": 24.99},
    )

    client.create_order(LISTING_ID)

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)
    assert body["listing_id"] == LISTING_ID


def test_create_order_accepts_uuid_object(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/orders",
        json={"id": ORDER_ID, "listing_id": LISTING_ID, "status": "pending", "total": 1.0},
    )

    result = client.create_order(uuid.UUID(LISTING_ID))

    assert isinstance(result, OrderResponse)


def test_update_banking_returns_response(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/account/banking",
        json={"account_masked": "••••••7890", "routing_masked": "•••••0021", "token": "btok_abc"},
    )

    result = client.update_banking("021000021", "1234567890")

    assert isinstance(result, BankAccountUpdatedResponse)
    assert result.token == "btok_abc"
    assert result.account_masked == "••••••7890"


def test_update_banking_sends_correct_body(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/account/banking",
        json={"account_masked": "••••••7890", "routing_masked": "•••••0021", "token": "btok_abc"},
    )

    client.update_banking("021000021", "1234567890")

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)
    assert body["routing_number"] == "021000021"
    assert body["account_number"] == "1234567890"


def test_update_payment_returns_response(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/account/payment",
        json={"card_brand": "visa", "exp_month": 12, "exp_year": 2027, "last4": "4242", "token": "tok_abc"},
    )

    result = client.update_payment("Alice Smith", "4242424242424242", 12, 2027, "123")

    assert isinstance(result, PaymentMethodResponse)
    assert result.card_brand == "visa"
    assert result.last4 == "4242"
    assert result.token == "tok_abc"


def test_update_payment_sends_correct_body(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/account/payment",
        json={"card_brand": "visa", "exp_month": 12, "exp_year": 2027, "last4": "4242", "token": "tok_abc"},
    )

    client.update_payment("Alice Smith", "4242424242424242", 12, 2027, "123")

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)
    assert body["cardholder_name"] == "Alice Smith"
    assert body["card_number"] == "4242424242424242"
    assert body["exp_month"] == 12
    assert body["exp_year"] == 2027
    assert body["cvc"] == "123"


def test_401_raises_authentication_error(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/me",
        status_code=401,
        json={"message": "Unauthorized"},
    )

    with pytest.raises(AuthenticationError) as exc_info:
        client.get_me()

    assert exc_info.value.status_code == 401


def test_429_raises_rate_limit_error(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    for _ in range(3):
        httpx_mock.add_response(
            method="GET",
            url=f"{BASE_URL}/me",
            status_code=429,
            json={"message": "Too many requests"},
        )

    with pytest.raises(RateLimitError) as exc_info:
        client.get_me()

    assert exc_info.value.status_code == 429
    assert len(httpx_mock.get_requests()) == 3


def test_5xx_raises_api_error(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/me",
        status_code=500,
        json={"message": "Internal server error"},
    )

    with pytest.raises(APIError) as exc_info:
        client.get_me()

    assert exc_info.value.status_code == 500
    assert not isinstance(exc_info.value, AuthenticationError)
    assert not isinstance(exc_info.value, RateLimitError)


def test_error_without_json_body(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/me",
        status_code=503,
        text="Service Unavailable",
    )

    with pytest.raises(APIError) as exc_info:
        client.get_me()

    assert exc_info.value.status_code == 503


def test_error_json_without_message_key_uses_text(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    """Test when the error body is valid JSON but has no "message" key, detail
    falls back to response.text.
    """
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/me",
        status_code=400,
        json={"error": "bad_request"},
    )

    with pytest.raises(APIError) as exc_info:
        client.get_me()

    assert exc_info.value.status_code == 400
    assert "bad_request" in exc_info.value.detail


def test_reauthentication_replaces_token(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/auth/token",
        json={"mfa_required": True, "mfa_token": "mfa_new", "message": "MFA required"},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/auth/mfa/verify",
        json={"access_token": "new-token", "token_type": "Bearer", "expires_in": 3600, "refresh_token": "r2"},
    )

    client.authenticate("user@example.com", "newpass", "1234")

    assert client._access_token == "new-token"


def test_auth_endpoints_send_no_authorization_header(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    """Test /auth/token and /auth/mfa/verify use auth=False"""
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/auth/token",
        json={"mfa_required": True, "mfa_token": "mfa_t", "message": "ok"},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/auth/mfa/verify",
        json={"access_token": "tok", "token_type": "Bearer", "expires_in": 3600, "refresh_token": "r"},
    )

    client.authenticate("user@example.com", "pass", "1234")

    for req in httpx_mock.get_requests():
        assert "Authorization" not in req.headers


def test_unauthenticated_client_raises_on_all_methods(unauthenticated_client: OnsettoClient) -> None:

    with pytest.raises(NotAuthenticatedError):
        unauthenticated_client.get_listings()

    with pytest.raises(NotAuthenticatedError):
        unauthenticated_client.get_orders()

    with pytest.raises(NotAuthenticatedError):
        unauthenticated_client.create_order(str(uuid.uuid4()))

    with pytest.raises(NotAuthenticatedError):
        unauthenticated_client.update_banking("021000021", "1234567890")

    with pytest.raises(NotAuthenticatedError):
        unauthenticated_client.update_payment("Alice", "4242424242424242", 12, 2027, "123")


def test_get_listings_multiple_items(httpx_mock: HTTPXMock, client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/listings",
        json=[
            {"id": "a", "category": "electronics", "seller_id": SELLER_ID, "title": "Widget", "price": 9.99},
            {"id": "b", "category": "clothing", "seller_id": SELLER_ID, "title": "Shirt", "price": 19.99},
            {"id": "c", "category": "books", "seller_id": SELLER_ID, "title": "Novel", "price": 4.99},
        ],
    )

    result = client.get_listings()

    assert len(result) == 3
    assert all(isinstance(item, ListingResponse) for item in result)
    assert [item.title for item in result] == ["Widget", "Shirt", "Novel"]
