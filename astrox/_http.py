"""HTTP client with retry mechanism and ContextVar-based session management."""

from __future__ import annotations

import json
import time
from contextvars import ContextVar
from typing import Any, TypeVar

import requests

from astrox import exceptions

T = TypeVar("T")

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
        "Accept": "application/json",
    }


def _json_payload(data: Any) -> Any:
    model_dump_json = getattr(data, "model_dump_json", None)
    if callable(model_dump_json):
        return json.loads(model_dump_json(by_alias=True, exclude_none=True))
    if isinstance(data, list):
        return [_json_payload(item) for item in data]
    if isinstance(data, dict):
        return {key: _json_payload(value) for key, value in data.items()}
    return data


def _validation_errors(exc: Exception) -> list[Any]:
    errors = getattr(exc, "errors", None)
    if callable(errors):
        return errors()
    return []


def _validate_response_model(response_model: type[T], result: Any) -> T:
    model_validate = getattr(response_model, "model_validate", None)
    if not callable(model_validate):
        raise exceptions.AstroxValidationError(
            message="response_model must provide model_validate()",
            errors=[],
        )

    try:
        return model_validate(result)
    except Exception as exc:
        raise exceptions.AstroxValidationError(
            message=f"Failed to validate response: {exc}",
            errors=_validation_errors(exc),
        )


def _make_request(
    endpoint: str,
    json_body: Any,
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
    Make an HTTP request to the API with retry mechanism.

    Args:
        endpoint: API endpoint (e.g., "/Coverage/ComputeCoverage")
        json_body: Optional JSON request payload (dict or Pydantic model)
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
    json_data = _json_payload(json_body)

    last_exception = None

    total_attempts = max_retries + 1

    for attempt in range(total_attempts):
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
                if attempt < total_attempts - 1:
                    time.sleep(retry_delay * (2**attempt))
                    continue
                raise last_exception

            # Parse JSON response
            if (
                response.status_code == 204
                or getattr(response, "content", None) == b""
            ):
                return None

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
            if attempt < total_attempts - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            raise last_exception

        except requests.ConnectionError as e:
            last_exception = exceptions.AstroxConnectionError(
                message=f"Failed to connect to API: {e}",
                original_error=e,
            )
            if attempt < total_attempts - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            raise last_exception

        except requests.RequestException as e:
            last_exception = exceptions.AstroxConnectionError(
                message=f"Request failed: {e}",
                original_error=e,
            )
            if attempt < total_attempts - 1:
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
    data: Any,
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
        data: Request payload
        response_model: Optional model_validate-compatible class for response
        base_url: Base URL for the API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries
        session: Optional requests.Session to use

    Returns:
        Parsed response model if response_model provided, else dict

    Raises:
        AstroxValidationError: If response validation fails
        (Plus all exceptions from _make_request)
    """
    result = _make_request(
        endpoint=endpoint,
        json_body=data,
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
        session=session,
    )

    if response_model is None:
        return result

    return _validate_response_model(response_model, result)


class Client:
    """Client for the ASTROX API with retry mechanism.

    Wraps the low-level _make_request() function in a class-based interface
    with configurable connection parameters.

    Example:
        >>> client = Client(timeout=60)
        >>> result = client.raw.post("/Propagator/J2", json={...})

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
        timeout: float | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
        **request_kwargs: Any,
    ) -> Any:
        """Make a raw JSON request to an API endpoint."""
        return _make_request(
            endpoint=endpoint,
            json_body=json,
            method=method,
            base_url=self.base_url,
            timeout=timeout if timeout is not None else self.timeout,
            max_retries=max_retries if max_retries is not None else self.max_retries,
            retry_delay=retry_delay if retry_delay is not None else self.retry_delay,
            session=self._session,
            params=params,
            headers=headers,
            **request_kwargs,
        )

    def post(
        self,
        endpoint: str,
        data: Any,
        response_model: type[T] | None = None,
        params: dict[str, Any] | None = None,
    ) -> T | dict[str, Any]:
        """Make POST request to API endpoint.

        Args:
            endpoint: API endpoint (e.g., "/Propagator/J2")
            data: Request payload
            response_model: Optional model_validate-compatible class for response validation
            params: Optional query parameters

        Returns:
            Parsed response model if response_model provided, else dict

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

        return _validate_response_model(response_model, result)


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
        timeout: float | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
        client: Client | None = None,
        **request_kwargs: Any,
    ) -> Any:
        target = client or self._target()
        return target.request(
            method,
            endpoint,
            json=json,
            params=params,
            headers=headers,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            **request_kwargs,
        )

    def get(
        self,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
        client: Client | None = None,
        **request_kwargs: Any,
    ) -> Any:
        return self.request(
            "GET",
            endpoint,
            params=params,
            headers=headers,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            client=client,
            **request_kwargs,
        )

    def post(
        self,
        endpoint: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
        client: Client | None = None,
        **request_kwargs: Any,
    ) -> Any:
        return self.request(
            "POST",
            endpoint,
            json=json,
            params=params,
            headers=headers,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            client=client,
            **request_kwargs,
        )


raw = RawClient()


def get_session() -> Client:
    """Get the current default session, creating one if needed.

    Returns:
        Client instance (either existing default or newly created)

    Example:
        >>> sess = get_session()
        >>> result = sess.raw.post("/Propagator/J2", json={...})
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
        >>> from astrox import orbits, propagator
        >>> orbit = orbits.keplerian(...)
        >>> period_s, position = propagator.j2(..., orbit=orbit)
    """
    sess = Client(
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )
    _default_session.set(sess)
    return sess
