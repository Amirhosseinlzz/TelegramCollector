"""Generate a Telethon StringSession for GitHub Actions.

Run locally:
    python scripts/generate_string_session.py

Never commit the generated session string. Store it only in GitHub Secrets.
"""

from __future__ import annotations

import asyncio
import getpass
import os
from typing import Callable

from telethon import TelegramClient
from telethon.sessions import StringSession

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[assignment]


if load_dotenv is not None:
    load_dotenv()


def _read_api_id() -> int:
    raw_value = os.getenv("TELEGRAM_API_ID") or input("TELEGRAM_API_ID: ").strip()
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError("TELEGRAM_API_ID must be an integer.") from exc


def _read_api_hash() -> str:
    value = os.getenv("TELEGRAM_API_HASH") or input("TELEGRAM_API_HASH: ").strip()
    if not value:
        raise ValueError("TELEGRAM_API_HASH is required.")
    return value


def _phone_callback() -> str:
    return input("Telegram phone number with country code, for example +994501234567: ").strip()


def _code_callback() -> str:
    return input("Telegram login code: ").strip()


def _password_callback() -> str:
    return getpass.getpass("Two-step verification password, if enabled: ")


async def main() -> None:
    api_id = _read_api_id()
    api_hash = _read_api_hash()

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start(
        phone=_phone_callback,
        code_callback=_code_callback,
        password=_password_callback,
    )

    session_string = StringSession.save(client.session)
    await client.disconnect()

    print("\nTELEGRAM_STRING_SESSION:")
    print(session_string)
    print("\nKeep this value private. Add it to GitHub Secrets and never commit it.")


if __name__ == "__main__":
    asyncio.run(main())
