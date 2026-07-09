"""Base browser interface."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from ..utils.logger import get_logger
from ..antidetect.fingerprint import FingerprintProfile
from ..antidetect.profile import BrowserProfile
from ..antidetect.behavioral import BehavioralSimulator

logger = get_logger(__name__)


@dataclass
class BrowserConfig:
    """Configuration for browser launch."""

    # Profile
    profile: Optional[BrowserProfile] = None
    fingerprint: Optional[FingerprintProfile] = None

    # Proxy
    proxy_host: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None

    # Display
    headless: bool = False
    window_width: int = 1920
    window_height: int = 1080
    window_x: int = 0
    window_y: int = 0

    # Behavior
    use_stealth: bool = True
    behavioral_simulator: bool = True
    load_images: bool = True
    block_ads: bool = False

    # Navigation
    default_timeout: int = 30000  # ms
    navigation_timeout: int = 60000  # ms

    # User data
    user_data_dir: Optional[str] = None
    profile_dir: Optional[str] = None

    # Extensions
    extensions: List[str] = field(default_factory=list)

    # Browser executable
    executable_path: Optional[str] = None

    # Additional args
    additional_args: List[str] = field(default_factory=list)

    def get_proxy_url(self) -> Optional[str]:
        """Get proxy URL for browser configuration."""
        if not self.proxy_host:
            return None

        if self.proxy_username and self.proxy_password:
            return f"http://{self.proxy_username}:{self.proxy_password}@{self.proxy_host}:{self.proxy_port}"
        elif self.proxy_port:
            return f"http://{self.proxy_host}:{self.proxy_port}"
        else:
            return f"http://{self.proxy_host}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "proxy": self.get_proxy_url(),
            "headless": self.headless,
            "window_size": (self.window_width, self.window_height),
            "window_position": (self.window_x, self.window_y),
            "use_stealth": self.use_stealth,
            "fingerprint": self.fingerprint.to_dict() if self.fingerprint else None,
        }


class BaseBrowser(ABC):
    """
    Abstract base class for browser automation.

    This class provides the common interface for all browser implementations
    including Camoufox, CloakBrowser, and Playwright-based solutions.
    """

    def __init__(self, config: BrowserConfig):
        """
        Initialize browser.

        Args:
            config: Browser configuration
        """
        self.config = config
        self._page = None
        self._context = None
        self._browser = None
        self._behavior: Optional[BehavioralSimulator] = None

        if config.behavioral_simulator:
            self._behavior = BehavioralSimulator()

    @abstractmethod
    async def launch(self) -> None:
        """Launch the browser."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the browser."""
        pass

    @abstractmethod
    async def new_page(self) -> None:
        """Create a new page."""
        pass

    async def goto(self, url: str, wait_until: str = "domcontentloaded") -> None:
        """
        Navigate to URL.

        Args:
            url: Target URL
            wait_until: When to consider navigation complete
        """
        if not self._page:
            await self.new_page()

        await self._page.goto(url, wait_until=wait_until, timeout=self.config.navigation_timeout)
        logger.info(f"Navigated to {url}")

    async def screenshot(
        self,
        path: Optional[str] = None,
        full_page: bool = False,
    ) -> Optional[bytes]:
        """
        Take a screenshot.

        Args:
            path: Path to save screenshot
            full_page: Capture full scrollable page

        Returns:
            Screenshot bytes or None
        """
        if not self._page:
            return None

        try:
            if path:
                await self._page.screenshot(path=path, full_page=full_page)
                logger.info(f"Screenshot saved to {path}")
                return None
            else:
                return await self._page.screenshot(full_page=full_page)
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

    async def fill(self, selector: str, value: str) -> None:
        """
        Fill a form field.

        Args:
            selector: CSS selector for the element
            value: Value to fill
        """
        if not self._page:
            raise RuntimeError("No page available")

        # Use behavioral typing for more human-like input
        if self._behavior:
            await self._behavior.human_delay(0.1, 0.3)

        await self._page.fill(selector, value)
        logger.debug(f"Filled '{selector}' with '{value[:10]}...'")

    async def type_text(
        self,
        selector: str,
        text: str,
        delay: Optional[int] = None,
    ) -> None:
        """
        Type text into a field with typing simulation.

        Args:
            selector: CSS selector
            text: Text to type
            delay: Delay between keystrokes in ms
        """
        if not self._page:
            raise RuntimeError("No page available")

        if self._behavior:
            # Use behavioral typing
            element = await self._page.query_selector(selector)
            if element:
                box = await element.bounding_box()
                if box:
                    await self._behavior.move_mouse(
                        self._page,
                        (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2),
                        (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2),
                    )

            await self._behavior.type_with_log_normal(self._page, text)
        else:
            # Direct typing
            await self._page.type(selector, text, delay=delay)

        logger.debug(f"Typed text into '{selector}'")

    async def click(
        self,
        selector: str,
        button: str = "left",
        modifiers: Optional[List[str]] = None,
    ) -> None:
        """
        Click an element.

        Args:
            selector: CSS selector
            button: Mouse button ('left', 'right', 'middle')
            modifiers: Keyboard modifiers ('Alt', 'Control', etc.)
        """
        if not self._page:
            raise RuntimeError("No page available")

        if self._behavior:
            element = await self._page.query_selector(selector)
            if element:
                box = await element.bounding_box()
                if box:
                    await self._behavior.move_mouse(
                        self._page,
                        (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2),
                        (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2),
                    )
                    await self._behavior.click(
                        self._page,
                        box["x"] + box["width"] / 2,
                        box["y"] + box["height"] / 2,
                        button=button,
                    )
                    return

        await self._page.click(selector, button=button, modifiers=modifiers or [])
        logger.debug(f"Clicked '{selector}'")

    async def select_option(
        self,
        selector: str,
        value: str,
    ) -> None:
        """
        Select an option from a dropdown.

        Args:
            selector: CSS selector for select element
            value: Value to select
        """
        if not self._page:
            raise RuntimeError("No page available")

        await self._page.select_option(selector, value)
        logger.debug(f"Selected '{value}' in '{selector}'")

    async def check(self, selector: str) -> None:
        """Check a checkbox."""
        if not self._page:
            raise RuntimeError("No page available")

        await self._page.check(selector)
        logger.debug(f"Checked '{selector}'")

    async def uncheck(self, selector: str) -> None:
        """Uncheck a checkbox."""
        if not self._page:
            raise RuntimeError("No page available")

        await self._page.uncheck(selector)
        logger.debug(f"Unchecked '{selector}'")

    async def press(self, selector: str, key: str) -> None:
        """
        Press a key on an element.

        Args:
            selector: CSS selector
            key: Key name (e.g., 'Enter', 'Tab', 'Escape')
        """
        if not self._page:
            raise RuntimeError("No page available")

        await self._page.press(selector, key)
        logger.debug(f"Pressed '{key}' on '{selector}'")

    async def evaluate(self, script: str) -> Any:
        """
        Execute JavaScript in the page context.

        Args:
            script: JavaScript code to execute

        Returns:
            Result of script execution
        """
        if not self._page:
            raise RuntimeError("No page available")

        return await self._page.evaluate(script)

    async def wait_for_selector(
        self,
        selector: str,
        timeout: Optional[int] = None,
        state: str = "visible",
    ) -> bool:
        """
        Wait for an element to be in a certain state.

        Args:
            selector: CSS selector
            timeout: Timeout in ms
            state: Element state ('attached', 'detached', 'visible', 'hidden')

        Returns:
            True if element found, False if timeout
        """
        if not self._page:
            return False

        try:
            await self._page.wait_for_selector(
                selector,
                timeout=timeout or self.config.default_timeout,
                state=state,
            )
            return True
        except Exception:
            return False

    async def wait_for_load_state(
        self,
        state: str = "networkidle",
        timeout: Optional[int] = None,
    ) -> None:
        """
        Wait for page to reach a load state.

        Args:
            state: Load state ('load', 'domcontentloaded', 'networkidle')
            timeout: Timeout in ms
        """
        if not self._page:
            return

        await self._page.wait_for_load_state(
            state,
            timeout=timeout or self.config.default_timeout,
        )

    async def scroll(
        self,
        x: int = 0,
        y: int = 0,
        smooth: bool = True,
    ) -> None:
        """
        Scroll the page.

        Args:
            x: X position to scroll to
            y: Y position to scroll to
            smooth: Use smooth scrolling
        """
        if not self._page:
            return

        if smooth and self._behavior:
            await self._behavior.scroll(self._page, y)
        else:
            await self._page.evaluate(f"window.scrollTo({x}, {y})")

    async def scroll_to_element(self, selector: str) -> None:
        """
        Scroll to bring an element into view.

        Args:
            selector: CSS selector
        """
        if not self._page:
            return

        if self._behavior:
            await self._behavior.scroll_to_element(self._page, selector)
        else:
            await self._page.evaluate(f"""
                document.querySelector('{selector}').scrollIntoView({{
                    behavior: 'smooth',
                    block: 'center'
                }})
            """)

    def get_page(self):
        """Get the underlying page object."""
        return self._page

    @property
    def is_running(self) -> bool:
        """Check if browser is running."""
        return self._browser is not None and self._page is not None

    async def __aenter__(self) -> "BaseBrowser":
        """Async context manager entry."""
        await self.launch()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
