"""Unit tests for the scraper CLI entry point (__main__.py)."""

from unittest.mock import AsyncMock, patch

import pytest
from onsetto_scraper.exceptions import LoginError, NavigationError


def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ONSETTO_BASE_URL", "https://example.com")
    monkeypatch.setenv("ONSETTO_TEST_USERNAME", "user@test.com")
    monkeypatch.setenv("ONSETTO_TEST_PASSWORD", "pass")
    monkeypatch.setenv("ONSETTO_TEST_MFA_CODE", "1234")


def _make_mock_scraper(run_side_effect: Exception | None = None) -> AsyncMock:
    mock = AsyncMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    if run_side_effect is not None:
        mock.run.side_effect = run_side_effect
    return mock


def test_main_config_error_exits() -> None:
    # Simulate any config loading failure. We patch ScraperConfig directly because
    # pydantic-settings also reads from .env files, so deleting env vars alone is
    # not sufficient to force a failure in all environments.
    from onsetto_scraper.__main__ import main

    with (
        patch("onsetto_scraper.__main__.ScraperConfig", side_effect=Exception("Field required")),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 1


def test_main_login_error_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)
    from onsetto_scraper.__main__ import main

    mock = _make_mock_scraper(LoginError("bad creds"))
    with (
        patch("onsetto_scraper.__main__.AccountScraper", return_value=mock),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 1


def test_main_navigation_error_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)
    from onsetto_scraper.__main__ import main

    with (
        patch(
            "onsetto_scraper.__main__.AccountScraper",
            return_value=_make_mock_scraper(NavigationError("https://example.com/app/account", "timeout")),
        ),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 1


def test_main_success_calls_run(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)
    from onsetto_scraper.__main__ import main

    mock = _make_mock_scraper()

    with patch("onsetto_scraper.__main__.AccountScraper", return_value=mock):
        main()

    mock.run.assert_called_once()


def test_main_passes_credentials_to_run(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)
    from onsetto_scraper.__main__ import main

    mock = _make_mock_scraper()

    with patch("onsetto_scraper.__main__.AccountScraper", return_value=mock):
        main()

    kwargs = mock.run.call_args.kwargs
    assert kwargs["username"] == "user@test.com"
    assert kwargs["password"] == "pass"
    assert kwargs["mfa_code"] == "1234"


def test_main_invalid_account_data_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)
    monkeypatch.setenv("ONSETTO_ROUTING_NUMBER", "tooshort")  # invalid routing
    from onsetto_scraper.__main__ import main

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
