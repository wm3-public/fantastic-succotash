"""CLI entry point: `uv run python -m onsetto_client`."""

import logging
import os
import sys

from pydantic import ValidationError

from .client import OnsettoClient
from .config import CLIConfig
from .exceptions import OnsettoError

logger = logging.getLogger("onsetto_client")


def main() -> None:
    """Main entry point for the command line. Checks the configuration, reports
    any missing required config values, then runs what was requested per the
    challenge instructions:

    • Auth flow: POST /auth/token → POST /auth/mfa/verify to obtain a bearer
      token.
    • Call PUT /account/banking and PUT /account/payment with the bearer token.
    • Print the masked confirmation returned for each update.
    • Handle errors gracefully (bad credentials, wrong MFA, validation, rate
      limits).
    """
    _level = getattr(logging, os.getenv("ONSETTO_LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=_level, format="%(levelname)s %(name)s: %(message)s")

    try:
        cli = CLIConfig()  # type: ignore[call-arg]  # fields loaded from env
    except Exception as exc:
        logger.error("Configuration error: %s", exc)
        logger.error(
            "\nRequired environment variables:\n"
            "  ONSETTO_USERNAME        your login email\n"
            "  ONSETTO_PASSWORD        your password\n"
            "  ONSETTO_MFA_CODE        your MFA code\n"
            "  ONSETTO_ROUTING_NUMBER  9-digit routing number\n"
            "  ONSETTO_ACCOUNT_NUMBER  4–17 digit account number\n"
            "  ONSETTO_CARDHOLDER_NAME cardholder name\n"
            "  ONSETTO_CARD_NUMBER     Luhn-valid card number\n"
            "  ONSETTO_EXP_MONTH       expiry month (1–12)\n"
            "  ONSETTO_EXP_YEAR        expiry year (e.g. 2028)\n"
            "  ONSETTO_CVC             3–4 digit CVC\n"
            "\nOptional:\n"
            "  ONSETTO_API_BASE_URL    override API base URL\n"
            "  ONSETTO_TIMEOUT         HTTP request timeout in seconds (default 10)\n"
            "  ONSETTO_LOG_LEVEL       DEBUG, INFO, WARNING, ERROR (default INFO)"
        )
        sys.exit(1)

    try:
        with OnsettoClient(cli) as client:
            logger.info("Authenticating…")
            client.authenticate(
                cli.username,
                cli.password.get_secret_value(),
                cli.mfa_code.get_secret_value(),
            )
            logger.info("Authentication successful")

            banking = client.update_banking(cli.routing_number, cli.account_number)
            print(f"Banking updated  → account: {banking.account_masked}  routing: {banking.routing_masked}")

            payment = client.update_payment(
                cli.cardholder_name,
                cli.card_number,
                cli.exp_month,
                cli.exp_year,
                cli.cvc,
            )
            print(
                f"Payment updated  → {payment.card_brand} ending {payment.last4}"
                f"  exp {payment.exp_month:02d}/{payment.exp_year}"
            )

    except OnsettoError as exc:
        logger.error("Error: %s", exc)
        sys.exit(1)
    except ValidationError as exc:
        logger.error("Unexpected API response shape: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
