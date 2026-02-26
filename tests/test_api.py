"""Tests for the Stoat REST API wrapper."""

from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

from discord_ferry.errors import MigrationError
from discord_ferry.migrator.api import (
    api_create_category,
    api_create_channel,
    api_create_role,
    api_create_server,
    api_edit_category,
    api_edit_role,
    api_edit_server,
    api_fetch_server,
)

BASE_URL = "https://api.test"
TOKEN = "test-session-token"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_aiohttp() -> aioresponses:
    with aioresponses() as m:
        yield m


# ---------------------------------------------------------------------------
# api_create_server
# ---------------------------------------------------------------------------


async def test_api_create_server(mock_aiohttp: aioresponses) -> None:
    """POST /servers/create returns the new server dict including _id."""
    mock_aiohttp.post(f"{BASE_URL}/servers/create", payload={"_id": "srv123", "name": "Test"})
    async with aiohttp.ClientSession() as session:
        result = await api_create_server(session, BASE_URL, TOKEN, "Test")
    assert result["_id"] == "srv123"
    assert result["name"] == "Test"


# ---------------------------------------------------------------------------
# api_fetch_server
# ---------------------------------------------------------------------------


async def test_api_fetch_server(mock_aiohttp: aioresponses) -> None:
    """GET /servers/abc123 returns the server info dict."""
    mock_aiohttp.get(
        f"{BASE_URL}/servers/abc123",
        payload={"_id": "abc123", "name": "My Server"},
    )
    async with aiohttp.ClientSession() as session:
        result = await api_fetch_server(session, BASE_URL, TOKEN, "abc123")
    assert result["_id"] == "abc123"
    assert result["name"] == "My Server"


# ---------------------------------------------------------------------------
# api_create_role
# ---------------------------------------------------------------------------


async def test_api_create_role(mock_aiohttp: aioresponses) -> None:
    """POST /servers/srv1/roles returns the new role dict including id."""
    mock_aiohttp.post(
        f"{BASE_URL}/servers/srv1/roles",
        payload={"id": "role99", "name": "Moderator"},
        status=200,
    )
    async with aiohttp.ClientSession() as session:
        result = await api_create_role(session, BASE_URL, TOKEN, "srv1", "Moderator")
    assert result["id"] == "role99"
    assert result["name"] == "Moderator"


# ---------------------------------------------------------------------------
# api_edit_role
# ---------------------------------------------------------------------------


async def test_api_edit_role(mock_aiohttp: aioresponses) -> None:
    """PATCH /servers/srv1/roles/role1 sends colour in the JSON body."""
    mock_aiohttp.patch(
        f"{BASE_URL}/servers/srv1/roles/role1",
        payload={"id": "role1", "colour": "#FF0000"},
    )
    async with aiohttp.ClientSession() as session:
        result = await api_edit_role(
            session, BASE_URL, TOKEN, "srv1", "role1", colour="#FF0000", hoist=True
        )
    assert result["colour"] == "#FF0000"


# ---------------------------------------------------------------------------
# api_create_category
# ---------------------------------------------------------------------------


async def test_api_create_category(mock_aiohttp: aioresponses) -> None:
    """POST /servers/srv1/categories returns the new category dict including id."""
    mock_aiohttp.post(
        f"{BASE_URL}/servers/srv1/categories",
        payload={"id": "cat42", "title": "General"},
        status=201,
    )
    async with aiohttp.ClientSession() as session:
        result = await api_create_category(session, BASE_URL, TOKEN, "srv1", "General")
    assert result["id"] == "cat42"
    assert result["title"] == "General"


# ---------------------------------------------------------------------------
# api_edit_category
# ---------------------------------------------------------------------------


async def test_api_edit_category(mock_aiohttp: aioresponses) -> None:
    """PATCH /servers/srv1/categories/cat1 sends the channels list in the body."""
    channels = ["ch1", "ch2", "ch3"]
    mock_aiohttp.patch(
        f"{BASE_URL}/servers/srv1/categories/cat1",
        payload={"id": "cat1", "channels": channels},
    )
    async with aiohttp.ClientSession() as session:
        result = await api_edit_category(session, BASE_URL, TOKEN, "srv1", "cat1", channels)
    assert result["channels"] == channels


# ---------------------------------------------------------------------------
# api_create_channel
# ---------------------------------------------------------------------------


async def test_api_create_channel(mock_aiohttp: aioresponses) -> None:
    """POST /servers/srv1/channels sends name and type and returns the channel dict."""
    mock_aiohttp.post(
        f"{BASE_URL}/servers/srv1/channels",
        payload={"_id": "ch99", "name": "general", "channel_type": "Text"},
        status=201,
    )
    async with aiohttp.ClientSession() as session:
        result = await api_create_channel(
            session, BASE_URL, TOKEN, "srv1", name="general", channel_type="Text"
        )
    assert result["_id"] == "ch99"
    assert result["name"] == "general"


# ---------------------------------------------------------------------------
# api_edit_server
# ---------------------------------------------------------------------------


async def test_api_edit_server(mock_aiohttp: aioresponses) -> None:
    """PATCH /servers/srv1 passes kwargs as the JSON body."""
    mock_aiohttp.patch(
        f"{BASE_URL}/servers/srv1",
        payload={"_id": "srv1", "name": "Renamed Server"},
    )
    async with aiohttp.ClientSession() as session:
        result = await api_edit_server(session, BASE_URL, TOKEN, "srv1", name="Renamed Server")
    assert result["name"] == "Renamed Server"


# ---------------------------------------------------------------------------
# Error and retry tests
# ---------------------------------------------------------------------------


async def test_api_error_403(mock_aiohttp: aioresponses) -> None:
    """A 403 response raises MigrationError immediately (not retried)."""
    mock_aiohttp.get(f"{BASE_URL}/servers/srv1", status=403, body="Forbidden")
    async with aiohttp.ClientSession() as session:
        with pytest.raises(MigrationError, match="API error 403"):
            await api_fetch_server(session, BASE_URL, TOKEN, "srv1")


async def test_api_429_retry(mock_aiohttp: aioresponses) -> None:
    """A 429 response triggers a retry; the subsequent 200 returns the result."""
    # First response: 429 with 100 ms retry_after
    mock_aiohttp.get(
        f"{BASE_URL}/servers/srv1",
        status=429,
        payload={"retry_after": 100},
    )
    # Second response: success
    mock_aiohttp.get(
        f"{BASE_URL}/servers/srv1",
        payload={"_id": "srv1", "name": "Recovered"},
    )
    async with aiohttp.ClientSession() as session:
        result = await api_fetch_server(session, BASE_URL, TOKEN, "srv1")
    assert result["_id"] == "srv1"
