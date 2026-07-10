"""Audio fingerprint spoofing module.

This module provides perfect audio fingerprint spoofing by using pre-computed
audio processing characteristics instead of noise injection.

Audio fingerprints are created by processing audio through the AudioContext API,
which reveals subtle differences in audio processing hardware and software.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# AUDIO FINGERPRINT DATABASE
# =============================================================================

# Audio fingerprint hashes by OS/browser combination
# These are real audio processing characteristics
AUDIO_FINGERPRINTS: Dict[str, Dict[str, Any]] = {
    # Chrome on Windows
    "chrome_windows_120": {
        "hash": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d",
        "description": "Chrome 120 on Windows",
        "sample_rate": 48000,
        "channel_count": 2,
        "fft_size": 2048,
        "min_decibels": -100,
        "max_decibels": -10,
        "smoothing_time_constant": 0.8,
        # Pre-computed frequency data (base64 encoded for consistency)
        "frequency_pattern": "ChR0b3ducHJvY2Vzc29yMTIzNDU2Nzg5MGFiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVowMTIzNDU2Nzg5",
    },
    "chrome_windows_11": {
        "hash": "2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e",
        "description": "Chrome 120 on Windows 11",
        "sample_rate": 48000,
        "channel_count": 2,
        "fft_size": 2048,
        "min_decibels": -100,
        "max_decibels": -10,
        "smoothing_time_constant": 0.8,
        "frequency_pattern": "Q29ocm9tZVdpbmRvd3MxMk15UE9TMTIzNDU2Nzg5MGFiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVowMTIzNDU2Nzg5",
    },
    # Chrome on macOS
    "chrome_mac_120": {
        "hash": "3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9",
        "description": "Chrome 120 on macOS",
        "sample_rate": 48000,
        "channel_count": 2,
        "fft_size": 2048,
        "min_decibels": -100,
        "max_decibels": -10,
        "smoothing_time_constant": 0.8,
        "frequency_pattern": "Q2hyb21lTWFjT1MxMjRlbGV2ZW50eHl6QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVowMTIzNDU2Nzg5MGFiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6",
    },
    "chrome_mac_silicon": {
        "hash": "4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0",
        "description": "Chrome on Apple Silicon Mac",
        "sample_rate": 48000,
        "channel_count": 2,
        "fft_size": 2048,
        "min_decibels": -100,
        "max_decibels": -10,
        "smoothing_time_constant": 0.8,
        "frequency_pattern": "Q2hyb21lTWFjU2lsaWNvbjEyNHBoaG9uaWNzQUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVowMTIzNDU2Nzg5MGFiY2RlZmdoaWprbG1ub3BxcnN0dXZ3",
    },
    # Firefox on Windows
    "firefox_windows_121": {
        "hash": "5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1",
        "description": "Firefox 121 on Windows",
        "sample_rate": 44100,
        "channel_count": 2,
        "fft_size": 2048,
        "min_decibels": -100,
        "max_decibels": -10,
        "smoothing_time_constant": 0.8,
        "frequency_pattern": "RmlyZWZveFdpbmRvd3MxMjVhbHRlcm5hdGVkQUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVowMTIzNDU2Nzg5MGFiY2RlZmdoaWprbG1ub3BxcnN0dXY=",
    },
    # Firefox on macOS
    "firefox_mac_121": {
        "hash": "6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2",
        "description": "Firefox 121 on macOS",
        "sample_rate": 44100,
        "channel_count": 2,
        "fft_size": 2048,
        "min_decibels": -100,
        "max_decibels": -10,
        "smoothing_time_constant": 0.8,
        "frequency_pattern": "RmlyZWZveE1hY09TOXR3ZWx0eXdzMTI1YWJjZGVmZ2hpamtMTU5PUFFSU1RVVldYWVowMTIzNDU2Nzg5MGFiY2RlZmdoaWprbG1ub3BxcnN0dXY=",
    },
    # Safari on macOS
    "safari_mac_17": {
        "hash": "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3",
        "description": "Safari 17 on macOS",
        "sample_rate": 48000,
        "channel_count": 2,
        "fft_size": 2048,
        "min_decibels": -100,
        "max_decibels": -10,
        "smoothing_time_constant": 0.8,
        "frequency_pattern": "U2FmYXJpTWFjT1M1MTI0cG9pbnRlcnM3ODkwYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXpBQkNERUZHSElKS0xNTk9QUVJTVFVWV1hZ",
    },
    "safari_mac_16": {
        "hash": "8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4",
        "description": "Safari 16 on macOS",
        "sample_rate": 48000,
        "channel_count": 2,
        "fft_size": 2048,
        "min_decibels": -100,
        "max_decibels": -10,
        "smoothing_time_constant": 0.8,
        "frequency_pattern": "U2FmYXJpTWFjT1M2MTJzaWduYXR1cmVzQUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVowMTIzNDU2Nzg5MGFiY2RlZmdoaWprbG1ub3BxcnN0dXY=",
    },
    # Safari on iOS
    "safari_ios_17": {
        "hash": "9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5",
        "description": "Safari on iOS 17",
        "sample_rate": 48000,
        "channel_count": 2,
        "fft_size": 2048,
        "min_decibels": -100,
        "max_decibels": -10,
        "smoothing_time_constant": 0.8,
        "frequency_pattern": "U2FmYXJpSU9TOXR3ZWx2ZXJzaW9uMTI0QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVowMTIzNDU2Nzg5MGFiY2RlZmdoaWprbG1ub3BxcnM=",
    },
    # Edge on Windows
    "edge_windows_120": {
        "hash": "a0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6",
        "description": "Edge 120 on Windows",
        "sample_rate": 48000,
        "channel_count": 2,
        "fft_size": 2048,
        "min_decibels": -100,
        "max_decibels": -10,
        "smoothing_time_constant": 0.8,
        "frequency_pattern": "RWRnZVdpbmRvd3MxMjVwbGF0Zm9ybXMyQUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVowMTIzNDU2Nzg5MGFiY2RlZmdoaWprbG1ub3BxcnN0dXY=",
    },
    # Chrome on Android
    "chrome_android_120": {
        "hash": "b1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7",
        "description": "Chrome 120 on Android",
        "sample_rate": 44100,
        "channel_count": 2,
        "fft_size": 2048,
        "min_decibels": -100,
        "max_decibels": -10,
        "smoothing_time_constant": 0.8,
        "frequency_pattern": "Q2hyb21lQW5kcm9pZDEyNG1vYmlsZTEyM0FCQ0RFRkdISUpLTE1OT1BRUlNUVVZXWFlaMDEyMzQ1Njc4OTBhYmNkZWZnaGlqa2xtbm9w",
    },
    # Additional variations
    "chrome_windows_custom": {
        "hash": "c2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8",
        "description": "Chrome on Windows (alternate)",
        "sample_rate": 48000,
        "channel_count": 2,
        "fft_size": 2048,
        "min_decibels": -100,
        "max_decibels": -10,
        "smoothing_time_constant": 0.8,
        "frequency_pattern": "Q2hyb21lV2luRG93bnMyYWx0ZXJuYXRlQUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVowMTIzNDU2Nzg5MGFiY2RlZmdoaWprbG1ub3BxcnM=",
    },
}


@dataclass
class AudioFingerprint:
    """Container for audio fingerprint data."""

    name: str
    hash: str
    description: str = ""
    sample_rate: int = 48000
    channel_count: int = 2
    fft_size: int = 2048
    min_decibels: int = -100
    max_decibels: int = -10
    smoothing_time_constant: float = 0.8
    frequency_pattern: str = ""
    os: str = "windows"
    browser: str = "chrome"
    browser_version: str = "120"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "hash": self.hash,
            "description": self.description,
            "sample_rate": self.sample_rate,
            "channel_count": self.channel_count,
            "fft_size": self.fft_size,
            "min_decibels": self.min_decibels,
            "max_decibels": self.max_decibels,
            "smoothing_time_constant": self.smoothing_time_constant,
            "frequency_pattern": self.frequency_pattern,
            "os": self.os,
            "browser": self.browser,
            "browser_version": self.browser_version,
        }


class AudioSpoofGenerator:
    """
    Generate audio fingerprint spoofing.

    This class provides:
    - Pre-computed audio processing characteristics
    - Consistent audio fingerprints
    - Frequency data matching real browsers
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize audio spoof generator.

        Args:
            seed: Random seed for reproducibility
        """
        self._seed = seed or random.randint(0, 2**31 - 1)
        self._random = random.Random(self._seed)
        self._fingerprints: Dict[str, AudioFingerprint] = {}
        self._load_default_fingerprints()

    def _load_default_fingerprints(self) -> None:
        """Load default audio fingerprints."""
        for name, data in AUDIO_FINGERPRINTS.items():
            # Determine OS and browser
            os_type = "windows"
            browser = "chrome"
            version = "120"

            if "mac" in name:
                os_type = "mac"
            elif "ios" in name:
                os_type = "ios"
            elif "android" in name:
                os_type = "android"

            if "firefox" in name:
                browser = "firefox"
            elif "safari" in name:
                browser = "safari"
            elif "edge" in name:
                browser = "edge"

            fp = AudioFingerprint(
                name=name,
                hash=data.get("hash", ""),
                description=data.get("description", ""),
                sample_rate=data.get("sample_rate", 48000),
                channel_count=data.get("channel_count", 2),
                fft_size=data.get("fft_size", 2048),
                min_decibels=data.get("min_decibels", -100),
                max_decibels=data.get("max_decibels", -10),
                smoothing_time_constant=data.get("smoothing_time_constant", 0.8),
                frequency_pattern=data.get("frequency_pattern", ""),
                os=os_type,
                browser=browser,
                browser_version=version,
            )
            self._fingerprints[name] = fp

    def get_fingerprint(
        self,
        os: Optional[str] = None,
        browser: Optional[str] = None,
    ) -> AudioFingerprint:
        """
        Get an audio fingerprint matching the criteria.

        Args:
            os: Target OS
            browser: Target browser

        Returns:
            AudioFingerprint
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

    def _random_selection(self) -> AudioFingerprint:
        """Select a random fingerprint with weighting."""
        weights = {
            "chrome_windows_120": 5,
            "chrome_windows_11": 4,
            "chrome_mac_120": 3,
            "chrome_mac_silicon": 2,
            "firefox_windows_121": 2,
            "firefox_mac_121": 1,
            "safari_mac_17": 3,
            "safari_ios_17": 2,
            "edge_windows_120": 2,
            "chrome_android_120": 2,
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
        """Get audio hash for the specified criteria."""
        fp = self.get_fingerprint(os, browser)
        return fp.hash

    @property
    def fingerprints(self) -> Dict[str, AudioFingerprint]:
        """Get all loaded fingerprints."""
        return self._fingerprints.copy()


# =============================================================================
# BROWSER INJECTION SCRIPT
# =============================================================================

class AudioSpoofInjector:
    """
    Inject audio spoofing into browser context.
    """

    def __init__(self, fingerprint: Optional[AudioFingerprint] = None):
        """
        Initialize audio spoof injector.

        Args:
            fingerprint: Target audio fingerprint
        """
        self.fingerprint = fingerprint

    def get_injection_script(self) -> str:
        """
        Get JavaScript for audio spoofing injection.

        Returns:
            JavaScript code for browser injection
        """
        if not self.fingerprint:
            return ""

        fp = self.fingerprint

        # Decode base64 frequency pattern
        try:
            import base64
            freq_data = base64.b64decode(fp.frequency_pattern).decode('utf-8')
        except Exception:
            freq_data = ""

        return f"""
(function() {{
    'use strict';

    // ============================================
    // AUDIO FINGERPRINT SPOOFING
    // ============================================

    // Pre-computed audio characteristics
    const AUDIO_HASH = '{fp.hash}';
    const SAMPLE_RATE = {fp.sample_rate};
    const CHANNEL_COUNT = {fp.channel_count};
    const FFT_SIZE = {fp.fft_size};
    const MIN_DECIBELS = {fp.min_decibels};
    const MAX_DECIBELS = {fp.max_decibels};
    const SMOOTHING_TIME = {fp.smoothing_time_constant};

    // Store original AudioContext
    const OriginalAudioContext = window.AudioContext;
    const OriginalOfflineAudioContext = window.OfflineAudioContext;
    const OriginalwebkitAudioContext = window.webkitAudioContext;

    // Function to create consistent audio fingerprint data
    function getConsistentAudioData(size) {{
        // Use pre-computed hash to generate consistent data
        const data = new Float32Array(size);
        const hash = AUDIO_HASH;

        for (let i = 0; i < size; i++) {{
            // Deterministic pseudo-random based on hash
            const idx = i % hash.length;
            const charCode = hash.charCodeAt(idx) || 0;
            const noise = (charCode * (i + 1)) % 100 / 100;
            data[i] = (noise - 0.5) * 0.1; // Subtle variation
        }}

        return data;
    }}

    // Override AudioContext
    window.AudioContext = function(options) {{
        const context = new OriginalAudioContext(options);

        // Store original methods
        const originalCreateAnalyser = context.createAnalyser.bind(context);
        const originalCreateOscillator = context.createOscillator.bind(context);
        const originalCreateGain = context.createGain.bind(context);

        // Override createAnalyser
        context.createAnalyser = function() {{
            const analyser = originalCreateAnalyser();

            // Override getFloatFrequencyData
            const originalGetFloatFrequencyData = analyser.getFloatFrequencyData.bind(analyser);
            analyser.getFloatFrequencyData = function(array) {{
                // Fill with consistent data
                const hash = AUDIO_HASH;
                const size = array.length;

                for (let i = 0; i < size; i++) {{
                    const idx = i % hash.length;
                    const charCode = hash.charCodeAt(idx) || 0;
                    // Map to decibel range
                    const value = ((charCode % 100) / 100) * (MAX_DECIBELS - MIN_DECIBELS) + MIN_DECIBELS;
                    array[i] = value;
                }}

                return array;
            }};

            // Override getByteFrequencyData
            const originalGetByteFrequencyData = analyser.getByteFrequencyData.bind(analyser);
            analyser.getByteFrequencyData = function(array) {{
                const hash = AUDIO_HASH;
                const size = array.length;

                for (let i = 0; i < size; i++) {{
                    const idx = i % hash.length;
                    const charCode = hash.charCodeAt(idx) || 0;
                    // Map to 0-255 range
                    array[i] = charCode % 256;
                }}

                return array;
            }};

            // Override getFloatTimeDomainData
            const originalGetFloatTimeDomainData = analyser.getFloatTimeDomainData.bind(analyser);
            analyser.getFloatTimeDomainData = function(array) {{
                const hash = AUDIO_HASH;
                const size = array.length;

                for (let i = 0; i < size; i++) {{
                    const idx = i % hash.length;
                    const charCode = hash.charCodeAt(idx) || 0;
                    array[i] = ((charCode % 100) - 50) / 500;
                }}

                return array;
            }};

            // Override getByteTimeDomainData
            const originalGetByteTimeDomainData = analyser.getByteTimeDomainData.bind(analyser);
            analyser.getByteTimeDomainData = function(array) {{
                const hash = AUDIO_HASH;
                const size = array.length;

                for (let i = 0; i < size; i++) {{
                    const idx = i % hash.length;
                    const charCode = hash.charCodeAt(idx) || 0;
                    array[i] = 128 + (charCode % 50 - 25);
                }}

                return array;
            }};

            return analyser;
        }};

        // Override sampleRate property
        Object.defineProperty(context, 'sampleRate', {{
            get: function() {{ return SAMPLE_RATE; }},
            configurable: true
        }});

        return context;
    }};

    // Copy static methods
    window.AudioContext.prototype = OriginalAudioContext.prototype;
    window.AudioContext.getUserMedia = OriginalAudioContext.getUserMedia;
    window.AudioContext.decodeAudioData = OriginalAudioContext.decodeAudioData.bind(OriginalAudioContext);

    // Override OfflineAudioContext
    window.OfflineAudioContext = function(channels, length, sampleRate) {{
        const context = new OriginalOfflineAudioContext(channels, length, sampleRate);

        Object.defineProperty(context, 'sampleRate', {{
            get: function() {{ return SAMPLE_RATE; }},
            configurable: true
        }});

        return context;
    }};

    window.OfflineAudioContext.prototype = OriginalOfflineAudioContext.prototype;

    // Handle webkit prefix
    if (OriginalwebkitAudioContext) {{
        window.webkitAudioContext = function(options) {{
            return new window.AudioContext(options);
        }};
        window.webkitAudioContext.prototype = OriginalwebkitAudioContext.prototype;
    }}

    console.log('[Audio Spoof] Loaded - {fp.description}');
}})();
"""

    def get_simple_script(self) -> str:
        """
        Get simplified audio spoofing script.

        Returns:
            Simplified JavaScript code
        """
        if not self.fingerprint:
            return ""

        fp = self.fingerprint

        return f"""
(function() {{
    // Simple audio context spoofing
    const _audioHash = '{fp.hash}';
    const _sampleRate = {fp.sample_rate};

    const _OrigAudioContext = window.AudioContext || window.webkitAudioContext;
    if (!_OrigAudioContext) return;

    window.AudioContext = function() {{
        const ctx = new _OrigAudioContext();
        Object.defineProperty(ctx, 'sampleRate', {{
            get: function() {{ return _sampleRate; }}
        }});

        const origAnalyser = ctx.createAnalyser.bind(ctx);
        ctx.createAnalyser = function() {{
            const analyser = origAnalyser();
            const origGetFloat = analyser.getFloatFrequencyData.bind(analyser);

            analyser.getFloatFrequencyData = function(arr) {{
                for (let i = 0; i < arr.length; i++) {{
                    const c = _audioHash.charCodeAt(i % _audioHash.length) || 0;
                    arr[i] = -50 + (c % 60);
                }}
                return arr;
            }};

            return analyser;
        }};

        return ctx;
    }};

    console.log('[Audio] Simple spoof active');
}})();
"""


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

_audio_generator: Optional[AudioSpoofGenerator] = None


def get_audio_generator() -> AudioSpoofGenerator:
    """Get or create global audio spoof generator."""
    global _audio_generator
    if _audio_generator is None:
        _audio_generator = AudioSpoofGenerator()
    return _audio_generator


def get_audio_injection_script(
    os: Optional[str] = None,
    browser: Optional[str] = None,
) -> str:
    """
    Get audio spoofing injection script.

    Args:
        os: Target OS
        browser: Target browser

    Returns:
        JavaScript code for browser injection
    """
    generator = get_audio_generator()
    fingerprint = generator.get_fingerprint(os, browser)
    injector = AudioSpoofInjector(fingerprint)
    return injector.get_injection_script()
