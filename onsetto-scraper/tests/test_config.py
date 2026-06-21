import pytest
from onsetto_scraper.config import ScraperConfig
from pydantic import ValidationError


def test_config_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ONSETTO_BASE_URL", "https://example.com")
    monkeypatch.setenv("ONSETTO_TEST_USERNAME", "user@test.com")
    monkeypatch.setenv("ONSETTO_TEST_PASSWORD", "secret")
    monkeypatch.setenv("ONSETTO_TEST_MFA_CODE", "123456")

    config = ScraperConfig()
    assert config.base_url == "https://example.com"
    assert config.test_username == "user@test.com"
    assert config.test_password == "secret"
    assert config.test_mfa_code == "123456"


def test_config_headless_defaults_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ONSETTO_BASE_URL", "https://example.com")
    monkeypatch.setenv("ONSETTO_TEST_USERNAME", "u")
    monkeypatch.setenv("ONSETTO_TEST_PASSWORD", "p")
    monkeypatch.setenv("ONSETTO_TEST_MFA_CODE", "c")
    monkeypatch.delenv("ONSETTO_HEADLESS", raising=False)

    config = ScraperConfig()
    assert config.headless is True


def test_config_headless_can_be_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ONSETTO_BASE_URL", "https://example.com")
    monkeypatch.setenv("ONSETTO_TEST_USERNAME", "u")
    monkeypatch.setenv("ONSETTO_TEST_PASSWORD", "p")
    monkeypatch.setenv("ONSETTO_TEST_MFA_CODE", "c")
    monkeypatch.setenv("ONSETTO_HEADLESS", "false")

    config = ScraperConfig()
    assert config.headless is False


def test_config_timeout_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ONSETTO_BASE_URL", "https://example.com")
    monkeypatch.setenv("ONSETTO_TEST_USERNAME", "u")
    monkeypatch.setenv("ONSETTO_TEST_PASSWORD", "p")
    monkeypatch.setenv("ONSETTO_TEST_MFA_CODE", "c")
    monkeypatch.delenv("ONSETTO_TIMEOUT", raising=False)

    config = ScraperConfig()
    assert config.timeout == 30_000.0


def test_config_missing_required_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ONSETTO_BASE_URL", raising=False)
    monkeypatch.delenv("ONSETTO_TEST_USERNAME", raising=False)
    monkeypatch.delenv("ONSETTO_TEST_PASSWORD", raising=False)
    monkeypatch.delenv("ONSETTO_TEST_MFA_CODE", raising=False)

    with pytest.raises(ValidationError):
        ScraperConfig(_env_file=None)
