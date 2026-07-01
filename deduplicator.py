"""Config cleanup, deduplication, and deterministic sorting."""

from __future__ import annotations

from typing import Iterable


def normalize_config(config: str) -> str:
    """Normalize a single config line without changing its semantic content."""

    return config.strip()


def deduplicate_configs(configs: Iterable[str]) -> list[str]:
    """Remove empty lines and duplicates, then sort output deterministically.

    Deduplication is case-sensitive because some encoded payloads can be
    case-sensitive. Sorting is case-insensitive first, then case-sensitive as a
    stable tie-breaker.
    """

    unique: set[str] = set()
    for config in configs:
        normalized = normalize_config(config)
        if normalized:
            unique.add(normalized)

    return sorted(unique, key=lambda item: (item.lower(), item))
