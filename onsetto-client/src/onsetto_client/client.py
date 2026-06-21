from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from .config import ClientConfig
from .exceptions import (
    APIError,
    AuthenticationError,
    NotAuthenticatedError,
    RateLimitError,
)
from .models.input_models import (
    BankAccountUpdate,
    MFARequest,
    OrderCreate,
    PaymentMethodUpdate,
)
from .models.output_models import (
    AuthResponse,
    BankAccountUpdatedResponse,
    ListingResponse,
    MFAResponse,
    OrderResponse,
    PaymentMethodResponse,
    UserProfileResponse,
)


class OnsettoClient:
    """Client for the Onsetto API."""

    def __init__(self, config: ClientConfig | None = None) -> None:
        """Initialize the OnsettoClient.

        Args:
            config (ClientConfig): The configuration for the client
        """
        self._access_token: str | None = None
        self._config = config or ClientConfig()
        self._http = httpx.Client(
            base_url=self._config.base_url,
            timeout=self._config.timeout,
        )

    def __enter__(self) -> OnsettoClient:
        """Handle entering the context manager."""
        # Nothing really to do here
        return self

    def __exit__(self, *_: Any) -> None:
        """Handle exiting the context manager."""
        # Close the httpx client as we exit
        self.close()

    def _auth_headers(self) -> dict[str, str]:
        """Ensure every request has the authorization header.

        Raise:
            NotAuthenticatedError if the client is not authenticated

        Return:
            the header dict with the access token if there is one
        """
        if self._access_token is None:
            raise NotAuthenticatedError()
        return {"Authorization": f"Bearer {self._access_token}"}

    def close(self) -> None:
        """Close the client."""
        self._http.close()

    # @retry(
    #     retry=retry_if_exception_type(RateLimitError),
    #     wait=wait_fixed(2),
    #     stop=stop_after_attempt(3),
    #     reraise=True,
    # )
    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        auth: bool = True,
    ) -> Any:
        """Handle any request running through the client.

        Args:
            method (str): The method of the request
            path (str): The path we are making the request to
            json (dict[str, any]): The JSON data for the request
            auth (bool): True if request should be authenticated

        Raise:
            AuthenticationError: If the request should be authenticated, but
                                 the client doesn't have an access token
            RateLimitError: If the request received a 429 rate limit error
            APIError: If there is a different non-200 response from the API

        Return:
            The response from the API
        """
        headers = self._auth_headers() if auth else {}
        response = self._http.request(method, path, json=json, headers=headers)

        if response.is_success:
            return response.json()

        try:
            detail = response.json().get("message", response.text)
        except Exception:
            detail = response.text

        if response.status_code == 401:
            raise AuthenticationError(response.status_code, detail)

        if response.status_code == 429:
            raise RateLimitError(response.status_code, detail)

        raise APIError(response.status_code, detail)

    def authenticate(self, email: str, password: str, mfa_code: str) -> MFAResponse:
        """Authenticate the client using the given information.

        Args:
            email (str): The email to authenticate with
            password (str): The password to authenticate with
            mfa_code (str): The multi-factor auth code to authenticate with

        Return:
            the MFAResponse from the API
        """
        auth_request = self._request(
            "POST",
            "/auth/token",
            json={"email": email, "password": password},
            auth=False,
        )
        auth_response = AuthResponse.model_validate(auth_request)

        mfa_request = self._request(
            "POST",
            "/auth/mfa/verify",
            json=MFARequest(
                mfa_token=auth_response.mfa_token, code=mfa_code
            ).model_dump(),
            auth=False,
        )
        mfa_response = MFAResponse.model_validate(mfa_request)

        # Set the access token and return the MFAResponse
        self._access_token = mfa_response.access_token
        return mfa_response

    def create_order(self, listing_id: UUID | str) -> OrderResponse:
        body = OrderCreate(
            listing_id=UUID(str(listing_id))
            if isinstance(listing_id, str)
            else listing_id
        )
        return OrderResponse.model_validate(
            self._request("POST", "/orders", json=body.model_dump(mode="json"))
        )

    def get_me(self) -> UserProfileResponse:
        return UserProfileResponse.model_validate(self._request("GET", "/me"))

    def get_listings(self) -> list[ListingResponse]:
        return [
            ListingResponse.model_validate(item)
            for item in self._request("GET", "/listings")
        ]

    def get_orders(self) -> list[OrderResponse]:
        return [
            OrderResponse.model_validate(item)
            for item in self._request("GET", "/orders")
        ]

    def update_banking(
        self, routing_number: str, account_number: str
    ) -> BankAccountUpdatedResponse:
        body = BankAccountUpdate(
            routing_number=routing_number, account_number=account_number
        )
        return BankAccountUpdatedResponse.model_validate(
            self._request("PUT", "/account/banking", json=body.model_dump())
        )

    def update_payment(
        self,
        cardholder_name: str,
        card_number: str,
        exp_month: int,
        exp_year: int,
        cvc: str,
    ) -> PaymentMethodResponse:
        body = PaymentMethodUpdate(
            cardholder_name=cardholder_name,
            card_number=card_number,
            exp_month=exp_month,
            exp_year=exp_year,
            cvc=cvc,
        )
        return PaymentMethodResponse.model_validate(
            self._request("PUT", "/account/payment", json=body.model_dump())
        )
