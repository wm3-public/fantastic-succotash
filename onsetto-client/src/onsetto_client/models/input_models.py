"""Contains all of the models representing API input."""

import re
from datetime import date
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator

from ..luhn import luhn_is_valid


class AuthRequest(BaseModel):
    """Represents an authentication request."""

    email: str
    password: str


class BankAccountUpdate(BaseModel):
    """Represents an account update payload."""

    account_number: str
    routing_number: str

    @field_validator("routing_number")
    @classmethod
    def validate_routing(cls, value: str) -> str:
        """Validate the routing number is the expected number of digits.

        Args:
            value (str): The value of the routing number

        Raise:
            ValueError if the routing number is not the expected format

        Return:
            the str valid routing number
        """
        if not re.fullmatch(r"\d{9}", value):
            raise ValueError("routing_number must be exactly 9 digits")
        return value

    @field_validator("account_number")
    @classmethod
    def validate_account(cls, value: str) -> str:
        """Validate the account number is the expected number of digits.

        Args:
            value (str): The value of the account number

        Raise:
            ValueError if the account number is invalid

        Return:
            the str valid account number
        """
        if not re.fullmatch(r"\d{4,17}", value):
            raise ValueError("account_number must be 4–17 digits")
        return value


class MFARequest(BaseModel):
    """Represents a multi-factor auth request."""

    code: str
    mfa_token: str


class OrderCreate(BaseModel):
    """Represents an order creation payload."""

    listing_id: UUID


class PaymentMethodUpdate(BaseModel):
    """Represents a payment method update payload."""

    cardholder_name: str
    card_number: str
    cvc: str
    exp_month: int
    exp_year: int

    @field_validator("cardholder_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Validate the name field to ensure it isn't blank.

        Args:
            value (str): The value of the name field

        Raise:
            ValueError if the name is empty

        Return:
            The name with any surrounding whitespace stripped
        """
        if not value.strip():
            raise ValueError("cardholder_name must not be blank")
        return value.strip()

    @field_validator("card_number")
    @classmethod
    def validate_card(cls, value: str) -> str:
        """Validate the credit card number is a valid one.

        Args:
            value (str): The value of the credit card number

        Raise:
            ValueError if the number is not valid

        Return:
            The str card number if it is valid
        """
        digits = re.sub(r"[\s\-]", "", value)
        if not re.fullmatch(r"\d{13,19}", digits):
            raise ValueError("card_number must be 13–19 digits")
        if not luhn_is_valid(digits):
            raise ValueError("card_number failed Luhn check")
        return digits

    @field_validator("cvc")
    @classmethod
    def validate_cvc(cls, value: str) -> str:
        """Validate the CVC is 3 or 4 digits long.

        Args:
            value (str): The value of the CVC

        Raise:
            ValueError if it is not 3-4 digits as expected

        Return:
            str valid CVC
        """
        if not re.fullmatch(r"\d{3,4}", value):
            raise ValueError("cvc must be 3 or 4 digits")
        return value

    @field_validator("exp_month")
    @classmethod
    def validate_month(cls, value: int) -> int:
        """Validate that the credit card expiration has a valid month.

        Args:
            value (int): The value of the expiration month

        Raise:
            ValueError if the value is not a valid month

        Return:
            the int valid month
        """
        if not 1 <= value <= 12:
            raise ValueError("exp_month must be 1–12")
        return value

    @model_validator(mode="after")
    def validate_expiry(self) -> "PaymentMethodUpdate":
        """Validate the card isn't expired.

        Raise:
            ValueError if the card is expired as of today

        Return:
            the payload if the card isn't expired
        """
        today = date.today()
        if self.exp_year < today.year or (self.exp_year == today.year and self.exp_month < today.month):
            raise ValueError("card is expired")
        return self
