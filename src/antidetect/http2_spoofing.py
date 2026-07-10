"""HTTP/2 fingerprint spoofing module.

This module provides HTTP/2 SETTINGS frame manipulation and header spoofing
to match authentic browser HTTP/2 fingerprints.

HTTP/2 fingerprints are created from:
- SETTINGS frame values
- Header order and naming conventions
- Window update patterns
- Dependency frame structures
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# HTTP/2 FINGERPRINT PROFILES
# =============================================================================

# HTTP/2 SETTINGS values for different browsers
# These values affect the HTTP/2 fingerprint
HTTP2_PROFILES: Dict[str, Dict[str, Any]] = {
    "chrome_windows": {
        "description": "Chrome on Windows HTTP/2 settings",
        "settings": {
            "header_table_size": 65536,
            "enable_push": 1,
            "max_concurrent_streams": 1000,
            "initial_window_size": 6291456,
            "max_frame_size": 16384,
            "max_header_list_size": 262144,
        },
        "header_order": [
            ":method",
            ":authority",
            ":scheme",
            ":path",
            "accept",
            "accept-encoding",
            "accept-language",
            "cookie",
            "referer",
            "user-agent",
        ],
        "window_update": True,
        "dependency_exclusive": False,
    },
    "chrome_mac": {
        "description": "Chrome on macOS HTTP/2 settings",
        "settings": {
            "header_table_size": 65536,
            "enable_push": 1,
            "max_concurrent_streams": 1000,
            "initial_window_size": 6291456,
            "max_frame_size": 16384,
            "max_header_list_size": 262144,
        },
        "header_order": [
            ":method",
            ":authority",
            ":scheme",
            ":path",
            "accept",
            "accept-encoding",
            "accept-language",
            "accept-charset",
            "cookie",
            "referer",
            "user-agent",
        ],
        "window_update": True,
        "dependency_exclusive": False,
    },
    "firefox_windows": {
        "description": "Firefox on Windows HTTP/2 settings",
        "settings": {
            "header_table_size": 65536,
            "enable_push": 0,
            "max_concurrent_streams": 100,
            "initial_window_size": 131072,
            "max_frame_size": 16384,
            "max_header_list_size": 65536,
        },
        "header_order": [
            ":method",
            ":host",
            ":scheme",
            ":path",
            "user-agent",
            "accept",
            "accept-language",
            "accept-encoding",
            "cookie",
            "referer",
        ],
        "window_update": True,
        "dependency_exclusive": True,
    },
    "firefox_mac": {
        "description": "Firefox on macOS HTTP/2 settings",
        "settings": {
            "header_table_size": 65536,
            "enable_push": 0,
            "max_concurrent_streams": 100,
            "initial_window_size": 131072,
            "max_frame_size": 16384,
            "max_header_list_size": 65536,
        },
        "header_order": [
            ":method",
            ":host",
            ":scheme",
            ":path",
            "user-agent",
            "accept",
            "accept-language",
            "accept-encoding",
            "cookie",
            "referer",
        ],
        "window_update": True,
        "dependency_exclusive": True,
    },
    "safari_mac": {
        "description": "Safari on macOS HTTP/2 settings",
        "settings": {
            "header_table_size": 4096,
            "enable_push": 0,
            "max_concurrent_streams": 100,
            "initial_window_size": 262144,
            "max_frame_size": 16384,
            "max_header_list_size": 65536,
        },
        "header_order": [
            ":method",
            ":path",
            ":scheme",
            "accept",
            "accept-language",
            "accept-encoding",
            "user-agent",
            "upgrade-insecure-requests",
        ],
        "window_update": False,
        "dependency_exclusive": True,
    },
    "edge_windows": {
        "description": "Edge on Windows HTTP/2 settings",
        "settings": {
            "header_table_size": 65536,
            "enable_push": 1,
            "max_concurrent_streams": 1000,
            "initial_window_size": 6291456,
            "max_frame_size": 16384,
            "max_header_list_size": 262144,
        },
        "header_order": [
            ":method",
            ":authority",
            ":scheme",
            ":path",
            "accept",
            "accept-encoding",
            "accept-language",
            "cookie",
            "referer",
            "user-agent",
        ],
        "window_update": True,
        "dependency_exclusive": False,
    },
    "chrome_android": {
        "description": "Chrome on Android HTTP/2 settings",
        "settings": {
            "header_table_size": 65536,
            "enable_push": 1,
            "max_concurrent_streams": 100,
            "initial_window_size": 262144,
            "max_frame_size": 16384,
            "max_header_list_size": 65536,
        },
        "header_order": [
            ":method",
            ":authority",
            ":scheme",
            ":path",
            "accept",
            "accept-encoding",
            "accept-language",
            "cookie",
        ],
        "window_update": True,
        "dependency_exclusive": False,
    },
}


@dataclass
class HTTP2Profile:
    """Container for HTTP/2 fingerprint profile."""

    name: str
    description: str = ""
    settings: Dict[str, int] = field(default_factory=dict)
    header_order: List[str] = field(default_factory=list)
    window_update: bool = True
    dependency_exclusive: bool = False
    os: str = "windows"
    browser: str = "chrome"

    # HTTP/2 fingerprint hash (calculated)
    _fingerprint_hash: Optional[str] = None

    def __post_init__(self):
        """Calculate fingerprint hash after initialization."""
        self._fingerprint_hash = self._calculate_fingerprint()

    def _calculate_fingerprint(self) -> str:
        """Calculate HTTP/2 fingerprint hash."""
        data = json.dumps({
            "settings": self.settings,
            "header_order": self.header_order,
            "window_update": self.window_update,
            "dependency_exclusive": self.dependency_exclusive,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def format_headers(
        self,
        method: str,
        path: str,
        scheme: str = "https",
        host: Optional[str] = None,
        authority: Optional[str] = None,
        user_agent: Optional[str] = None,
        accept: Optional[str] = None,
        accept_language: Optional[str] = None,
        accept_encoding: Optional[str] = None,
        cookie: Optional[str] = None,
        referer: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Format headers according to this profile's order.

        Args:
            method: HTTP method
            path: Request path
            scheme: URL scheme
            host: Host header
            authority: Authority header (HTTP/2 pseudo-header)
            user_agent: User-Agent header
            accept: Accept header
            accept_language: Accept-Language header
            accept_encoding: Accept-Encoding header
            cookie: Cookie header
            referer: Referer header
            extra_headers: Additional headers

        Returns:
            Ordered headers dict
        """
        headers = {}

        for header_name in self.header_order:
            if header_name == ":method":
                headers[":method"] = method
            elif header_name == ":scheme":
                headers[":scheme"] = scheme
            elif header_name == ":path":
                headers[":path"] = path
            elif header_name == ":authority":
                headers[":authority"] = authority or host or ""
            elif header_name == ":host":
                headers[":host"] = host or ""
            elif header_name == "user-agent":
                if user_agent:
                    headers["user-agent"] = user_agent
            elif header_name == "accept":
                if accept:
                    headers["accept"] = accept
            elif header_name == "accept-language":
                if accept_language:
                    headers["accept-language"] = accept_language
            elif header_name == "accept-encoding":
                if accept_encoding:
                    headers["accept-encoding"] = accept_encoding
            elif header_name == "accept-charset":
                pass  # Optional header
            elif header_name == "cookie":
                if cookie:
                    headers["cookie"] = cookie
            elif header_name == "referer":
                if referer:
                    headers["referer"] = referer
            elif header_name == "upgrade-insecure-requests":
                headers["upgrade-insecure-requests"] = "1"

        # Add extra headers
        if extra_headers:
            headers.update(extra_headers)

        return headers

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "settings": self.settings,
            "header_order": self.header_order,
            "window_update": self.window_update,
            "dependency_exclusive": self.dependency_exclusive,
            "fingerprint_hash": self._fingerprint_hash,
            "os": self.os,
            "browser": self.browser,
        }


class HTTP2FingerprintGenerator:
    """
    Generate and manage HTTP/2 fingerprints for anti-detection.

    This class provides:
    - Pre-built HTTP/2 fingerprint profiles
    - Header ordering matching
    - SETTINGS frame value spoofing
    - curl_cffi integration for HTTP requests
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize HTTP/2 fingerprint generator.

        Args:
            seed: Random seed for reproducibility
        """
        self._seed = seed or random.randint(0, 2**31 - 1)
        self._random = random.Random(self._seed)
        self._profiles: Dict[str, HTTP2Profile] = {}
        self._load_default_profiles()

    def _load_default_profiles(self) -> None:
        """Load default HTTP/2 profiles."""
        for name, data in HTTP2_PROFILES.items():
            # Determine OS and browser
            os_type = "windows"
            browser = "chrome"
            if "mac" in name:
                os_type = "mac"
            elif "android" in name:
                os_type = "android"

            if "chrome" in name or "edge" in name:
                browser = "chrome"
            elif "safari" in name:
                browser = "safari"
            elif "firefox" in name:
                browser = "firefox"

            profile = HTTP2Profile(
                name=name,
                description=data.get("description", ""),
                settings=data.get("settings", {}),
                header_order=data.get("header_order", []),
                window_update=data.get("window_update", True),
                dependency_exclusive=data.get("dependency_exclusive", False),
                os=os_type,
                browser=browser,
            )
            self._profiles[name] = profile

    def get_profile(
        self,
        os: Optional[str] = None,
        browser: Optional[str] = None,
    ) -> HTTP2Profile:
        """
        Get an HTTP/2 profile matching the specified criteria.

        Args:
            os: Target OS (windows, mac, linux, android)
            browser: Target browser (chrome, firefox, safari, edge)

        Returns:
            Matching HTTP2Profile
        """
        if os is None and browser is None:
            return self._random_selection()

        candidates = []
        for name, profile in self._profiles.items():
            if os and profile.os != os:
                continue
            if browser and profile.browser != browser:
                continue
            candidates.append(profile)

        if candidates:
            return self._random.choice(candidates)

        return self._random_selection()

    def _random_selection(self) -> HTTP2Profile:
        """Select a random profile with weighting."""
        weights = {
            "chrome_windows": 5,
            "chrome_mac": 4,
            "firefox_windows": 2,
            "firefox_mac": 2,
            "safari_mac": 3,
            "edge_windows": 2,
            "chrome_android": 2,
        }

        names = list(weights.keys())
        weight_values = list(weights.values())

        total = sum(weight_values)
        probs = [w / total for w in weight_values]

        r = self._random.random()
        cumulative = 0
        for name, prob in zip(names, probs):
            cumulative += prob
            if r <= cumulative:
                return self._profiles[name]

        return self._profiles["chrome_windows"]

    def get_settings_values(self, os: Optional[str] = None, browser: Optional[str] = None) -> Dict[str, int]:
        """
        Get HTTP/2 SETTINGS values for a profile.

        Args:
            os: Target OS
            browser: Target browser

        Returns:
            Dict of SETTINGS name to value
        """
        profile = self.get_profile(os, browser)
        return profile.settings.copy()

    def get_header_order(self, os: Optional[str] = None, browser: Optional[str] = None) -> List[str]:
        """
        Get HTTP/2 header order for a profile.

        Args:
            os: Target OS
            browser: Target browser

        Returns:
            List of header names in order
        """
        profile = self.get_profile(os, browser)
        return profile.header_order.copy()

    @property
    def profiles(self) -> Dict[str, HTTP2Profile]:
        """Get all loaded profiles."""
        return self._profiles.copy()


# =============================================================================
# HTTP/2 HEADER MANIPULATION FOR BROWSER
# =============================================================================

class HTTP2HeaderManipulator:
    """
    Manipulate HTTP/2 headers in browser context to match target profile.

    This class provides JavaScript for browser injection to:
    - Reorder headers to match target profile
    - Add/remove headers to match authentic patterns
    - Match header capitalization
    """

    def __init__(self, profile: Optional[HTTP2Profile] = None):
        """
        Initialize HTTP/2 header manipulator.

        Args:
            profile: Target HTTP/2 profile
        """
        self.profile = profile

    def get_header_order_script(self) -> str:
        """
        Get JavaScript to enforce header order.

        Returns:
            JavaScript code for browser injection
        """
        if not self.profile:
            return ""

        order = self.profile.header_order

        return f"""
(function() {{
    // HTTP/2 Header Order Enforcement
    // Target order: {json.dumps(order)}

    const targetOrder = {json.dumps(order)};

    // Intercept fetch to reorder headers
    const originalFetch = window.fetch;
    window.fetch = async function(url, options = {{}}) {{
        if (options && options.headers) {{
            const headers = new Headers(options.headers);
            const orderedHeaders = new Headers();

            // First add pseudo-headers in order
            targetOrder.forEach(name => {{
                if (name.startsWith(':')) {{
                    const value = headers.get(name);
                    if (value) orderedHeaders.append(name, value);
                }}
            }});

            // Then add regular headers in order
            targetOrder.forEach(name => {{
                if (!name.startsWith(':')) {{
                    const value = headers.get(name);
                    if (value) orderedHeaders.append(name, value);
                }}
            }});

            // Add any remaining headers not in target order
            headers.forEach((value, name) => {{
                if (!targetOrder.includes(name) && !orderedHeaders.has(name)) {{
                    orderedHeaders.append(name, value);
                }}
            }});

            options.headers = orderedHeaders;
        }}
        return originalFetch.call(this, url, options);
    }};

    // Intercept XMLHttpRequest
    const originalXHROpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {{
        this._customHeaders = [];
        this._customHeadersMap = {{}};
        return originalXHROpen.call(this, method, url, async, user, password);
    }};

    const originalXHRSetRequestHeader = XMLHttpRequest.prototype.setRequestHeader;
    XMLHttpRequest.prototype.setRequestHeader = function(name, value) {{
        if (!this._customHeadersMap[name]) {{
            this._customHeaders.push(name);
            this._customHeadersMap[name] = value;
        }}
        return originalXHRSetRequestHeader.call(this, name, value);
    }};

    console.log('[HTTP2 Spoofing] Header order script loaded');
}})();
"""

    def get_stealth_headers_script(self) -> str:
        """
        Get JavaScript to add stealth headers.

        Returns:
            JavaScript code for browser injection
        """
        return """
(function() {
    // Additional HTTP/2 Stealth Headers
    // These headers help match authentic browser patterns

    // Override headers to match Chrome patterns
    Object.defineProperty(navigator, 'platform', {
        get: function() { return 'Win32'; }
    });

    Object.defineProperty(navigator, 'vendor', {
        get: function() { return 'Google Inc.'; }
    });

    console.log('[HTTP2 Spoofing] Stealth headers loaded');
})();
"""


# =============================================================================
# curl_cffi HTTP/2 INTEGRATION
# =============================================================================

class HTTP2TLSClient:
    """
    Combined HTTP/2 and TLS client using curl_cffi.

    This client automatically handles:
    - TLS fingerprint spoofing
    - HTTP/2 settings matching
    - Header ordering
    """

    def __init__(self, default_profile: Optional[str] = None):
        """
        Initialize HTTP/2 TLS client.

        Args:
            default_profile: Default profile name
        """
        self.default_profile = default_profile or "chrome_windows"
        self._http2_gen = HTTP2FingerprintGenerator()
        self._profile = self._http2_gen.get_profile()

    def get_profile(self) -> HTTP2Profile:
        """Get current HTTP/2 profile."""
        return self._profile

    def set_profile(self, os: Optional[str] = None, browser: Optional[str] = None) -> HTTP2Profile:
        """
        Set HTTP/2 profile.

        Args:
            os: Target OS
            browser: Target browser
        """
        self._profile = self._http2_gen.get_profile(os, browser)
        return self._profile

    def get_impersonate_target(self) -> str:
        """
        Get curl_cffi impersonate target.

        Returns:
            curl_cffi impersonate string
        """
        # Map HTTP/2 profile to curl_cffi target
        browser = self._profile.browser
        if self._profile.os == "mac":
            return "safari15_5" if browser == "safari" else "chrome120"
        elif self._profile.os == "android":
            return "android13"
        else:
            return "chrome120" if browser == "chrome" else "firefox120"

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: int = 30,
        **kwargs,
    ) -> Any:
        """
        Make HTTP request with HTTP/2 and TLS spoofing.

        Args:
            method: HTTP method
            url: Target URL
            headers: Request headers
            proxy: Proxy URL
            timeout: Timeout in seconds
            **kwargs: Additional arguments

        Returns:
            Response object
        """
        try:
            from curl_cffi.requests import async_request

            impersonate = self.get_impersonate_target()

            # Reorder headers if provided
            if headers:
                ordered_headers = self._reorder_headers(headers)
            else:
                ordered_headers = None

            response = await async_request(
                method=method,
                url=url,
                headers=ordered_headers,
                impersonate=impersonate,
                proxy=proxy,
                timeout=timeout,
                **kwargs,
            )

            return response

        except ImportError:
            logger.error("curl_cffi not installed. Install with: pip install curl_cffi")
            raise

    def _reorder_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Reorder headers according to profile.

        Args:
            headers: Original headers

        Returns:
            Reordered headers
        """
        target_order = self._profile.header_order
        ordered = {}

        # Add headers in target order
        for name in target_order:
            # Map HTTP/2 pseudo-headers
            mapped_name = name
            if name == ":authority" and "host" in headers:
                mapped_name = "host"
            elif name == ":host" and "host" in headers:
                mapped_name = "host"

            if mapped_name in headers:
                ordered[name] = headers[mapped_name]

        # Add remaining headers
        for name, value in headers.items():
            if name not in ordered.values() and name not in ordered:
                ordered[name] = value

        return ordered

    async def get(self, url: str, **kwargs) -> Any:
        """Make GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> Any:
        """Make POST request."""
        return await self.request("POST", url, **kwargs)


# Global instances
_http2_generator: Optional[HTTP2FingerprintGenerator] = None
_http2_tls_client: Optional[HTTP2TLSClient] = None


def get_http2_generator() -> HTTP2FingerprintGenerator:
    """Get or create global HTTP/2 fingerprint generator."""
    global _http2_generator
    if _http2_generator is None:
        _http2_generator = HTTP2FingerprintGenerator()
    return _http2_generator


def get_http2_tls_client() -> HTTP2TLSClient:
    """Get or create global HTTP/2 TLS client."""
    global _http2_tls_client
    if _http2_tls_client is None:
        _http2_tls_client = HTTP2TLSClient()
    return _http2_tls_client
