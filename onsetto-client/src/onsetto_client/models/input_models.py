"""Contains all of the models representing API input."""

from uuid import UUID

from pydantic import BaseModel


class AuthRequest(BaseModel):
    email: str
    password: str


class BankAccountUpdate(BaseModel):
    account_number: str
    routing_number: str


class MFARequest(BaseModel):
    code: str
    mfa_token: str


class OrderCreate(BaseModel):
    listing_id: UUID


class PaymentMethodUpdate(BaseModel):
    cardholder_name: str
    card_number: str
    cvc: str
    exp_month: int
    exp_year: int
