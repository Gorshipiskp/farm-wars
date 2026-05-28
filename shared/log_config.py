"""Shared logging setup for client and server."""

import logging
import os


def setup_logging() -> None:
    level_name = os.environ.get("FARM_WARS_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    if not logging.root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
    logging.getLogger().setLevel(level)
