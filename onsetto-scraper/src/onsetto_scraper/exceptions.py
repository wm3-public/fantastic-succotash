class ScraperError(Exception):
    """Base exception for all onsetto-scraper errors."""


class NavigationError(ScraperError):
    """Raised when a page navigation fails or times out."""

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Navigation to {url!r} failed: {reason}")


class LoginError(ScraperError):
    """Raised when login or MFA verification fails."""


class ElementNotFoundError(ScraperError):
    """Raised when a required element is not visible after waiting."""

    def __init__(self, selector: str) -> None:
        self.selector = selector
        super().__init__(f"Element not found: {selector!r}")


class VerificationError(ScraperError):
    """Raised when saved data does not appear in the summary section."""
