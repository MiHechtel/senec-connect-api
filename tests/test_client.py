"""Tests for the SENEC.Connect client."""

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer

from senec_connect_api import (
    SenecApiError,
    SenecAuthError,
    SenecClient,
    SenecConnectionError,
)
from senec_connect_api import client as client_module


@pytest.mark.asyncio
async def test_get_device_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return systems and authenticate with the subscription key."""
    request_headers: dict[str, str] = {}

    async def handle(request: web.Request) -> web.Response:
        request_headers.update(request.headers)
        return web.json_response(
            [{"bessNameplate": {"serial_number": "system-1"}, "battery": {"power": 1}}]
        )

    app = web.Application()
    app.router.add_get("/device-data", handle)
    server = TestServer(app)
    await server.start_server()
    monkeypatch.setattr(client_module, "API_URL", str(server.make_url("/device-data")))

    async with ClientSession() as session:
        result = await SenecClient("test-key", session).async_get_device_data()

    await server.close()
    assert result == [
        {"bessNameplate": {"serial_number": "system-1"}, "battery": {"power": 1}}
    ]
    assert request_headers["Ocp-Apim-Subscription-Key"] == "test-key"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [401, 403])
async def test_auth_error(status: int, monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise the authentication error for rejected subscription keys."""
    await _assert_status_error(status, SenecAuthError, monkeypatch)


@pytest.mark.asyncio
async def test_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise the API error for server failures."""
    await _assert_status_error(500, SenecApiError, monkeypatch)


async def _assert_status_error(
    status: int,
    error: type[Exception],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def handle(_: web.Request) -> web.Response:
        return web.Response(status=status)

    app = web.Application()
    app.router.add_get("/device-data", handle)
    server = TestServer(app)
    await server.start_server()
    monkeypatch.setattr(client_module, "API_URL", str(server.make_url("/device-data")))

    async with ClientSession() as session:
        with pytest.raises(error):
            await SenecClient("test-key", session).async_get_device_data()

    await server.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [[], [{}], [{"bessNameplate": {"serial_number": ""}}]],
)
async def test_invalid_data(
    payload: list[dict], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject empty system lists and systems without serial numbers."""

    async def handle(_: web.Request) -> web.Response:
        return web.json_response(payload)

    app = web.Application()
    app.router.add_get("/device-data", handle)
    server = TestServer(app)
    await server.start_server()
    monkeypatch.setattr(client_module, "API_URL", str(server.make_url("/device-data")))

    async with ClientSession() as session:
        with pytest.raises(SenecApiError):
            await SenecClient("test-key", session).async_get_device_data()

    await server.close()


@pytest.mark.asyncio
async def test_duplicate_serials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject responses that identify multiple systems with the same serial."""

    async def handle(_: web.Request) -> web.Response:
        return web.json_response(
            [
                {"bessNameplate": {"serial_number": "same"}},
                {"bessNameplate": {"serial_number": "same"}},
            ]
        )

    app = web.Application()
    app.router.add_get("/device-data", handle)
    server = TestServer(app)
    await server.start_server()
    monkeypatch.setattr(client_module, "API_URL", str(server.make_url("/device-data")))

    async with ClientSession() as session:
        with pytest.raises(SenecApiError):
            await SenecClient("test-key", session).async_get_device_data()

    await server.close()


@pytest.mark.asyncio
async def test_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Translate network failures into the library connection exception."""
    monkeypatch.setattr(client_module, "API_URL", "http://127.0.0.1:1/device-data")
    async with ClientSession() as session:
        with pytest.raises(SenecConnectionError):
            await SenecClient("test-key", session).async_get_device_data()
