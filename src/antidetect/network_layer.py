"""Network layer integration module.

This module provides the integration between:
- TLS fingerprint spoofing (curl_cffi)
- HTTP/2 settings spoofing
- Proxy rotation
- Browser fingerprinting

It ensures network-level fingerprints are consistent across all requests.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from ..utils.logger import get_logger
from ..proxy.rotator import ProxyConfig

from .tls_fingerprint import TLSFingerprintGenerator, TLSHTTPClient, get_tls_generator, get_tls_http_client
from .http2_spoofing import HTTP2FingerprintGenerator, HTTP2TLSClient, get_http2_generator

logger = get_logger(__name__)


@dataclass
class NetworkProfile:
    """Complete network fingerprint profile."""

    # TLS fingerprint
    tls_profile: str = "chrome120"
    ja3_hash: str = ""
    curl_impersonate: str = "chrome120"

    # HTTP/2 fingerprint
    http2_profile: str = "chrome_windows"
    http2_settings: Dict[str, int] = field(default_factory=dict)
    header_order: List[str] = field(default_factory=list)

    # OS/Browser matching
    os: str = "windows"
    browser: str = "chrome"
    browser_version: str = "120"

    # Timing
    connection_timeout: int = 30
    read_timeout: int = 60

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tls_profile": self.tls_profile,
            "ja3_hash": self.ja3_hash,
            "curl_impersonate": self.curl_impersonate,
            "http2_profile": self.http2_profile,
            "http2_settings": self.http2_settings,
            "header_order": self.header_order,
            "os": self.os,
            "browser": self.browser,
            "browser_version": self.browser_version,
            "connection_timeout": self.connection_timeout,
            "read_timeout": self.read_timeout,
        }


class NetworkLayer:
    """
    Central network layer for fingerprint management.

    This class coordinates:
    - TLS fingerprint generation
    - HTTP/2 fingerprint generation
    - Network request execution
    - Proxy-aware fingerprint selection
    """

    def __init__(
        self,
        default_tls_profile: Optional[str] = None,
        default_http2_profile: Optional[str] = None,
    ):
        """
        Initialize network layer.

        Args:
            default_tls_profile: Default TLS profile name
            default_http2_profile: Default HTTP/2 profile name
        """
        self._tls_generator = get_tls_generator()
        self._http2_generator = get_http2_generator()
        self._tls_client = get_tls_http_client()

        self._default_tls_profile = default_tls_profile or "chrome120"
        self._default_http2_profile = default_http2_profile or "chrome_windows"

        # Track current profiles
        self._current_profile: Optional[NetworkProfile] = None

        # Session statistics
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "by_profile": {},
        }

    def generate_profile(
        self,
        os: Optional[str] = None,
        browser: Optional[str] = None,
        country: Optional[str] = None,
    ) -> NetworkProfile:
        """
        Generate a complete network profile.

        Args:
            os: Target OS
            browser: Target browser
            country: Target country (for geo-specific profiles)

        Returns:
            Complete NetworkProfile
        """
        # Get TLS profile
        tls_profile = self._tls_generator.get_profile(os, browser, country)
        tls_impersonate = tls_profile.curl_impersonate

        # Get HTTP/2 profile
        http2_profile = self._http2_generator.get_profile(os, browser)

        # Create network profile
        profile = NetworkProfile(
            tls_profile=tls_profile.name,
            ja3_hash=tls_profile.ja3_hash,
            curl_impersonate=tls_impersonate,
            http2_profile=http2_profile.name,
            http2_settings=http2_profile.settings,
            header_order=http2_profile.header_order,
            os=tls_profile.os,
            browser=tls_profile.browser,
            browser_version=tls_profile.browser_version,
        )

        self._current_profile = profile
        logger.debug(f"Generated network profile: {profile.tls_profile}/{profile.http2_profile}")

        return profile

    def get_profile(self) -> Optional[NetworkProfile]:
        """Get current network profile."""
        return self._current_profile

    def set_profile(self, profile_name: str) -> NetworkProfile:
        """
        Set profile by name.

        Args:
            profile_name: Profile name (e.g., "chrome120", "chrome_windows")

        Returns:
            NetworkProfile
        """
        # Determine OS/browser from profile name
        os = "windows"
        browser = "chrome"

        if "mac" in profile_name.lower():
            os = "mac"
        elif "linux" in profile_name.lower():
            os = "linux"
        elif "android" in profile_name.lower():
            os = "android"

        if "firefox" in profile_name.lower():
            browser = "firefox"
        elif "safari" in profile_name.lower():
            browser = "safari"
        elif "edge" in profile_name.lower():
            browser = "edge"

        return self.generate_profile(os, browser)

    # =========================================================================
    # HTTP REQUESTS WITH FINGERPRINT SPOOFING
    # =========================================================================

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        proxy: Optional[ProxyConfig] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> Any:
        """
        Make HTTP request with fingerprint spoofing.

        Args:
            method: HTTP method
            url: Target URL
            headers: Request headers
            data: Form data
            json: JSON data
            proxy: Proxy configuration
            timeout: Request timeout
            **kwargs: Additional arguments

        Returns:
            Response object
        """
        profile = self._current_profile or self.generate_profile()

        # Get proxy URL
        proxy_url = proxy.get_url() if proxy else None

        # Get timeout
        req_timeout = timeout or profile.connection_timeout

        self._stats["total_requests"] += 1

        try:
            if method.upper() == "GET":
                response = await self._tls_client.get(
                    url=url,
                    os=profile.os,
                    browser=profile.browser,
                    proxy=proxy_url,
                    timeout=req_timeout,
                    headers=headers,
                    **kwargs,
                )
            elif method.upper() == "POST":
                response = await self._tls_client.post(
                    url=url,
                    data=data,
                    json=json,
                    os=profile.os,
                    browser=profile.browser,
                    proxy=proxy_url,
                    timeout=req_timeout,
                    headers=headers,
                    **kwargs,
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            self._stats["successful_requests"] += 1
            self._update_profile_stats(profile, success=True)

            return response

        except Exception as e:
            self._stats["failed_requests"] += 1
            self._update_profile_stats(profile, success=False)
            logger.error(f"Request failed: {e}")
            raise

    async def get(self, url: str, **kwargs) -> Any:
        """Make GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> Any:
        """Make POST request."""
        return await self.request("POST", url, **kwargs)

    def sync_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        proxy: Optional[ProxyConfig] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> Any:
        """
        Make synchronous HTTP request with fingerprint spoofing.

        Args:
            method: HTTP method
            url: Target URL
            headers: Request headers
            data: Form data
            json: JSON data
            proxy: Proxy configuration
            timeout: Request timeout
            **kwargs: Additional arguments

        Returns:
            Response object
        """
        profile = self._current_profile or self.generate_profile()
        proxy_url = proxy.get_url() if proxy else None
        req_timeout = timeout or profile.connection_timeout

        self._stats["total_requests"] += 1

        try:
            if method.upper() == "GET":
                response = self._tls_client.sync_get(
                    url=url,
                    os=profile.os,
                    browser=profile.browser,
                    proxy=proxy_url,
                    timeout=req_timeout,
                    headers=headers,
                    **kwargs,
                )
            elif method.upper() == "POST":
                response = self._tls_client.sync_post(
                    url=url,
                    data=data,
                    json=json,
                    os=profile.os,
                    browser=profile.browser,
                    proxy=proxy_url,
                    timeout=req_timeout,
                    headers=headers,
                    **kwargs,
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            self._stats["successful_requests"] += 1
            self._update_profile_stats(profile, success=True)

            return response

        except Exception as e:
            self._stats["failed_requests"] += 1
            self._update_profile_stats(profile, success=False)
            logger.error(f"Request failed: {e}")
            raise

    def sync_get(self, url: str, **kwargs) -> Any:
        """Make synchronous GET request."""
        return self.sync_request("GET", url, **kwargs)

    def sync_post(self, url: str, **kwargs) -> Any:
        """Make synchronous POST request."""
        return self.sync_request("POST", url, **kwargs)

    # =========================================================================
    # BROWSER-LEVEL FINGERPRINT SCRIPTS
    # =========================================================================

    def get_browser_stealth_script(self) -> str:
        """
        Get JavaScript for browser injection to enhance network stealth.

        Returns:
            JavaScript code for browser injection
        """
        http2_manip = HTTP2TLSClient(self._default_http2_profile)

        return f"""
(function() {{
    'use strict';

    // ============================================
    // NETWORK LAYER STEALTH SCRIPT
    // ============================================

    // 1. Remove automation indicators
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined,
        configurable: true
    }});

    // 2. Spoof chrome object
    window.chrome = {{
        runtime: {{}},
        loadTimes: function() {{}},
        csi: function() {{}},
        app: {{}}
    }};

    // 3. Remove automation-specific properties
    Object.defineProperty(navigator, 'automation', {{
        get: () => undefined
    }});

    // 4. Remove permissions API manipulation
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({{ state: Notification.permission }}) :
            originalQuery(parameters)
    );

    // 5. Spoof connection properties
    Object.defineProperty(navigator, 'connection', {{
        get: () => {{
            return {{
                effectiveType: '4g',
                downlink: 10,
                rtt: 50,
                saveData: false,
                onchange: null,
                addEventListener: () => {{}},
                removeEventListener: () => {{}},
                dispatchEvent: () => true
            }};
        }}
    }});

    // 6. Spoof device memory
    Object.defineProperty(navigator, 'deviceMemory', {{
        get: () => 8
    }});

    // 7. Spoof hardware concurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: () => {random.randint(4, 12)}
    }});

    // 8. Remove iframe sandbox flags
    try {{
        const iframe = document.createElement('iframe');
        iframe.sandbox.add('allow-same-origin');
    }} catch(e) {{}}

    // 9. Override WebSocket to maintain fingerprint consistency
    const originalWebSocket = window.WebSocket;
    window.WebSocket = function(url, protocols) {{
        const ws = new originalWebSocket(url, protocols);
        // WebSocket fingerprinting mitigation could go here
        return ws;
    }};

    // 10. Spoof media devices
    Object.defineProperty(navigator, 'mediaDevices', {{
        get: () => {{
            return {{
                enumerateDevices: () => Promise.resolve([
                    {{ kind: 'audioinput', deviceId: 'default', groupId: 'group1', label: 'Microphone' }},
                    {{ kind: 'videoinput', deviceId: 'default', groupId: 'group2', label: 'Camera' }}
                ]),
                getUserMedia: () => Promise.resolve({{}}),
                getSupportedConstraints: () => {{}},
                addEventListener: () => {{}},
                removeEventListener: () => {{}}
            }};
        }}
    }});

    console.log('[Network Layer] Stealth script loaded');
}})();
"""

    def get_http2_header_script(self) -> str:
        """
        Get JavaScript for HTTP/2 header manipulation.

        Returns:
            JavaScript code for browser injection
        """
        http2_gen = get_http2_generator()
        profile = http2_gen.get_profile()

        manipulator = HTTP2TLSClient(profile.name)
        return manipulator.get_header_order_script()

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def _update_profile_stats(
        self,
        profile: NetworkProfile,
        success: bool,
    ) -> None:
        """Update statistics for a profile."""
        key = f"{profile.tls_profile}/{profile.http2_profile}"
        if key not in self._stats["by_profile"]:
            self._stats["by_profile"][key] = {
                "success": 0,
                "failed": 0,
            }

        if success:
            self._stats["by_profile"][key]["success"] += 1
        else:
            self._stats["by_profile"][key]["failed"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get network layer statistics."""
        stats = self._stats.copy()

        # Calculate success rate
        if stats["total_requests"] > 0:
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
        else:
            stats["success_rate"] = 0

        return stats

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "by_profile": {},
        }


# =============================================================================
# BROWSER FINGERPRINT INTEGRATION
# =============================================================================

class BrowserFingerprintBridge:
    """
    Bridge between network layer and browser fingerprinting.

    This class ensures:
    - Browser fingerprints match network fingerprints
    - TLS/HTTP2 profiles are consistent
    - Browser launch arguments are correct
    """

    def __init__(self, network_layer: Optional[NetworkLayer] = None):
        """
        Initialize browser fingerprint bridge.

        Args:
            network_layer: NetworkLayer instance
        """
        self._network_layer = network_layer or NetworkLayer()

    def get_chrome_args(self, profile: Optional[NetworkProfile] = None) -> List[str]:
        """
        Get Chrome launch arguments for stealth.

        Args:
            profile: Network profile to match

        Returns:
            List of Chrome arguments
        """
        if profile is None:
            profile = self._network_layer.get_profile() or self._network_layer.generate_profile()

        args = [
            # Remove automation indicators
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote",
            "--window-size=1920,1080",
            "--start-maximized",

            # Additional stealth args
            "--disable-blink-features=AutomationDetector",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-web-security",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-breakpad",
            "--disable-client-side-phishing-detection",
            "--disable-component-extensions-with-background-pages",
            "--disable-component-update",
            "--disable-default-apps",
            "--disable-derivatives",
            "--disable-desktop-notifications",
            "--disable-device-discovery-notifications",
            "--disable-domain-reliability",
            "--disable-extensions",
            "--disable-features=TranslateUI",
            "--disable-geolocation",
            "--disable-hang-monitor",
            "--disable-ipc-flooding-protection",
            "--disable-logging",
            "--disable-login-animations",
            "--disable-logging-redirect",
            "--disable-network-information",
            "--disable-new-menu-style",
            "--disable-offer-store-unmasked-wallet-cards",
            "--disable-password-generation",
            "--disable-popup-blocking",
            "--disable-prompt-on-repost",
            "--disable-renderer-backgrounding",
            "--disable-session-crashed-bubble",
            "--disable-settings-window",
            "--disable-silent-googledrive-sso",
            "--disable-speech-api",
            "--disable-sync",
            "--disable-tab-for-metrics",
            "--disable-translate",
            "--disable-wake-on-wifi",
            "--disable-web-resources",
            "--enable-features=NetworkService,NetworkServiceInProcess",
            "--force-color-profile=srgb",
            "--metrics-recording-only",
            "--mute-audio",
        ]

        # Add OS-specific args
        if profile.os == "mac":
            args.extend([
                "--disable-mac-hyperthreading",
            ])
        elif profile.os == "linux":
            args.extend([
                "--disable-gpu-sandbox",
            ])

        return args

    def get_stealth_scripts(self) -> List[str]:
        """
        Get all stealth scripts for browser injection.

        Returns:
            List of JavaScript scripts
        """
        return [
            self._network_layer.get_browser_stealth_script(),
            self._network_layer.get_http2_header_script(),
        ]


# Global instance
_network_layer: Optional[NetworkLayer] = None
_bridge: Optional[BrowserFingerprintBridge] = None


def get_network_layer() -> NetworkLayer:
    """Get or create global network layer."""
    global _network_layer
    if _network_layer is None:
        _network_layer = NetworkLayer()
    return _network_layer


def get_browser_bridge() -> BrowserFingerprintBridge:
    """Get or create global browser fingerprint bridge."""
    global _bridge
    if _bridge is None:
        _bridge = BrowserFingerprintBridge()
    return _bridge
