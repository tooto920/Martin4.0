"""
Structured logging for Martin.
"""
import logging
import logging.handlers
from pathlib import Path

from app.core.config import get_config


def setup_logger(name: str = "martin") -> logging.Logger:
    """Set up and return a configured logger instance."""
    config = get_config()
    log_config = config.get_section("logging")

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_config.get("level", "INFO")))

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_file = log_config.get("file", "data/logs/martin.log")
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=log_config.get("max_size_mb", 10) * 1024 * 1024,
        backupCount=log_config.get("backup_count", 5),
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "martin") -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)