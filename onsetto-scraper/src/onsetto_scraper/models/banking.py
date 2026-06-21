import re

from pydantic import BaseModel, field_validator


class BankingDetails(BaseModel):
    """Models a bank account for the scraper."""

    routing_number: str
    account_number: str

    @field_validator("routing_number")
    @classmethod
    def validate_routing(cls, value: str) -> str:
        """Validate the routing number is the correct number of digits.

        Args:
            value (str): The current value for the routing number

        Raise:
            ValueError if the routing number is not 9 digits

        Return:
            the valid str routing number
        """
        if not re.fullmatch(r"\d{9}", value):
            raise ValueError("routing_number must be exactly 9 digits")
        return value

    @field_validator("account_number")
    @classmethod
    def validate_account(cls, value: str) -> str:
        """Valiedate the accound number is the correct number of digits.

        Args:
            value (str): The current value for the account number

        Raise:
            ValueError if the account number is not 4-17 digits long

        Return:
            the valid account number
        """
        if not re.fullmatch(r"\d{4,17}", value):
            raise ValueError("account_number must be 4–17 digits")
        return value
