"""VPN configuration link extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Pattern


SUPPORTED_PROTOCOLS: tuple[str, ...] = (
    "vless",
    "vmess",
    "trojan",
    "ss",
    "ssr",
    "hysteria",
    "hysteria2",
    "tuic",
    "wireguard",
)

# Characters that commonly appear after a URL in prose, Telegram posts, or captions.
_TRAILING_PUNCTUATION = " .,!?:;)]}>\"'`،؛。؟\n\r\t"


@dataclass(frozen=True)
class ExtractionResult:
    """Structured result of a config extraction pass."""

    configs: list[str]
    scanned_messages: int
    extracted_count: int


class ConfigExtractor:
    """Extract supported VPN config links from plain text messages."""

    def __init__(self, protocols: tuple[str, ...] = SUPPORTED_PROTOCOLS) -> None:
        escaped_protocols = "|".join(re.escape(protocol) for protocol in protocols)
        self._pattern: Pattern[str] = re.compile(
            rf"(?P<config>(?:{escaped_protocols})://[^\s<>\"'`|\\\[\]{{}}]+)",
            flags=re.IGNORECASE,
        )

    def extract_from_text(self, text: str) -> list[str]:
        """Return all supported config links found in one text block."""

        if not text:
            return []

        configs: list[str] = []
        for match in self._pattern.finditer(text):
            config = self._clean_match(match.group("config"))
            if config:
                configs.append(config)
        return configs

    def extract_from_messages(self, messages: Iterable[str]) -> ExtractionResult:
        """Extract config links from many Telegram messages."""

        configs: list[str] = []
        scanned = 0

        for message in messages:
            scanned += 1
            configs.extend(self.extract_from_text(message))

        return ExtractionResult(
            configs=configs,
            scanned_messages=scanned,
            extracted_count=len(configs),
        )

    @staticmethod
    def _clean_match(value: str) -> str:
        """Normalize URL-like matches extracted from Telegram prose."""

        cleaned = value.strip().strip(_TRAILING_PUNCTUATION)

        # Some Telegram posts wrap links in markdown punctuation or HTML-ish brackets.
        while cleaned and cleaned[-1] in _TRAILING_PUNCTUATION:
            cleaned = cleaned[:-1].strip()

        return cleaned
