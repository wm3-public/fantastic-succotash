# Onsetto — Integration Engineer Challenge

A monorepo with two packages:

| Package | Description |
|---|---|
| [`onsetto-client`](./onsetto-client) | Python SDK + CLI for the Onsetto REST API (Part 2) |
| [`onsetto-scraper`](./onsetto-scraper) | Playwright browser automation for the Onsetto web app (Part 1) |

Both are managed as a [uv workspace](https://docs.astral.sh/uv/concepts/workspaces/).

---

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Python 3.13 (installed automatically by uv)

## Install

```bash
git clone <repo-url>
cd onsetto
uv sync --all-groups
```

## Run Part 1 — Web Scraper

See [onsetto-scraper/README.md](./onsetto-scraper/README.md) for full details.

```bash
# Install Playwright browsers (first time only)
uv run playwright install chromium

# Set required env vars, then run
export ONSETTO_BASE_URL="https://..."
export ONSETTO_TEST_USERNAME="you@example.com"
export ONSETTO_TEST_PASSWORD="yourpassword"
export ONSETTO_TEST_MFA_CODE="1234"

uv run python -m onsetto_scraper
```

## Run Part 2 — API Client

See [onsetto-client/README.md](./onsetto-client/README.md) for full details.

```bash
export ONSETTO_USERNAME="you@example.com"
export ONSETTO_PASSWORD="yourpassword"
export ONSETTO_MFA_CODE="1234"
export ONSETTO_ROUTING_NUMBER="021000021"
export ONSETTO_ACCOUNT_NUMBER="123456789012"
export ONSETTO_CARDHOLDER_NAME="Test User"
export ONSETTO_CARD_NUMBER="4242424242424242"
export ONSETTO_EXP_MONTH="12"
export ONSETTO_EXP_YEAR="2030"
export ONSETTO_CVC="123"

uv run python -m onsetto_client
```

## Run Tests

```bash
# All unit tests
uv run pytest onsetto-client/tests/ onsetto-scraper/tests/

# With coverage
uv run pytest onsetto-client/tests/ --cov=onsetto_client --cov-report=term-missing
uv run pytest onsetto-scraper/tests/ --cov=onsetto_scraper --cov-report=term-missing

# Integration tests (require live app + env vars)
uv run pytest onsetto-scraper/tests/ -m integration
```

## Lint & Type Check

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy onsetto-client/src/onsetto_client
uv run mypy onsetto-scraper/src/onsetto_scraper
```

CI runs all of the above on every push via [GitHub Actions](.github/workflows/ci.yml).

---

## Approach & tradeoffs

### Part 1 — Scraper

**Playwright async** was chosen over Selenium for its first-class async
support, reliable auto-waits, and better handling of modern JavaScript heavy
sites. The `input-otp` component required `force=True` on the OTP click to
bypass a `pointer-events: none` wrapper and reach the actual input for the MFA
form.

The page object model pattern (`LoginPage`, `MfaPage`, `AccountPage`) keeps all
selectors and interaction logic co-located with the page they describe. The
orchestrator (`AccountScraper.run()`) expresses intent without any raw CSS
selectors. Integration tests import behaviour, not selectors.

Pydantic models validate data before the browser is launched. This way, a bad
routing number or expired card raises a `ValidationError` immediately rather
than failing mid-flow after a browser window opens.

The tenacity package retries navigation on transient failures (up to 3 attempts,
exponential backoff with jitter). Form submissions are intentionally not
retried to avoid duplicate submits.

### Part 2 — API client

We used `httpx` over `requests` for better timeout defaults and connection
pooling. Async is the natural next step but adds complexity for a short-lived
challenge script.

Again, pydantic models validate all inputs (routing/account number format,
Luhn check, expiry, CVC) at model construction time and parses every API
response, which will catch schema drift at the boundary before it
propagates. Also, `tenacity` handles 429 rate-limit responses with exponential
backoff with jitter (up to 3 retries) without manual retry loops.

I extended Pydantic's `Secret` for masking sensitive data in a way that makes
more sense for card numbers and account numbers (exposing the last 4 digits),
but since the API already returned masked values, I didn't end up using it much.
I also added a filter to the logger to try to catch anything that looked like a
sensitive value, since logging PCI data in plaintext is a huge problem.

---

## What I'd improve with more time
 - Async client (`httpx.AsyncClient`) for concurrent requests.
 - Utilize the refresh token instead of just discarding it when obtaining the
   bearer token.
 - Pagination if/where the API supports it (Doesn't appear to right now).
 - Publish the packages to AWS CodeArtifact or similar private PyPi.
 - Idempotent form retries to be more resistent to transient failures.
 - Record a `playwright` trace (`page.tracing`) on failure for debugging reasons.
 - Parameterize the banking and payment data via CLI flags instead of hardcoded
   fixtures if this wasn't a one-off challenge to allow for reuse.
 - Add visual regression snapshots alongside the functional verification.
 - Support Firefox and WebKit via Playwright's multi-browser config.
