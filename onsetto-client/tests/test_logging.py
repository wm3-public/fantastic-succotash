import logging

from onsetto_client.logging import SensitiveDataFilter


def _apply_filter(message: str) -> str:
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg=message, args=(), exc_info=None,
    )
    SensitiveDataFilter().filter(record)
    return record.msg


def test_card_number_redacted() -> None:
    result = _apply_filter("Card: 4242424242424242 charged")
    assert "4242424242424242" not in result


def test_card_number_with_spaces_redacted() -> None:
    result = _apply_filter("Card: 4242 4242 4242 4242 charged")
    assert "4242 4242 4242 4242" not in result


def test_routing_number_redacted() -> None:
    result = _apply_filter("Routing: 021000021")
    assert "021000021" not in result


def test_cvc_redacted_colon_format() -> None:
    result = _apply_filter("cvc: 123 submitted")
    assert "123" not in result


def test_cvc_redacted_equals_format() -> None:
    result = _apply_filter("CVC=456 submitted")
    assert "456" not in result


def test_ssn_redacted() -> None:
    result = _apply_filter("SSN: 123-45-6789 on file")
    assert "123-45-6789" not in result


def test_normal_text_not_redacted() -> None:
    message = "User logged in successfully"
    assert _apply_filter(message) == message


def test_email_not_redacted() -> None:
    message = "Email: user@example.com"
    assert _apply_filter(message) == message


def test_card_number_with_dashes_redacted() -> None:
    result = _apply_filter("Card: 4242-4242-4242-4242 charged")
    assert "4242-4242-4242-4242" not in result


def test_card_number_13_digits_redacted() -> None:
    # 13-digit Visa (minimum per regex)
    result = _apply_filter("Card: 4111111111111 charged")
    assert "4111111111111" not in result


def test_card_number_19_digits_redacted() -> None:
    # 19-digit Maestro (maximum per regex)
    result = _apply_filter("Card: 6759649826438453106 charged")
    assert "6759649826438453106" not in result


def test_cvc_4_digits_redacted() -> None:
    # Amex uses a 4-digit CVC
    result = _apply_filter("cvc: 1234 submitted")
    assert "1234" not in result


def test_10_digit_number_not_matched_as_routing() -> None:
    # Routing pattern is \b\d{9}\b — a 10-digit number has no word boundary at position 9
    result = _apply_filter("Account: 1234567890")
    assert "1234567890" in result


def test_multiple_sensitive_fields_all_redacted() -> None:
    message = "Card: 4242424242424242 routing: 021000021 SSN: 123-45-6789"
    result = _apply_filter(message)
    assert "4242424242424242" not in result
    assert "021000021" not in result
    assert "123-45-6789" not in result


def test_filter_applied_to_module_logger() -> None:
    import onsetto_client.logging as ol
    assert any(
        isinstance(f, SensitiveDataFilter) for f in ol.logger.filters
    )
