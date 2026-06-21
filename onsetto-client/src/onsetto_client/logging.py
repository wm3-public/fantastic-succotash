"""Logging configuration for the package, with PCI DSS in mind."""

import logging
import re


REDACT_CHARACTER: str = "*"
REDACT_PATTERNS: dict[str, re.Pattern[str]] = {
    "card_number": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    "routing_number": re.compile(r"\b\d{9}\b"),
    "cvc": re.compile(r"(?i)\bcvc[\"']?\s*[:=]\s*[\"']?\d{3,4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}


class SensitiveDataFilter(logging.Filter):
    """We have SensitiveModel configured in the models directory, but when I
    worked at American Greetings, we had people accidentally put card numbers
    in the name fields, etc. This is the last chance to prevent logging
    anything that _looks_ like sensitive information.

    Also, since this is a technical challenge, I'm sticking with only flat
    fields here, but I'm aware there is a limitation on this function that
    would miss things like extra={"account": {"routing": "####"}}, so this
    isn't production ready. Just wanted to call that out. :-)
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Take a log record, filter it, let the logger know we're done.

        Args:
            record (logging.LogRecord): The record to filter

        Return:
            True once filtering is completed
        """
        message = record.getMessage()
        for pattern in REDACT_PATTERNS.values():
            message = pattern.sub()
        return True
