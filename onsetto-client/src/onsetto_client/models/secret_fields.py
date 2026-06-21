from pydantic import Secret


class SecretStr(Secret[str]):
    """Special field to mask each character individually."""

    def _display(self) -> str:
        """Get the display str.

        Return:
            str with all characters censored with "*"
        """
        return "*" * len(self.get_secret_value())


class SecretStrExceptLast4(Secret[str]):
    """Special field to mask each character individually except for the
    last 4.
    """

    def _display(self) -> str:
        """Get the display str.

        Return:
            str with all characters except the last 4 censored with "*"
        """
        val = self.get_secret_value()
        return "*" * (len(val) - 4) + val[-4:]
