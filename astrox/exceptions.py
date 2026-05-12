"""Custom exceptions for the astrox package."""

from __future__ import annotations

from typing import Any


class AstroxError(Exception):
    """Base exception for all astrox errors."""

    pass


class AstroxAPIError(AstroxError):
    """API returned IsSuccess=false or other API-level error."""

    def __init__(self, message: str, endpoint: str, response: Any):
        """Initialize API error.

        Args:
            message: Error message from API
            endpoint: API endpoint that was called
            response: Response object from requests
        """
        self.message = message
        self.endpoint = endpoint
        self.response = response
        super().__init__(message)


class AstroxHTTPError(AstroxError):
    """HTTP status code indicates error."""

    def __init__(self, status_code: int, message: str, endpoint: str, response: Any):
        """Initialize HTTP error.

        Args:
            status_code: HTTP status code
            message: Error message
            endpoint: API endpoint that was called
            response: Response object from requests
        """
        self.status_code = status_code
        self.message = message
        self.endpoint = endpoint
        self.response = response
        super().__init__(f"HTTP {status_code}: {message}")


class AstroxTimeoutError(AstroxError):
    """Request timed out."""

    def __init__(self, endpoint: str, timeout: float):
        """Initialize timeout error.

        Args:
            endpoint: API endpoint that was called
            timeout: Timeout value in seconds
        """
        self.endpoint = endpoint
        self.timeout = timeout
        super().__init__(f"Request to {endpoint} timed out after {timeout}s")


class AstroxConnectionError(AstroxError):
    """Failed to connect to API."""

    def __init__(self, message: str, original_error: Exception | None):
        """Initialize connection error.

        Args:
            message: Error message
            original_error: Original exception that caused the error
        """
        self.message = message
        self.original_error = original_error
        super().__init__(message)


class AstroxValidationError(AstroxError):
    """Response validation failed."""

    def __init__(self, message: str, errors: list[dict[str, Any]]):
        """Initialize validation error.

        Args:
            message: Error message
            errors: List of validation errors from Pydantic
        """
        self.message = message
        self.errors = errors
        super().__init__(message)
