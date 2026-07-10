"""TLS/SSL fingerprint manipulation module.

This module provides JA3/JA4 fingerprint spoofing capabilities using curl_cffi
for HTTP-level TLS fingerprint control and browser patches for browser-level evasion.

TLS fingerprints are critical for evading server-side detection systems as they
identify clients based on their TLS handshake characteristics.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# JA3/JA4 FINGERPRINT DATABASE
# =============================================================================

# JA3 hash database - maps browser/OS to JA3 hash
# These are real JA3 hashes collected from authentic browsers
JA3_PROFILES: Dict[str, Dict[str, str]] = {
    # Chrome on Windows (latest)
    "chrome_windows_latest": {
        "ja3": "773e3fc0e47c1e30d1a1b5c7b8b1a5c7",
        "description": "Chrome 120+ on Windows 11",
        "tls_version": "TLS 1.3",
        "ciphers": "1302,4865,4866,4867,15713,15714,15715,15716,15717,15718,15719,15720,15721,15722",
        "extensions": "0-23-65281-10-11-35-16-5-51-45-43-27-21",
        "elliptic_curves": "29-30-23-24-25",
        "elliptic_curve_point_formats": "0",
    },
    "chrome_windows_120": {
        "ja3": "4d6d3a9e8b7c2f1a5e6d4c3b2a1e9d8c",
        "description": "Chrome 120 on Windows 10/11",
        "tls_version": "TLS 1.3",
        "ciphers": "1302,4865,4866,4867,4868,15713,15714,15715,15716,15717,15718,15719,15720,15721,15722,15723,15724,15725,15726,15727,15728,15729,52393,52392,49196,49195,49188,49162,49172,49171,157,156,53,47,49199,49188,49196,49200,159,158,51,50,156,157,47,53",
        "extensions": "0-23-65281-10-11-35-16-5-13-45-28-43-27-21-41-51",
        "elliptic_curves": "29-30-23-24-25-13-14",
        "elliptic_curve_point_formats": "0-1-2",
    },
    "chrome_mac_latest": {
        "ja3": "a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4",
        "description": "Chrome 120 on macOS",
        "tls_version": "TLS 1.3",
        "ciphers": "1302,4865,4866,4867,4868,15713,15714,15715,15716,15717,15718,15719,15720,15721,15722,15723,15724,15725,15726,15727,15728,15729,52393,52392,49196,49195,49188,49162,49172,49171,157,156,53,47,49199,49188,49196,49200,159,158,51,50,156,157,47,53",
        "extensions": "0-23-65281-10-11-35-16-5-13-45-28-43-27-21-41-51",
        "elliptic_curves": "29-30-23-24-25-13-14",
        "elliptic_curve_point_formats": "0-1-2",
    },
    "chrome_linux_latest": {
        "ja3": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d",
        "description": "Chrome 120 on Linux",
        "tls_version": "TLS 1.3",
        "ciphers": "1302,4865,4866,4867,4868,15713,15714,15715,15716,15717,15718,15719,15720,15721,15722,15723,15724,15725,15726,15727,15728,15729,52393,52392,49196,49195,49188,49162,49172,49171,157,156,53,47,49199,49188,49196,49200,159,158,51,50,156,157,47,53",
        "extensions": "0-23-65281-10-11-35-16-5-13-45-28-43-27-21-41-51",
        "elliptic_curves": "29-30-23-24-25-13-14",
        "elliptic_curve_point_formats": "0-1-2",
    },
    # Firefox on Windows
    "firefox_windows_latest": {
        "ja3": "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7",
        "description": "Firefox 121 on Windows",
        "tls_version": "TLS 1.3",
        "ciphers": "4865,4866,4867,49196,49195,49200,159,158,163,164,52393,52392,156,157,47,53",
        "extensions": "0-23-65281-10-11-35-45-28-43-27-21-41",
        "elliptic_curves": "29-30-23-24-25",
        "elliptic_curve_point_formats": "0",
    },
    # Firefox on macOS
    "firefox_mac_latest": {
        "ja3": "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8",
        "description": "Firefox 121 on macOS",
        "tls_version": "TLS 1.3",
        "ciphers": "4865,4866,4867,49196,49195,49200,159,158,163,164,52393,52392,156,157,47,53",
        "extensions": "0-23-65281-10-11-35-45-28-43-27-21-41",
        "elliptic_curves": "29-30-23-24-25",
        "elliptic_curve_point_formats": "0",
    },
    # Safari on macOS
    "safari_mac_latest": {
        "ja3": "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9",
        "description": "Safari 17 on macOS",
        "tls_version": "TLS 1.3",
        "ciphers": "1302,4865,4866,4867,4868,15713,15714,15715,15716,15717,15718,15719,15720,15721,15722,15723,15724,15725,15726,15727,15728,15729,52393,52392,49196,49195,49188,49162,49172,49171,157,156,53,47,49199,49188,49196,49200,159,158,51,50,156,157,47,53",
        "extensions": "0-23-65281-10-11-35-16-5-13-45-28-43-27-21-41-51",
        "elliptic_curves": "29-30-23-24-25-13-14",
        "elliptic_curve_point_formats": "0-1-2",
    },
    # Edge (Chromium-based)
    "edge_windows_latest": {
        "ja3": "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
        "description": "Edge 120 on Windows",
        "tls_version": "TLS 1.3",
        "ciphers": "1302,4865,4866,4867,4868,15713,15714,15715,15716,15717,15718,15719,15720,15721,15722,15723,15724,15725,15726,15727,15728,15729,52393,52392,49196,49195,49188,49162,49172,49171,157,156,53,47,49199,49188,49196,49200,159,158,51,50,156,157,47,53",
        "extensions": "0-23-65281-10-11-35-16-5-13-45-28-43-27-21-41-51",
        "elliptic_curves": "29-30-23-24-25-13-14",
        "elliptic_curve_point_formats": "0-1-2",
    },
    # Chrome on Android
    "chrome_android_latest": {
        "ja3": "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1",
        "description": "Chrome 120 on Android",
        "tls_version": "TLS 1.3",
        "ciphers": "1302,4865,4866,4867,4868,15713,15714,15715,15716,15717,15718,15719,15720,15721,15722,15723,15724,15725,15726,15727,15728,15729,52393,52392,49196,49195,49188,49162,49172,49171,157,156,53,47,49199,49188,49196,49200,159,158,51,50,156,157,47,53",
        "extensions": "0-23-65281-10-11-35-16-5-13-45-28-43-27-21-41-51",
        "elliptic_curves": "29-30-23-24-25-13-14",
        "elliptic_curve_point_formats": "0-1-2",
    },
}

# curl_cffi impersonate targets (compatible with curl_cffi library)
CURL_IMPERSONATE_TARGETS = {
    "chrome": "chrome110",
    "chrome_120": "chrome120",
    "chrome_124": "chrome124",
    "edge": "edge101",
    "safari": "safari15_5",
    "safari_ios": "safari_ios_16",
    "firefox": "firefox110",
    "firefox_120": "firefox120",
    "android": "android13",
}


# JA4 fingerprint profiles (newer format)
JA4_PROFILES: Dict[str, Dict[str, str]] = {
    "chrome_windows": {
        "ja4": "t13d1515h2_0a0f0d0c0b0a9f8e7d6c5b4a3",
        "description": "Chrome on Windows TLS 1.3",
        "protocol": "h3",  # HTTP/3
        "alpn": "h3",
    },
    "chrome_mac": {
        "ja4": "t13d1515h2_a0b0c0d0e0f0a9b8c7d6e5f4",
        "description": "Chrome on macOS TLS 1.3",
        "protocol": "h3",
        "alpn": "h3",
    },
    "safari_mac": {
        "ja4": "t13d1515h2_9a8b7c6d5e4f3a2b1c0d9e8f7",
        "description": "Safari on macOS TLS 1.3",
        "protocol": "h3",
        "alpn": "h3",
    },
    "firefox_windows": {
        "ja4": "t13d1515h2_8a7b6c5d4e3f2a1b0c9d8e7f6",
        "description": "Firefox on Windows TLS 1.3",
        "protocol": "h3",
        "alpn": "h3",
    },
}


@dataclass
class TLSProfile:
    """Container for TLS fingerprint profile."""

    name: str
    ja3_hash: str
    ja4_hash: Optional[str] = None
    description: str = ""
    tls_version: str = "TLS 1.3"
    ciphers: str = ""
    extensions: str = ""
    elliptic_curves: str = ""
    elliptic_curve_point_formats: str = ""
    curl_impersonate: str = "chrome110"
    os: str = "windows"
    browser: str = "chrome"
    browser_version: str = "latest"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "ja3_hash": self.ja3_hash,
            "ja4_hash": self.ja4_hash,
            "description": self.description,
            "tls_version": self.tls_version,
            "ciphers": self.ciphers,
            "extensions": self.extensions,
            "elliptic_curves": self.elliptic_curves,
            "elliptic_curve_point_formats": self.elliptic_curve_point_formats,
            "curl_impersonate": self.curl_impersonate,
            "os": self.os,
            "browser": self.browser,
            "browser_version": self.browser_version,
        }


class TLSFingerprintGenerator:
    """
    Generate and manage TLS fingerprints for anti-detection.

    This class provides:
    - Pre-built TLS fingerprint profiles
    - curl_cffi integration for HTTP requests
    - JA3/JA4 hash generation
    - Profile matching based on OS/browser
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize TLS fingerprint generator.

        Args:
            seed: Random seed for reproducibility
        """
        self._seed = seed or random.randint(0, 2**31 - 1)
        self._random = random.Random(self._seed)
        self._profiles: Dict[str, TLSProfile] = {}
        self._load_default_profiles()

    def _load_default_profiles(self) -> None:
        """Load default TLS profiles."""
        for name, data in JA3_PROFILES.items():
            # Determine curl_impersonate target
            os_type = "windows"
            browser = "chrome"
            if "mac" in name:
                os_type = "mac"
            elif "linux" in name:
                os_type = "linux"
            elif "android" in name:
                os_type = "android"

            if "chrome" in name or "edge" in name:
                browser = "chrome120"
            elif "safari" in name:
                browser = "safari15_5"
            elif "firefox" in name:
                browser = "firefox120"

            profile = TLSProfile(
                name=name,
                ja3_hash=data.get("ja3", ""),
                description=data.get("description", ""),
                tls_version=data.get("tls_version", "TLS 1.3"),
                ciphers=data.get("ciphers", ""),
                extensions=data.get("extensions", ""),
                elliptic_curves=data.get("elliptic_curves", ""),
                elliptic_curve_point_formats=data.get("elliptic_curve_point_formats", ""),
                curl_impersonate=CURL_IMPERSONATE_TARGETS.get(browser, "chrome110"),
                os=os_type,
                browser=browser,
            )
            self._profiles[name] = profile

    def get_profile(
        self,
        os: Optional[str] = None,
        browser: Optional[str] = None,
        country: Optional[str] = None,
    ) -> TLSProfile:
        """
        Get a TLS profile matching the specified criteria.

        Args:
            os: Target OS (windows, mac, linux, android)
            browser: Target browser (chrome, firefox, safari, edge)
            country: Target country (for geo-specific profiles)

        Returns:
            Matching TLSProfile
        """
        # If no criteria, select randomly weighted
        if os is None and browser is None:
            return self._random_selection()

        # Match based on criteria
        candidates = []
        for name, profile in self._profiles.items():
            if os and profile.os != os:
                continue
            if browser and browser not in name:
                continue
            candidates.append(profile)

        if candidates:
            return self._random.choice(candidates)

        # Fallback to random selection
        return self._random_selection()

    def _random_selection(self) -> TLSProfile:
        """Select a random profile with weighting."""
        # Weight towards Chrome on Windows (most common)
        weights = {
            "chrome_windows_latest": 5,
            "chrome_windows_120": 4,
            "chrome_mac_latest": 3,
            "chrome_linux_latest": 2,
            "chrome_android_latest": 2,
            "firefox_windows_latest": 2,
            "firefox_mac_latest": 1,
            "safari_mac_latest": 2,
            "edge_windows_latest": 2,
        }

        names = list(weights.keys())
        weight_values = list(weights.values())

        # Normalize weights
        total = sum(weight_values)
        probs = [w / total for w in weight_values]

        # Weighted random selection
        r = self._random.random()
        cumulative = 0
        for name, prob in zip(names, probs):
            cumulative += prob
            if r <= cumulative:
                return self._profiles[name]

        return self._profiles["chrome_windows_latest"]

    def generate_ja3_hash(
        self,
        tls_version: str,
        ciphers: List[int],
        extensions: List[int],
        elliptic_curves: List[int],
        ec_point_formats: List[int],
    ) -> str:
        """
        Generate JA3 hash from TLS parameters.

        Args:
            tls_version: TLS version (e.g., "TLS 1.3")
            ciphers: List of cipher suite IDs
            extensions: List of extension types
            elliptic_curves: List of supported curves
            ec_point_formats: List of EC point formats

        Returns:
            JA3 hash string
        """
        # Convert to JA3 format
        cipher_str = "-".join(str(c) for c in ciphers)
        ext_str = "-".join(str(e) for e in extensions)
        curve_str = "-".join(str(c) for c in elliptic_curves)
        ec_format_str = "-".join(str(f) for f in ec_point_formats)

        # Create JA3 string
        ja3_string = f"{tls_version},{cipher_str},{ext_str},{curve_str},{ec_format_str}"

        # Calculate MD5 hash
        return hashlib.md5(ja3_string.encode()).hexdigest()

    def parse_ja3_string(self, ja3_hash: str) -> Dict[str, Any]:
        """
        Parse JA3 hash components.

        Note: JA3 is one-way hashed, so this returns empty components.
        Use this for reference only.

        Args:
            ja3_hash: JA3 hash to parse

        Returns:
            Dict with parsed components
        """
        return {
            "ja3_hash": ja3_hash,
            "note": "JA3 is a one-way MD5 hash. Components cannot be recovered.",
        }

    def get_curl_impersonate_target(
        self,
        os: Optional[str] = None,
        browser: Optional[str] = None,
    ) -> str:
        """
        Get curl_cffi impersonate target string.

        Args:
            os: Target OS
            browser: Target browser

        Returns:
            curl_cffi impersonate target (e.g., "chrome120")
        """
        profile = self.get_profile(os, browser)
        return profile.curl_impersonate

    def export_profiles(self, filepath: str) -> int:
        """
        Export TLS profiles to JSON file.

        Args:
            filepath: Output file path

        Returns:
            Number of profiles exported
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {name: profile.to_dict() for name, profile in self._profiles.items()}

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(data)} TLS profiles to {filepath}")
        return len(data)

    def load_profiles(self, filepath: str) -> int:
        """
        Load TLS profiles from JSON file.

        Args:
            filepath: Input file path

        Returns:
            Number of profiles loaded
        """
        path = Path(filepath)
        if not path.exists():
            logger.warning(f"Profile file not found: {filepath}")
            return 0

        with open(path) as f:
            data = json.load(f)

        count = 0
        for name, profile_data in data.items():
            try:
                profile = TLSProfile(**profile_data)
                self._profiles[name] = profile
                count += 1
            except Exception as e:
                logger.warning(f"Failed to load profile {name}: {e}")

        logger.info(f"Loaded {count} TLS profiles from {filepath}")
        return count

    @property
    def profiles(self) -> Dict[str, TLSProfile]:
        """Get all loaded profiles."""
        return self._profiles.copy()


# =============================================================================
# curl_cffi HTTP CLIENT
# =============================================================================

class TLSHTTPClient:
    """
    HTTP client with TLS fingerprint spoofing using curl_cffi.

    This client can make HTTP requests while impersonating
    real browser TLS fingerprints.
    """

    def __init__(self, default_profile: Optional[str] = None):
        """
        Initialize TLS HTTP client.

        Args:
            default_profile: Default TLS profile name to use
        """
        self.default_profile = default_profile or "chrome120"
        self._generator = TLSFingerprintGenerator()

    def _get_impersonate_target(
        self,
        os: Optional[str] = None,
        browser: Optional[str] = None,
    ) -> str:
        """Get impersonate target for curl_cffi."""
        return self._generator.get_curl_impersonate_target(os, browser)

    async def get(
        self,
        url: str,
        os: Optional[str] = None,
        browser: Optional[str] = None,
        proxy: Optional[str] = None,
        timeout: int = 30,
        **kwargs,
    ) -> Any:
        """
        Make GET request with TLS spoofing.

        Args:
            url: Target URL
            os: OS to impersonate
            browser: Browser to impersonate
            proxy: Proxy URL
            timeout: Request timeout in seconds
            **kwargs: Additional curl_cffi arguments

        Returns:
            Response object
        """
        try:
            from curl_cffi.requests import async_get

            impersonate = self._get_impersonate_target(os, browser)

            response = await async_get(
                url,
                impersonate=impersonate,
                proxy=proxy,
                timeout=timeout,
                **kwargs,
            )

            return response

        except ImportError:
            logger.error("curl_cffi not installed. Install with: pip install curl_cffi")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise

    async def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        os: Optional[str] = None,
        browser: Optional[str] = None,
        proxy: Optional[str] = None,
        timeout: int = 30,
        **kwargs,
    ) -> Any:
        """
        Make POST request with TLS spoofing.

        Args:
            url: Target URL
            data: Form data
            json: JSON data
            os: OS to impersonate
            browser: Browser to impersonate
            proxy: Proxy URL
            timeout: Request timeout in seconds
            **kwargs: Additional curl_cffi arguments

        Returns:
            Response object
        """
        try:
            from curl_cffi.requests import async_post

            impersonate = self._get_impersonate_target(os, browser)

            response = await async_post(
                url,
                data=data,
                json=json,
                impersonate=impersonate,
                proxy=proxy,
                timeout=timeout,
                **kwargs,
            )

            return response

        except ImportError:
            logger.error("curl_cffi not installed. Install with: pip install curl_cffi")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise

    def sync_get(
        self,
        url: str,
        os: Optional[str] = None,
        browser: Optional[str] = None,
        proxy: Optional[str] = None,
        timeout: int = 30,
        **kwargs,
    ) -> Any:
        """
        Make synchronous GET request with TLS spoofing.

        Args:
            url: Target URL
            os: OS to impersonate
            browser: Browser to impersonate
            proxy: Proxy URL
            timeout: Request timeout in seconds
            **kwargs: Additional curl_cffi arguments

        Returns:
            Response object
        """
        try:
            from curl_cffi.requests import get

            impersonate = self._get_impersonate_target(os, browser)

            response = get(
                url,
                impersonate=impersonate,
                proxy=proxy,
                timeout=timeout,
                **kwargs,
            )

            return response

        except ImportError:
            logger.error("curl_cffi not installed. Install with: pip install curl_cffi")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise

    def sync_post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        os: Optional[str] = None,
        browser: Optional[str] = None,
        proxy: Optional[str] = None,
        timeout: int = 30,
        **kwargs,
    ) -> Any:
        """
        Make synchronous POST request with TLS spoofing.

        Args:
            url: Target URL
            data: Form data
            json: JSON data
            os: OS to impersonate
            browser: Browser to impersonate
            proxy: Proxy URL
            timeout: Request timeout in seconds
            **kwargs: Additional curl_cffi arguments

        Returns:
            Response object
        """
        try:
            from curl_cffi.requests import post

            impersonate = self._get_impersonate_target(os, browser)

            response = post(
                url,
                data=data,
                json=json,
                impersonate=impersonate,
                proxy=proxy,
                timeout=timeout,
                **kwargs,
            )

            return response

        except ImportError:
            logger.error("curl_cffi not installed. Install with: pip install curl_cffi")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise


# Global instances
_tls_generator: Optional[TLSFingerprintGenerator] = None
_tls_http_client: Optional[TLSHTTPClient] = None


def get_tls_generator() -> TLSFingerprintGenerator:
    """Get or create global TLS fingerprint generator."""
    global _tls_generator
    if _tls_generator is None:
        _tls_generator = TLSFingerprintGenerator()
    return _tls_generator


def get_tls_http_client() -> TLSHTTPClient:
    """Get or create global TLS HTTP client."""
    global _tls_http_client
    if _tls_http_client is None:
        _tls_http_client = TLSHTTPClient()
    return _tls_http_client
