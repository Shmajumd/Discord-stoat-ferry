"""Tests for Discord REST API client."""

from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

from discord_ferry.discord.client import fetch_guild_channels, fetch_guild_roles
from discord_ferry.errors import DiscordAuthError

DISCORD_API = "https://discord.com/api/v10"
TOKEN = "test-discord-token"
GUILD_ID = "111222333"


@pytest.fixture
def mock_discord() -> aioresponses:
    with aioresponses() as m:
        yield m


async def test_fetch_guild_roles_parses_response(mock_discord: aioresponses) -> None:
    mock_discord.get(
        f"{DISCORD_API}/guilds/{GUILD_ID}/roles",
        payload=[
            {
                "id": "role1",
                "name": "Admin",
                "permissions": "2147483647",  # String, not int!
                "position": 5,
                "color": 16711680,
                "hoist": True,
                "managed": False,
            },
            {
                "id": "role2",
                "name": "BotRole",
                "permissions": "8",
                "position": 3,
                "color": 0,
                "hoist": False,
                "managed": True,
            },
        ],
    )
    async with aiohttp.ClientSession() as session:
        roles = await fetch_guild_roles(session, TOKEN, GUILD_ID)
    assert len(roles) == 2
    assert roles[0].id == "role1"
    assert roles[0].permissions == 2147483647  # Parsed from string
    assert roles[1].managed is True


async def test_fetch_guild_channels_parses_nsfw_and_overwrites(
    mock_discord: aioresponses,
) -> None:
    mock_discord.get(
        f"{DISCORD_API}/guilds/{GUILD_ID}/channels",
        payload=[
            {
                "id": "ch1",
                "name": "general",
                "type": 0,
                "nsfw": False,
                "permission_overwrites": [],
            },
            {
                "id": "ch2",
                "name": "nsfw-channel",
                "type": 0,
                "nsfw": True,
                "permission_overwrites": [
                    {"id": "role1", "type": 0, "allow": "4194304", "deny": "0"},
                ],
            },
        ],
    )
    async with aiohttp.ClientSession() as session:
        channels = await fetch_guild_channels(session, TOKEN, GUILD_ID)
    assert len(channels) == 2
    assert channels[0].nsfw is False
    assert channels[1].nsfw is True
    assert len(channels[1].permission_overwrites) == 1
    assert channels[1].permission_overwrites[0].allow == 4194304  # Parsed from string


async def test_fetch_guild_roles_401_raises_discord_auth_error(
    mock_discord: aioresponses,
) -> None:
    mock_discord.get(
        f"{DISCORD_API}/guilds/{GUILD_ID}/roles",
        status=401,
        body="401: Unauthorized",
    )
    async with aiohttp.ClientSession() as session:
        with pytest.raises(DiscordAuthError):
            await fetch_guild_roles(session, TOKEN, GUILD_ID)


async def test_fetch_guild_roles_429_retries(mock_discord: aioresponses) -> None:
    url = f"{DISCORD_API}/guilds/{GUILD_ID}/roles"
    mock_discord.get(url, status=429, payload={"retry_after": 0.01})
    mock_discord.get(
        url,
        payload=[
            {
                "id": "r1",
                "name": "R",
                "permissions": "0",
                "position": 0,
                "color": 0,
                "hoist": False,
                "managed": False,
            }
        ],
    )
    async with aiohttp.ClientSession() as session:
        roles = await fetch_guild_roles(session, TOKEN, GUILD_ID)
    assert len(roles) == 1
