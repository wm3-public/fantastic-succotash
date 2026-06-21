# onsetto-client

A typed Python SDK and CLI for the Onsetto account API. Handles the full
two-step auth flow (username/password to MFA) and exposes typed methods
for updating banking and payment details.

## Install

From the workspace root:

```bash
uv sync --all-groups
```

Or as a standalone package:

```bash
pip install onsetto-client
```

## CLI Usage (Part 2)

The CLI authenticates, updates banking details, and updates the payment method.
It prints the masked confirmations returned by the API.

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `ONSETTO_USERNAME` | ✓ | Login email |
| `ONSETTO_PASSWORD` | ✓ | Login password |
| `ONSETTO_MFA_CODE` | ✓ | MFA code (static for test environment) |
| `ONSETTO_ROUTING_NUMBER` | ✓ | 9-digit ABA routing number |
| `ONSETTO_ACCOUNT_NUMBER` | ✓ | 4–17 digit account number |
| `ONSETTO_CARDHOLDER_NAME` | ✓ | Cardholder name |
| `ONSETTO_CARD_NUMBER` | ✓ | Luhn-valid card number (no spaces) |
| `ONSETTO_EXP_MONTH` | ✓ | Expiry month (1–12) |
| `ONSETTO_EXP_YEAR` | ✓ | Expiry year (e.g. 2030) |
| `ONSETTO_CVC` | ✓ | 3–4 digit CVC |
| `ONSETTO_API_BASE_URL` | — | Override API base URL (has a default) |
| `ONSETTO_TIMEOUT` | — | HTTP request timeout in seconds (default `10`) |
| `ONSETTO_LOG_LEVEL` | — | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default `INFO`) |

Variables can be placed in a `.env` file in the working directory.

### Run

```bash
uv run python -m onsetto_client
```

### Example output

```
Banking updated  → account: ••••••7890  routing: •••••0021
Payment updated  → visa ending 4242  exp 12/2030
```

## SDK Usage

```python
from onsetto_client import OnsettoClient

with OnsettoClient() as client:
    client.authenticate("you@example.com", "password", "1234")

    banking = client.update_banking("021000021", "123456789012")
    print(banking.account_masked, banking.routing_masked)

    payment = client.update_payment("Test User", "4242424242424242", 12, 2030, "123")
    print(payment.card_brand, payment.last4)
```

## Error handling

```python
from onsetto_client import (
    AuthenticationError,   # 401
    RateLimitError,        # 429 — automatically retried up to 3 times
    APIError,              # other non-2xx
    NotAuthenticatedError, # called a method before authenticate()
)
```

Rate-limited requests are retried automatically with exponential backoff
with jitter (up to 3 attempts).

## Tests

```bash
uv run pytest onsetto-client/tests/ -v
```

## Approach & tradeoffs

 - `httpx` over `requests`: better timeout defaults, connection pooling, and
    async-ready when needed.
 - `pydantic` for both input validation (routing/account/Luhn checks) and
   response parsing. Catches bad data at the boundary before it hits the API.
 - `tenacity` for rate-limit retries with exponential backoff, which handles the
   "rate-limit awareness" requirement cleanly without manual retry loops.
 - Custom secret fields (`SecretStrExceptLast4`) expose only the last 4
   characters of sensitive strings in `repr`/`str`, preventing accidental logging
   of card/account numbers. Didn't end up using this as much as I thought, since
   the API already returns censored values.
 - PCI DSS-aware logging filter (`SensitiveDataFilter`) redacts card numbers,
   routing numbers, and CVCs from all log output as a last-resort safety net.
 - Sync-only `httpx.Client` is used here because the challenge is a short-lived
   CLI script. I would add async processing for a server-side SDK.

## What I'd improve with more time

 - Async client (`httpx.AsyncClient`) for concurrent requests.
 - Utilize the refresh token instead of just discarding it when obtaining the
   bearer token.
 - Pagination if/where the API supports it (Doesn't appear to right now).
 - Publish the packages to AWS CodeArtifact or similar private PyPi.
