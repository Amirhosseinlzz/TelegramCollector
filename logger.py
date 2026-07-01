"""Logging utilities for the project."""

from __future__ import annotations

import logging
import sys


def setup_logger(name: str = "vpn_collector", level: str = "INFO") -> logging.Logger:
    """Create and configure an application logger.

    The logger writes to stdout so logs are visible in GitHub Actions.
    Repeated calls are safe and will not duplicate handlers.
    """

    logger = logging.getLogger(name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        for handler in logger.handlers:
            handler.setLevel(numeric_level)

    return logger
