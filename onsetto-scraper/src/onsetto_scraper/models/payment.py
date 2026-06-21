import re
from datetime import date

from pydantic import BaseModel, field_validator, model_validator

from onsetto_scraper.luhn import luhn_is_valid


class PaymentMethod(BaseModel):
    """Models a payment method (credit card) for the scraper."""

    cardholder_name: str
    card_number: str  # digits only, no spaces/dashes
    exp_month: int
    exp_year: int
    cvc: str

    @field_validator("cardholder_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("cardholder_name cannot be blank")
        return value.strip()

    @field_validator("card_number")
    @classmethod
    def validate_card_number(cls, value: str) -> str:
        if not re.fullmatch(r"\d{13,19}", value):
            raise ValueError("card_number must be 13–19 digits")
        if not luhn_is_valid(value):
            raise ValueError("card_number fails Luhn check")
        return value

    @field_validator("cvc")
    @classmethod
    def validate_cvc(cls, value: str) -> str:
        if not re.fullmatch(r"\d{3,4}", value):
            raise ValueError("cvc must be 3 or 4 digits")
        return value

    @model_validator(mode="after")
    def validate_expiry(self) -> "PaymentMethod":
        today = date.today()
        if not 1 <= self.exp_month <= 12:
            raise ValueError("exp_month must be between 1 and 12")
        if self.exp_year < today.year or (self.exp_year == today.year and self.exp_month < today.month):
            raise ValueError("Card is expired")
        return self
