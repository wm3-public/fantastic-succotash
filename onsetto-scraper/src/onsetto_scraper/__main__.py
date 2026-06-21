"""CLI entry point: python -m onsetto_scraper"""

import asyncio
import logging
import os
import sys

from pydantic import ValidationError

from onsetto_scraper.config import ScraperConfig
from onsetto_scraper.exceptions import ScraperError
from onsetto_scraper.luhn import luhn_generate
from onsetto_scraper.models.banking import BankingDetails
from onsetto_scraper.models.payment import PaymentMethod
from onsetto_scraper.scraper import AccountScraper

logger = logging.getLogger("onsetto_scraper")


async def _run() -> None:
    try:
        config = ScraperConfig()  # type: ignore[call-arg]  # fields loaded from env
    except Exception as exc:
        logger.error("Configuration error: %s", exc)
        logger.error(
            "\nRequired environment variables:\n"
            "  ONSETTO_BASE_URL         app base URL\n"
            "  ONSETTO_TEST_USERNAME    login email\n"
            "  ONSETTO_TEST_PASSWORD    login password\n"
            "  ONSETTO_TEST_MFA_CODE    MFA code\n"
            "\nOptional:\n"
            "  ONSETTO_HEADLESS         true (default) or false\n"
            "  ONSETTO_SLOW_MO          milliseconds between actions (default 0)\n"
            "  ONSETTO_TIMEOUT          element wait timeout in ms (default 30000)\n"
            "  ONSETTO_LOG_LEVEL        DEBUG, INFO, WARNING, ERROR (default INFO)\n"
            "  ONSETTO_ROUTING_NUMBER   9-digit routing number (default 021000021)\n"
            "  ONSETTO_ACCOUNT_NUMBER   4–17 digit account number (default 123456789012)\n"
            "  ONSETTO_CARDHOLDER_NAME  cardholder name (default 'Test User')\n"
            "  ONSETTO_CARD_NUMBER      Luhn-valid card number (default: auto-generated)\n"
            "  ONSETTO_EXP_MONTH        expiry month 1–12 (default 12)\n"
            "  ONSETTO_EXP_YEAR         expiry year (default 2030)\n"
            "  ONSETTO_CVC              3–4 digit CVC (default 123)"
        )
        sys.exit(1)

    card_num = config.card_number or luhn_generate(prefix="4", length=16)

    try:
        banking = BankingDetails(routing_number=config.routing_number, account_number=config.account_number)
        payment = PaymentMethod(
            cardholder_name=config.cardholder_name,
            card_number=card_num,
            exp_month=config.exp_month,
            exp_year=config.exp_year,
            cvc=config.cvc,
        )
    except ValidationError as exc:
        logger.error("Invalid account data configuration: %s", exc)
        sys.exit(1)

    try:
        async with AccountScraper(config) as scraper:
            await scraper.run(
                banking,
                payment,
                username=config.test_username,
                password=config.test_password,
                mfa_code=config.test_mfa_code,
            )
        logger.info("Account update completed successfully.")
    except ScraperError as exc:
        logger.error("Scraper error: %s", exc)
        sys.exit(1)


def main() -> None:
    _level = getattr(logging, os.getenv("ONSETTO_LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=_level, format="%(levelname)s %(name)s: %(message)s")
    asyncio.run(_run())


if __name__ == "__main__":
    main()
