from enum import Enum


class OrderStatus(Enum):
    """Represents the status of an order in our system."""

    PAID = "paid"
    PENDING = "pending"
