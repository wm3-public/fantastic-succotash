class OnsettoError(Exception):
    """Base exception for all onsetto-client errors."""


class NotAuthenticatedError(OnsettoError):
    """Raised when an authenticated endpoint is called before authenticate()."""

    def __init__(self) -> None:
        super().__init__("Call authenticate() before using authenticated endpoints.")


class APIError(OnsettoError):
    """Raised when the API returns a non-2xx response."""

    def __init__(self, status_code: int, detail: str) -> None:
        """Initialize the APIError.

        Args:
            status_code (int): The HTTP status code of the response
            detail (str): Information about the error
        """
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API error {status_code}: {detail}")


class AuthenticationError(APIError):
    """Raised on 401 responses."""


class RateLimitError(APIError):
    """Raised on 429 responses."""
