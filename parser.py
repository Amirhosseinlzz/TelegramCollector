"""Channel parsing and Telegram message collection."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from telethon import TelegramClient
from telethon.errors import (
    ChannelInvalidError,
    ChannelPrivateError,
    FloodWaitError,
    UsernameInvalidError,
    UsernameNotOccupiedError,
)


class ChannelConfigError(ValueError):
    """Raised when channels.json is invalid."""


@dataclass(frozen=True)
class ChannelSource:
    """A Telegram source channel configured by the user."""

    name: str
    enabled: bool = True


def load_channels(path: Path) -> list[ChannelSource]:
    """Load Telegram channel identifiers from a JSON file.

    Supported formats:
        {"channels": ["@channel", "https://t.me/channel"]}
        {"channels": [{"name": "@channel", "enabled": true}]}
        ["@channel", "https://t.me/channel"]
    """

    if not path.exists():
        raise ChannelConfigError(f"Channels file not found: {path}")

    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ChannelConfigError(f"Invalid JSON in channels file: {path}") from exc

    entries: Any
    if isinstance(raw_data, dict):
        entries = raw_data.get("channels")
    else:
        entries = raw_data

    if not isinstance(entries, list):
        raise ChannelConfigError("channels.json must contain a list or a 'channels' list.")

    channels: list[ChannelSource] = []
    for entry in entries:
        channels.append(_parse_channel_entry(entry))

    enabled_channels = [channel for channel in channels if channel.enabled]
    if not enabled_channels:
        raise ChannelConfigError("No enabled channels found in channels.json.")

    return enabled_channels


def _parse_channel_entry(entry: Any) -> ChannelSource:
    if isinstance(entry, str):
        name = normalize_channel_identifier(entry)
        if not name:
            raise ChannelConfigError("Channel name cannot be empty.")
        return ChannelSource(name=name, enabled=True)

    if isinstance(entry, dict):
        raw_name = entry.get("name") or entry.get("url") or entry.get("channel")
        if not isinstance(raw_name, str):
            raise ChannelConfigError("Each channel object must contain a string 'name'.")

        enabled = entry.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ChannelConfigError("Channel 'enabled' value must be true or false.")

        name = normalize_channel_identifier(raw_name)
        if not name:
            raise ChannelConfigError("Channel name cannot be empty.")

        return ChannelSource(name=name, enabled=enabled)

    raise ChannelConfigError("Each channel entry must be a string or an object.")


def normalize_channel_identifier(value: str) -> str:
    """Normalize public Telegram channel links into @username form when possible."""

    cleaned = value.strip()
    if not cleaned:
        return ""

    lowered = cleaned.lower()
    prefixes = ("https://t.me/", "http://t.me/", "t.me/")

    for prefix in prefixes:
        if lowered.startswith(prefix):
            suffix = cleaned[len(prefix) :].strip().strip("/")
            if not suffix:
                return ""

            # Private invite links and t.me/c links cannot safely be converted to @username.
            if suffix.startswith("+") or suffix.startswith("joinchat/") or suffix.startswith("c/"):
                return cleaned

            username = suffix.split("/")[0].strip()
            if not username:
                return ""
            return username if username.startswith("@") else f"@{username}"

    return cleaned


class TelegramMessageCollector:
    """Collect recent text messages from configured Telegram channels."""

    def __init__(
        self,
        client: TelegramClient,
        message_limit_per_channel: int,
        request_delay_seconds: float,
        max_flood_wait_seconds: int,
    ) -> None:
        self._client = client
        self._message_limit_per_channel = message_limit_per_channel
        self._request_delay_seconds = request_delay_seconds
        self._max_flood_wait_seconds = max_flood_wait_seconds

    async def collect_all(self, channels: Iterable[ChannelSource]) -> dict[str, list[str]]:
        """Collect recent messages from all channels.

        A failure in one channel does not stop the entire collection process.
        The returned dictionary contains only successfully collected channels.
        """

        collected: dict[str, list[str]] = {}

        for channel in channels:
            messages = await self.collect_channel(channel.name)
            if messages:
                collected[channel.name] = messages

            if self._request_delay_seconds > 0:
                await asyncio.sleep(self._request_delay_seconds)

        return collected

    async def collect_channel(self, channel_name: str) -> list[str]:
        """Collect recent text messages from one Telegram channel."""

        try:
            return await self._collect_channel_once(channel_name)
        except FloodWaitError as exc:
            if exc.seconds <= self._max_flood_wait_seconds:
                await asyncio.sleep(exc.seconds)
                return await self._collect_channel_once(channel_name)
            raise

    async def _collect_channel_once(self, channel_name: str) -> list[str]:
        messages: list[str] = []

        async for message in self._client.iter_messages(
            channel_name,
            limit=self._message_limit_per_channel,
        ):
            text = getattr(message, "raw_text", None) or getattr(message, "message", None)
            if isinstance(text, str) and text.strip():
                messages.append(text)

        return messages


def is_channel_access_error(exc: BaseException) -> bool:
    """Return true for expected Telegram channel access/identifier failures."""

    return isinstance(
        exc,
        (
            ChannelInvalidError,
            ChannelPrivateError,
            UsernameInvalidError,
            UsernameNotOccupiedError,
        ),
    )
