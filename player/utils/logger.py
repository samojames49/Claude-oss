"""راه‌اندازی لاگ‌گیری در فایل و کنسول."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .. import config

LOG_FILE = config.BASE_DIR / "player.log"
_configured = False


def setup_logging() -> logging.Logger:
    global _configured
    logger = logging.getLogger("player")
    if _configured:
        return logger

    level = getattr(logging, config.LOG_LEVEL, logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)

    handlers: list[logging.Handler] = [stream]
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    except OSError:
        pass

    root = logging.getLogger()
    root.setLevel(level)
    for handler in handlers:
        root.addHandler(handler)

    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("pytgcalls").setLevel(logging.WARNING)
    logging.getLogger("ntgcalls").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    logger.setLevel(level)
    _configured = True
    return logger


LOGGER = setup_logging()


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"player.{name}")
