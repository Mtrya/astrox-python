"""HTTP client with retry mechanism and ContextVar-based session management."""

from __future__ import annotations

import json
import time
from contextvars import ContextVar
from typing import Any, TypeVar

import requests
from pydantic import BaseModel, ValidationError

from astrox import exceptions

T = TypeVar("T", bound=BaseModel)

# Default configuration
DEFAULT_BASE_URL = "http://astrox.cn:8765"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0  # seconds

# ContextVar for thread-safe default session management
_default_session: ContextVar[HTTPClient | None] = ContextVar("session", default=None)


def _make_request(
    endpoint: str,
    data: dict[str, Any] | BaseModel,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    session: requests.Session | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Make a POST request to the API with retry mechanism.

    Args:
        endpoint: API endpoint (e.g., "/Coverage/ComputeCoverage")
        data: Request payload (dict or Pydantic model)
        base_url: Base URL for the API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (exponential backoff)
        session: Optional requests.Session to use
        params: Optional query parameters

    Returns:
        Parsed JSON response as dict

    Raises:
        AstroxAPIError: If IsSuccess=false in response
        AstroxHTTPError: If HTTP status code indicates error
        AstroxTimeoutError: If request times out
        AstroxConnectionError: If connection fails after all retries
    """
    url = f"{base_url.rstrip('/')}{endpoint}"
    use_session = session or requests.Session()

    # Set headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Convert Pydantic model to dict if needed
    if isinstance(data, BaseModel):
        json_data = json.loads(
            data.model_dump_json(by_alias=True, exclude_none=True)
        )
    else:
        json_data = data

    last_exception = None

    for attempt in range(max_retries):
        try:
            response = use_session.post(
                url,
                json=json_data,
                headers=headers,
                timeout=timeout,
                params=params,
            )

            # Check HTTP status
            if response.status_code >= 400:
                # Don't retry client errors (4xx), only server errors (5xx)
                if response.status_code < 500:
                    raise exceptions.AstroxHTTPError(
                        status_code=response.status_code,
                        message=response.text or response.reason,
                        endpoint=endpoint,
                        response=response,
                    )
                # Server error - will retry
                last_exception = exceptions.AstroxHTTPError(
                    status_code=response.status_code,
                    message=response.text or response.reason,
                    endpoint=endpoint,
                    response=response,
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2**attempt))
                    continue
                raise last_exception

            # Parse JSON response
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                raise exceptions.AstroxAPIError(
                    message=f"Failed to parse JSON response: {e}",
                    endpoint=endpoint,
                    response=response,
                )

            # Check API-level success (if response has IsSuccess field)
            if isinstance(result, dict) and "IsSuccess" in result:
                if not result.get("IsSuccess"):
                    message = result.get("Message", "Unknown error")
                    raise exceptions.AstroxAPIError(
                        message=message,
                        endpoint=endpoint,
                        response=response,
                    )

            return result

        except requests.Timeout:
            last_exception = exceptions.AstroxTimeoutError(
                endpoint=endpoint,
                timeout=timeout,
            )
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            raise last_exception

        except requests.ConnectionError as e:
            last_exception = exceptions.AstroxConnectionError(
                message=f"Failed to connect to API: {e}",
                original_error=e,
            )
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            raise last_exception

        except requests.RequestException as e:
            last_exception = exceptions.AstroxConnectionError(
                message=f"Request failed: {e}",
                original_error=e,
            )
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            raise last_exception

    # Should not reach here, but just in case
    if last_exception:
        raise last_exception
    raise exceptions.AstroxConnectionError(
        message="Request failed after all retries",
        original_error=None,
    )


def post(
    endpoint: str,
    data: dict[str, Any] | BaseModel,
    response_model: type[T] | None = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    session: requests.Session | None = None,
) -> T | dict[str, Any]:
    """
    Make a POST request and optionally parse response into a Pydantic model.

    Args:
        endpoint: API endpoint
        data: Request payload (dict or Pydantic model)
        response_model: Optional Pydantic model class for response
        base_url: Base URL for the API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries
        session: Optional requests.Session to use

    Returns:
        Parsed response as Pydantic model if response_model provided, else dict

    Raises:
        AstroxValidationError: If response validation fails
        (Plus all exceptions from _make_request)
    """
    result = _make_request(
        endpoint=endpoint,
        data=data,
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
        session=session,
    )

    if response_model is None:
        return result

    try:
        return response_model.model_validate(result)
    except ValidationError as e:
        raise exceptions.AstroxValidationError(
            message=f"Failed to validate response: {e}",
            errors=e.errors(),
        )


class HTTPClient:
    """HTTP client for the ASTROX API with retry mechanism.

    Wraps the low-level _make_request() function in a class-based interface
    with configurable connection parameters.

    Example:
        >>> client = HTTPClient(timeout=60)
        >>> result = client.post("/api/Coverage/GetGridPoints", data={...})

        >>> # Global configuration
        >>> configure(base_url="http://custom:8765", timeout=120)
        >>> # All subsequent calls use this configuration
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        """Initialize HTTP client.

        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session = requests.Session()

    def post(
        self,
        endpoint: str,
        data: dict[str, Any] | BaseModel,
        response_model: type[T] | None = None,
        params: dict[str, Any] | None = None,
    ) -> T | dict[str, Any]:
        """Make POST request to API endpoint.

        Args:
            endpoint: API endpoint (e.g., "/api/Coverage/GetGridPoints")
            data: Request payload (dict or Pydantic model)
            response_model: Optional Pydantic model class for response validation
            params: Optional query parameters

        Returns:
            Parsed response as Pydantic model if response_model provided, else dict

        Raises:
            AstroxAPIError: If IsSuccess=false in response
            AstroxHTTPError: If HTTP status code indicates error
            AstroxTimeoutError: If request times out
            AstroxConnectionError: If connection fails after all retries
            AstroxValidationError: If response validation fails
        """
        result = _make_request(
            endpoint=endpoint,
            data=data,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            session=self._session,
            params=params,
        )

        if response_model is None:
            return result

        try:
            return response_model.model_validate(result)
        except ValidationError as e:
            raise exceptions.AstroxValidationError(
                message=f"Failed to validate response: {e}",
                errors=e.errors(),
            )


def get_session() -> HTTPClient:
    """Get the current default session, creating one if needed.

    Returns:
        HTTPClient instance (either existing default or newly created)

    Example:
        >>> sess = get_session()
        >>> result = sess.post("/api/Coverage/GetGridPoints", data={...})
    """
    sess = _default_session.get()
    if sess is None:
        sess = HTTPClient()
        _default_session.set(sess)
    return sess


def configure(
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
) -> HTTPClient:
    """Configure the default session globally.

    Args:
        base_url: Base URL for the API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries

    Returns:
        Configured HTTPClient instance

    Example:
        >>> import astrox
        >>> astrox.configure(base_url="http://custom:8765", timeout=120)
        >>> # All subsequent calls use this configuration
        >>> from astrox.coverage import compute_coverage
        >>> result = compute_coverage(...)  # Uses configured session
    """
    sess = HTTPClient(
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )
    _default_session.set(sess)
    return sess
