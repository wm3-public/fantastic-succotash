from pydantic import Secret


class SecretCardNumber(Secret[str]):
    def _display(self) -> str:
        return None
