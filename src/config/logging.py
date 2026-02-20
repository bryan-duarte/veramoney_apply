import logging
import sys

from src.config.settings import settings


_NOISY_LOGGERS = ("httpx", "httpcore", "chromadb")

_VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


def configure_logging() -> str:
    raw_log_level = settings.log_level.upper()

    is_valid_log_level = raw_log_level in _VALID_LOG_LEVELS
    log_level = raw_log_level if is_valid_log_level else "INFO"

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    for noisy_logger_name in _NOISY_LOGGERS:
        logging.getLogger(noisy_logger_name).setLevel(logging.WARNING)

    return log_level
