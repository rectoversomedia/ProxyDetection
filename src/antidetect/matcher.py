"""Consistency checker for fingerprint coherence.

This module ensures that all fingerprint attributes are consistent
with each other and with the claimed identity.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple

from .fingerprint import FingerprintProfile, COUNTRY_TIMEZONES

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConsistencyIssue:
    """Represents a fingerprint consistency issue."""

    def __init__(
        self,
        severity: str,
        category: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.severity = severity  # 'error', 'warning', 'info'
        self.category = category
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        return f"[{self.severity.upper()}] {self.category}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "details": self.details,
        }


class ConsistencyChecker:
    """
    Check fingerprint consistency across all attributes.

    This ensures that:
    - Timezone matches country
    - User-Agent matches OS/browser
    - Screen resolution matches OS distribution
    - WebGL vendor/renderer is consistent
    - Fonts are appropriate for OS/language
    - Language matches country
    """

    # OS to User-Agent pattern mapping
    UA_OS_PATTERNS = {
        "windows": [
            r"Windows NT \d+\.\d+",
            r"Windows Phone",
            r"Win64",
            r"Win32",
        ],
        "mac": [
            r"Macintosh",
            r"Mac OS X",
            r"Mac_PowerPC",
        ],
        "linux": [
            r"Linux",
            r"X11",
            r"Ubuntu",
            r"Fedora",
            r"Debian",
        ],
    }

    # Browser to User-Agent pattern mapping
    UA_BROWSER_PATTERNS = {
        "chrome": [r"Chrome/\d+"],
        "firefox": [r"Firefox/\d+"],
        "safari": [r"Version/\d+.*Safari"],
        "edge": [r"Edg/\d+"],
    }

    def __init__(self):
        """Initialize consistency checker."""
        self.issues: List[ConsistencyIssue] = []

    def check(self, fingerprint: FingerprintProfile) -> List[ConsistencyIssue]:
        """
        Check a fingerprint for consistency issues.

        Args:
            fingerprint: FingerprintProfile to check

        Returns:
            List of consistency issues found
        """
        self.issues = []

        self._check_timezone_country(fingerprint)
        self._check_user_agent_os(fingerprint)
        self._check_user_agent_browser(fingerprint)
        self._check_screen_resolution(fingerprint)
        self._check_webgl_consistency(fingerprint)
        self._check_language_country(fingerprint)
        self._check_hardware_concurrency(fingerprint)
        self._check_fonts_os(fingerprint)

        return self.issues

    def _check_timezone_country(self, fp: FingerprintProfile) -> None:
        """Check if timezone matches country."""
        if not fp.country:
            self.issues.append(ConsistencyIssue(
                severity="warning",
                category="timezone",
                message="No country specified, cannot verify timezone consistency",
            ))
            return

        expected_timezones = COUNTRY_TIMEZONES.get(fp.country, [])

        if fp.timezone not in expected_timezones:
            self.issues.append(ConsistencyIssue(
                severity="warning",
                category="timezone",
                message=f"Timezone '{fp.timezone}' doesn't match country '{fp.country}'",
                details={
                    "expected_timezones": expected_timezones,
                    "actual_timezone": fp.timezone,
                    "country": fp.country,
                },
            ))

    def _check_user_agent_os(self, fp: FingerprintProfile) -> None:
        """Check if User-Agent matches claimed OS."""
        if not fp.user_agent:
            self.issues.append(ConsistencyIssue(
                severity="warning",
                category="user_agent",
                message="No User-Agent specified",
            ))
            return

        ua = fp.user_agent.lower()
        os = fp.os.lower()

        patterns = self.UA_OS_PATTERNS.get(os, [])

        if not any(re.search(p, ua, re.IGNORECASE) for p in patterns):
            self.issues.append(ConsistencyIssue(
                severity="error",
                category="user_agent",
                message=f"User-Agent doesn't match OS '{fp.os}'",
                details={
                    "user_agent": fp.user_agent,
                    "claimed_os": fp.os,
                },
            ))

    def _check_user_agent_browser(self, fp: FingerprintProfile) -> None:
        """Check if User-Agent matches claimed browser."""
        if not fp.user_agent:
            return

        ua = fp.user_agent.lower()
        browser = fp.browser.lower()

        patterns = self.UA_BROWSER_PATTERNS.get(browser, [])

        if not any(re.search(p, ua, re.IGNORECASE) for p in patterns):
            self.issues.append(ConsistencyIssue(
                severity="error",
                category="user_agent",
                message=f"User-Agent doesn't match browser '{fp.browser}'",
                details={
                    "user_agent": fp.user_agent,
                    "claimed_browser": fp.browser,
                },
            ))

    def _check_screen_resolution(self, fp: FingerprintProfile) -> None:
        """Check if screen resolution is reasonable for OS."""
        width = fp.screen_width
        height = fp.screen_height

        # Common resolutions by OS
        common_resolutions = {
            "windows": [(1920, 1080), (1366, 768), (1536, 864), (1440, 900), (1280, 720)],
            "mac": [(2560, 1600), (1440, 900), (2880, 1800), (1680, 1050), (1920, 1200)],
            "linux": [(1920, 1080), (1366, 768), (1440, 900), (1280, 800), (1024, 768)],
        }

        expected = common_resolutions.get(fp.os, [])

        if (width, height) not in expected:
            # Check if it's a valid but uncommon resolution
            if width < 800 or height < 600:
                self.issues.append(ConsistencyIssue(
                    severity="error",
                    category="screen",
                    message=f"Unusually small screen resolution: {width}x{height}",
                    details={"os": fp.os},
                ))
            elif (width, height) in [(800, 600), (1024, 768)] and fp.os == "windows":
                # This is fine, Windows VMs often use these
                pass
            else:
                self.issues.append(ConsistencyIssue(
                    severity="info",
                    category="screen",
                    message=f"Uncommon screen resolution for {fp.os}: {width}x{height}",
                    details={"common_resolutions": expected},
                ))

    def _check_webgl_consistency(self, fp: FingerprintProfile) -> None:
        """Check if WebGL vendor/renderer is consistent."""
        vendor = fp.webgl_vendor.lower()
        renderer = fp.webgl_renderer.lower()
        os = fp.os.lower()

        # Check for impossible combinations
        if "nvidia" in vendor.lower() and "intel" in renderer.lower():
            self.issues.append(ConsistencyIssue(
                severity="error",
                category="webgl",
                message="Inconsistent WebGL: NVIDIA vendor with Intel renderer",
            ))

        if "amd" in vendor.lower() or "radeon" in vendor.lower():
            if "intel" in renderer.lower():
                self.issues.append(ConsistencyIssue(
                    severity="error",
                    category="webgl",
                    message="Inconsistent WebGL: AMD vendor with Intel renderer",
                ))

        # Check OS-specific patterns
        if os == "mac" or os == "macos":
            if "nvidia" in vendor.lower() and "gtx" in renderer.lower():
                self.issues.append(ConsistencyIssue(
                    severity="error",
                    category="webgl",
                    message="Mac profiles should not use NVIDIA GeForce GPUs",
                ))

        if os == "linux":
            if "intel" in vendor.lower() and "mac" in renderer.lower():
                self.issues.append(ConsistencyIssue(
                    severity="error",
                    category="webgl",
                    message="Linux profiles should not use Mac GPUs",
                ))

    def _check_language_country(self, fp: FingerprintProfile) -> None:
        """Check if language matches country."""
        if not fp.country or not fp.language:
            return

        # Language to country mapping
        lang_countries = {
            "en": ["US", "GB", "CA", "AU", "NZ", "IE", "ZA"],
            "de": ["DE", "AT", "CH"],
            "fr": ["FR", "BE", "CA", "CH"],
            "es": ["ES", "MX", "AR", "CO"],
            "pt": ["BR", "PT"],
            "ja": ["JP"],
            "ko": ["KR"],
            "zh": ["CN", "TW", "HK", "SG"],
            "it": ["IT"],
            "nl": ["NL", "BE"],
            "ru": ["RU"],
            "ar": ["AE", "SA", "EG"],
            "th": ["TH"],
            "vi": ["VN"],
            "id": ["ID"],
            "ms": ["MY"],
            "hi": ["IN"],
            "tl": ["PH"],
        }

        lang_code = fp.language.split("-")[0].lower()
        expected_countries = lang_countries.get(lang_code, [])

        if fp.country not in expected_countries:
            self.issues.append(ConsistencyIssue(
                severity="warning",
                category="language",
                message=f"Language '{fp.language}' may not match country '{fp.country}'",
                details={
                    "language": fp.language,
                    "country": fp.country,
                    "common_countries": expected_countries,
                },
            ))

    def _check_hardware_concurrency(self, fp: FingerprintProfile) -> None:
        """Check if hardware concurrency is reasonable."""
        cores = fp.hardware_concurrency

        # OS-specific reasonable ranges
        ranges = {
            "windows": (1, 128),
            "mac": (2, 128),
            "linux": (1, 256),
        }

        min_cores, max_cores = ranges.get(fp.os, (1, 128))

        if cores < min_cores or cores > max_cores:
            self.issues.append(ConsistencyIssue(
                severity="warning",
                category="hardware",
                message=f"Unusual hardware concurrency: {cores} for {fp.os}",
                details={"range": (min_cores, max_cores)},
            ))

        # Check for unrealistic core counts
        if cores in [0, 1] and fp.os == "windows" and "64" in fp.platform:
            self.issues.append(ConsistencyIssue(
                severity="warning",
                category="hardware",
                message="64-bit Windows with only 1 core is unusual",
            ))

    def _check_fonts_os(self, fp: FingerprintProfile) -> None:
        """Check if fonts are appropriate for OS."""
        fonts = [f.lower() for f in fp.fonts]
        os = fp.os.lower()

        # OS-specific fonts
        os_fonts = {
            "windows": ["segoe", "calibri", "arial", "times new roman", "consolas"],
            "mac": ["helvetica", "san francisco", "lucida", "monaco", "avenir"],
            "linux": ["ubuntu", "dejavu", "liberation", "noto", "freefont"],
        }

        expected_fonts = [f.lower() for f in os_fonts.get(os, [])]

        # Check if at least some expected fonts are present
        if expected_fonts:
            match_count = sum(1 for f in fonts if any(exp in f for exp in expected_fonts))

            if match_count == 0:
                self.issues.append(ConsistencyIssue(
                    severity="warning",
                    category="fonts",
                    message=f"No common {os} fonts found",
                    details={
                        "expected": expected_fonts,
                        "found": fonts[:10],
                    },
                ))

        # Check for impossible fonts
        if os == "linux" and any("segoe" in f for f in fonts):
            self.issues.append(ConsistencyIssue(
                severity="warning",
                category="fonts",
                message="Linux profile should not have Segoe fonts",
            ))

        if os == "mac" and any("segoe" in f for f in fonts):
            self.issues.append(ConsistencyIssue(
                severity="warning",
                category="fonts",
                message="Mac profile should not have Segoe fonts",
            ))

    def generate_report(self, fingerprint: FingerprintProfile) -> str:
        """
        Generate a consistency report for a fingerprint.

        Args:
            fingerprint: FingerprintProfile to report on

        Returns:
            Formatted report string
        """
        self.check(fingerprint)

        if not self.issues:
            return "✓ Fingerprint is consistent"

        lines = ["Fingerprint Consistency Report", "=" * 40]

        # Group by severity
        errors = [i for i in self.issues if i.severity == "error"]
        warnings = [i for i in self.issues if i.severity == "warning"]
        infos = [i for i in self.issues if i.severity == "info"]

        if errors:
            lines.append(f"\n❌ Errors ({len(errors)}):")
            for issue in errors:
                lines.append(f"  • {issue.category}: {issue.message}")

        if warnings:
            lines.append(f"\n⚠️ Warnings ({len(warnings)}):")
            for issue in warnings:
                lines.append(f"  • {issue.category}: {issue.message}")

        if infos:
            lines.append(f"\nℹ️ Info ({len(infos)}):")
            for issue in infos:
                lines.append(f"  • {issue.category}: {issue.message}")

        return "\n".join(lines)
