"""Anti-detection modules for ProxyDetection.

This package provides multi-layer anti-detection capabilities:
- Network Layer: TLS/JA3/JA4 fingerprinting, HTTP/2 spoofing
- Browser Layer: Canvas, WebGL, Audio fingerprint spoofing
- Behavioral Layer: ML-resistant human-like patterns
- Captcha Solving: 2Captcha, CapSolver integration
"""

from .fingerprint import FingerprintGenerator, FingerprintProfile
from .behavioral import BehavioralSimulator, Point, KeyPress
from .behavioral_ml import (
    MLResistantBehavioralSystem,
    get_ml_behavior_system,
    CognitiveSimulator,
    MLResistantTiming,
)
from .profile import BrowserProfile, ProfileManager
from .matcher import ConsistencyChecker

# Network layer modules
from .tls_fingerprint import (
    TLSFingerprintGenerator,
    TLSHTTPClient,
    get_tls_generator,
    get_tls_http_client,
)
from .http2_spoofing import (
    HTTP2FingerprintGenerator,
    HTTP2TLSClient,
    get_http2_generator,
)
from .network_layer import (
    NetworkLayer,
    NetworkProfile,
    BrowserFingerprintBridge,
    get_network_layer,
    get_browser_bridge,
)

# Browser fingerprint modules
from .canvas_spoof import (
    CanvasSpoofGenerator,
    CanvasSpoofInjector,
    get_canvas_generator,
    get_canvas_injection_script,
)
from .webgl_spoof import (
    WebGLSpoofGenerator,
    WebGLSpoofInjector,
    get_webgl_generator,
    get_webgl_injection_script,
)
from .audio_spoof import (
    AudioSpoofGenerator,
    AudioSpoofInjector,
    get_audio_generator,
    get_audio_injection_script,
)

# Captcha solving
from .captcha_solver import (
    CaptchaSolver,
    CaptchaResponse,
    TwoCaptchaSolver,
    CapSolver,
    get_captcha_solver,
)

__all__ = [
    # Core modules
    "FingerprintGenerator",
    "FingerprintProfile",
    "BehavioralSimulator",
    "Point",
    "KeyPress",
    "BrowserProfile",
    "ProfileManager",
    "ConsistencyChecker",

    # ML-resistant behavioral
    "MLResistantBehavioralSystem",
    "get_ml_behavior_system",
    "CognitiveSimulator",
    "MLResistantTiming",

    # Network layer
    "TLSFingerprintGenerator",
    "TLSHTTPClient",
    "get_tls_generator",
    "get_tls_http_client",
    "HTTP2FingerprintGenerator",
    "HTTP2TLSClient",
    "get_http2_generator",
    "NetworkLayer",
    "NetworkProfile",
    "BrowserFingerprintBridge",
    "get_network_layer",
    "get_browser_bridge",

    # Browser fingerprint
    "CanvasSpoofGenerator",
    "CanvasSpoofInjector",
    "get_canvas_generator",
    "get_canvas_injection_script",
    "WebGLSpoofGenerator",
    "WebGLSpoofInjector",
    "get_webgl_generator",
    "get_webgl_injection_script",
    "AudioSpoofGenerator",
    "AudioSpoofInjector",
    "get_audio_generator",
    "get_audio_injection_script",

    # Captcha solving
    "CaptchaSolver",
    "CaptchaResponse",
    "TwoCaptchaSolver",
    "CapSolver",
    "get_captcha_solver",
]
