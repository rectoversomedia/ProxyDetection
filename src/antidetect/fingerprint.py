"""Fingerprint generation with C++-level accuracy.

This module generates coherent fingerprints that pass advanced detection systems
by leveraging mathematical models and real-world browser data distributions.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from fake_useragent import UserAgent
import numpy as np

from ..utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# INDONESIA-FOCUSED FINGERPRINT CONFIGURATION
# =============================================================================

# Country to timezone mapping (EXPANDED for Indonesia)
COUNTRY_TIMEZONES: Dict[str, List[str]] = {
    # Indonesia - Multiple cities for geo-targeting
    "ID": [
        "Asia/Jakarta",      # WIB (UTC+7)
        "Asia/Jakarta",      # Jakarta
        "Asia/Makassar",     # WITA (UTC+8) - Makassar, Denpasar
        "Asia/Jayapura",     # WIT (UTC+9) - Papua
        "Asia/Pontianak",    # WIB (UTC+7) - Kalimantan
        "Asia/Bangkok",      # Alternative for mixed SE Asia
    ],
    # Indonesia Province Targeting
    "ID-JK": ["Asia/Jakarta"],      # DKI Jakarta
    "ID-JB": ["Asia/Jakarta"],      # Jawa Barat
    "ID-JT": ["Asia/Jakarta"],      # Jawa Tengah
    "ID-JI": ["Asia/Jakarta"],      # Jawa Timur
    "ID-BT": ["Asia/Jakarta"],      # Banten
    "ID-DKI": ["Asia/Jakarta"],     # Jakarta
    "ID-SU": ["Asia/Jakarta"],      # Sumatera Utara (displays as WIB)
    "ID-SS": ["Asia/Jakarta"],      # Sumatera Selatan
    "ID-SB": ["Asia/Makassar"],    # Sumatera Barat (WIB but different ISP patterns)
    "ID-CA": ["Asia/Makassar"],     # Kalimantan
    "ID-KT": ["Asia/Makassar"],     # Kalimantan Tengah
    "ID-KI": ["Asia/Makassar"],     # Kalimantan Timur
    "ID-SA": ["Asia/Makassar"],     # Sulawesi
    "ID-BA": ["Asia/Makassar"],     # Bali (WITA)
    "ID-NT": ["Asia/Makassar"],     # Nusa Tenggara
    "ID-MA": ["Asia/Jayapura"],     # Maluku
    "ID-PP": ["Asia/Jayapura"],     # Papua
    # ASEAN neighbors (for mixed traffic)
    "MY": ["Asia/Kuala_Lumpur"],
    "SG": ["Asia/Singapore"],
    "TH": ["Asia/Bangkok"],
    "VN": ["Asia/Ho_Chi_Minh"],
    "PH": ["Asia/Manila"],
    # Global (kept for reference, deprioritized)
    "US": ["America/New_York"],
    "GB": ["Europe/London"],
    "DE": ["Europe/Berlin"],
    "JP": ["Asia/Tokyo"],
    "AU": ["Australia/Sydney"],
}

# Indonesian Cities for geo-targeting
INDONESIAN_CITIES: Dict[str, Dict[str, Any]] = {
    "jakarta": {
        "name": "Jakarta",
        "province": "DKI Jakarta",
        "timezone": "Asia/Jakarta",
        "tz_offset": 25200,  # UTC+7 in seconds
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "biznet", "myrepublic", "indosat", "xl", "three", "firstmedia", "cbn"],
    },
    "bandung": {
        "name": "Bandung",
        "province": "Jawa Barat",
        "timezone": "Asia/Jakarta",
        "tz_offset": 25200,
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "ceria", "cotome", "myrepublic"],
    },
    "surabaya": {
        "name": "Surabaya",
        "province": "Jawa Timur",
        "timezone": "Asia/Jakarta",
        "tz_offset": 25200,
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "myspeed", "jagoanhosting"],
    },
    "semarang": {
        "name": "Semarang",
        "province": "Jawa Tengah",
        "timezone": "Asia/Jakarta",
        "tz_offset": 25200,
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "starwifi"],
    },
    "yogyakarta": {
        "name": "Yogyakarta",
        "province": "DI Yogyakarta",
        "timezone": "Asia/Jakarta",
        "tz_offset": 25200,
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "fastnet"],
    },
    "medan": {
        "name": "Medan",
        "province": "Sumatera Utara",
        "timezone": "Asia/Jakarta",
        "tz_offset": 25200,
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "executable", "orbit"],
    },
    "makassar": {
        "name": "Makassar",
        "province": "Sulawesi Selatan",
        "timezone": "Asia/Makassar",
        "tz_offset": 28800,  # UTC+8
        "tz_offset_minutes": 480,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "citranet"],
    },
    "denpasar": {
        "name": "Denpasar",
        "province": "Bali",
        "timezone": "Asia/Makassar",
        "tz_offset": 28800,
        "tz_offset_minutes": 480,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "baliwifi", "bosnet"],
    },
    "manado": {
        "name": "Manado",
        "province": "Sulawesi Utara",
        "timezone": "Asia/Makassar",
        "tz_offset": 28800,
        "tz_offset_minutes": 480,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "sorong"],
    },
    "jayapura": {
        "name": "Jayapura",
        "province": "Papua",
        "timezone": "Asia/Jayapura",
        "tz_offset": 32400,  # UTC+9
        "tz_offset_minutes": 540,
        "locale": "id-ID",
        "isp_patterns": ["telkom"],
    },
    "palembang": {
        "name": "Palembang",
        "province": "Sumatera Selatan",
        "timezone": "Asia/Jakarta",
        "tz_offset": 25200,
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "palcom"],
    },
    "tangerang": {
        "name": "Tangerang",
        "province": "Banten",
        "timezone": "Asia/Jakarta",
        "tz_offset": 25200,
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "cbn", "biznet", "indosat"],
    },
    "bekasi": {
        "name": "Bekasi",
        "province": "Jawa Barat",
        "timezone": "Asia/Jakarta",
        "tz_offset": 25200,
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "firstmedia", "indosat"],
    },
    "depok": {
        "name": "Depok",
        "province": "Jawa Barat",
        "timezone": "Asia/Jakarta",
        "tz_offset": 25200,
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "cbn"],
    },
    "bogor": {
        "name": "Bogor",
        "province": "Jawa Barat",
        "timezone": "Asia/Jakarta",
        "tz_offset": 25200,
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "iconpln"],
    },
    "solo": {
        "name": "Surakarta",
        "province": "Jawa Tengah",
        "timezone": "Asia/Jakarta",
        "tz_offset": 25200,
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "sura"],
    },
    "malang": {
        "name": "Malang",
        "province": "Jawa Timur",
        "timezone": "Asia/Jakarta",
        "tz_offset": 25200,
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom", "polinema"],
    },
    "pontianak": {
        "name": "Pontianak",
        "province": "Kalimantan Barat",
        "timezone": "Asia/Pontianak",
        "tz_offset": 25200,
        "tz_offset_minutes": 420,
        "locale": "id-ID",
        "isp_patterns": ["telkom"],
    },
    "samarinda": {
        "name": "Samarinda",
        "province": "Kalimantan Timur",
        "timezone": "Asia/Makassar",
        "tz_offset": 28800,
        "tz_offset_minutes": 480,
        "locale": "id-ID",
        "isp_patterns": ["telkom"],
    },
    "banjarmasin": {
        "name": "Banjarmasin",
        "province": "Kalimantan Selatan",
        "timezone": "Asia/Makassar",
        "tz_offset": 28800,
        "tz_offset_minutes": 480,
        "locale": "id-ID",
        "isp_patterns": ["telkom"],
    },
}

# Indonesian Mobile Carriers
INDONESIAN_MOBILE_CARRIERS: Dict[str, Dict[str, Any]] = {
    "telkomsel": {
        "name": "Telkomsel",
        "prefixes": ["812", "813", "852", "855", "857", "858", "859"],
        "apn": "internet",
    },
    "indosat": {
        "name": "Indosat Ooredoo",
        "prefixes": ["814", "815", "816", "855", "856"],
        "apn": "indosatgprs",
    },
    "xl": {
        "name": "XL Axiata",
        "prefixes": ["817", "818", "819", "859"],
        "apn": "xlgprs",
    },
    "three": {
        "name": "3 (Three)",
        "prefixes": ["895", "896", "897", "898", "899"],
        "apn": "3gprs",
    },
    "smartfren": {
        "name": "Smartfren",
        "prefixes": ["881", "882", "883", "884", "886", "887", "888", "889"],
        "apn": "smartfren",
    },
    "axis": {
        "name": "Axis",
        "prefixes": ["831", "832", "833", "838"],
        "apn": "axis",
    },
}

# Indonesian ISPs (Fixed/Broadband)
INDONESIAN_ISPS: Dict[str, Dict[str, Any]] = {
    "telkom": {
        "name": "PT Telkom Indonesia",
        "product": "Indihome",
        "asn_patterns": ["AS17974", "AS131111", "AS131112", "AS23700"],
    },
    "biznet": {
        "name": "Biznet Networks",
        "asn_patterns": ["AS17488", "AS5549"],
    },
    "myrepublic": {
        "name": "MyRepublic",
        "asn_patterns": ["AS134045"],
    },
    "cbn": {
        "name": "CBN",
        "asn_patterns": ["AS9244"],
    },
    "firstmedia": {
        "name": "First Media",
        "asn_patterns": ["AS55660"],
    },
    "indosat_gaming": {
        "name": "Indosat Gaming",
        "asn_patterns": ["AS4761"],
    },
    "xl_home": {
        "name": "XL Home",
        "asn_patterns": ["AS24218"],
    },
}

# Screen resolutions by OS
OS_RESOLUTIONS: Dict[str, List[str]] = {
    "windows": [
        "1920x1080", "1366x768", "1536x864", "1440x900", "1280x720",
        "1600x900", "1280x800", "1024x768", "2560x1440", "3840x2160"
    ],
    "mac": [
        "2560x1600", "1440x900", "2880x1800", "1680x1050", "1920x1200",
        "2048x1536", "2560x1440", "2304x1440", "3072x1920", "3456x2234"
    ],
    "linux": [
        "1920x1080", "1366x768", "1440x900", "1280x720", "1600x900",
        "1024x768", "1280x800", "2560x1440", "3840x2160", "1680x1050"
    ],
}

# WebGL vendors and renderers by OS
WEBGL_CONFIGS: Dict[str, List[Dict[str, str]]] = {
    "windows": [
        {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0)"},
        {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)"},
        {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)"},
        {"vendor": "Intel Inc.", "renderer": "Intel Iris OpenGL Engine"},
        {"vendor": "NVIDIA Corporation", "renderer": "GeForce GTX 1070/PCIe/SSE2"},
    ],
    "mac": [
        {"vendor": "Intel Inc.", "renderer": "Intel Iris Pro OpenGL Engine"},
        {"vendor": "Intel Inc.", "renderer": "Intel Iris Plus Graphics OpenGL Engine"},
        {"vendor": "AMD Inc.", "renderer": "AMD Radeon Pro 5500M OpenGL Engine"},
        {"vendor": "Apple Inc.", "renderer": "Apple M1"},
        {"vendor": "NVIDIA Corporation", "renderer": "NVIDIA GeForce GT 750M OpenGL Engine"},
    ],
    "linux": [
        {"vendor": "Intel Inc.", "renderer": "Mesa/X.org (Intel HD Graphics 620)"},
        {"vendor": "NVIDIA Corporation", "renderer": "GeForce GTX 1050 Ti/PCIe/SSE2"},
        {"vendor": "Mesa/X.org", "renderer": "Radeon RX 580 Series (POLARIS10)"},
        {"vendor": "Intel Inc.", "renderer": "Intel HD Graphics 630"},
    ],
}

# Indonesian fonts (for locale-aware fingerprinting)
FONT_LISTS: Dict[str, List[str]] = {
    "windows": [
        # International fonts (common in Indonesia)
        "Arial", "Arial Black", "Calibri", "Cambria", "Cambria Math",
        "Comic Sans MS", "Consolas", "Courier New", "Georgia", "Impact",
        "Lucida Console", "Lucida Sans Unicode", "Microsoft Sans Serif",
        "Palatino Linotype", "Segoe UI", "Segoe UI Symbol", "Tahoma",
        "Times New Roman", "Trebuchet MS", "Verdana", "Webdings", "Wingdings",
        "Trebuchet MS", "Verdana", "Segoe UI",
    ],
    "mac": [
        "Arial", "Arial Black", "Brush Script MT", "Comic Sans MS", "Courier New",
        "Georgia", "Helvetica", "Helvetica Neue", "Monaco", "Palatino",
        "San Francisco", "Times New Roman", "Trebuchet MS", "Verdana",
        "Menlo", "Monaco",
    ],
    "linux": [
        "DejaVu Sans", "DejaVu Serif", "Liberation Sans", "Liberation Serif",
        "Ubuntu", "Ubuntu Mono", "Noto Sans", "Noto Serif", "Droid Sans",
        "FreeSans", "Liberation Mono", "Courier New",
    ],
    # Indonesian-specific locales
    "id": [
        "Arial", "Segoe UI", "Tahoma", "Verdana", "Trebuchet MS",
        "Microsoft Sans Serif", "Calibri", "Lucida Sans Unicode",
        "Times New Roman", "Courier New",
    ],
}

# Indonesian Locale Configuration
INDONESIAN_LANGUAGES: Dict[str, List[str]] = {
    "id-ID": ["id-ID", "id", "en-US", "en"],
    "id": ["id", "en-US", "en"],
    "jv-ID": ["jv-ID", "id-ID", "id", "en-US"],  # Javanese
    "su-ID": ["su-ID", "id-ID", "id", "en-US"],  # Sundanese
}


@dataclass
class FingerprintProfile:
    """Container for all fingerprint data."""

    id: str = field(default_factory=lambda: random.choice("abcdefghijklmnopqrstuvwxyz") * 8 + str(datetime.utcnow().timestamp()))
    os: str = "windows"
    browser: str = "chrome"
    user_agent: str = ""
    platform: str = "Win32"
    vendor: str = "Google Inc."
    product: str = "Gecko"

    # Screen
    screen_width: int = 1920
    screen_height: int = 1080
    screen_color_depth: int = 24
    screen_pixel_ratio: float = 1.0

    # Timezone - DEFAULT TO INDONESIA
    timezone: str = "Asia/Jakarta"
    timezone_offset: int = 420  # UTC+7 (WIB) in minutes

    # Language - DEFAULT TO INDONESIA
    language: str = "id-ID"
    languages: List[str] = field(default_factory=lambda: ["id-ID", "id", "en-US"])

    # Geo targeting
    country: str = "ID"
    city: Optional[str] = None  # Indonesian city for precise geo-targeting
    province: Optional[str] = None

    # Canvas
    canvas_hash: str = ""

    # WebGL
    webgl_vendor: str = "Google Inc."
    webgl_renderer: str = "ANGLE (NVIDIA GeForce GTX 1060)"
    webgl_extensions: List[str] = field(default_factory=list)

    # Audio
    audio_hash: str = ""

    # Fonts
    fonts: List[str] = field(default_factory=list)

    # Hardware
    hardware_concurrency: int = 4
    device_memory: int = 8

    # Network
    connection_type: str = "unknown"
    downlink: float = 10.0
    effective_type: str = "4g"

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    seed: int = field(default_factory=lambda: random.randint(0, 2**31 - 1))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FingerprintProfile:
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> FingerprintProfile:
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


class FingerprintGenerator:
    """
    Generate coherent browser fingerprints with C++-level accuracy.

    This generator creates fingerprints that:
    - Match OS/browser combinations realistically
    - Have consistent timezone/geoIP alignment
    - Use proper mathematical distributions for noise injection
    - Pass advanced fingerprinting systems
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the fingerprint generator.

        Args:
            seed: Random seed for reproducibility
        """
        self._seed = seed or random.randint(0, 2**31 - 1)
        self._random = random.Random(self._seed)
        self._ua_generator = UserAgent(fallback="Chrome")

    def generate(
        self,
        os: Optional[str] = None,
        browser: Optional[str] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
        city: Optional[str] = None,
    ) -> FingerprintProfile:
        """
        Generate a coherent fingerprint.

        Args:
            os: Target OS (windows, mac, linux). If None, randomly selected.
            browser: Target browser (chrome, firefox, safari). If None, randomly selected.
            country: Target country for timezone matching. If None, defaults to Indonesia (ID).
            language: Target language. If None, based on country or default to id-ID.
            city: Specific Indonesian city for geo-targeting.

        Returns:
            Generated FingerprintProfile with all fingerprint data
        """
        # Initialize seeded random
        seed = self._seed
        self._seed = random.randint(0, 2**31 - 1)
        rng = random.Random(self._seed)

        # Select OS and browser - WEIGHTED FOR INDONESIA
        if os is None:
            os = rng.choice(["windows", "windows", "windows", "mac", "linux"])
        if browser is None:
            browser = "chrome" if os != "mac" else rng.choice(["chrome", "safari"])
        if browser == "firefox":
            browser = "firefox"
        elif browser == "safari":
            browser = "safari"
        else:
            browser = "chrome"

        # Select country - DEFAULT TO INDONESIA
        if country is None:
            # Heavy weight on Indonesia for Indonesia-focused operations
            country = rng.choice([
                "ID", "ID", "ID", "ID", "ID",  # 50% Indonesia
                "ID-JK", "ID-JB", "ID-JT", "ID-JI", "ID-BT",  # Province targeting
                "SG", "MY",  # SE Asia neighbors
                "US", "GB",  # International (low weight)
            ])

        # Handle city-level targeting for Indonesia
        city_data = None
        province = None
        if city and city in INDONESIAN_CITIES:
            city_data = INDONESIAN_CITIES[city]
            province = city_data["province"]
        elif country.startswith("ID-"):
            # Province-level targeting
            province_code = country
            # Map province code to city
            province_map = {
                "ID-JK": "jakarta", "ID-DKI": "jakarta",
                "ID-JB": "bandung", "ID-JT": "semarang", "ID-JI": "surabaya",
                "ID-BT": "tangerang", "ID-SU": "medan",
                "ID-SS": "palembang", "ID-CA": "pontianak",
                "ID-KI": "samarinda", "ID-SA": "makassar", "ID-BA": "denpasar",
            }
            city_name = province_map.get(province_code, "jakarta")
            if city_name in INDONESIAN_CITIES:
                city_data = INDONESIAN_CITIES[city_name]
                province = city_data["province"]
                country = "ID"  # Normalize to ID for timezone lookup

        # Generate timezone from country (falls back to Jakarta)
        timezones = COUNTRY_TIMEZONES.get(country, COUNTRY_TIMEZONES["ID"])
        timezone = rng.choice(timezones)

        # Override with city-specific timezone if available
        if city_data:
            timezone = city_data["timezone"]

        # Generate user agent - Chrome is dominant in Indonesia
        if browser == "chrome":
            if os == "windows":
                ua = self._ua_generator.Chrome
            elif os == "mac":
                ua = self._ua_generator.Chrome.replace("Windows", "Macintosh").replace("Win", "Mac")
            else:
                ua = self._ua_generator.Chrome.replace("Windows", "X11").replace("Win", "Linux")
        elif browser == "firefox":
            ua = self._ua_generator.Firefox
        else:
            ua = self._ua_generator.Safari

        # Platform string
        platform_map = {
            "windows": "Win32",
            "mac": "MacIntel",
            "linux": "X11; Linux x86_64",
        }
        platform = platform_map.get(os, "Win32")

        # Screen resolution - Common in Indonesia
        resolutions = OS_RESOLUTIONS.get(os, OS_RESOLUTIONS["windows"])
        screen_res = rng.choice(resolutions)
        screen_width, screen_height = map(int, screen_res.split("x"))

        # Pixel ratio based on OS
        if os == "mac":
            pixel_ratios = [1.0, 2.0, 2.25, 3.0]
        elif os == "windows":
            pixel_ratios = [1.0, 1.0, 1.25, 1.5]
        else:
            pixel_ratios = [1.0, 1.0, 1.0]
        pixel_ratio = rng.choice(pixel_ratios)

        # WebGL config
        webgl_configs = WEBGL_CONFIGS.get(os, WEBGL_CONFIGS["windows"])
        webgl_config = rng.choice(webgl_configs)

        # Fonts - Use Indonesian locale if targeting ID
        if country == "ID" or country.startswith("ID-"):
            fonts = FONT_LISTS.get("id", FONT_LISTS["windows"])
        else:
            fonts = FONT_LISTS.get(os, FONT_LISTS["windows"])
        num_fonts = rng.randint(15, min(30, len(fonts)))
        selected_fonts = rng.sample(fonts, min(num_fonts, len(fonts)))

        # Language - DEFAULT TO INDONESIA
        if language is None:
            lang_map = {
                "ID": "id-ID", "ID-JK": "id-ID", "ID-JB": "id-ID",
                "ID-JT": "id-ID", "ID-JI": "id-ID", "ID-BT": "id-ID",
                "ID-SU": "id-ID", "ID-SS": "id-ID", "ID-CA": "id-ID",
                "ID-KI": "id-ID", "ID-SA": "id-ID", "ID-BA": "id-ID",
                "SG": "en-SG", "MY": "ms-MY", "TH": "th-TH",
                "US": "en-US", "GB": "en-GB", "CA": "en-CA",
                "AU": "en-AU", "DE": "de-DE", "FR": "fr-FR",
                "JP": "ja-JP", "CN": "zh-CN", "KR": "ko-KR",
                "BR": "pt-BR", "MX": "es-MX", "ES": "es-ES",
            }
            language = lang_map.get(country, "id-ID")  # Default to Indonesian

        # Use Indonesian language config
        if language.startswith("id"):
            languages = INDONESIAN_LANGUAGES.get(language, ["id-ID", "id", "en-US"])
        else:
            languages = [language]
            if not language.startswith("en"):
                languages.append("en-US")  # Add English as fallback

        # Hardware - Common specs in Indonesia
        hardware_concurrency = rng.choice([2, 4, 4, 4, 6, 8, 8, 12])
        device_memory = rng.choice([2, 4, 4, 8, 8, 16])

        # Create profile
        profile = FingerprintProfile(
            id=self._generate_id(),
            os=os,
            browser=browser,
            user_agent=ua,
            platform=platform,
            vendor="Google Inc." if browser == "chrome" else "Mozilla",
            product="Gecko" if browser != "safari" else "AppleWebKit",

            screen_width=screen_width,
            screen_height=screen_height,
            screen_color_depth=rng.choice([24, 32]),
            screen_pixel_ratio=pixel_ratio,

            timezone=timezone,
            timezone_offset=self._get_timezone_offset(timezone),

            language=language,
            languages=languages,

            canvas_hash=self._generate_canvas_hash(ua, webgl_config, selected_fonts, rng),
            webgl_vendor=webgl_config["vendor"],
            webgl_renderer=webgl_config["renderer"],

            audio_hash=self._generate_audio_hash(ua, rng),

            fonts=selected_fonts,

            hardware_concurrency=hardware_concurrency,
            device_memory=device_memory,

            connection_type=rng.choice(["wifi", "4g", "4g", "unknown"]),
            downlink=rng.uniform(5, 50),
            effective_type="4g",

            country=country if not country.startswith("ID-") else "ID",
            city=city or (city_data["name"] if city_data else None),
            province=province or (city_data["province"] if city_data else None),

            seed=self._seed,
        )

        return profile

    def generate_batch(
        self,
        count: int,
        os: Optional[str] = None,
        browser: Optional[str] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
    ) -> List[FingerprintProfile]:
        """
        Generate multiple fingerprints with variations.

        Args:
            count: Number of fingerprints to generate
            os: Target OS (optional)
            browser: Target browser (optional)
            country: Target country (optional)
            language: Target language (optional)

        Returns:
            List of FingerprintProfile
        """
        profiles = []
        for i in range(count):
            # Vary the seed for each profile
            self._seed = random.randint(0, 2**31 - 1)
            profile = self.generate(
                os=os,
                browser=browser,
                country=country,
                language=language,
            )
            profiles.append(profile)

        return profiles

    def _generate_id(self) -> str:
        """Generate unique fingerprint ID."""
        return hashlib.md5(
            f"{self._seed}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

    def _generate_canvas_hash(
        self,
        user_agent: str,
        webgl_config: Dict[str, str],
        fonts: List[str],
        rng: random.Random,
    ) -> str:
        """
        Generate canvas fingerprint hash with realistic noise.

        Uses a combination of factors to create a deterministic but varied hash.
        """
        # Seeded random for canvas noise
        canvas_seed = rng.randint(0, 2**31 - 1)

        # Simulate canvas hash based on UA, fonts, and random noise
        data = f"{user_agent}{' '.join(fonts[:10])}{webgl_config['renderer']}{canvas_seed}"

        # Add some realistic variation
        noise = rng.uniform(0.0001, 0.001)

        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def _generate_audio_hash(self, user_agent: str, rng: random.Random) -> str:
        """
        Generate audio context fingerprint hash.
        """
        audio_seed = rng.randint(0, 2**31 - 1)
        data = f"{user_agent}{audio_seed}"

        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def _get_timezone_offset(self, timezone: str) -> int:
        """
        Get timezone offset in minutes from UTC.

        Includes Indonesia timezones (WIB, WITA, WIT).
        """
        # Indonesia timezones
        indonesia_offsets = {
            "Asia/Jakarta": 420,      # WIB (UTC+7)
            "Asia/Pontianak": 420,    # WIB (UTC+7)
            "Asia/Makassar": 480,     # WITA (UTC+8)
            "Asia/Jayapura": 540,      # WIT (UTC+9)
        }

        if timezone in indonesia_offsets:
            return indonesia_offsets[timezone]

        # Other timezone offsets
        offsets = {
            "America/New_York": -300,
            "America/Chicago": -360,
            "America/Denver": -420,
            "America/Los_Angeles": -480,
            "Europe/London": 0,
            "Europe/Berlin": 60,
            "Europe/Paris": 60,
            "Asia/Tokyo": 540,
            "Asia/Shanghai": 480,
            "Asia/Singapore": 480,
            "Asia/Seoul": 540,
            "Asia/Kuala_Lumpur": 480,
            "Asia/Bangkok": 420,
            "Asia/Ho_Chi_Minh": 420,
            "Asia/Manila": 480,
            "Australia/Sydney": 600,
        }

        return offsets.get(timezone, 0)

    def get_realistic_user_agent(
        self,
        os: Optional[str] = None,
        browser: Optional[str] = None,
    ) -> str:
        """
        Get a realistic user agent string.

        Args:
            os: Operating system
            browser: Browser name

        Returns:
            User agent string
        """
        if browser == "chrome" or browser is None:
            if os == "mac":
                return (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            elif os == "linux":
                return (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            else:
                return (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
        elif browser == "firefox":
            if os == "mac":
                return (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) "
                    "Gecko/20100101 Firefox/120.0"
                )
            elif os == "linux":
                return (
                    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) "
                    "Gecko/20100101 Firefox/120.0"
                )
            else:
                return (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) "
                    "Gecko/20100101 Firefox/120.0"
                )
        elif browser == "safari":
            return (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.1 Safari/605.1.15"
            )

        return self._ua_generator.random
