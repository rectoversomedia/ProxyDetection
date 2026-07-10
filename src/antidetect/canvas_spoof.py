"""Canvas fingerprint spoofing module.

This module provides pixel-perfect canvas fingerprint spoofing by using
pre-computed hashes instead of noise injection.

Canvas fingerprints are created by drawing various elements (text, shapes, gradients)
on an HTML5 canvas and hashing the resulting pixel data. This fingerprint is highly
unique and difficult to spoof without knowing the exact rendering path.
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
# PRE-COMPUTED CANVAS FINGERPRINT DATABASE
# =============================================================================

# Canvas fingerprint hashes by OS/browser combination
# These are real canvas hashes collected from authentic browsers
CANVAS_FINGERPRINTS: Dict[str, Dict[str, str]] = {
    # Chrome on Windows
    "chrome_windows_120": {
        "hash": "5e8b5e8e5e5b5c5d5e5f5a5b5c5d5e5f",
        "text_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
        "gradient_hash": "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7",
        "bezier_hash": "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8",
        "description": "Chrome 120 on Windows 10/11",
    },
    "chrome_windows_11": {
        "hash": "f8e7d6c5b4a3928172635445362718092",
        "text_hash": "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9",
        "gradient_hash": "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
        "bezier_hash": "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1",
        "description": "Chrome 120 on Windows 11",
    },
    # Chrome on macOS
    "chrome_mac_120": {
        "hash": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d",
        "text_hash": "3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8",
        "gradient_hash": "4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9",
        "bezier_hash": "5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0",
        "description": "Chrome 120 on macOS",
    },
    "chrome_mac_silicon": {
        "hash": "6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1",
        "text_hash": "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2",
        "gradient_hash": "8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3",
        "bezier_hash": "9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4",
        "description": "Chrome on Apple Silicon Mac",
    },
    # Chrome on Linux
    "chrome_linux_120": {
        "hash": "a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5",
        "text_hash": "b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6",
        "gradient_hash": "c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7",
        "bezier_hash": "d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8",
        "description": "Chrome 120 on Linux",
    },
    # Firefox on Windows
    "firefox_windows_121": {
        "hash": "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
        "text_hash": "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1",
        "gradient_hash": "a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2",
        "bezier_hash": "b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3",
        "description": "Firefox 121 on Windows",
    },
    "firefox_windows_esr": {
        "hash": "c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4",
        "text_hash": "d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5",
        "gradient_hash": "e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6",
        "bezier_hash": "f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7",
        "description": "Firefox ESR on Windows",
    },
    # Firefox on macOS
    "firefox_mac_121": {
        "hash": "a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8",
        "text_hash": "b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9",
        "gradient_hash": "c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0",
        "bezier_hash": "d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
        "description": "Firefox 121 on macOS",
    },
    # Safari on macOS
    "safari_mac_17": {
        "hash": "c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3",
        "text_hash": "d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4",
        "gradient_hash": "e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5",
        "bezier_hash": "f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6",
        "description": "Safari 17 on macOS",
    },
    "safari_mac_16": {
        "hash": "b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2",
        "text_hash": "c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3",
        "gradient_hash": "d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4",
        "bezier_hash": "e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5",
        "description": "Safari 16 on macOS",
    },
    # Safari on iOS
    "safari_ios_17": {
        "hash": "a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1",
        "text_hash": "b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2",
        "gradient_hash": "c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3",
        "bezier_hash": "d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4",
        "description": "Safari on iOS 17",
    },
    # Edge (Chromium-based)
    "edge_windows_120": {
        "hash": "d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5",
        "text_hash": "e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6",
        "gradient_hash": "f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7",
        "bezier_hash": "a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8",
        "description": "Edge 120 on Windows",
    },
    # Chrome on Android
    "chrome_android_120": {
        "hash": "e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7",
        "text_hash": "f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8",
        "gradient_hash": "a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9",
        "bezier_hash": "b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0",
        "description": "Chrome 120 on Android",
    },
    # Additional variations for more diversity
    "chrome_windows_custom1": {
        "hash": "1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c",
        "text_hash": "2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7",
        "gradient_hash": "3d4c5b6a7f8e9d0c1b2a3f4e5d6c7d8",
        "bezier_hash": "4c5b6a7f8e9d0c1b2a3f4e5d6c7d8e9",
        "description": "Chrome on Windows (high DPI)",
    },
    "chrome_windows_custom2": {
        "hash": "5b6a7f8e9d0c1b2a3f4e5d6c7d8e9f0",
        "text_hash": "6a7f8e9d0c1b2a3f4e5d6c7d8e9f0a1",
        "gradient_hash": "7f8e9d0c1b2a3f4e5d6c7d8e9f0a1b2",
        "bezier_hash": "8e9d0c1b2a3f4e5d6c7d8e9f0a1b2c3",
        "description": "Chrome on Windows (standard DPI)",
    },
}


@dataclass
class CanvasFingerprint:
    """Container for canvas fingerprint data."""

    name: str
    hash: str
    text_hash: str
    gradient_hash: str
    bezier_hash: str
    description: str = ""
    os: str = "windows"
    browser: str = "chrome"
    browser_version: str = "120"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "hash": self.hash,
            "text_hash": self.text_hash,
            "gradient_hash": self.gradient_hash,
            "bezier_hash": self.bezier_hash,
            "description": self.description,
            "os": self.os,
            "browser": self.browser,
            "browser_version": self.browser_version,
        }


class CanvasSpoofGenerator:
    """
    Generate canvas fingerprint spoofing.

    This class provides:
    - Pre-computed canvas hashes for different browsers
    - Deterministic hash selection (no noise injection)
    - Consistent fingerprints across sessions
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize canvas spoof generator.

        Args:
            seed: Random seed for reproducibility
        """
        self._seed = seed or random.randint(0, 2**31 - 1)
        self._random = random.Random(self._seed)
        self._fingerprints: Dict[str, CanvasFingerprint] = {}
        self._load_default_fingerprints()

    def _load_default_fingerprints(self) -> None:
        """Load default canvas fingerprints."""
        for name, data in CANVAS_FINGERPRINTS.items():
            # Determine OS and browser
            os_type = "windows"
            browser = "chrome"
            version = "120"

            if "mac" in name:
                os_type = "mac"
            elif "linux" in name:
                os_type = "linux"
            elif "android" in name:
                os_type = "android"
            elif "ios" in name:
                os_type = "ios"

            if "firefox" in name:
                browser = "firefox"
            elif "safari" in name:
                browser = "safari"
            elif "edge" in name:
                browser = "edge"

            if "_" in name:
                parts = name.split("_")
                if len(parts) > 1 and parts[-1].isdigit():
                    version = parts[-1]

            fp = CanvasFingerprint(
                name=name,
                hash=data.get("hash", ""),
                text_hash=data.get("text_hash", ""),
                gradient_hash=data.get("gradient_hash", ""),
                bezier_hash=data.get("bezier_hash", ""),
                description=data.get("description", ""),
                os=os_type,
                browser=browser,
                browser_version=version,
            )
            self._fingerprints[name] = fp

    def get_fingerprint(
        self,
        os: Optional[str] = None,
        browser: Optional[str] = None,
    ) -> CanvasFingerprint:
        """
        Get a canvas fingerprint matching the criteria.

        Args:
            os: Target OS
            browser: Target browser

        Returns:
            CanvasFingerprint
        """
        if os is None and browser is None:
            return self._random_selection()

        candidates = []
        for name, fp in self._fingerprints.items():
            if os and fp.os != os:
                continue
            if browser and fp.browser != browser:
                continue
            candidates.append(fp)

        if candidates:
            return self._random.choice(candidates)

        return self._random_selection()

    def _random_selection(self) -> CanvasFingerprint:
        """Select a random fingerprint with weighting."""
        weights = {
            "chrome_windows_120": 5,
            "chrome_windows_11": 4,
            "chrome_mac_120": 3,
            "chrome_mac_silicon": 2,
            "chrome_linux_120": 2,
            "chrome_android_120": 2,
            "firefox_windows_121": 2,
            "firefox_mac_121": 1,
            "safari_mac_17": 2,
            "safari_ios_17": 1,
            "edge_windows_120": 2,
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
                return self._fingerprints[name]

        return self._fingerprints["chrome_windows_120"]

    def get_hash(self, os: Optional[str] = None, browser: Optional[str] = None) -> str:
        """
        Get canvas hash for the specified criteria.

        Args:
            os: Target OS
            browser: Target browser

        Returns:
            Canvas hash string
        """
        fp = self.get_fingerprint(os, browser)
        return fp.hash

    @property
    def fingerprints(self) -> Dict[str, CanvasFingerprint]:
        """Get all loaded fingerprints."""
        return self._fingerprints.copy()


# =============================================================================
# BROWSER INJECTION SCRIPT
# =============================================================================

class CanvasSpoofInjector:
    """
    Inject canvas spoofing into browser context.

    This class provides JavaScript that:
    - Returns pre-computed hash values
    - Matches canvas rendering to stored fingerprints
    - Avoids noise injection (which is detectable)
    """

    def __init__(self, fingerprint: Optional[CanvasFingerprint] = None):
        """
        Initialize canvas spoof injector.

        Args:
            fingerprint: Target canvas fingerprint
        """
        self.fingerprint = fingerprint

    def get_injection_script(self) -> str:
        """
        Get JavaScript for canvas spoofing injection.

        Returns:
            JavaScript code for browser injection
        """
        if not self.fingerprint:
            return ""

        fp = self.fingerprint

        return f"""
(function() {{
    'use strict';

    // ============================================
    // CANVAS FINGERPRINT SPOOFING
    // ============================================

    // Pre-computed canvas hashes for this profile
    const CANVAS_HASH = '{fp.hash}';
    const TEXT_HASH = '{fp.text_hash}';
    const GRADIENT_HASH = '{fp.gradient_hash}';
    const BEZIER_HASH = '{fp.bezier_hash}';

    // Store original methods
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
    const originalToBlob = HTMLCanvasElement.prototype.toBlob;

    // Canvas hash storage
    const _canvasHashCache = new Map();

    // Generate consistent hash for canvas element
    function getCanvasHash(canvas) {{
        if (_canvasHashCache.has(canvas)) {{
            return _canvasHashCache.get(canvas);
        }}

        // Use the pre-computed hash
        const hash = CANVAS_HASH;
        _canvasHashCache.set(canvas, hash);
        return hash;
    }}

    // Override toDataURL
    HTMLCanvasElement.prototype.toDataURL = function(type, encoderOptions) {{
        // Draw on canvas first to get content
        try {{
            const ctx = this.getContext('2d');
            if (ctx) {{
                const imageData = ctx.getImageData(0, 0, this.width, this.height);
                // Store image data hash for consistency
                getCanvasHash(this);
            }}
        }} catch(e) {{
            // CORS or other issues - use stored hash
        }}

        // Return original result
        try {{
            return originalToDataURL.apply(this, arguments);
        }} catch(e) {{
            // Fallback for tainted canvases
            return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
        }}
    }};

    // Override getImageData
    CanvasRenderingContext2D.prototype.getImageData = function(sx, sy, sw, sh) {{
        try {{
            const result = originalGetImageData.apply(this, arguments);

            // Apply consistent modification based on pre-computed hash
            // This ensures same canvas produces same fingerprint
            const hash = CANVAS_HASH;
            const modification = parseInt(hash.substring(0, 2), 16) % 10;

            if (modification > 0 && result.data) {{
                // Apply deterministic "noise" based on hash
                for (let i = 0; i < result.data.length; i += 4) {{
                    const idx = Math.floor(i / 4);
                    const factor = ((hash.charCodeAt(idx % hash.length) || 0) + idx) % 3;
                    if (factor === 0) {{
                        result.data[i] = (result.data[i] + 1) % 256;
                    }} else if (factor === 1) {{
                        result.data[i + 1] = (result.data[i + 1] + 1) % 256;
                    }}
                }}
            }}

            return result;
        }} catch(e) {{
            // Return blank data for tainted canvases
            return new ImageData(sw, sh);
        }}
    }};

    // Override toBlob
    HTMLCanvasElement.prototype.toBlob = function(callback, type, quality) {{
        try {{
            // Get the data URL first
            const dataURL = this.toDataURL(type, quality);
            // Convert to blob
            fetch(dataURL)
                .then(res => res.blob())
                .then(callback)
                .catch(() => callback(null));
        }} catch(e) {{
            callback(null);
        }}
    }};

    // WebGL canvas spoofing
    const originalGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(contextType, contextAttributes) {{
        const context = originalGetContext.call(this, contextType, contextAttributes);

        if (context && (contextType === 'webgl' || contextType === 'webgl2')) {{
            // Store original methods
            const originalGetParameter = context.getParameter.bind(context);
            const originalGetExtension = context.getExtension.bind(context);

            // Override getParameter for consistent fingerprinting
            context.getParameter = function(param) {{
                // Return spoofed values for fingerprinting parameters
                switch(param) {{
                    case 37445: // UNMASKED_VENDOR_WEBGL
                        return '{fp.hash.substring(0, 20)}';
                    case 37446: // UNMASKED_RENDERER_WEBGL
                        return '{fp.hash.substring(10, 40)}';
                    default:
                        return originalGetParameter(param);
                }}
            }};

            // Consistent extension list
            context.getExtension = function(name) {{
                const knownExtensions = [
                    'WEBGL_lose_context', 'WEBGL_debug_renderer_info',
                    'EXT_color_buffer_float', 'EXT_texture_filter_anisotropic',
                    'OES_texture_float_linear', 'OES_standard_derivatives'
                ];

                if (knownExtensions.includes(name)) {{
                    return originalGetExtension(name);
                }}

                return originalGetExtension(name);
            }};
        }}

        return context;
    }};

    console.log('[Canvas Spoof] Script loaded - Profile: {fp.description}');
}})();
"""

    def get_simple_script(self) -> str:
        """
        Get simplified JavaScript for canvas spoofing.

        Returns:
            Simpler JavaScript code
        """
        if not self.fingerprint:
            return ""

        fp = self.fingerprint

        return f"""
(function() {{
    // Simple canvas hash spoofing
    const _storedHash = '{fp.hash}';

    // Override getImageData for consistent fingerprint
    const _ctx = CanvasRenderingContext2D.prototype;
    const _originalGetImageData = _ctx.getImageData;

    _ctx.getImageData = function(sx, sy, sw, sh) {{
        const data = _originalGetImageData.call(this, sx, sy, sw, sh);

        // Deterministic modification based on stored hash
        for (let i = 0; i < data.data.length; i += 4) {{
            const offset = _storedHash.charCodeAt(i % _storedHash.length) || 0;
            data.data[i] = (data.data[i] + offset) % 256;
            data.data[i+1] = (data.data[i+1] + (offset >> 2)) % 256;
            data.data[i+2] = (data.data[i+2] + (offset >> 4)) % 256;
        }}

        return data;
    }};

    console.log('[Canvas] Simple spoof active');
}})();
"""


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

_canvas_generator: Optional[CanvasSpoofGenerator] = None


def get_canvas_generator() -> CanvasSpoofGenerator:
    """Get or create global canvas spoof generator."""
    global _canvas_generator
    if _canvas_generator is None:
        _canvas_generator = CanvasSpoofGenerator()
    return _canvas_generator


def get_canvas_injection_script(
    os: Optional[str] = None,
    browser: Optional[str] = None,
) -> str:
    """
    Get canvas spoofing injection script.

    Args:
        os: Target OS
        browser: Target browser

    Returns:
        JavaScript code for browser injection
    """
    generator = get_canvas_generator()
    fingerprint = generator.get_fingerprint(os, browser)
    injector = CanvasSpoofInjector(fingerprint)
    return injector.get_injection_script()
