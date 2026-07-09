"""Browser launcher factory."""

from __future__ import annotations

from typing import Optional

from ..utils.logger import get_logger
from ..utils.config import get_settings

from .base import BaseBrowser, BrowserConfig
from .camoufox import CamoufoxBrowser

logger = get_logger(__name__)


class BrowserLauncher:
    """
    Factory for launching anti-detect browsers.

    Supports multiple browser backends:
    - Camoufox (recommended - C++ fingerprinting)
    - Playwright (fallback)
    - Custom browser implementations
    """

    def __init__(self, browser_type: Optional[str] = None):
        """
        Initialize browser launcher.

        Args:
            browser_type: Browser type to use ('camoufox', 'playwright', 'auto')
        """
        settings = get_settings()
        self.browser_type = browser_type or settings.browser_type or "auto"
        self.settings = settings

    async def launch(
        self,
        config: Optional[BrowserConfig] = None,
        **kwargs,
    ) -> BaseBrowser:
        """
        Launch a browser with the specified configuration.

        Args:
            config: Browser configuration
            **kwargs: Additional configuration options

        Returns:
            Browser instance
        """
        if config is None:
            config = BrowserConfig(**kwargs)

        # Try to launch requested browser type
        if self.browser_type in ("camoufox", "auto"):
            try:
                browser = CamoufoxBrowser(config)
                await browser.launch()
                return browser
            except Exception as e:
                logger.warning(f"Camoufox launch failed: {e}")

        # Fallback to Playwright
        if self.browser_type in ("playwright", "auto", "cloackbrowser"):
            try:
                browser = PlaywrightBrowser(config)
                await browser.launch()
                return browser
            except Exception as e:
                logger.error(f"Playwright launch failed: {e}")

        raise RuntimeError(f"Failed to launch browser of type '{self.browser_type}'")

    def get_available_browsers(self) -> list[str]:
        """Get list of available browser types."""
        browsers = []

        # Check for Camoufox
        try:
            import camoufox
            browsers.append("camoufox")
        except ImportError:
            pass

        # Check for Playwright
        try:
            import playwright
            browsers.append("playwright")
        except ImportError:
            pass

        return browsers if browsers else ["playwright"]  # Always at least Playwright


class PlaywrightBrowser(BaseBrowser):
    """
    Standard Playwright browser implementation.

    This is used as a fallback when Camoufox is not available.
    It includes basic stealth modifications but is less effective
    at evading bot detection than Camoufox.
    """

    def __init__(self, config: BrowserConfig):
        """Initialize Playwright browser."""
        super().__init__(config)
        self._playwright = None

    async def launch(self) -> None:
        """Launch Playwright browser."""
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()

        # Build launch options
        options = {
            "headless": self.config.headless,
            "args": self._get_args(),
        }

        if self.config.executable_path:
            options["executable_path"] = self.config.executable_path

        # Launch browser
        self._browser = await self._playwright.chromium.launch(**options)

        # Build context options
        context_options = {
            "viewport": {
                "width": self.config.window_width,
                "height": self.config.window_height,
            },
            "ignore_https_errors": True,
        }

        if self.config.fingerprint and self.config.fingerprint.user_agent:
            context_options["user_agent"] = self.config.fingerprint.user_agent

        # Set proxy if configured
        if self.config.proxy_host:
            context_options["proxy"] = self._get_proxy_dict()

        self._context = await self._browser.new_context(**context_options)

        # Apply stealth
        await self._apply_stealth()

        # Create page
        self._page = await self._context.new_page()

        logger.info("Playwright browser launched")

    async def close(self) -> None:
        """Close the browser."""
        if self._page:
            await self._page.close()
            self._page = None

        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        logger.info("Playwright browser closed")

    async def new_page(self) -> None:
        """Create a new page."""
        if self._context:
            self._page = await self._context.new_page()
        else:
            raise RuntimeError("Browser not launched")

    def _get_args(self) -> list[str]:
        """Get Chromium launch arguments for stealth."""
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote",
            "--disable-gpu",
            "--window-size=1920,1080",
        ]

        if self.config.fingerprint:
            fp = self.config.fingerprint
            if fp.language:
                args.append(f"--lang={fp.language}")

        args.extend(self.config.additional_args)

        return args

    def _get_proxy_dict(self) -> dict:
        """Get proxy configuration."""
        proxy = {
            "server": f"http://{self.config.proxy_host}:{self.config.proxy_port or 80}",
        }

        if self.config.proxy_username and self.config.proxy_password:
            proxy["username"] = self.config.proxy_username
            proxy["password"] = self.config.proxy_password

        return proxy

    async def _apply_stealth(self) -> None:
        """Apply stealth modifications."""
        if not self._page or not self.config.use_stealth:
            return

        # Remove webdriver property
        await self._page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Remove automation flags
        await self._page.add_init_script("""
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

        # Canvas noise injection
        await self._page.add_init_script("""
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function() {
                const ctx = this.getContext('2d');
                if (ctx) {
                    const imageData = ctx.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.random() * 0.1;
                        imageData.data[i + 1] += Math.random() * 0.1;
                        imageData.data[i + 2] += Math.random() * 0.1;
                    }
                    ctx.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, arguments);
            };
        """)


# Global launcher instance
_launcher: Optional[BrowserLauncher] = None


def get_browser_launcher(browser_type: Optional[str] = None) -> BrowserLauncher:
    """
    Get or create browser launcher instance.

    Args:
        browser_type: Browser type to use

    Returns:
        BrowserLauncher instance
    """
    global _launcher
    if _launcher is None:
        _launcher = BrowserLauncher(browser_type)
    return _launcher
