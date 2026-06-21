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
    """Last-chance redaction for anything that looks like PCI-sensitive data.

    Covers cases where sensitive values are inadvertently placed in free-text
    fields (e.g. a card number typed into a name field). Note: only flat
    string-formatted log messages are scanned. Nested structures passed as
    `extra` dicts bypass this filter and must be sanitised upstream (known
    limitation for this exercise).
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
            message = pattern.sub(REDACT_CHARACTER, message)
        record.msg = message
        record.args = ()
        return True


logger = logging.getLogger("onsetto_client")
logger.addFilter(SensitiveDataFilter())
