from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClientConfig(BaseSettings):
    """Loads in the settings from the .env file."""

    model_config = SettingsConfigDict(env_prefix="", populate_by_name=True)

    base_url: str = Field(
        default="https://zvyhufnwclhcvmgtqxwp.supabase.co/functions/v1/api-v1",
        alias="ONSETTO_API_BASE_URL",
    )
    timeout: float = 10.0
