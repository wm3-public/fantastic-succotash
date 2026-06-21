from pydantic_settings import BaseSettings, SettingsConfigDict


class ScraperConfig(BaseSettings):
    """Loads scraper settings from environment / .env file.

    All fields are read from env vars with the ONSETTO_ prefix, e.g.
    ONSETTO_BASE_URL, ONSETTO_TEST_USERNAME, ONSETTO_TEST_PASSWORD, etc.
    """

    model_config = SettingsConfigDict(
        env_prefix="ONSETTO_",
        env_file=".env",
        extra="ignore",
    )

    # App URL and credentials
    base_url: str
    test_username: str
    test_password: str
    test_mfa_code: str

    # Browser settings
    headless: bool = True
    slow_mo: float = 0.0
    timeout: float = 30_000.0
    log_level: str = "INFO"

    # Banking details submitted on the account page
    routing_number: str = "021000021"
    account_number: str = "123456789012"

    # Payment details submitted on the account page (card_number="" → auto-generated)
    cardholder_name: str = "Test User"
    card_number: str = ""
    exp_month: int = 12
    exp_year: int = 2030
    cvc: str = "123"
