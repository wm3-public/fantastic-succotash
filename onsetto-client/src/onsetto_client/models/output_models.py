"""Contains all of the models that are returned by the API."""

from uuid import UUID

from pydantic import BaseModel

from .enums import OrderStatus


class AuthResponse(BaseModel):
    mfa_required: bool
    mfa_token: str
    message: str


class BankAccountUpdatedResponse(BaseModel):
    account_masked: str
    routing_masked: str
    token: str


class ListingResponse(BaseModel):
    id: str
    category: str
    seller_id: UUID
    title: str
    price: float


class MFAResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str


class OrderResponse(BaseModel):
    id: UUID
    listing_id: UUID
    status: OrderStatus = OrderStatus.PENDING
    total: float


class PaymentMethodResponse(BaseModel):
    card_brand: str
    exp_month: int
    exp_year: int
    last4: str
    token: str


class UserProfileResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
