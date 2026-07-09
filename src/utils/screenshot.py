"""Screenshot utility for capturing browser states."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional, Union

from .logger import get_logger
from .config import get_settings

logger = get_logger(__name__)


async def save_screenshot(
    page,
    name: str,
    directory: Optional[str] = None,
    full_page: bool = False,
) -> Optional[str]:
    """
    Save a screenshot from a browser page.

    Args:
        page: Browser page object
        name: Name for the screenshot file (without extension)
        directory: Directory to save screenshot. If None, uses settings.
        full_page: Whether to capture full scrollable page

    Returns:
        Path to saved screenshot, or None if failed
    """
    if directory is None:
        settings = get_settings()
        directory = settings.screenshot_dir

    screenshot_dir = Path(directory)
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{name}_{get_timestamp()}.png"
    filepath = screenshot_dir / filename

    try:
        await page.screenshot(path=str(filepath), full_page=full_page)
        logger.info(f"Screenshot saved: {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"Failed to save screenshot: {e}")
        return None


async def save_screenshot_as_bytes(
    page,
    name: str,
    full_page: bool = False,
) -> Optional[bytes]:
    """
    Save a screenshot as bytes.

    Args:
        page: Browser page object
        name: Name prefix for logging
        full_page: Whether to capture full scrollable page

    Returns:
        Screenshot as bytes, or None if failed
    """
    try:
        screenshot_bytes = await page.screenshot(full_page=full_page)
        logger.debug(f"Screenshot '{name}' captured ({len(screenshot_bytes)} bytes)")
        return screenshot_bytes
    except Exception as e:
        logger.error(f"Failed to capture screenshot '{name}': {e}")
        return None


async def get_base64_screenshot(page, full_page: bool = False) -> Optional[str]:
    """
    Get screenshot as base64 encoded string.

    Args:
        page: Browser page object
        full_page: Whether to capture full scrollable page

    Returns:
        Base64 encoded screenshot, or None if failed
    """
    try:
        screenshot_bytes = await page.screenshot(full_page=full_page)
        return base64.b64encode(screenshot_bytes).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to get base64 screenshot: {e}")
        return None


def get_timestamp() -> str:
    """Get current timestamp string for filename."""
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")
