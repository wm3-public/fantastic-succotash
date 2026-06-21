"""Verify the scraper logger redacts sensitive data."""

import logging

from onsetto_scraper.logging import SensitiveDataFilter
from onsetto_scraper.logging import logger as scraper_logger


def _apply_filter(message: str) -> str:
    record = logging.LogRecord(
        name="onsetto_scraper",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    f = SensitiveDataFilter()
    f.filter(record)
    return record.getMessage()


def test_scraper_logger_has_filter() -> None:
    assert any(isinstance(f, SensitiveDataFilter) for f in scraper_logger.filters)


def test_card_number_redacted() -> None:
    result = _apply_filter("Card: 4242424242424242")
    assert "4242424242424242" not in result


def test_routing_number_redacted() -> None:
    result = _apply_filter("Routing: 021000021")
    assert "021000021" not in result


def test_cvc_redacted() -> None:
    result = _apply_filter('cvc: "123"')
    assert "123" not in result


def test_normal_text_unchanged() -> None:
    result = _apply_filter("User logged in successfully")
    assert result == "User logged in successfully"
