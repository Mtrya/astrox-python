"""Focused tests for the public client and raw route foundation."""

from __future__ import annotations

import json

import pytest
import requests
from pydantic import BaseModel, Field

import astrox
from astrox import exceptions
from astrox import _http


class NestedPayload(BaseModel):
    wire_value: int = Field(alias="WireValue")


class WirePayload:
    def __init__(self, value: int) -> None:
        self.value = value

    def model_dump_json(self, *, by_alias: bool, exclude_none: bool) -> str:
        assert by_alias is True
        assert exclude_none is True
        return json.dumps({"WireValue": self.value})


class FakeResponse:
    def __init__(
        self,
        status_code: int = 200,
        payload: object | None = None,
        *,
        text: str = "",
        reason: str = "OK",
        content: bytes | None = None,
        json_error: Exception | None = None,
    ) -> None:
        self.status_code = status_code
        self.payload = payload if payload is not None else {"ok": True}
        self.text = text
        self.reason = reason
        if content is not None:
            self.content = content
        self.json_error = json_error

    def json(self) -> object:
        if self.json_error is not None:
            raise self.json_error
        return self.payload


class RecordingSession:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[dict[str, object]] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        json: object | None = None,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: object,
    ) -> object:
        self.calls.append(
            {
                "method": method.upper(),
                "url": url,
                "json": json,
                "params": params,
                "headers": headers,
                "timeout": timeout,
                "kwargs": kwargs,
            }
        )
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def post(
        self,
        url: str,
        *,
        json: object | None = None,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: object,
    ) -> object:
        return self.request(
            "POST",
            url,
            json=json,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    def get(
        self,
        url: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: object,
    ) -> object:
        return self.request(
            "GET",
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )


@pytest.fixture(autouse=True)
def reset_default_session() -> None:
    _http._default_session.set(None)


def install_recording_session(
    monkeypatch: pytest.MonkeyPatch,
    outcomes: list[object],
) -> RecordingSession:
    session = RecordingSession(outcomes)
    monkeypatch.setattr(_http.requests, "Session", lambda: session)
    return session


def test_package_exports_client_without_legacy_httpclient_alias() -> None:
    assert "Client" in astrox.__all__
    assert "raw" in astrox.__all__
    assert "configure" in astrox.__all__
    assert "HTTPClient" not in astrox.__all__
    assert not hasattr(astrox, "HTTPClient")
    assert not hasattr(_http, "HTTPClient")


def test_configure_returns_canonical_client() -> None:
    assert hasattr(astrox, "Client")

    configured = astrox.configure(
        base_url="https://astrox.example",
        timeout=12,
        max_retries=2,
        retry_delay=0,
    )

    assert isinstance(configured, astrox.Client)
    assert astrox.get_session() is configured
    assert configured.base_url == "https://astrox.example"
    assert configured.timeout == 12
    assert configured.max_retries == 2
    assert configured.retry_delay == 0


def test_raw_post_uses_hidden_default_client_and_json_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = install_recording_session(
        monkeypatch,
        [FakeResponse(payload={"IsSuccess": True, "Data": {"id": 1}})],
    )
    astrox.configure(base_url="https://astrox.example/api", timeout=7, retry_delay=0)

    result = astrox.raw.post("/Propagator/J2", json={"Start": "2026-01-01T00:00:00Z"})

    assert result == {"IsSuccess": True, "Data": {"id": 1}}
    assert session.calls == [
        {
            "method": "POST",
            "url": "https://astrox.example/api/Propagator/J2",
            "json": {"Start": "2026-01-01T00:00:00Z"},
            "params": None,
            "headers": {
                "Accept": "application/json",
            },
            "timeout": 7,
            "kwargs": {},
        }
    ]


def test_bound_raw_get_accepts_endpoint_without_leading_slash_and_query_params(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = install_recording_session(
        monkeypatch,
        [FakeResponse(payload=[{"city": "Beijing"}])],
    )

    client = astrox.Client(base_url="https://astrox.example/root", timeout=5)
    result = client.raw.get("WeatherForecast", params={"city": "Beijing"})

    assert result == [{"city": "Beijing"}]
    assert session.calls == [
        {
            "method": "GET",
            "url": "https://astrox.example/root/WeatherForecast",
            "json": None,
            "params": {"city": "Beijing"},
            "headers": {
                "Accept": "application/json",
            },
            "timeout": 5,
            "kwargs": {},
        }
    ]


def test_raw_request_normalizes_method_and_merges_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = install_recording_session(
        monkeypatch,
        [FakeResponse(payload={"ok": True})],
    )
    client = astrox.Client(base_url="https://astrox.example", timeout=9)

    result = astrox.raw.request(
        "post",
        "Coverage/ComputeCoverage",
        json={"Grid": {"GridType": "LatLonRegion"}},
        headers={"X-Astrox-Debug": "1"},
        client=client,
    )

    assert result == {"ok": True}
    assert session.calls == [
        {
            "method": "POST",
            "url": "https://astrox.example/Coverage/ComputeCoverage",
            "json": {"Grid": {"GridType": "LatLonRegion"}},
            "params": None,
            "headers": {
                "Accept": "application/json",
                "X-Astrox-Debug": "1",
            },
            "timeout": 9,
            "kwargs": {},
        }
    ]


def test_raw_request_forwards_advanced_request_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = install_recording_session(
        monkeypatch,
        [FakeResponse(payload={"uploaded": True})],
    )
    client = astrox.Client(base_url="https://astrox.example")
    files = {"archive": ("archive.zip", b"archive")}

    result = astrox.raw.request(
        "POST",
        "/ssc/admin/upload-database-archive",
        client=client,
        files=files,
        verify=False,
    )

    assert result == {"uploaded": True}
    assert session.calls[0]["headers"] == {"Accept": "application/json"}
    assert session.calls[0]["kwargs"] == {
        "files": files,
        "verify": False,
    }


def test_client_request_accepts_per_request_transport_overrides() -> None:
    session = RecordingSession([FakeResponse(payload={"ok": True})])
    client = astrox.Client(
        base_url="https://astrox.example",
        timeout=20,
        max_retries=5,
        retry_delay=10,
    )
    client._session = session

    result = client.request(
        "POST",
        "/override",
        json={},
        timeout=2,
        max_retries=0,
        retry_delay=0,
    )

    assert result == {"ok": True}
    assert len(session.calls) == 1
    assert session.calls[0]["timeout"] == 2


def test_raw_request_accepts_per_request_transport_overrides() -> None:
    session = RecordingSession([FakeResponse(payload={"ok": True})])
    client = astrox.Client(base_url="https://astrox.example", timeout=20)
    client._session = session

    result = astrox.raw.request(
        "POST",
        "/override",
        client=client,
        json={},
        timeout=4,
        max_retries=0,
        retry_delay=0,
    )

    assert result == {"ok": True}
    assert len(session.calls) == 1
    assert session.calls[0]["timeout"] == 4


def test_json_payload_normalizes_nested_pydantic_models() -> None:
    payload = {
        "items": [NestedPayload(WireValue=3)],
        "nested": {"model": NestedPayload(WireValue=4)},
        "plain": True,
    }

    assert _http._json_payload(payload) == {
        "items": [{"WireValue": 3}],
        "nested": {"model": {"WireValue": 4}},
        "plain": True,
    }


def test_json_payload_accepts_model_dump_json_objects_without_base_model() -> None:
    payload = {
        "items": [WirePayload(3)],
        "nested": {"model": WirePayload(4)},
        "plain": True,
    }

    assert _http._json_payload(payload) == {
        "items": [{"WireValue": 3}],
        "nested": {"model": {"WireValue": 4}},
        "plain": True,
    }


def test_raw_204_response_returns_none() -> None:
    session = RecordingSession([FakeResponse(status_code=204, payload=None)])
    client = astrox.Client(base_url="https://astrox.example")
    client._session = session

    assert client.raw.post("/empty", json={}) is None


def test_raw_empty_200_response_returns_none() -> None:
    session = RecordingSession(
        [
            FakeResponse(
                status_code=200,
                payload=None,
                content=b"",
                json_error=json.JSONDecodeError("empty", doc="", pos=0),
            )
        ]
    )
    client = astrox.Client(base_url="https://astrox.example")
    client._session = session

    assert client.raw.post("/empty-200", json={}) is None


def test_http_error_400_is_not_retried() -> None:
    session = RecordingSession([FakeResponse(status_code=400, text="bad request")])
    client = astrox.Client(base_url="https://astrox.example", retry_delay=0)
    client._session = session

    with pytest.raises(exceptions.AstroxHTTPError) as exc_info:
        client.post("/bad", data={"x": 1})

    assert exc_info.value.status_code == 400
    assert exc_info.value.endpoint == "/bad"
    assert len(session.calls) == 1


def test_http_error_500_retries_then_succeeds() -> None:
    session = RecordingSession(
        [
            FakeResponse(status_code=500, text="server error"),
            FakeResponse(payload={"IsSuccess": True, "Data": "ok"}),
        ]
    )
    client = astrox.Client(
        base_url="https://astrox.example",
        max_retries=2,
        retry_delay=0,
    )
    client._session = session

    result = client.post("/retry", data={"x": 1})

    assert result == {"IsSuccess": True, "Data": "ok"}
    assert len(session.calls) == 2


def test_max_retries_zero_still_makes_one_attempt() -> None:
    session = RecordingSession([FakeResponse(payload={"ok": True})])
    client = astrox.Client(
        base_url="https://astrox.example",
        max_retries=0,
        retry_delay=0,
    )
    client._session = session

    assert client.post("/once", data={}) == {"ok": True}
    assert len(session.calls) == 1


def test_api_error_is_raised_for_unsuccessful_astrox_payload() -> None:
    session = RecordingSession(
        [FakeResponse(payload={"IsSuccess": False, "Message": "nope"})]
    )
    client = astrox.Client(base_url="https://astrox.example", retry_delay=0)
    client._session = session

    with pytest.raises(exceptions.AstroxAPIError) as exc_info:
        client.post("/api-error", data={})

    assert str(exc_info.value) == "nope"
    assert exc_info.value.endpoint == "/api-error"


def test_invalid_json_response_is_api_error() -> None:
    session = RecordingSession(
        [
            FakeResponse(
                json_error=json.JSONDecodeError("bad json", doc="not-json", pos=0)
            )
        ]
    )
    client = astrox.Client(base_url="https://astrox.example", retry_delay=0)
    client._session = session

    with pytest.raises(exceptions.AstroxAPIError, match="Failed to parse JSON"):
        client.post("/invalid-json", data={})


def test_timeout_retries_and_raises_timeout_error() -> None:
    session = RecordingSession(
        [requests.Timeout(), requests.Timeout(), requests.Timeout()]
    )
    client = astrox.Client(
        base_url="https://astrox.example",
        timeout=3,
        max_retries=2,
        retry_delay=0,
    )
    client._session = session

    with pytest.raises(exceptions.AstroxTimeoutError) as exc_info:
        client.post("/timeout", data={})

    assert exc_info.value.endpoint == "/timeout"
    assert exc_info.value.timeout == 3
    assert len(session.calls) == 3


def test_connection_error_retries_and_raises_connection_error() -> None:
    session = RecordingSession(
        [
            requests.ConnectionError("offline"),
            requests.ConnectionError("offline"),
            requests.ConnectionError("offline"),
        ]
    )
    client = astrox.Client(
        base_url="https://astrox.example",
        max_retries=2,
        retry_delay=0,
    )
    client._session = session

    with pytest.raises(exceptions.AstroxConnectionError) as exc_info:
        client.post("/offline", data={})

    assert "Failed to connect to API" in str(exc_info.value)
    assert len(session.calls) == 3
