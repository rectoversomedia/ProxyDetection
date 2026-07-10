"""WebGL fingerprint spoofing module.

This module provides perfect WebGL fingerprint spoofing by using GPU-family-matched
renderers instead of generic values.

WebGL fingerprints are created from:
- WebGL vendor string
- WebGL renderer string
- Supported extensions
- Shader precision formats
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
# WEBGL FINGERPRINT DATABASE
# =============================================================================

# Realistic WebGL configurations by OS/GPU family
WEBGL_CONFIGS: Dict[str, Dict[str, Any]] = {
    # Windows with NVIDIA GPUs
    "windows_nvidia_gtx1060": {
        "vendor": "Google Inc. (NVIDIA)",
        "renderer": "ANGLE (NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0)",
        "vendor_id": "10de",
        "renderer_id": "1c03",
        "description": "NVIDIA GTX 1060 on Windows",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
            "GL_EXTENSIONS",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
        "aliased_line_width_range": [1, 1],
        "aliased_point_size_range": [1, 1024],
    },
    "windows_nvidia_gtx1070": {
        "vendor": "Google Inc. (NVIDIA)",
        "renderer": "ANGLE (NVIDIA GeForce GTX 1070 Direct3D11 vs_5_0 ps_5_0)",
        "vendor_id": "10de",
        "renderer_id": "1c02",
        "description": "NVIDIA GTX 1070 on Windows",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
            "GL_EXTENSIONS",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    "windows_nvidia_gtx1080": {
        "vendor": "Google Inc. (NVIDIA)",
        "renderer": "ANGLE (NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)",
        "vendor_id": "10de",
        "renderer_id": "1c03",
        "description": "NVIDIA GTX 1080 on Windows",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    "windows_nvidia_rtx3060": {
        "vendor": "Google Inc. (NVIDIA)",
        "renderer": "ANGLE (NVIDIA GeForce RTX 3060 Ti Direct3D11 vs_5_0 ps_5_0)",
        "vendor_id": "10de",
        "renderer_id": "2489",
        "description": "NVIDIA RTX 3060 Ti on Windows",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
            "EXT_color_buffer_float",
            "EXT_texture_filter_anisotropic",
        ],
        "max_texture_size": 32768,
        "max_viewport_dims": [32768, 32768],
    },
    "windows_nvidia_rtx4070": {
        "vendor": "Google Inc. (NVIDIA)",
        "renderer": "ANGLE (NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0)",
        "vendor_id": "10de",
        "renderer_id": "2782",
        "description": "NVIDIA RTX 4070 on Windows",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
            "EXT_color_buffer_float",
            "EXT_texture_filter_anisotropic",
        ],
        "max_texture_size": 32768,
        "max_viewport_dims": [32768, 32768],
    },
    # Windows with AMD GPUs
    "windows_amd_rx580": {
        "vendor": "Google Inc. (AMD)",
        "renderer": "ANGLE (AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0)",
        "vendor_id": "1002",
        "renderer_id": "67df",
        "description": "AMD RX 580 on Windows",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    "windows_amd_rx6700": {
        "vendor": "Google Inc. (AMD)",
        "renderer": "ANGLE (AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0)",
        "vendor_id": "1002",
        "renderer_id": "73df",
        "description": "AMD RX 6700 XT on Windows",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
            "EXT_color_buffer_float",
            "EXT_texture_filter_anisotropic",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    # Windows with Intel GPUs
    "windows_intel_uhd630": {
        "vendor": "Google Inc. (Intel)",
        "renderer": "ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
        "vendor_id": "8086",
        "renderer_id": "5912",
        "description": "Intel UHD 630 on Windows",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    "windows_intel_iris": {
        "vendor": "Google Inc. (Intel)",
        "renderer": "ANGLE (Intel(R) Iris(R) Plus Graphics Direct3D11 vs_5_0 ps_5_0)",
        "vendor_id": "8086",
        "renderer_id": "8a52",
        "description": "Intel Iris Plus on Windows",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    # macOS with Intel GPUs
    "mac_intel_iris": {
        "vendor": "Intel Inc.",
        "renderer": "Intel Iris Pro OpenGL Engine",
        "vendor_id": "8086",
        "renderer_id": "0d26",
        "description": "Intel Iris Pro on macOS",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
            "OES_texture_float",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    "mac_intel_iris_plus": {
        "vendor": "Intel Inc.",
        "renderer": "Intel Iris Plus Graphics OpenGL Engine",
        "vendor_id": "8086",
        "renderer_id": "8a52",
        "description": "Intel Iris Plus on macOS",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    # macOS with Apple Silicon
    "mac_apple_m1": {
        "vendor": "Apple Inc.",
        "renderer": "Apple M1",
        "vendor_id": "apple",
        "renderer_id": "m1",
        "description": "Apple M1 on macOS",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
            "EXT_color_buffer_float",
            "EXT_texture_filter_anisotropic",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    "mac_apple_m2": {
        "vendor": "Apple Inc.",
        "renderer": "Apple M2",
        "vendor_id": "apple",
        "renderer_id": "m2",
        "description": "Apple M2 on macOS",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
            "EXT_color_buffer_float",
            "EXT_texture_filter_anisotropic",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    "mac_apple_m3": {
        "vendor": "Apple Inc.",
        "renderer": "Apple M3 Pro",
        "vendor_id": "apple",
        "renderer_id": "m3pro",
        "description": "Apple M3 Pro on macOS",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
            "EXT_color_buffer_float",
            "EXT_texture_filter_anisotropic",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    # macOS with AMD GPUs
    "mac_amd_radeon": {
        "vendor": "AMD Inc.",
        "renderer": "AMD Radeon Pro 5500M OpenGL Engine",
        "vendor_id": "1002",
        "renderer_id": "7340",
        "description": "AMD Radeon Pro 5500M on macOS",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    # Linux with NVIDIA
    "linux_nvidia": {
        "vendor": "NVIDIA Corporation",
        "renderer": "GeForce GTX 1050 Ti/PCIe/SSE2",
        "vendor_id": "10de",
        "renderer_id": "1c02",
        "description": "NVIDIA GTX 1050 Ti on Linux",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
        ],
        "max_texture_size": 32768,
        "max_viewport_dims": [32768, 32768],
    },
    # Linux with Intel
    "linux_intel": {
        "vendor": "Intel Inc.",
        "renderer": "Mesa/X.org (Intel HD Graphics 620)",
        "vendor_id": "8086",
        "renderer_id": "5912",
        "description": "Intel HD 620 on Linux",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    # Linux with AMD
    "linux_amd": {
        "vendor": "Mesa/X.org",
        "renderer": "Radeon RX 580 Series (POLARIS10)",
        "vendor_id": "1002",
        "renderer_id": "67df",
        "description": "AMD RX 580 on Linux",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    # Android with Adreno
    "android_adreno_618": {
        "vendor": "Qualcomm",
        "renderer": "Adreno (TM) 618",
        "vendor_id": "1002",
        "renderer_id": "6d76",
        "description": "Adreno 618 on Android",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    "android_adreno_730": {
        "vendor": "Qualcomm",
        "renderer": "Adreno (TM) 730",
        "vendor_id": "1002",
        "renderer_id": "730",
        "description": "Adreno 730 on Android",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
            "EXT_color_buffer_float",
        ],
        "max_texture_size": 16384,
        "max_viewport_dims": [16384, 16384],
    },
    # Android with Mali
    "android_mali_g76": {
        "vendor": "ARM",
        "renderer": "Mali-G76",
        "vendor_id": "13b5",
        "renderer_id": "7212",
        "description": "Mali-G76 on Android",
        "extensions": [
            "WEBGL_debug_renderer_info",
            "WEBGL_lose_context",
        ],
        "max_texture_size": 8192,
        "max_viewport_dims": [8192, 8192],
    },
}


@dataclass
class WebGLFingerprint:
    """Container for WebGL fingerprint data."""

    name: str
    vendor: str
    renderer: str
    vendor_id: str = ""
    renderer_id: str = ""
    description: str = ""
    extensions: List[str] = field(default_factory=list)
    max_texture_size: int = 16384
    max_viewport_dims: List[int] = field(default_factory=lambda: [16384, 16384])
    os: str = "windows"
    gpu_family: str = "nvidia"

    # Computed hash
    _fingerprint_hash: Optional[str] = None

    def __post_init__(self):
        """Calculate fingerprint hash."""
        self._fingerprint_hash = hashlib.sha256(
            f"{self.vendor}{self.renderer}".encode()
        ).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "vendor": self.vendor,
            "renderer": self.renderer,
            "vendor_id": self.vendor_id,
            "renderer_id": self.renderer_id,
            "description": self.description,
            "extensions": self.extensions,
            "max_texture_size": self.max_texture_size,
            "max_viewport_dims": self.max_viewport_dims,
            "os": self.os,
            "gpu_family": self.gpu_family,
            "fingerprint_hash": self._fingerprint_hash,
        }


class WebGLSpoofGenerator:
    """
    Generate WebGL fingerprint spoofing.

    This class provides:
    - GPU-family-matched renderers
    - Consistent WebGL extension lists
    - Vendor/renderer consistency
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize WebGL spoof generator.

        Args:
            seed: Random seed for reproducibility
        """
        self._seed = seed or random.randint(0, 2**31 - 1)
        self._random = random.Random(self._seed)
        self._fingerprints: Dict[str, WebGLFingerprint] = {}
        self._load_default_fingerprints()

    def _load_default_fingerprints(self) -> None:
        """Load default WebGL fingerprints."""
        for name, data in WEBGL_CONFIGS.items():
            # Determine OS and GPU family
            os_type = "windows"
            gpu_family = "nvidia"

            if "mac_" in name:
                os_type = "mac"
                if "apple_m" in name:
                    gpu_family = "apple_silicon"
                elif "amd" in name or "radeon" in name:
                    gpu_family = "amd"
                else:
                    gpu_family = "intel"
            elif "linux_" in name:
                os_type = "linux"
                if "nvidia" in name:
                    gpu_family = "nvidia"
                elif "amd" in name:
                    gpu_family = "amd"
                else:
                    gpu_family = "intel"
            elif "android_" in name:
                os_type = "android"
                if "adreno" in name:
                    gpu_family = "adreno"
                elif "mali" in name:
                    gpu_family = "mali"
                else:
                    gpu_family = "unknown"
            else:
                # Windows
                if "nvidia" in name:
                    gpu_family = "nvidia"
                elif "amd" in name or "radeon" in name or "rx" in name:
                    gpu_family = "amd"
                else:
                    gpu_family = "intel"

            fp = WebGLFingerprint(
                name=name,
                vendor=data.get("vendor", ""),
                renderer=data.get("renderer", ""),
                vendor_id=data.get("vendor_id", ""),
                renderer_id=data.get("renderer_id", ""),
                description=data.get("description", ""),
                extensions=data.get("extensions", []),
                max_texture_size=data.get("max_texture_size", 16384),
                max_viewport_dims=data.get("max_viewport_dims", [16384, 16384]),
                os=os_type,
                gpu_family=gpu_family,
            )
            self._fingerprints[name] = fp

    def get_fingerprint(
        self,
        os: Optional[str] = None,
        gpu_family: Optional[str] = None,
    ) -> WebGLFingerprint:
        """
        Get a WebGL fingerprint matching the criteria.

        Args:
            os: Target OS
            gpu_family: Target GPU family (nvidia, amd, intel, apple_silicon, adreno, mali)

        Returns:
            WebGLFingerprint
        """
        if os is None and gpu_family is None:
            return self._random_selection()

        candidates = []
        for name, fp in self._fingerprints.items():
            if os and fp.os != os:
                continue
            if gpu_family and fp.gpu_family != gpu_family:
                continue
            candidates.append(fp)

        if candidates:
            return self._random.choice(candidates)

        return self._random_selection()

    def _random_selection(self) -> WebGLFingerprint:
        """Select a random fingerprint with weighting."""
        weights = {
            # Windows - more common configurations
            "windows_nvidia_gtx1060": 5,
            "windows_nvidia_rtx3060": 4,
            "windows_nvidia_rtx4070": 3,
            "windows_intel_uhd630": 4,
            "windows_amd_rx580": 3,
            "windows_amd_rx6700": 2,
            # macOS
            "mac_apple_m1": 4,
            "mac_apple_m2": 3,
            "mac_apple_m3": 2,
            "mac_intel_iris": 2,
            # Linux
            "linux_nvidia": 3,
            "linux_intel": 2,
            # Android
            "android_adreno_730": 3,
            "android_adreno_618": 2,
            "android_mali_g76": 2,
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

        return self._fingerprints["windows_nvidia_gtx1060"]

    def get_vendor(self, os: Optional[str] = None, gpu_family: Optional[str] = None) -> str:
        """Get WebGL vendor string."""
        fp = self.get_fingerprint(os, gpu_family)
        return fp.vendor

    def get_renderer(self, os: Optional[str] = None, gpu_family: Optional[str] = None) -> str:
        """Get WebGL renderer string."""
        fp = self.get_fingerprint(os, gpu_family)
        return fp.renderer

    @property
    def fingerprints(self) -> Dict[str, WebGLFingerprint]:
        """Get all loaded fingerprints."""
        return self._fingerprints.copy()


# =============================================================================
# BROWSER INJECTION SCRIPT
# =============================================================================

class WebGLSpoofInjector:
    """
    Inject WebGL spoofing into browser context.
    """

    def __init__(self, fingerprint: Optional[WebGLFingerprint] = None):
        """
        Initialize WebGL spoof injector.

        Args:
            fingerprint: Target WebGL fingerprint
        """
        self.fingerprint = fingerprint

    def get_injection_script(self) -> str:
        """
        Get JavaScript for WebGL spoofing injection.

        Returns:
            JavaScript code for browser injection
        """
        if not self.fingerprint:
            return ""

        fp = self.fingerprint

        # Format extensions for JavaScript
        extensions_str = json.dumps(fp.extensions)

        return f"""
(function() {{
    'use strict';

    // ============================================
    // WEBGL FINGERPRINT SPOOFING
    // ============================================

    const WEBGL_VENDOR = '{fp.vendor}';
    const WEBGL_RENDERER = '{fp.renderer}';
    const WEBGL_EXTENSIONS = {extensions_str};
    const MAX_TEXTURE_SIZE = {fp.max_texture_size};
    const MAX_VIEWPORT_DIMS = {json.dumps(fp.max_viewport_dims)};

    // Store original methods
    const _originalGetParameter = WebGLRenderingContext.prototype.getParameter;
    const _originalGetExtension = WebGLRenderingContext.prototype.getExtension;
    const _originalGetSupportedExtensions = WebGLRenderingContext.prototype.getSupportedExtensions;

    // Override getParameter
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
        switch(parameter) {{
            case 37445: // UNMASKED_VENDOR_WEBGL
                return WEBGL_VENDOR;
            case 37446: // UNMASKED_RENDERER_WEBGL
                return WEBGL_RENDERER;
            case 3379: // ALIASED_LINE_WIDTH_RANGE
                return [1, 1];
            case 33901: // ALIASED_POINT_SIZE_RANGE
                return [1, 1024];
            case 3377: // MAX_TEXTURE_SIZE
                return MAX_TEXTURE_SIZE;
            case 3386: // MAX_VIEWPORT_DIMS
                return MAX_VIEWPORT_DIMS;
            default:
                return _originalGetParameter.call(this, parameter);
        }}
    }};

    // Override getExtension
    WebGLRenderingContext.prototype.getExtension = function(name) {{
        if (WEBGL_EXTENSIONS.includes(name)) {{
            return _originalGetExtension.call(this, name);
        }}
        return null;
    }};

    // Override getSupportedExtensions
    WebGLRenderingContext.prototype.getSupportedExtensions = function() {{
        return WEBGL_EXTENSIONS;
    }};

    // WebGL2 context override
    if (typeof WebGL2RenderingContext !== 'undefined') {{
        const _originalGetParameter2 = WebGL2RenderingContext.prototype.getParameter;
        const _originalGetExtension2 = WebGL2RenderingContext.prototype.getExtension;
        const _originalGetSupportedExtensions2 = WebGL2RenderingContext.prototype.getSupportedExtensions;

        WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
            switch(parameter) {{
                case 37445:
                    return WEBGL_VENDOR;
                case 37446:
                    return WEBGL_RENDERER;
                case 33307: // MAX_TEXTURE_SIZE
                    return MAX_TEXTURE_SIZE;
                case 33309: // MAX_VIEWPORT_DIMS
                    return MAX_VIEWPORT_DIMS;
                default:
                    return _originalGetParameter2.call(this, parameter);
            }}
        }};

        WebGL2RenderingContext.prototype.getExtension = function(name) {{
            if (WEBGL_EXTENSIONS.includes(name)) {{
                return _originalGetExtension2.call(this, name);
            }}
            return null;
        }};

        WebGL2RenderingContext.prototype.getSupportedExtensions = function() {{
            return WEBGL_EXTENSIONS;
        }};
    }}

    // Override debug renderer info extension
    const originalGetExtensionDebug = WebGLDebugRendererInfo ? WebGLDebugRendererInfo.getParameter.bind(WebGLDebugRendererInfo) : null;

    console.log('[WebGL Spoof] Loaded - {fp.description}');
}})();
"""

    def get_simple_script(self) -> str:
        """
        Get simplified WebGL spoofing script.

        Returns:
            Simplified JavaScript code
        """
        if not self.fingerprint:
            return ""

        fp = self.fingerprint

        return f"""
(function() {{
    // WebGL Vendor/Renderer spoofing
    const _getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(p) {{
        if (p === 37445) return '{fp.vendor}';
        if (p === 37446) return '{fp.renderer}';
        return _getParameter.call(this, p);
    }};

    if (typeof WebGL2RenderingContext !== 'undefined') {{
        const _getParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(p) {{
            if (p === 37445) return '{fp.vendor}';
            if (p === 37446) return '{fp.renderer}';
            return _getParameter2.call(this, p);
        }};
    }}

    console.log('[WebGL] Spoof active');
}})();
"""


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

_webgl_generator: Optional[WebGLSpoofGenerator] = None


def get_webgl_generator() -> WebGLSpoofGenerator:
    """Get or create global WebGL spoof generator."""
    global _webgl_generator
    if _webgl_generator is None:
        _webgl_generator = WebGLSpoofGenerator()
    return _webgl_generator


def get_webgl_injection_script(
    os: Optional[str] = None,
    gpu_family: Optional[str] = None,
) -> str:
    """
    Get WebGL spoofing injection script.

    Args:
        os: Target OS
        gpu_family: Target GPU family

    Returns:
        JavaScript code for browser injection
    """
    generator = get_webgl_generator()
    fingerprint = generator.get_fingerprint(os, gpu_family)
    injector = WebGLSpoofInjector(fingerprint)
    return injector.get_injection_script()
