from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClientConfig(BaseSettings):
    """Loads SDK settings from environment/.env file with sensible defaults."""

    model_config = SettingsConfigDict(
        env_prefix="ONSETTO_",
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    # Uses a full explicit alias to avoid colliding with the scraper's
    # `ONSETTO_BASE_URL` (which points to the web app URL, not the API).
    base_url: str = Field(
        default="https://zvyhufnwclhcvmgtqxwp.supabase.co/functions/v1/api-v1",
        validation_alias="ONSETTO_API_BASE_URL",
    )
    timeout: float = 10.0
    log_level: str = "INFO"


class CLIConfig(ClientConfig):
    """Extends ClientConfig with credentials and account data for the
    challenge submission.
    """

    # Auth credentials — SecretStr prevents accidental repr/log exposure.
    username: str
    password: SecretStr
    mfa_code: SecretStr

    # Banking details
    routing_number: str
    account_number: str

    # Payment details
    cardholder_name: str
    card_number: str
    exp_month: int
    exp_year: int
    cvc: str
