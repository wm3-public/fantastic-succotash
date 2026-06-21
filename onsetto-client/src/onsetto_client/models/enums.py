from enum import Enum


class OrderStatus(Enum):
    """Represents the status of an order in our system.

    NOTE: I've only seen paid and pending through the UI, but this could be
    expanded if necessary.
    """

    PAID = "paid"
    PENDING = "pending"
