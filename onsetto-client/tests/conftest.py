import pytest
from onsetto_client import OnsettoClient
from onsetto_client.config import ClientConfig

BASE_URL = "http://test"
TEST_TOKEN = "test-access-token"


@pytest.fixture
def config() -> ClientConfig:
    return ClientConfig(ONSETTO_API_BASE_URL=BASE_URL)


@pytest.fixture
def unauthenticated_client(config: ClientConfig) -> OnsettoClient:
    return OnsettoClient(config)


@pytest.fixture
def client(config: ClientConfig) -> OnsettoClient:
    c = OnsettoClient(config)
    c._access_token = TEST_TOKEN
    return c
