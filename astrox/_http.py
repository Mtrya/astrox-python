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

# ContextVar for thread-safe default client management
_default_session: ContextVar[Client | None] = ContextVar("session", default=None)


def _join_url(base_url: str, endpoint: str) -> str:
    return f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"


def _default_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _json_payload(data: Any) -> Any:
    if isinstance(data, BaseModel):
        return json.loads(data.model_dump_json(by_alias=True, exclude_none=True))
    return data


def _make_request(
    endpoint: str,
    data: Any,
    *,
    method: str = "POST",
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    session: requests.Session | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    **request_kwargs: Any,
) -> Any:
    """
    Make a JSON request to the API with retry mechanism.

    Args:
        endpoint: API endpoint (e.g., "/Coverage/ComputeCoverage")
        data: Request payload (dict or Pydantic model)
        method: HTTP method
        base_url: Base URL for the API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (exponential backoff)
        session: Optional requests.Session to use
        params: Optional query parameters
        headers: Optional extra headers

    Returns:
        Parsed JSON response

    Raises:
        AstroxAPIError: If IsSuccess=false in response
        AstroxHTTPError: If HTTP status code indicates error
        AstroxTimeoutError: If request times out
        AstroxConnectionError: If connection fails after all retries
    """
    url = _join_url(base_url, endpoint)
    use_session = session or requests.Session()
    request_headers = _default_headers()
    if headers:
        request_headers.update(headers)
    json_data = _json_payload(data)

    last_exception = None

    for attempt in range(max_retries):
        try:
            response = use_session.request(
                method.upper(),
                url,
                json=json_data,
                headers=request_headers,
                timeout=timeout,
                params=params,
                **request_kwargs,
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


class Client:
    """Client for the ASTROX API with retry mechanism.

    Wraps the low-level _make_request() function in a class-based interface
    with configurable connection parameters.

    Example:
        >>> client = Client(timeout=60)
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
        self.raw = RawClient(self)

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **request_kwargs: Any,
    ) -> Any:
        """Make a raw JSON request to an API endpoint."""
        return _make_request(
            endpoint=endpoint,
            data=json,
            method=method,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            session=self._session,
            params=params,
            headers=headers,
            **request_kwargs,
        )

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
        result = self.request("POST", endpoint, json=data, params=params)

        if response_model is None:
            return result

        try:
            return response_model.model_validate(result)
        except ValidationError as e:
            raise exceptions.AstroxValidationError(
                message=f"Failed to validate response: {e}",
                errors=e.errors(),
            )


class RawClient:
    """Advanced raw route access bound to a client or the default client."""

    def __init__(self, client: Client | None = None) -> None:
        self._client = client

    def _target(self) -> Client:
        return self._client or get_session()

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **request_kwargs: Any,
    ) -> Any:
        return self._target().request(
            method,
            endpoint,
            json=json,
            params=params,
            headers=headers,
            **request_kwargs,
        )

    def get(
        self,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **request_kwargs: Any,
    ) -> Any:
        return self.request(
            "GET",
            endpoint,
            params=params,
            headers=headers,
            **request_kwargs,
        )

    def post(
        self,
        endpoint: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **request_kwargs: Any,
    ) -> Any:
        return self.request(
            "POST",
            endpoint,
            json=json,
            params=params,
            headers=headers,
            **request_kwargs,
        )


HTTPClient = Client
raw = RawClient()


def get_session() -> Client:
    """Get the current default session, creating one if needed.

    Returns:
        Client instance (either existing default or newly created)

    Example:
        >>> sess = get_session()
        >>> result = sess.post("/api/Coverage/GetGridPoints", data={...})
    """
    sess = _default_session.get()
    if sess is None:
        sess = Client()
        _default_session.set(sess)
    return sess


def configure(
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
) -> Client:
    """Configure the default session globally.

    Args:
        base_url: Base URL for the API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries

    Returns:
        Configured Client instance

    Example:
        >>> import astrox
        >>> astrox.configure(base_url="http://custom:8765", timeout=120)
        >>> # All subsequent calls use this configuration
        >>> from astrox.coverage import compute_coverage
        >>> result = compute_coverage(...)  # Uses configured session
    """
    sess = Client(
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )
    _default_session.set(sess)
    return sess
