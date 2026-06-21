"""Contains all of the models that are returned by the API."""

from uuid import UUID

from pydantic import BaseModel

from .enums import OrderStatus


class AuthResponse(BaseModel):
    """Represents a response after authenticating with the API."""

    mfa_required: bool
    mfa_token: str
    message: str


class BankAccountUpdatedResponse(BaseModel):
    """Represents a response after updating the user's bank account.

    NOTE: Since the API returns masked values, it's okay to use str here.
    """

    account_masked: str
    routing_masked: str
    token: str


class ListingResponse(BaseModel):
    """Represents a response for a single listing from the API."""

    id: str
    category: str
    seller_id: UUID
    title: str
    price: float


class MFAResponse(BaseModel):
    """Represents a response after passing the multi-factor auth challenge
    via the API.
    """

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str


class OrderResponse(BaseModel):
    """Represents the response after creating an order via the API.

    NOTE: Defaulting the status to pending because I've only seen that and
    the paid status.
    """

    id: UUID
    listing_id: UUID
    status: OrderStatus = OrderStatus.PENDING
    total: float


class PaymentMethodResponse(BaseModel):
    """Represents the response after updating the payment method."""

    card_brand: str
    exp_month: int
    exp_year: int
    last4: str
    token: str


class UserProfileResponse(BaseModel):
    """Represents the response to getting the user's profile via the API."""

    id: UUID
    email: str
    display_name: str
