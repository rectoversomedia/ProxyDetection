"""Logging configuration for ProxyDetection."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from .config import get_settings


def setup_logger(
    log_file: Optional[str] = None,
    log_level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "7 days",
) -> None:
    """
    Configure loguru logger with file and console outputs.

    Args:
        log_file: Path to log file. If None, uses settings.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation: When to rotate log files
        retention: How long to keep old log files
    """
    # Remove default handler
    logger.remove()

    # Get settings if not provided
    if log_file is None:
        try:
            settings = get_settings()
            log_file = settings.log_file
        except Exception:
            log_file = "logs/app.log"

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Console output with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # File output
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation=rotation,
        retention=retention,
        compression="zip",
        serialize=False,
    )

    logger.info(f"Logger initialized. Log file: {log_file}")


def get_logger(name: str) -> logger:
    """
    Get a logger instance for a module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logger.bind(name=name)
