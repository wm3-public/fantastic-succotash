import json

import pytest
from onsetto_client import AuthenticationError, NotAuthenticatedError, OnsettoClient
from onsetto_client.config import ClientConfig
from pytest_httpx import HTTPXMock

BASE_URL = "http://test"

AUTH_TOKEN_RESPONSE = {
    "mfa_required": True,
    "mfa_token": "mfa_abc123",
    "message": "MFA code required",
}

MFA_VERIFY_RESPONSE = {
    "access_token": "eyJfake",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "refresh_fake",
}


@pytest.fixture
def fresh_client() -> OnsettoClient:
    return OnsettoClient(ClientConfig(ONSETTO_API_BASE_URL=BASE_URL))


def test_authenticate_success(httpx_mock: HTTPXMock, fresh_client: OnsettoClient) -> None:
    httpx_mock.add_response(method="POST", url=f"{BASE_URL}/auth/token", json=AUTH_TOKEN_RESPONSE)
    httpx_mock.add_response(method="POST", url=f"{BASE_URL}/auth/mfa/verify", json=MFA_VERIFY_RESPONSE)

    result = fresh_client.authenticate("user@example.com", "password123", "1234")

    assert fresh_client._access_token == "eyJfake"
    assert result.access_token == "eyJfake"
    assert result.token_type == "Bearer"
    assert result.expires_in == 3600


def test_authenticate_sends_correct_credentials(httpx_mock: HTTPXMock, fresh_client: OnsettoClient) -> None:
    httpx_mock.add_response(method="POST", url=f"{BASE_URL}/auth/token", json=AUTH_TOKEN_RESPONSE)
    httpx_mock.add_response(method="POST", url=f"{BASE_URL}/auth/mfa/verify", json=MFA_VERIFY_RESPONSE)

    fresh_client.authenticate("user@example.com", "s3cr3t", "1234")

    token_request = httpx_mock.get_requests()[0]

    body = json.loads(token_request.content)
    assert body["email"] == "user@example.com"
    assert body["password"] == "s3cr3t"

    mfa_request = httpx_mock.get_requests()[1]
    mfa_body = json.loads(mfa_request.content)
    assert mfa_body["mfa_token"] == "mfa_abc123"
    assert mfa_body["code"] == "1234"


def test_authenticate_wrong_password_raises(httpx_mock: HTTPXMock, fresh_client: OnsettoClient) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/auth/token",
        status_code=401,
        json={"message": "Invalid credentials"},
    )

    with pytest.raises(AuthenticationError) as exc_info:
        fresh_client.authenticate("user@example.com", "wrongpass", "1234")

    assert exc_info.value.status_code == 401


def test_authenticate_bad_mfa_code_raises(httpx_mock: HTTPXMock, fresh_client: OnsettoClient) -> None:
    httpx_mock.add_response(method="POST", url=f"{BASE_URL}/auth/token", json=AUTH_TOKEN_RESPONSE)
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/auth/mfa/verify",
        status_code=401,
        json={"message": "Invalid MFA code"},
    )

    with pytest.raises(AuthenticationError) as exc_info:
        fresh_client.authenticate("user@example.com", "password123", "9999")

    assert exc_info.value.status_code == 401
    assert fresh_client._access_token is None


def test_not_authenticated_raises(unauthenticated_client: OnsettoClient) -> None:
    with pytest.raises(NotAuthenticatedError):
        unauthenticated_client.get_me()


def test_context_manager_closes_client(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/me",
        json={
            "id": "00000000-0000-0000-0000-000000000001",
            "email": "u@example.com",
            "display_name": "u",
        },
    )

    with OnsettoClient(ClientConfig(ONSETTO_API_BASE_URL=BASE_URL)) as c:
        c._access_token = "tok"
        result = c.get_me()
    assert result.email == "u@example.com"
