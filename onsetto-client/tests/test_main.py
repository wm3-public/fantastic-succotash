"""Unit tests for the CLI entry point (__main__.py)."""

from unittest.mock import MagicMock, patch

import pytest
from onsetto_client.models.output_models import BankAccountUpdatedResponse, PaymentMethodResponse


def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ONSETTO_USERNAME", "user@example.com")
    monkeypatch.setenv("ONSETTO_PASSWORD", "password123")
    monkeypatch.setenv("ONSETTO_MFA_CODE", "1234")
    monkeypatch.setenv("ONSETTO_ROUTING_NUMBER", "021000021")
    monkeypatch.setenv("ONSETTO_ACCOUNT_NUMBER", "123456789012")
    monkeypatch.setenv("ONSETTO_CARDHOLDER_NAME", "Test User")
    monkeypatch.setenv("ONSETTO_CARD_NUMBER", "4242424242424242")
    monkeypatch.setenv("ONSETTO_EXP_MONTH", "12")
    monkeypatch.setenv("ONSETTO_EXP_YEAR", "2030")
    monkeypatch.setenv("ONSETTO_CVC", "123")


def _make_mock_client(
    banking: BankAccountUpdatedResponse | None = None,
    payment: PaymentMethodResponse | None = None,
) -> MagicMock:
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=None)
    if banking is not None:
        mock.update_banking.return_value = banking
    if payment is not None:
        mock.update_payment.return_value = payment
    return mock


_BANKING = BankAccountUpdatedResponse(account_masked="••••••7890", routing_masked="•••••0021", token="btok")
_PAYMENT = PaymentMethodResponse(card_brand="visa", exp_month=12, exp_year=2030, last4="4242", token="tok")


def test_main_config_error_exits() -> None:
    # Simulate any config loading failure (e.g. missing required env vars).
    # We patch CLIConfig directly because pydantic-settings also reads from
    # .env files, so deleting env vars alone is not sufficient to force a
    # failure in all environments.
    from onsetto_client.__main__ import main

    with (
        patch("onsetto_client.__main__.CLIConfig", side_effect=Exception("Field required")),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 1


def test_main_authentication_error_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)
    from onsetto_client.__main__ import main
    from onsetto_client.exceptions import AuthenticationError

    mock = _make_mock_client(_BANKING, _PAYMENT)
    mock.authenticate.side_effect = AuthenticationError(401, "Invalid credentials")

    with patch("onsetto_client.__main__.OnsettoClient", return_value=mock), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_api_error_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)
    from onsetto_client.__main__ import main
    from onsetto_client.exceptions import APIError

    mock = _make_mock_client(_BANKING, _PAYMENT)
    mock.update_banking.side_effect = APIError(500, "Server error")

    with patch("onsetto_client.__main__.OnsettoClient", return_value=mock), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_success_prints_banking_confirmation(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _set_env(monkeypatch)
    from onsetto_client.__main__ import main

    with patch("onsetto_client.__main__.OnsettoClient", return_value=_make_mock_client(_BANKING, _PAYMENT)):
        main()

    out = capsys.readouterr().out
    assert "••••••7890" in out
    assert "•••••0021" in out


def test_main_success_prints_payment_confirmation(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _set_env(monkeypatch)
    from onsetto_client.__main__ import main

    with patch("onsetto_client.__main__.OnsettoClient", return_value=_make_mock_client(_BANKING, _PAYMENT)):
        main()

    out = capsys.readouterr().out
    assert "visa" in out
    assert "4242" in out
    assert "12/2030" in out


def test_main_passes_credentials_to_authenticate(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)
    from onsetto_client.__main__ import main

    mock = _make_mock_client(_BANKING, _PAYMENT)

    with patch("onsetto_client.__main__.OnsettoClient", return_value=mock):
        main()

    mock.authenticate.assert_called_once_with("user@example.com", "password123", "1234")


def test_main_passes_banking_details(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)
    from onsetto_client.__main__ import main

    mock = _make_mock_client(_BANKING, _PAYMENT)

    with patch("onsetto_client.__main__.OnsettoClient", return_value=mock):
        main()

    mock.update_banking.assert_called_once_with("021000021", "123456789012")


def test_main_passes_payment_details(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)
    from onsetto_client.__main__ import main

    mock = _make_mock_client(_BANKING, _PAYMENT)

    with patch("onsetto_client.__main__.OnsettoClient", return_value=mock):
        main()

    mock.update_payment.assert_called_once_with("Test User", "4242424242424242", 12, 2030, "123")
