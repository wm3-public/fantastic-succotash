"""Logging configuration for onsetto-scraper, with PCI DSS in mind."""

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
    """Last-chance filter that redacts anything that looks like sensitive PCI data."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in REDACT_PATTERNS.values():
            message = pattern.sub(REDACT_CHARACTER, message)
        record.msg = message
        record.args = ()
        return True


logger = logging.getLogger("onsetto_scraper")
logger.addFilter(SensitiveDataFilter())
