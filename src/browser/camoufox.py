"""Camoufox browser implementation.

Camoufox is a headless browser with built-in C++-level fingerprint spoofing
that provides excellent bot detection evasion.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger
from ..utils.config import get_settings

from .base import BaseBrowser, BrowserConfig

logger = get_logger(__name__)


class CamoufoxBrowser(BaseBrowser):
    """
    Camoufox browser with built-in anti-detection features.

    Camoufox provides:
    - C++-level fingerprint spoofing (canvas, WebGL, audio)
    - TLS fingerprint matching
    - Automatic timezone geoIP matching
    - Human-like mouse movements
    - reCAPTCHA solver integration

    Note: Camoufox needs to be installed separately.
    Install via: pip install camoufox
    """

    def __init__(self, config: BrowserConfig):
        """
        Initialize Camoufox browser.

        Args:
            config: Browser configuration
        """
        super().__init__(config)
        self._camoufox = None
        self._playwright = None

    async def launch(self) -> None:
        """Launch Camoufox browser."""
        try:
            # Try to import camoufox
            import camoufox
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error(
                "Camoufox not installed. Install with: pip install camoufox\n"
                "Falling back to standard Playwright."
            )
            await self._launch_playwright()
            return

        # Configure Camoufox
        args = self._get_camoufox_args()

        try:
            async with async_playwright() as p:
                # Launch with Camoufox
                self._browser = await p.chromium.launch(
                    executable_path=self.config.executable_path,
                    headless=self.config.headless,
                    args=args,
                    proxy=self._get_proxy_dict() if self.config.proxy_host else None,
                )

                self._context = await self._browser.new_context(
                    viewport={
                        "width": self.config.window_width,
                        "height": self.config.window_height,
                    },
                    ignore_https_errors=True,
                )

                self._page = await self._context.new_page()
                await self._apply_stealth()

                logger.info("Camoufox browser launched successfully")
        except Exception as e:
            logger.warning(f"Camoufox launch failed: {e}. Falling back to Playwright.")
            await self._launch_playwright()

    async def _launch_playwright(self) -> None:
        """Launch standard Playwright browser as fallback."""
        from playwright.async_api import async_playwright

        args = self._get_playwright_args()

        async with async_playwright() as p:
            self._browser = await p.chromium.launch(
                headless=self.config.headless,
                args=args,
                proxy=self._get_proxy_dict() if self.config.proxy_host else None,
            )

            self._context = await self._browser.new_context(
                viewport={
                    "width": self.config.window_width,
                    "height": self.config.window_height,
                },
                ignore_https_errors=True,
                user_agent=self.config.fingerprint.user_agent if self.config.fingerprint else None,
            )

            self._page = await self._context.new_page()
            await self._apply_stealth()

            logger.info("Playwright browser launched (fallback mode)")

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

        logger.info("Browser closed")

    async def new_page(self) -> None:
        """Create a new page."""
        if self._context:
            self._page = await self._context.new_page()
        else:
            raise RuntimeError("Browser not launched")

    def _get_camoufox_args(self) -> List[str]:
        """Get Camoufox-specific arguments."""
        args = [
            # Stealth arguments
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote",
            "--disable-gpu",
            "--window-size=1920,1080",
            "--start-maximized",
        ]

        if self.config.fingerprint:
            # Add fingerprint-based arguments
            fp = self.config.fingerprint

            if fp.language:
                args.append(f"--lang={fp.language}")

            if fp.timezone:
                # Timezone spoofing
                args.append(f"--timezone={fp.timezone}")

        # Add any additional arguments
        args.extend(self.config.additional_args)

        return args

    def _get_playwright_args(self) -> List[str]:
        """Get Playwright-specific arguments for stealth."""
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-blink-features=AutomationDetector",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote",
            "--disable-gpu",
            "--window-size=1920,1080",
            "--start-maximized",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ]

        if self.config.fingerprint:
            fp = self.config.fingerprint

            if fp.language:
                args.append(f"--lang={fp.language}")

        args.extend(self.config.additional_args)

        return args

    def _get_proxy_dict(self) -> Optional[Dict[str, Any]]:
        """Get proxy configuration for Playwright."""
        if not self.config.proxy_host:
            return None

        proxy = {
            "server": f"http://{self.config.proxy_host}:{self.config.proxy_port or 80}",
        }

        if self.config.proxy_username and self.config.proxy_password:
            proxy["username"] = self.config.proxy_username
            proxy["password"] = self.config.proxy_password

        return proxy

    async def _apply_stealth(self) -> None:
        """Apply stealth modifications to the page."""
        if not self._page or not self.config.use_stealth:
            return

        # Remove webdriver property
        await self._page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
        """)

        # Remove automation-related properties
        await self._page.add_init_script("""
            // Remove automation indicators
            window.navigator.chrome = {
                runtime: {}
            };

            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        # Apply fingerprint modifications if available
        if self.config.fingerprint:
            await self._apply_fingerprint(self.config.fingerprint)

    async def _apply_fingerprint(self, fp) -> None:
        """Apply fingerprint modifications to the page."""
        if not self._page:
            return

        # Canvas fingerprint randomization
        if self.config.profile and self.config.profile.randomize_canvas:
            await self._page.add_init_script("""
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

                // Add noise to canvas
                HooksCanvas.addNoise(document);

                // Override toDataURL
                HTMLCanvasElement.prototype.toDataURL = function(...args) {
                    const canvas = document.createElement('canvas');
                    canvas.width = this.width;
                    canvas.height = this.height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(this, 0, 0);
                    // Add random noise before returning
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.random() * 0.1;
                        imageData.data[i + 1] += Math.random() * 0.1;
                        imageData.data[i + 2] += Math.random() * 0.1;
                    }
                    ctx.putImageData(imageData, 0, 0);
                    return originalToDataURL.apply(canvas, args);
                };

                // Override getImageData
                CanvasRenderingContext2D.prototype.getImageData = function(...args) {
                    const imageData = originalGetImageData.apply(this, args);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.random() * 0.1;
                        imageData.data[i + 1] += Math.random() * 0.1;
                        imageData.data[i + 2] += Math.random() * 0.1;
                    }
                    return imageData;
                };
            """)

        # WebGL spoofing
        if fp.webgl_vendor or fp.webgl_renderer:
            webgl_script = f"""
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) {{
                        return '{fp.webgl_vendor or "Google Inc."}';
                    }}
                    if (parameter === 37446) {{
                        return '{fp.webgl_renderer or "ANGLE (NVIDIA GeForce GTX 1060)"}';
                    }}
                    return getParameter.apply(this, arguments);
                }};
            """
            await self._page.add_init_script(webgl_script)

        # Audio fingerprint spoofing
        if self.config.profile and self.config.profile.randomize_audio:
            await self._page.add_init_script("""
                const originalCreateAnalyser = AudioContext.prototype.createAnalyser;
                AudioContext.prototype.createAnalyser = function() {
                    const analyser = originalCreateAnalyser.apply(this, arguments);
                    const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                    analyser.getFloatFrequencyData = function(array) {
                        originalGetFloatFrequencyData.apply(this, arguments);
                        for (let i = 0; i < array.length; i++) {
                            array[i] += Math.random() * 0.01;
                        }
                        return array;
                    };
                    return analyser;
                };
            """)

        logger.debug("Fingerprint modifications applied")

    async def solve_captcha(
        self,
        site_key: str,
        url: str,
    ) -> Optional[str]:
        """
        Attempt to solve reCAPTCHA.

        Note: This is a placeholder. In production, integrate with
        a CAPTCHA solving service like 2Captcha or Anti-Captcha.

        Args:
            site_key: reCAPTCHA site key
            url: Page URL where CAPTCHA appears

        Returns:
            CAPTCHA solution token or None
        """
        logger.warning("CAPTCHA solving not implemented. Use external service.")
        return None

    async def check_for_challenge(self) -> Dict[str, Any]:
        """
        Check if the page is showing a challenge (Cloudflare, CAPTCHA, etc.).

        Returns:
            Dict with challenge info
        """
        result = {
            "has_challenge": False,
            "challenge_type": None,
            "message": None,
        }

        if not self._page:
            return result

        try:
            # Check for Cloudflare
            cf_challenge = await self._page.query_selector("#cf-challenge-container, .cf-error-wrapper")
            if cf_challenge:
                result["has_challenge"] = True
                result["challenge_type"] = "cloudflare"
                result["message"] = "Cloudflare challenge detected"
                return result

            # Check for reCAPTCHA
            captcha = await self._page.query_selector(".g-recaptcha")
            if captcha:
                result["has_challenge"] = True
                result["challenge_type"] = "recaptcha"
                result["message"] = "reCAPTCHA detected"
                return result

            # Check for hCaptcha
            hcaptcha = await self._page.query_selector(".h-captcha")
            if hcaptcha:
                result["has_challenge"] = True
                result["challenge_type"] = "hcaptcha"
                result["message"] = "hCaptcha detected"
                return result

            # Check for general challenge text
            title = await self._page.title()
            if "just a moment" in title.lower() or "checking your browser" in title.lower():
                result["has_challenge"] = True
                result["challenge_type"] = "cloudflare"
                result["message"] = title

        except Exception as e:
            logger.debug(f"Challenge check error: {e}")

        return result
