import logging
import sys

from config.settings import Config


def setup_logger(name: str = "subsplease") -> logging.Logger:
    logger = logging.getLogger(name)
    level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(fmt)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger
