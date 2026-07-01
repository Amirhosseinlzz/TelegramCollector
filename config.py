"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is installed via requirements.txt
    load_dotenv = None  # type: ignore[assignment]


if load_dotenv is not None:
    load_dotenv()


class ConfigError(ValueError):
    """Raised when required runtime configuration is missing or invalid."""


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise ConfigError(f"Required environment variable is missing: {name}")
    return value.strip()


def _get_int_env(name: str, default: Optional[int] = None) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        if default is None:
            raise ConfigError(f"Required integer environment variable is missing: {name}")
        return default

    try:
        return int(raw_value.strip())
    except ValueError as exc:
        raise ConfigError(f"Environment variable {name} must be an integer.") from exc


def _get_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        return float(raw_value.strip())
    except ValueError as exc:
        raise ConfigError(f"Environment variable {name} must be a float.") from exc


def _get_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    raise ConfigError(f"Environment variable {name} must be a boolean value.")


@dataclass(frozen=True)
class AppConfig:
    """Runtime settings for the Telegram VPN config collector."""

    telegram_api_id: int
    telegram_api_hash: str
    telegram_string_session: Optional[str]
    telegram_session_name: str
    channels_file: Path
    output_file: Path
    message_limit_per_channel: int
    request_delay_seconds: float
    max_flood_wait_seconds: int
    allow_empty_output: bool
    log_level: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Build configuration from environment variables.

        Required:
            TELEGRAM_API_ID
            TELEGRAM_API_HASH

        Recommended for GitHub Actions:
            TELEGRAM_STRING_SESSION
        """

        message_limit = _get_int_env("MESSAGE_LIMIT_PER_CHANNEL", default=100)
        if message_limit <= 0:
            raise ConfigError("MESSAGE_LIMIT_PER_CHANNEL must be greater than zero.")

        max_flood_wait = _get_int_env("MAX_FLOOD_WAIT_SECONDS", default=60)
        if max_flood_wait < 0:
            raise ConfigError("MAX_FLOOD_WAIT_SECONDS cannot be negative.")

        request_delay = _get_float_env("REQUEST_DELAY_SECONDS", default=0.5)
        if request_delay < 0:
            raise ConfigError("REQUEST_DELAY_SECONDS cannot be negative.")

        string_session = os.getenv("TELEGRAM_STRING_SESSION")
        if string_session is not None:
            string_session = string_session.strip() or None

        return cls(
            telegram_api_id=_get_int_env("TELEGRAM_API_ID"),
            telegram_api_hash=_get_required_env("TELEGRAM_API_HASH"),
            telegram_string_session=string_session,
            telegram_session_name=os.getenv("TELEGRAM_SESSION_NAME", "telegram_vpn_collector").strip(),
            channels_file=Path(os.getenv("CHANNELS_FILE", "channels.json")).expanduser(),
            output_file=Path(os.getenv("OUTPUT_FILE", "subscriptions.txt")).expanduser(),
            message_limit_per_channel=message_limit,
            request_delay_seconds=request_delay,
            max_flood_wait_seconds=max_flood_wait,
            allow_empty_output=_get_bool_env("ALLOW_EMPTY_OUTPUT", default=False),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        )
