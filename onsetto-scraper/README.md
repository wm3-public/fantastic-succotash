# onsetto-scraper

Playwright-based browser automation for the Onsetto web app. Logs in,
completes MFA, then updates banking details and payment method on the
`/app/account` page, and verifies the saved summaries.

## Install

From the workspace root:

```bash
uv sync --all-groups

# Install Playwright browsers (first time only)
uv run playwright install chromium
```

## Usage (Part 1)

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `ONSETTO_BASE_URL` | ✓ | App base URL (e.g. `https://app.example.com`) |
| `ONSETTO_TEST_USERNAME` | ✓ | Login email |
| `ONSETTO_TEST_PASSWORD` | ✓ | Login password |
| `ONSETTO_TEST_MFA_CODE` | ✓ | MFA code (static for the test environment) |
| `ONSETTO_HEADLESS` | — | `true` (default) or `false` to watch the browser |
| `ONSETTO_SLOW_MO` | — | Milliseconds between actions, e.g. `500` (default 0) |
| `ONSETTO_TIMEOUT` | — | Element wait timeout in ms (default `30000`) |
| `ONSETTO_LOG_LEVEL` | — | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default `INFO`) |

Variables can be placed in a `.env` file in the working directory.

### Run

```bash
uv run python -m onsetto_scraper
```

Set `ONSETTO_HEADLESS=false` to watch the browser in action:

```bash
ONSETTO_HEADLESS=false uv run python -m onsetto_scraper
```

## Tests

Unit tests (no browser required):

```bash
uv run pytest onsetto-scraper/tests/ -v
```

Integration tests (require the live app and env vars above):

```bash
uv run pytest onsetto-scraper/tests/ -v -m integration
```

## Approach & tradeoffs
 - Used `playwright` over `selenium` because there are way more reliable waits,
   async support, and it's designed for modern JS heavy sites.
 - Opted for the Page Object Model pattern so each page can own its own
   selectors and interaction logic. Sometimes this can be difficult to manage
   with massive sites, but that wasn't the case here.
 - Used the `data-testid` selectors (with the exception of `#email` and
   `#password`) to match what was specified in the challenge. Generally with a
   scraper or GUI tests, the goal is to use the highest specificity CSS selector
   with the least fragility. IDs are often the best when there is no
   `data-testid` and XPaths are the worst (fragile, hard to read and maintain).
 - Used `pydantic` to validate data before submitting it into browser forms,
   since we don't want to input bad data on a scraper. This allows us to catch
   problems before `playwright` ever deals with them on things like bad card
   numbers or expired cards, etc.
 - Made a little Luhn card number generator for realistic card test data instead
   of hardcoding numbers.
 - Used `tenacity` to retry navigation where necessary, but not on form submission
   to avoid duplicate submits.
 - PCI DSS logging reused from `onsetto-client` to scrub sensitive info out of the
   logs.

## What I'd improve with more time

 - Idempotent form retries to be more resistent to transient failures.
 - Record a `playwright` trace (`page.tracing`) on failure for debugging reasons.
 - Parameterize the banking and payment data via CLI flags instead of hardcoded
   fixtures if this wasn't a one-off challenge to allow for reuse.
 - Add visual regression snapshots alongside the functional verification.
 - Support Firefox and WebKit via Playwright's multi-browser config.
