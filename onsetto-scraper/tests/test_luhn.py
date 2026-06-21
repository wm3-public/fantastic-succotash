import pytest
from onsetto_scraper.luhn import luhn_checksum, luhn_generate, luhn_is_valid


def test_luhn_is_valid_known_good() -> None:
    assert luhn_is_valid("4242424242424242") is True


def test_luhn_is_valid_known_bad() -> None:
    assert luhn_is_valid("4242424242424243") is False


def test_luhn_is_valid_visa_test_card() -> None:
    assert luhn_is_valid("4111111111111111") is True


def test_luhn_is_valid_mastercard_test_card() -> None:
    assert luhn_is_valid("5500005555555559") is True


def test_luhn_is_valid_non_digit_returns_false() -> None:
    assert luhn_is_valid("4242abcd42424242") is False


def test_luhn_is_valid_empty_returns_false() -> None:
    assert luhn_is_valid("") is False


def test_luhn_generate_passes_validation() -> None:
    card = luhn_generate()
    assert luhn_is_valid(card)


def test_luhn_generate_correct_default_length() -> None:
    card = luhn_generate()
    assert len(card) == 16


def test_luhn_generate_custom_length() -> None:
    card = luhn_generate(prefix="4", length=13)
    assert len(card) == 13
    assert luhn_is_valid(card)


def test_luhn_generate_respects_prefix() -> None:
    card = luhn_generate(prefix="51")
    assert card.startswith("51")


def test_luhn_generate_all_digits() -> None:
    card = luhn_generate()
    assert card.isdigit()


def test_luhn_checksum_known_value() -> None:
    # For "424242424242424" (15 digits), checksum should be 2
    assert luhn_checksum("424242424242424") == 2


def test_luhn_checksum_empty_raises() -> None:
    with pytest.raises(ValueError, match="non-empty digit string"):
        luhn_checksum("")


def test_luhn_checksum_non_digit_raises() -> None:
    with pytest.raises(ValueError, match="non-empty digit string"):
        luhn_checksum("abc")


def test_luhn_generate_non_digit_prefix_raises() -> None:
    with pytest.raises(ValueError, match="prefix must be"):
        luhn_generate(prefix="abc")


def test_luhn_generate_empty_prefix_raises() -> None:
    with pytest.raises(ValueError, match="prefix must be"):
        luhn_generate(prefix="")


def test_luhn_generate_length_too_short_raises() -> None:
    with pytest.raises(ValueError, match="too short"):
        luhn_generate(prefix="4242", length=4)
