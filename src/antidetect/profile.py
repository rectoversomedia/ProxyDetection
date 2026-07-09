"""Browser profile management."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger
from ..utils.config import get_settings

from .fingerprint import FingerprintProfile

logger = get_logger(__name__)


@dataclass
class BrowserProfile:
    """Browser profile configuration."""

    name: str
    os: str = "windows"
    browser: str = "chrome"
    headless: bool = False

    # Fingerprint settings
    use_stealth: bool = True
    randomize_canvas: bool = True
    randomize_webgl: bool = True
    randomize_audio: bool = True
    mask_webdriver: bool = True
    mask_plugins: bool = True

    # Window settings
    window_width: int = 1920
    window_height: int = 1080
    window_position_x: int = 0
    window_position_y: int = 0

    # Locale settings
    timezone: str = "America/New_York"
    locale: str = "en-US"
    languages: List[str] = field(default_factory=lambda: ["en-US", "en"])

    # Network settings
    user_agent: str = ""
    platform: str = "Win32"
    hardware_concurrency: int = 4
    device_memory: int = 8

    # Proxy settings
    proxy_enabled: bool = False
    proxy_host: str = ""
    proxy_port: int = 0
    proxy_username: str = ""
    proxy_password: str = ""

    # Extensions
    enabled_extensions: List[str] = field(default_factory=list)

    # Metadata
    created_at: str = ""
    modified_at: str = ""
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "os": self.os,
            "browser": self.browser,
            "headless": self.headless,
            "use_stealth": self.use_stealth,
            "randomize_canvas": self.randomize_canvas,
            "randomize_webgl": self.randomize_webgl,
            "randomize_audio": self.randomize_audio,
            "mask_webdriver": self.mask_webdriver,
            "mask_plugins": self.mask_plugins,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "window_position_x": self.window_position_x,
            "window_position_y": self.window_position_y,
            "timezone": self.timezone,
            "locale": self.locale,
            "languages": self.languages,
            "user_agent": self.user_agent,
            "platform": self.platform,
            "hardware_concurrency": self.hardware_concurrency,
            "device_memory": self.device_memory,
            "proxy_enabled": self.proxy_enabled,
            "proxy_host": self.proxy_host,
            "proxy_port": self.proxy_port,
            "proxy_username": self.proxy_username,
            "proxy_password": self.proxy_password,
            "enabled_extensions": self.enabled_extensions,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BrowserProfile:
        """Create from dictionary."""
        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> BrowserProfile:
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def to_file(self, path: Path) -> None:
        """Save profile to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_json())
        logger.info(f"Profile saved to {path}")

    @classmethod
    def from_file(cls, path: Path) -> BrowserProfile:
        """Load profile from file."""
        with open(path) as f:
            return cls.from_json(f.read())


class ProfileManager:
    """Manage browser profiles."""

    def __init__(self, profile_dir: Optional[str] = None):
        """
        Initialize profile manager.

        Args:
            profile_dir: Directory containing profile files
        """
        if profile_dir is None:
            settings = get_settings()
            profile_dir = settings.profile_dir

        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(parents=True, exist_ok=True)

        # Initialize default profiles
        self._initialize_default_profiles()

    def _initialize_default_profiles(self) -> None:
        """Create default profiles if they don't exist."""
        defaults = [
            self._create_windows_chrome_profile(),
            self._create_mac_safari_profile(),
            self._create_linux_firefox_profile(),
            self._create_windows_chrome_mobile_profile(),
        ]

        for profile in defaults:
            path = self.profile_dir / f"{profile.name}.json"
            if not path.exists():
                profile.to_file(path)

    def _create_windows_chrome_profile(self) -> BrowserProfile:
        """Create Windows Chrome profile."""
        return BrowserProfile(
            name="windows_chrome",
            os="windows",
            browser="chrome",
            headless=False,
            use_stealth=True,
            randomize_canvas=True,
            randomize_webgl=True,
            randomize_audio=True,
            mask_webdriver=True,
            window_width=1920,
            window_height=1080,
            timezone="America/New_York",
            locale="en-US",
            languages=["en-US", "en"],
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            platform="Win32",
            hardware_concurrency=8,
            device_memory=16,
        )

    def _create_mac_safari_profile(self) -> BrowserProfile:
        """Create macOS Safari profile."""
        return BrowserProfile(
            name="mac_safari",
            os="mac",
            browser="safari",
            headless=False,
            use_stealth=True,
            randomize_canvas=True,
            randomize_webgl=True,
            randomize_audio=False,  # Safari has different audio handling
            mask_webdriver=True,
            window_width=2560,
            window_height=1600,
            timezone="America/Los_Angeles",
            locale="en-US",
            languages=["en-US", "en"],
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.1 Safari/605.1.15"
            ),
            platform="MacIntel",
            hardware_concurrency=8,
            device_memory=16,
        )

    def _create_linux_firefox_profile(self) -> BrowserProfile:
        """Create Linux Firefox profile."""
        return BrowserProfile(
            name="linux_firefox",
            os="linux",
            browser="firefox",
            headless=False,
            use_stealth=True,
            randomize_canvas=True,
            randomize_webgl=True,
            randomize_audio=True,
            mask_webdriver=True,
            window_width=1920,
            window_height=1080,
            timezone="Europe/Berlin",
            locale="de-DE",
            languages=["de-DE", "de", "en-US", "en"],
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) "
                "Gecko/20100101 Firefox/120.0"
            ),
            platform="X11; Linux x86_64",
            hardware_concurrency=4,
            device_memory=8,
        )

    def _create_windows_chrome_mobile_profile(self) -> BrowserProfile:
        """Create Windows Chrome mobile emulation profile."""
        return BrowserProfile(
            name="windows_chrome_mobile",
            os="windows",
            browser="chrome",
            headless=False,
            use_stealth=True,
            randomize_canvas=True,
            randomize_webgl=True,
            randomize_audio=True,
            mask_webdriver=True,
            window_width=390,  # iPhone 14 Pro width
            window_height=844,  # iPhone 14 Pro height
            timezone="America/New_York",
            locale="en-US",
            languages=["en-US", "en"],
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.1 Mobile/15E148 Safari/604.1"
            ),
            platform="iPhone",
            hardware_concurrency=6,
            device_memory=4,
        )

    def list_profiles(self) -> List[str]:
        """List available profile names."""
        profiles = []
        for path in self.profile_dir.glob("*.json"):
            profiles.append(path.stem)
        return sorted(profiles)

    def get_profile(self, name: str) -> Optional[BrowserProfile]:
        """Get a profile by name."""
        path = self.profile_dir / f"{name}.json"
        if path.exists():
            return BrowserProfile.from_file(path)
        return None

    def save_profile(self, profile: BrowserProfile) -> None:
        """Save a profile."""
        path = self.profile_dir / f"{profile.name}.json"
        profile.to_file(path)

    def delete_profile(self, name: str) -> bool:
        """Delete a profile."""
        path = self.profile_dir / f"{name}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def create_profile(
        self,
        name: str,
        os: str = "windows",
        browser: str = "chrome",
        **kwargs,
    ) -> BrowserProfile:
        """Create a new profile."""
        profile = BrowserProfile(name=name, os=os, browser=browser, **kwargs)
        self.save_profile(profile)
        return profile

    def generate_from_fingerprint(
        self,
        name: str,
        fingerprint: FingerprintProfile,
    ) -> BrowserProfile:
        """Create a profile from a fingerprint."""
        profile = BrowserProfile(
            name=name,
            os=fingerprint.os,
            browser=fingerprint.browser,
            user_agent=fingerprint.user_agent,
            platform=fingerprint.platform,
            timezone=fingerprint.timezone,
            locale=fingerprint.language,
            languages=fingerprint.languages,
            window_width=fingerprint.screen_width,
            window_height=fingerprint.screen_height,
            hardware_concurrency=fingerprint.hardware_concurrency,
            device_memory=fingerprint.device_memory,
        )
        self.save_profile(profile)
        return profile
