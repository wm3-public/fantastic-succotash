"""Luhn algorithm utilities for card number validation and generation."""

import secrets


def luhn_checksum(digits: str) -> int:
    """Return the Luhn check digit for a string of digits (excluding the check
    digit itself).

    Args:
        digits (str): The card number to check

    Raise:
        ValueError if the digits aren't digits

    Return:
        the int Luhn checksum digit
    """
    if not digits or not digits.isdigit():
        raise ValueError(f"Expected a non-empty digit string, got {digits!r}")
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return (10 - (total % 10)) % 10


def luhn_is_valid(card_number: str) -> bool:
    """Return True if card_number passes the Luhn check.

    Args:
        card_number (str): The card number to check

    Return:
        True if it passes, False otherwise
    """
    if len(card_number) < 2 or not card_number.isdigit():
        return False
    return luhn_checksum(card_number[:-1]) == int(card_number[-1])


def luhn_generate(prefix: str = "4", length: int = 16) -> str:
    """Generate a Luhn-valid card number with the given prefix and total length.

    Fills (length - 1) positions with prefix + random digits, then computes
    and appends the Luhn check digit.

    Args:
        prefix (str): The card number prefix to use
        length (int): The length of the card nnumber to generate

    Return:
        the str generated valid card number
    """
    if not prefix or not prefix.isdigit():
        raise ValueError(f"prefix must be a non-empty digit string, got {prefix!r}")
    if length < len(prefix) + 1:
        raise ValueError(f"length {length} too short for prefix {prefix!r}")

    random_length = length - len(prefix) - 1
    random_digits = "".join(str(secrets.randbelow(10)) for _ in range(random_length))
    body = prefix + random_digits
    check = luhn_checksum(body)
    return body + str(check)
