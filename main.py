"""Entry point for the Telegram VPN subscription collector."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Sequence

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.sessions import StringSession

from config import AppConfig, ConfigError
from deduplicator import deduplicate_configs
from extractor import ConfigExtractor
from logger import setup_logger
from parser import ChannelConfigError, TelegramMessageCollector, is_channel_access_error, load_channels


def _build_client(config: AppConfig) -> TelegramClient:
    """Create a Telethon client using StringSession when provided."""

    session = (
        StringSession(config.telegram_string_session)
        if config.telegram_string_session
        else config.telegram_session_name
    )
    return TelegramClient(session, config.telegram_api_id, config.telegram_api_hash)


def _flatten_messages(channel_messages: dict[str, list[str]]) -> list[str]:
    """Flatten collected channel messages into a single list."""

    messages: list[str] = []
    for channel_name in sorted(channel_messages):
        messages.extend(channel_messages[channel_name])
    return messages


def _write_output(path: Path, configs: Sequence[str]) -> None:
    """Write normalized subscription configs to disk."""

    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(configs)
    if content:
        content += "\n"
    path.write_text(content, encoding="utf-8", newline="\n")


async def run() -> int:
    """Run the full collection pipeline."""

    try:
        config = AppConfig.from_env()
    except ConfigError as exc:
        logger = setup_logger(level="ERROR")
        logger.error("Configuration error: %s", exc)
        return 2

    logger = setup_logger(level=config.log_level)
    logger.info("Starting Telegram VPN config collection.")

    try:
        channels = load_channels(config.channels_file)
    except ChannelConfigError as exc:
        logger.error("Channel configuration error: %s", exc)
        return 2

    logger.info("Loaded %d enabled channel(s).", len(channels))

    client = _build_client(config)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.error(
                "Telegram session is not authorized. Generate TELEGRAM_STRING_SESSION first."
            )
            return 2

        collector = TelegramMessageCollector(
            client=client,
            message_limit_per_channel=config.message_limit_per_channel,
            request_delay_seconds=config.request_delay_seconds,
            max_flood_wait_seconds=config.max_flood_wait_seconds,
        )

        channel_messages: dict[str, list[str]] = {}
        for channel in channels:
            try:
                messages = await collector.collect_channel(channel.name)
                channel_messages[channel.name] = messages
                logger.info("%s: collected %d message(s).", channel.name, len(messages))
            except FloodWaitError as exc:
                logger.warning(
                    "%s: skipped due to Telegram flood wait of %d second(s).",
                    channel.name,
                    exc.seconds,
                )
            except Exception as exc:  # A bad channel must not stop the whole workflow.
                if is_channel_access_error(exc):
                    logger.warning("%s: channel access error: %s", channel.name, exc)
                else:
                    logger.exception("%s: unexpected collection error: %s", channel.name, exc)

        messages = _flatten_messages(channel_messages)
        extraction = ConfigExtractor().extract_from_messages(messages)
        unique_configs = deduplicate_configs(extraction.configs)

        logger.info(
            "Scanned %d message(s), extracted %d config(s), kept %d unique config(s).",
            extraction.scanned_messages,
            extraction.extracted_count,
            len(unique_configs),
        )

        if not unique_configs and not config.allow_empty_output:
            logger.warning(
                "No configs found. Output was not overwritten because ALLOW_EMPTY_OUTPUT=false."
            )
            return 0

        _write_output(config.output_file, unique_configs)
        logger.info("Wrote output file: %s", config.output_file)
        return 0

    except Exception as exc:
        logger.exception("Fatal runtime error: %s", exc)
        return 1
    finally:
        await client.disconnect()
        logger.info("Telegram client disconnected.")


def main() -> None:
    """Synchronous wrapper for the async entry point."""

    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
