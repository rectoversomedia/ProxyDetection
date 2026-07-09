"""Browser modules for ProxyDetection."""

from .base import BaseBrowser, BrowserConfig
from .camoufox import CamoufoxBrowser
from .launcher import BrowserLauncher, get_browser_launcher

__all__ = [
    "BaseBrowser",
    "BrowserConfig",
    "CamoufoxBrowser",
    "BrowserLauncher",
    "get_browser_launcher",
]
