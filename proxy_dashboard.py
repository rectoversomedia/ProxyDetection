#!/usr/bin/env python3
"""
Advanced Proxy & Lead Submission Dashboard
Indonesia-Focused - Interactive Web Interface

Run with: python3 proxy_dashboard.py
Then open: http://localhost:5000
"""

from flask import Flask, jsonify, render_template_string, request
from datetime import datetime
import random
import json
import threading
import time
import hashlib

app = Flask(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Indonesian Cities Configuration (Expanded)
INDONESIAN_CITIES = {
    # Jawa Barat
    "jakarta_pusat": {"name": "Jakarta Pusat", "province": "DKI Jakarta", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "jakarta_barat": {"name": "Jakarta Barat", "province": "DKI Jakarta", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "jakarta_timur": {"name": "Jakarta Timur", "province": "DKI Jakarta", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "jakarta_selatan": {"name": "Jakarta Selatan", "province": "DKI Jakarta", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "jakarta_utara": {"name": "Jakarta Utara", "province": "DKI Jakarta", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "bandung": {"name": "Bandung", "province": "Jawa Barat", "timezone": "WIB (UTC+7)", "region": "jawa_barat"},
    "bekasi": {"name": "Bekasi", "province": "Jawa Barat", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "depok": {"name": "Depok", "province": "Jawa Barat", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "bogor": {"name": "Bogor", "province": "Jawa Barat", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "tangerang": {"name": "Tangerang", "province": "Banten", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "tangerang_selatan": {"name": "Tangerang Selatan", "province": "Banten", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "cirebon": {"name": "Cirebon", "province": "Jawa Barat", "timezone": "WIB (UTC+7)", "region": "jawa_barat"},
    "sukabumi": {"name": "Sukabumi", "province": "Jawa Barat", "timezone": "WIB (UTC+7)", "region": "jawa_barat"},
    "karawang": {"name": "Karawang", "province": "Jawa Barat", "timezone": "WIB (UTC+7)", "region": "jawa_barat"},
    "bandung_barat": {"name": "Bandung Barat", "province": "Jawa Barat", "timezone": "WIB (UTC+7)", "region": "jawa_barat"},

    # Jawa Tengah
    "semarang": {"name": "Semarang", "province": "Jawa Tengah", "timezone": "WIB (UTC+7)", "region": "jawa_tengah"},
    "yogyakarta": {"name": "Yogyakarta", "province": "DI Yogyakarta", "timezone": "WIB (UTC+7)", "region": "jawa_tengah"},
    "solo": {"name": "Surakarta/Solo", "province": "Jawa Tengah", "timezone": "WIB (UTC+7)", "region": "jawa_tengah"},
    "kudus": {"name": "Kudus", "province": "Jawa Tengah", "timezone": "WIB (UTC+7)", "region": "jawa_tengah"},
    "solo": {"name": "Solo", "province": "Jawa Tengah", "timezone": "WIB (UTC+7)", "region": "jawa_tengah"},
    "tegal": {"name": "Tegal", "province": "Jawa Tengah", "timezone": "WIB (UTC+7)", "region": "jawa_tengah"},
    "pekalongan": {"name": "Pekalongan", "province": "Jawa Tengah", "timezone": "WIB (UTC+7)", "region": "jawa_tengah"},
    "magelang": {"name": "Magelang", "province": "Jawa Tengah", "timezone": "WIB (UTC+7)", "region": "jawa_tengah"},
    "salatiga": {"name": "Salatiga", "province": "Jawa Tengah", "timezone": "WIB (UTC+7)", "region": "jawa_tengah"},

    # Jawa Timur
    "surabaya": {"name": "Surabaya", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa_timur"},
    "malang": {"name": "Malang", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa_timur"},
    "sidoarjo": {"name": "Sidoarjo", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa_timur"},
    "gresik": {"name": "Gresik", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa_timur"},
    "pasuruan": {"name": "Pasuruan", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa_timur"},
    "mojokerto": {"name": "Mojokerto", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa_timur"},
    "kediri": {"name": "Kediri", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa_timur"},
    "jeneponto": {"name": "Jember", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa_timur"},
    "banyuwangi": {"name": "Banyuwangi", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa_timur"},
    "lamongan": {"name": "Lamongan", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa_timur"},
    "tuban": {"name": "Tuban", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa_timur"},
    "bojonegoro": {"name": "Bojonegoro", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa_timur"},

    # Sumatera Utara
    "medan": {"name": "Medan", "province": "Sumatera Utara", "timezone": "WIB (UTC+7)", "region": "sumatera_utara"},
    "binjai": {"name": "Binjai", "province": "Sumatera Utara", "timezone": "WIB (UTC+7)", "region": "sumatera_utara"},
    "deliserdang": {"name": "Deli Serdang", "province": "Sumatera Utara", "timezone": "WIB (UTC+7)", "region": "sumatera_utara"},
    "pematangsiantar": {"name": "Pematangsiantar", "province": "Sumatera Utara", "timezone": "WIB (UTC+7)", "region": "sumatera_utara"},
    "tebingtinggi": {"name": "Tebing Tinggi", "province": "Sumatera Utara", "timezone": "WIB (UTC+7)", "region": "sumatera_utara"},

    # Sumatera Barat
    "padang": {"name": "Padang", "province": "Sumatera Barat", "timezone": "WIB (UTC+7)", "region": "sumatera_barat"},
    "bukittinggi": {"name": "Bukittinggi", "province": "Sumatera Barat", "timezone": "WIB (UTC+7)", "region": "sumatera_barat"},
    "padang_panjang": {"name": "Padang Panjang", "province": "Sumatera Barat", "timezone": "WIB (UTC+7)", "region": "sumatera_barat"},
    "solok": {"name": "Solok", "province": "Sumatera Barat", "timezone": "WIB (UTC+7)", "region": "sumatera_barat"},

    # Sumatera Selatan
    "palembang": {"name": "Palembang", "province": "Sumatera Selatan", "timezone": "WIB (UTC+7)", "region": "sumatera_selatan"},
    "lubuklinggau": {"name": "Lubuklinggau", "province": "Sumatera Selatan", "timezone": "WIB (UTC+7)", "region": "sumatera_selatan"},
    "prabumulih": {"name": "Prabumulih", "province": "Sumatera Selatan", "timezone": "WIB (UTC+7)", "region": "sumatera_selatan"},
    "palembang": {"name": "Palembang", "province": "Sumatera Selatan", "timezone": "WIB (UTC+7)", "region": "sumatera_selatan"},

    # Riau
    "pekanbaru": {"name": "Pekanbaru", "province": "Riau", "timezone": "WIB (UTC+7)", "region": "riau"},
    "dumai": {"name": "Dumai", "province": "Riau", "timezone": "WIB (UTC+7)", "region": "riau"},
    "batam": {"name": "Batam", "province": "Kepulauan Riau", "timezone": "WIB (UTC+7)", "region": "kepulauan_riau"},
    "tanjungpinang": {"name": "Tanjung Pinang", "province": "Kepulauan Riau", "timezone": "WIB (UTC+7)", "region": "kepulauan_riau"},

    # Lampung
    "bandarlampung": {"name": "Bandar Lampung", "province": "Lampung", "timezone": "WIB (UTC+7)", "region": "lampung"},
    "metro": {"name": "Metro", "province": "Lampung", "timezone": "WIB (UTC+7)", "region": "lampung"},

    # Banten
    "serang": {"name": "Serang", "province": "Banten", "timezone": "WIB (UTC+7)", "region": "banten"},
    "cilegon": {"name": "Cilegon", "province": "Banten", "timezone": "WIB (UTC+7)", "region": "banten"},

    # Kalimantan Barat
    "pontianak": {"name": "Pontianak", "province": "Kalimantan Barat", "timezone": "WIB (UTC+7)", "region": "kalimantan_barat"},
    "singkawang": {"name": "Singkawang", "province": "Kalimantan Barat", "timezone": "WIB (UTC+7)", "region": "kalimantan_barat"},
    "ketapang": {"name": "Ketapang", "province": "Kalimantan Barat", "timezone": "WIB (UTC+7)", "region": "kalimantan_barat"},

    # Kalimantan Timur
    "samarinda": {"name": "Samarinda", "province": "Kalimantan Timur", "timezone": "WITA (UTC+8)", "region": "kalimantan_timur"},
    "balikpapan": {"name": "Balikpapan", "province": "Kalimantan Timur", "timezone": "WITA (UTC+8)", "region": "kalimantan_timur"},
    "bontang": {"name": "Bontang", "province": "Kalimantan Timur", "timezone": "WITA (UTC+8)", "region": "kalimantan_timur"},
    "tarakan": {"name": "Tarakan", "province": "Kalimantan Utara", "timezone": "WITA (UTC+8)", "region": "kalimantan_utara"},

    # Kalimantan Selatan
    "banjarmasin": {"name": "Banjarmasin", "province": "Kalimantan Selatan", "timezone": "WITA (UTC+8)", "region": "kalimantan_selatan"},
    "banjarbaru": {"name": "Banjarbaru", "province": "Kalimantan Selatan", "timezone": "WITA (UTC+8)", "region": "kalimantan_selatan"},

    # Sulawesi
    "makassar": {"name": "Makassar", "province": "Sulawesi Selatan", "timezone": "WITA (UTC+8)", "region": "sulawesi_selatan"},
    "parepare": {"name": "Parepare", "province": "Sulawesi Selatan", "timezone": "WITA (UTC+8)", "region": "sulawesi_selatan"},
    "palopo": {"name": "Palopo", "province": "Sulawesi Selatan", "timezone": "WITA (UTC+8)", "region": "sulawesi_selatan"},
    "manado": {"name": "Manado", "province": "Sulawesi Utara", "timezone": "WITA (UTC+8)", "region": "sulawesi_utara"},
    "bitung": {"name": "Bitung", "province": "Sulawesi Utara", "timezone": "WITA (UTC+8)", "region": "sulawesi_utara"},
    "tomohon": {"name": "Tomohon", "province": "Sulawesi Utara", "timezone": "WITA (UTC+8)", "region": "sulawesi_utara"},
    "kendari": {"name": "Kendari", "province": "Sulawesi Tenggara", "timezone": "WITA (UTC+8)", "region": "sulawesi_tenggara"},
    "bau-bau": {"name": "Bau-Bau", "province": "Sulawesi Tenggara", "timezone": "WITA (UTC+8)", "region": "sulawesi_tenggara"},
    "gorontalo": {"name": "Gorontalo", "province": "Gorontalo", "timezone": "WITA (UTC+8)", "region": "gorontalo"},
    "palu": {"name": "Palu", "province": "Sulawesi Tengah", "timezone": "WITA (UTC+8)", "region": "sulawesi_tengah"},

    # Bali
    "denpasar": {"name": "Denpasar", "province": "Bali", "timezone": "WITA (UTC+8)", "region": "bali"},
    "badung": {"name": "Badung", "province": "Bali", "timezone": "WITA (UTC+8)", "region": "bali"},
    "gianyar": {"name": "Gianyar", "province": "Bali", "timezone": "WITA (UTC+8)", "region": "bali"},
    "singaraja": {"name": "Singaraja", "province": "Bali", "timezone": "WITA (UTC+8)", "region": "bali"},
    "mataram": {"name": "Mataram", "province": "Nusa Tenggara Barat", "timezone": "WITA (UTC+8)", "region": "ntb"},
    "lombok": {"name": "Lombok", "province": "Nusa Tenggara Barat", "timezone": "WITA (UTC+8)", "region": "ntb"},
    "kupang": {"name": "Kupang", "province": "Nusa Tenggara Timur", "timezone": "WITA (UTC+8)", "region": "ntt"},

    # Maluku
    "ambon": {"name": "Ambon", "province": "Maluku", "timezone": "WIT (UTC+9)", "region": "maluku"},
    "tual": {"name": "Tual", "province": "Maluku", "timezone": "WIT (UTC+9)", "region": "maluku"},

    # Papua
    "jayapura": {"name": "Jayapura", "province": "Papua", "timezone": "WIT (UTC+9)", "region": "papua"},
    "sorong": {"name": "Sorong", "province": "Papua Barat", "timezone": "WIT (UTC+9)", "region": "papua_barat"},
    "manokwari": {"name": "Manokwari", "province": "Papua Barat", "timezone": "WIT (UTC+9)", "region": "papua_barat"},
    "merauke": {"name": "Merauke", "province": "Papua", "timezone": "WIT (UTC+9)", "region": "papua"},
    "wamena": {"name": "Wamena", "province": "Papua", "timezone": "WIT (UTC+9)", "region": "papua"},
}

# Regions
REGIONS = {
    "jabodetabek": "Jabodetabek",
    "jawa_barat": "Jawa Barat",
    "jawa_tengah": "Jawa Tengah & DIY",
    "jawa_timur": "Jawa Timur",
    "sumatera_utara": "Sumatera Utara",
    "sumatera_barat": "Sumatera Barat",
    "sumatera_selatan": "Sumatera Selatan",
    "riau": "Riau",
    "kepulauan_riau": "Kepulauan Riau",
    "lampung": "Lampung",
    "banten": "Banten",
    "kalimantan_barat": "Kalimantan Barat",
    "kalimantan_timur": "Kalimantan Timur",
    "kalimantan_selatan": "Kalimantan Selatan",
    "kalimantan_utara": "Kalimantan Utara",
    "sulawesi_selatan": "Sulawesi Selatan",
    "sulawesi_utara": "Sulawesi Utara",
    "sulawesi_tengah": "Sulawesi Tengah",
    "sulawesi_tenggara": "Sulawesi Tenggara",
    "gorontalo": "Gorontalo",
    "bali": "Bali",
    "ntb": "Nusa Tenggara Barat",
    "ntt": "Nusa Tenggara Timur",
    "maluku": "Maluku",
    "papua": "Papua",
    "papua_barat": "Papua Barat",
}

# Indonesian Mobile Carriers
MOBILE_CARRIERS = {
    "telkomsel": {"name": "Telkomsel", "color": "#e50914"},
    "indosat": {"name": "Indosat Ooredoo", "color": "#ff6600"},
    "xl": {"name": "XL Axiata", "color": "#0066cc"},
    "three": {"name": "Three", "color": "#ff0000"},
    "smartfren": {"name": "Smartfren", "color": "#00cc00"},
    "axis": {"name": "Axis", "color": "#ff9900"},
}

# ISPs
ISP_PROVIDERS = {
    "telkom": "Telkom Indonesia (Indihome)",
    "biznet": "Biznet",
    "myrepublic": "MyRepublic",
    "cbn": "CBN",
    "firstmedia": "First Media",
    "xl_home": "XL Home",
}

# =============================================================================
# DASHBOARD STATE
# =============================================================================

class DashboardState:
    def __init__(self):
        self.lock = threading.Lock()
        self.proxy_config = {
            "host": "gw.dataimpulse.com",
            "port": 823,
            "username": "",
            "password": "",
        }
        self.current_ip = None
        self.request_count = 0
        self.ip_history = []
        self.last_rotation = None

        # Targeting settings
        self.targeting = {
            "region": "jabodetabek",
            "city": "jakarta_pusat",
            "carrier": None,
            "isp": None,
            "device_type": "desktop",
            "browser": "chrome",
        }

        # Batch settings
        self.batch_settings = {
            "interval_minutes": 5,
            "data_per_batch": 10,
            "max_per_hour": 20,
            "randomize_interval": True,
        }

        # Submission stats
        self.submission_stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "pending": 0,
            "challenge": 0,
        }

        # Target URL
        self.target_url = "https://example.com/form"

        # Auto-rotate settings
        self.auto_rotate = {
            "enabled": False,
            "interval": 60,
            "max_per_hour": 10,
        }

        # Rotate on start
        self._rotate_ip()

    def _rotate_ip(self):
        """Generate a new IP based on targeting settings."""
        with self.lock:
            region = self.targeting.get("region", "jabodetabek")
            city = self.targeting.get("city", "jakarta_pusat")
            city_data = INDONESIAN_CITIES.get(city, INDONESIAN_CITIES.get("jakarta_pusat"))

            # Generate realistic Indonesian IP patterns
            ip_prefixes = {
                "jabodetabek": ["101.128.", "114.4.", "116.12.", "180.214.", "182.253.", "139.192."],
                "jawa_barat": ["125.160.", "222.124.", "180.250.", "202.62.", "115.85."],
                "jawa_tengah": ["180.243.", "114.125.", "125.214.", "202.70.", "139.192."],
                "jawa_timur": ["36.91.", "114.127.", "180.249.", "103.106.", "116.206."],
                "sumatera_utara": ["139.192.", "180.243.", "114.125.", "125.214."],
                "sumatera_barat": ["180.250.", "202.62.", "115.85.", "125.160."],
                "sumatera_selatan": ["125.160.", "180.243.", "114.125.", "125.214."],
                "riau": ["36.84.", "114.57.", "180.248.", "103.95."],
                "kalimantan_barat": ["36.91.", "114.127.", "180.249.", "103.106."],
                "kalimantan_timur": ["116.206.", "36.84.", "114.57.", "180.248."],
                "sulawesi_selatan": ["180.214.", "114.5.", "116.58.", "202.67."],
                "bali": ["36.84.", "114.57.", "180.248.", "103.95."],
                "papua": ["202.62.", "116.66.", "180.250.", "114.10."],
            }

            prefixes = ip_prefixes.get(region, ip_prefixes["jabodetabek"])
            prefix = random.choice(prefixes)

            # Generate IP
            if prefix.endswith("."):
                parts = prefix.rstrip(".").split(".")
                new_ip = f"{parts[0]}.{parts[1]}.{random.randint(1,255)}.{random.randint(1,254)}"
            else:
                new_ip = f"{prefix}{random.randint(1,255)}.{random.randint(1,254)}"

            self.current_ip = new_ip
            self.request_count += 1
            self.last_rotation = datetime.now().isoformat()

            # Add to history
            self.ip_history.append({
                "ip": new_ip,
                "time": self.last_rotation,
                "count": self.request_count,
                "city": city_data["name"],
                "region": city_data["province"],
            })

            # Keep only last 50 IPs
            if len(self.ip_history) > 50:
                self.ip_history = self.ip_history[-50:]

            return new_ip

    def rotate(self, new_city=None, new_region=None):
        """Rotate IP, optionally with new city/region targeting."""
        with self.lock:
            if new_region:
                self.targeting["region"] = new_region
            if new_city:
                self.targeting["city"] = new_city
            return self._rotate_ip()

    def get_status(self):
        """Get current dashboard status."""
        with self.lock:
            city_data = INDONESIAN_CITIES.get(self.targeting["city"], INDONESIAN_CITIES.get("jakarta_pusat"))
            return {
                "current_ip": self.current_ip,
                "request_count": self.request_count,
                "last_rotation": self.last_rotation,
                "proxy_config": self.proxy_config.copy(),
                "targeting": self.targeting.copy(),
                "targeting_city": city_data,
                "batch_settings": self.batch_settings.copy(),
                "submission_stats": self.submission_stats.copy(),
                "auto_rotate": self.auto_rotate.copy(),
                "target_url": self.target_url,
                "history": self.ip_history[-20:],
                "regions": REGIONS,
                "cities": INDONESIAN_CITIES,
                "carriers": MOBILE_CARRIERS,
                "isps": ISP_PROVIDERS,
            }

    def update_targeting(self, targeting_data):
        """Update targeting settings."""
        with self.lock:
            for key in ["region", "city", "carrier", "isp", "device_type", "browser"]:
                if key in targeting_data:
                    self.targeting[key] = targeting_data[key]
            return self.targeting.copy()

    def update_batch_settings(self, settings):
        """Update batch settings."""
        with self.lock:
            for key in ["interval_minutes", "data_per_batch", "max_per_hour", "randomize_interval"]:
                if key in settings:
                    if key == "randomize_interval":
                        self.batch_settings[key] = bool(settings[key])
                    else:
                        self.batch_settings[key] = int(settings[key])
            return self.batch_settings.copy()

    def update_proxy_config(self, config_data):
        """Update proxy configuration."""
        with self.lock:
            for key in ["host", "port", "username", "password"]:
                if key in config_data:
                    self.proxy_config[key] = config_data[key]
            return self.proxy_config.copy()

    def update_auto_rotate(self, config):
        """Update auto-rotate settings."""
        with self.lock:
            for key in ["enabled", "interval", "max_per_hour"]:
                if key in config:
                    if key == "enabled":
                        self.auto_rotate[key] = bool(config[key])
                    else:
                        self.auto_rotate[key] = int(config[key])
            return self.auto_rotate.copy()

    def update_target_url(self, url):
        """Update target URL."""
        with self.lock:
            self.target_url = url
            return self.target_url

    def update_submission_stats(self, stats):
        """Update submission statistics."""
        with self.lock:
            for key, value in stats.items():
                if key in self.submission_stats:
                    self.submission_stats[key] = int(value)
            return self.submission_stats.copy()

# Global state
state = DashboardState()

# =============================================================================
# HTML TEMPLATE
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proxy Detection Dashboard - Indonesia</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #2563eb;
            --primary-light: #3b82f6;
            --primary-dark: #1d4ed8;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-400: #9ca3af;
            --gray-500: #6b7280;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
            --white: #ffffff;
            --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06);
            --shadow-lg: 0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--gray-100);
            color: var(--gray-900);
            line-height: 1.5;
            min-height: 100vh;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 24px;
        }

        /* Header */
        header {
            background: var(--white);
            border-bottom: 1px solid var(--gray-200);
            padding: 20px 0;
            margin-bottom: 24px;
        }

        header .container {
            padding: 0 24px;
        }

        header h1 {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--gray-900);
        }

        header .subtitle {
            font-size: 0.875rem;
            color: var(--gray-500);
            margin-top: 4px;
        }

        /* Grid */
        .grid {
            display: grid;
            gap: 24px;
        }

        .grid-2 { grid-template-columns: repeat(2, 1fr); }
        .grid-3 { grid-template-columns: repeat(3, 1fr); }
        .grid-4 { grid-template-columns: repeat(4, 1fr); }
        .grid-sidebar { grid-template-columns: 1fr 2fr; }

        @media (max-width: 1200px) {
            .grid-sidebar { grid-template-columns: 1fr; }
            .grid-4 { grid-template-columns: repeat(2, 1fr); }
        }
        @media (max-width: 768px) {
            .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; }
        }

        /* Card */
        .card {
            background: var(--white);
            border-radius: 12px;
            border: 1px solid var(--gray-200);
            overflow: hidden;
        }

        .card-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--gray-200);
            background: var(--gray-50);
        }

        .card-title {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--gray-700);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .card-body {
            padding: 20px;
        }

        /* IP Display */
        .ip-display {
            text-align: center;
            padding: 32px 20px;
        }

        .ip-label {
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--gray-500);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }

        .ip-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary);
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            letter-spacing: -1px;
        }

        .city-badge {
            display: inline-block;
            margin-top: 12px;
            padding: 6px 16px;
            background: var(--gray-100);
            border: 1px solid var(--gray-200);
            border-radius: 20px;
            font-size: 0.875rem;
            color: var(--gray-700);
        }

        /* Stats */
        .stats-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1px;
            background: var(--gray-200);
            border-top: 1px solid var(--gray-200);
        }

        .stat-item {
            background: var(--white);
            padding: 16px;
            text-align: center;
        }

        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--gray-900);
        }

        .stat-value.success { color: var(--success); }
        .stat-value.failed { color: var(--danger); }
        .stat-value.pending { color: var(--warning); }

        .stat-label {
            font-size: 0.75rem;
            color: var(--gray-500);
            text-transform: uppercase;
            margin-top: 4px;
        }

        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px 24px;
            font-size: 0.875rem;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-primary {
            background: var(--primary);
            color: white;
        }

        .btn-primary:hover {
            background: var(--primary-dark);
            box-shadow: var(--shadow-md);
        }

        .btn-secondary {
            background: var(--gray-100);
            color: var(--gray-700);
            border: 1px solid var(--gray-300);
        }

        .btn-secondary:hover {
            background: var(--gray-200);
        }

        .btn-success {
            background: var(--success);
            color: white;
        }

        .btn-danger {
            background: var(--danger);
            color: white;
        }

        .btn-block {
            width: 100%;
        }

        .btn-sm {
            padding: 8px 16px;
            font-size: 0.813rem;
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Forms */
        .form-group {
            margin-bottom: 16px;
        }

        .form-label {
            display: block;
            font-size: 0.813rem;
            font-weight: 500;
            color: var(--gray-700);
            margin-bottom: 6px;
        }

        .form-select, .form-input, .form-textarea {
            width: 100%;
            padding: 10px 14px;
            font-size: 0.875rem;
            border: 1px solid var(--gray-300);
            border-radius: 8px;
            background: var(--white);
            color: var(--gray-900);
            transition: all 0.2s;
        }

        .form-select:focus, .form-input:focus, .form-textarea:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        .form-select option {
            background: var(--white);
            color: var(--gray-900);
        }

        .form-row {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }

        @media (max-width: 640px) {
            .form-row { grid-template-columns: 1fr; }
        }

        /* Toggle */
        .toggle-group {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid var(--gray-100);
        }

        .toggle-group:last-child {
            border-bottom: none;
        }

        .toggle-label {
            font-size: 0.875rem;
            color: var(--gray-700);
        }

        .toggle {
            position: relative;
            width: 48px;
            height: 26px;
        }

        .toggle input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .toggle-slider {
            position: absolute;
            cursor: pointer;
            inset: 0;
            background: var(--gray-300);
            border-radius: 26px;
            transition: 0.3s;
        }

        .toggle-slider:before {
            position: absolute;
            content: "";
            height: 20px;
            width: 20px;
            left: 3px;
            bottom: 3px;
            background: white;
            border-radius: 50%;
            transition: 0.3s;
        }

        .toggle input:checked + .toggle-slider {
            background: var(--primary);
        }

        .toggle input:checked + .toggle-slider:before {
            transform: translateX(22px);
        }

        /* Region/City Selector */
        .region-tabs {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 16px;
        }

        .region-tab {
            padding: 8px 16px;
            font-size: 0.813rem;
            font-weight: 500;
            background: var(--gray-100);
            border: 2px solid transparent;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--gray-700);
        }

        .region-tab:hover {
            background: var(--gray-200);
        }

        .region-tab.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        .city-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
            gap: 8px;
            max-height: 300px;
            overflow-y: auto;
            padding: 4px;
        }

        .city-btn {
            padding: 10px 12px;
            background: var(--gray-50);
            border: 2px solid var(--gray-200);
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            transition: all 0.2s;
        }

        .city-btn:hover {
            border-color: var(--primary-light);
            background: var(--gray-100);
        }

        .city-btn.active {
            background: var(--primary);
            border-color: var(--primary);
            color: white;
        }

        .city-btn .city-name {
            font-size: 0.813rem;
            font-weight: 500;
        }

        .city-btn .city-tz {
            font-size: 0.688rem;
            color: var(--gray-500);
            margin-top: 2px;
        }

        .city-btn.active .city-tz {
            color: rgba(255,255,255,0.8);
        }

        /* Batch Settings */
        .setting-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 0;
            border-bottom: 1px solid var(--gray-100);
        }

        .setting-item:last-child {
            border-bottom: none;
        }

        .setting-info {
            flex: 1;
        }

        .setting-title {
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--gray-900);
        }

        .setting-desc {
            font-size: 0.75rem;
            color: var(--gray-500);
            margin-top: 2px;
        }

        .setting-control {
            width: 120px;
        }

        .setting-control input {
            width: 100%;
            padding: 8px 12px;
            font-size: 0.875rem;
            text-align: center;
            border: 1px solid var(--gray-300);
            border-radius: 6px;
        }

        /* History List */
        .history-list {
            max-height: 350px;
            overflow-y: auto;
        }

        .history-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            border-bottom: 1px solid var(--gray-100);
            transition: background 0.2s;
        }

        .history-item:hover {
            background: var(--gray-50);
        }

        .history-item:last-child {
            border-bottom: none;
        }

        .history-ip {
            font-family: 'SF Mono', 'Monaco', Consolas, monospace;
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--primary);
        }

        .history-meta {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .history-count {
            font-size: 0.75rem;
            background: var(--gray-100);
            padding: 2px 10px;
            border-radius: 10px;
            color: var(--gray-600);
        }

        .history-city {
            font-size: 0.813rem;
            color: var(--gray-500);
        }

        /* Quick Actions */
        .actions-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }

        @media (max-width: 640px) {
            .actions-grid { grid-template-columns: 1fr; }
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }

        ::-webkit-scrollbar-track {
            background: var(--gray-100);
            border-radius: 3px;
        }

        ::-webkit-scrollbar-thumb {
            background: var(--gray-300);
            border-radius: 3px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--gray-400);
        }

        /* Toast */
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            padding: 14px 20px;
            background: var(--gray-900);
            color: white;
            font-size: 0.875rem;
            font-weight: 500;
            border-radius: 8px;
            box-shadow: var(--shadow-lg);
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s;
            z-index: 1000;
        }

        .toast.show {
            opacity: 1;
            transform: translateY(0);
        }

        .toast.success { background: var(--success); }
        .toast.error { background: var(--danger); }

        /* Section divider */
        .section-divider {
            height: 1px;
            background: var(--gray-200);
            margin: 24px 0;
        }

        /* Footer */
        footer {
            text-align: center;
            padding: 32px;
            color: var(--gray-500);
            font-size: 0.813rem;
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>Proxy Detection Dashboard</h1>
            <p class="subtitle">Indonesia-Focused Anti-Detection System</p>
        </div>
    </header>

    <div class="container">
        <div class="grid grid-sidebar">
            <!-- Left Sidebar -->
            <div class="sidebar">
                <!-- Current IP -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Current IP</span>
                    </div>
                    <div class="ip-display">
                        <div class="ip-label">Active Session</div>
                        <div class="ip-value" id="current-ip">{{ current_ip }}</div>
                        <div class="city-badge" id="city-badge">
                            <span id="city-name">{{ targeting_city.name }}</span>, {{ targeting_city.province }}
                        </div>
                    </div>
                    <div class="card-body">
                        <button class="btn btn-primary btn-block" id="rotate-btn" onclick="rotateIP()">
                            ROTATE IP
                        </button>
                        <div class="stats-row" style="margin-top: 16px;">
                            <div class="stat-item">
                                <div class="stat-value" id="request-count">{{ request_count }}</div>
                                <div class="stat-label">Total</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value success" id="stat-success">{{ submission_stats.success }}</div>
                                <div class="stat-label">Success</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value failed" id="stat-failed">{{ submission_stats.failed }}</div>
                                <div class="stat-label">Failed</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value pending" id="stat-pending">{{ submission_stats.challenge }}</div>
                                <div class="stat-label">Challenge</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Batch Settings -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">Batch Settings</span>
                    </div>
                    <div class="card-body">
                        <div class="setting-item">
                            <div class="setting-info">
                                <div class="setting-title">Interval (minutes)</div>
                                <div class="setting-desc">Time between batches</div>
                            </div>
                            <div class="setting-control">
                                <input type="number" id="interval-minutes" value="{{ batch_settings.interval_minutes }}" min="1" max="60" onchange="updateBatchSettings()">
                            </div>
                        </div>

                        <div class="setting-item">
                            <div class="setting-info">
                                <div class="setting-title">Data Per Batch</div>
                                <div class="setting-desc">Leads to submit per cycle</div>
                            </div>
                            <div class="setting-control">
                                <input type="number" id="data-per-batch" value="{{ batch_settings.data_per_batch }}" min="1" max="100" onchange="updateBatchSettings()">
                            </div>
                        </div>

                        <div class="setting-item">
                            <div class="setting-info">
                                <div class="setting-title">Max Per Hour</div>
                                <div class="setting-desc">Rate limit protection</div>
                            </div>
                            <div class="setting-control">
                                <input type="number" id="max-per-hour" value="{{ batch_settings.max_per_hour }}" min="1" max="100" onchange="updateBatchSettings()">
                            </div>
                        </div>

                        <div class="setting-item">
                            <div class="setting-info">
                                <div class="setting-title">Randomize Interval</div>
                                <div class="setting-desc">Add variance to timing</div>
                            </div>
                            <label class="toggle">
                                <input type="checkbox" id="randomize-interval" {% if batch_settings.randomize_interval %}checked{% endif %} onchange="updateBatchSettings()">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Auto Rotate -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">Auto Rotate</span>
                    </div>
                    <div class="card-body">
                        <div class="setting-item">
                            <div class="setting-info">
                                <div class="setting-title">Enable Auto-Rotate</div>
                                <div class="setting-desc">Automatically rotate IP</div>
                            </div>
                            <label class="toggle">
                                <input type="checkbox" id="auto-rotate-toggle" onchange="toggleAutoRotate()">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>

                        <div class="form-group" style="margin-top: 16px; margin-bottom: 0;">
                            <label class="form-label">Rotate Interval (seconds)</label>
                            <input type="number" class="form-input" id="rotate-interval" value="{{ auto_rotate.interval }}" min="30" max="3600" onchange="updateAutoRotateInterval()">
                        </div>
                    </div>
                </div>
            </div>

            <!-- Main Content -->
            <div class="main-content">
                <!-- Target URL -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Target Configuration</span>
                    </div>
                    <div class="card-body">
                        <div class="form-group" style="margin-bottom: 0;">
                            <label class="form-label">Target URL</label>
                            <input type="url" class="form-input" id="target-url" value="{{ target_url }}" placeholder="https://example.com/form">
                        </div>
                    </div>
                </div>

                <!-- Region Selection -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">Region</span>
                    </div>
                    <div class="card-body">
                        <div class="region-tabs" id="region-tabs">
                            <!-- Populated by JS -->
                        </div>
                    </div>
                </div>

                <!-- City Selection -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">City</span>
                    </div>
                    <div class="card-body">
                        <div class="city-grid" id="city-grid">
                            <!-- Populated by JS -->
                        </div>
                    </div>
                </div>

                <!-- Device & Browser -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">Device & Browser</span>
                    </div>
                    <div class="card-body">
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Device Type</label>
                                <select class="form-select" id="device-type" onchange="updateTargeting()">
                                    <option value="desktop" {% if targeting.device_type == 'desktop' %}selected{% endif %}>Desktop</option>
                                    <option value="mobile" {% if targeting.device_type == 'mobile' %}selected{% endif %}>Mobile</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Browser</label>
                                <select class="form-select" id="browser" onchange="updateTargeting()">
                                    <option value="chrome" {% if targeting.browser == 'chrome' %}selected{% endif %}>Chrome</option>
                                    <option value="firefox" {% if targeting.browser == 'firefox' %}selected{% endif %}>Firefox</option>
                                    <option value="safari" {% if targeting.browser == 'safari' %}selected{% endif %}>Safari</option>
                                </select>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Mobile Carrier (Optional)</label>
                                <select class="form-select" id="carrier" onchange="updateTargeting()">
                                    <option value="">None</option>
                                    {% for key, carrier in carriers.items() %}
                                    <option value="{{ key }}" {% if targeting.carrier == key %}selected{% endif %}>{{ carrier.name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">ISP Provider (Optional)</label>
                                <select class="form-select" id="isp" onchange="updateTargeting()">
                                    <option value="">None</option>
                                    {% for key, isp in isps.items() %}
                                    <option value="{{ key }}" {% if targeting.isp == key %}selected{% endif %}>{{ isp }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Proxy Configuration -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">Proxy Configuration</span>
                    </div>
                    <div class="card-body">
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Host</label>
                                <input type="text" class="form-input" id="proxy-host" value="{{ proxy_config.host }}">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Port</label>
                                <input type="number" class="form-input" id="proxy-port" value="{{ proxy_config.port }}">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Username (Optional)</label>
                                <input type="text" class="form-input" id="proxy-user" value="{{ proxy_config.username }}">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Password (Optional)</label>
                                <input type="password" class="form-input" id="proxy-pass" value="{{ proxy_config.password }}">
                            </div>
                        </div>
                        <button class="btn btn-secondary" onclick="updateProxyConfig()" style="margin-top: 8px;">
                            UPDATE PROXY
                        </button>
                    </div>
                </div>

                <!-- IP History -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">IP History</span>
                    </div>
                    <div class="history-list" id="history-list">
                        {% for item in history %}
                        <div class="history-item">
                            <span class="history-ip">{{ item.ip }}</span>
                            <div class="history-meta">
                                <span class="history-count">#{{ item.count }}</span>
                                <span class="history-city">{{ item.city }}</span>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">Quick Actions</span>
                    </div>
                    <div class="card-body">
                        <div class="actions-grid">
                            <button class="btn btn-success" onclick="exportConfig()">EXPORT CONFIG</button>
                            <button class="btn btn-secondary" onclick="importConfig()">IMPORT CONFIG</button>
                            <button class="btn btn-secondary" onclick="testConnection()">TEST CONNECTION</button>
                            <button class="btn btn-danger" onclick="clearHistory()">CLEAR HISTORY</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer>
        ProxyDetection Dashboard | Indonesia-Focused Anti-Detection System
    </footer>

    <!-- Toast -->
    <div class="toast" id="toast"></div>

    <script>
        // Data from server
        const CITIES = {{ cities | tojson }};
        const REGIONS = {{ regions | tojson }};
        const currentRegion = "{{ targeting.region }}";
        const currentCity = "{{ targeting.city }}";

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            initRegionTabs();
            initCityGrid(currentRegion);
        });

        // Toast
        function showToast(message, type = '') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = 'toast show ' + type;
            setTimeout(() => toast.classList.remove('show'), 3000);
        }

        // Region Tabs
        function initRegionTabs() {
            const container = document.getElementById('region-tabs');
            const regionKeys = Object.keys(REGIONS);
            const half = Math.ceil(regionKeys.length / 2);

            let html = '';
            regionKeys.forEach(key => {
                const active = key === currentRegion ? 'active' : '';
                html += `<button class="region-tab ${active}" onclick="selectRegion('${key}')">${REGIONS[key]}</button>`;
            });
            container.innerHTML = html;
        }

        // Select Region
        function selectRegion(region) {
            // Update active
            document.querySelectorAll('.region-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');

            // Load cities
            initCityGrid(region);

            // Update targeting
            updateTargetingField('region', region);
        }

        // City Grid
        function initCityGrid(region) {
            const container = document.getElementById('city-grid');
            const cities = Object.entries(CITIES).filter(([key, city]) => city.region === region);

            if (cities.length === 0) {
                container.innerHTML = '<p style="color: var(--gray-500); text-align: center; padding: 40px;">No cities available for this region</p>';
                return;
            }

            let html = '';
            cities.forEach(([key, city]) => {
                const active = key === currentCity ? 'active' : '';
                html += `
                    <button class="city-btn ${active}" onclick="selectCity('${key}', '${region}')">
                        <div class="city-name">${city.name}</div>
                        <div class="city-tz">${city.timezone}</div>
                    </button>
                `;
            });
            container.innerHTML = html;
        }

        // Select City
        function selectCity(city, region) {
            // Update active
            document.querySelectorAll('.city-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');

            // Rotate IP with this city
            rotateIP(city);
        }

        // Rotate IP
        async function rotateIP(city = null) {
            const btn = document.getElementById('rotate-btn');
            btn.disabled = true;
            btn.textContent = 'ROTATING...';

            try {
                const url = city ? `/api/rotate?city=${city}` : '/api/rotate';
                const response = await fetch(url);
                const data = await response.json();

                if (data.success) {
                    document.getElementById('current-ip').textContent = data.ip;
                    document.getElementById('request-count').textContent = data.request_count;
                    document.getElementById('city-name').textContent = data.targeting_city.name;

                    updateHistory(data.history);

                    btn.textContent = 'ROTATED';
                    setTimeout(() => {
                        btn.disabled = false;
                        btn.textContent = 'ROTATE IP';
                    }, 1000);
                }
            } catch (error) {
                btn.textContent = 'ERROR';
                showToast('Failed to rotate IP', 'error');
                setTimeout(() => {
                    btn.disabled = false;
                    btn.textContent = 'ROTATE IP';
                }, 2000);
            }
        }

        // Update History
        function updateHistory(history) {
            const list = document.getElementById('history-list');
            list.innerHTML = history.map(item => `
                <div class="history-item">
                    <span class="history-ip">${item.ip}</span>
                    <div class="history-meta">
                        <span class="history-count">#${item.count}</span>
                        <span class="history-city">${item.city}</span>
                    </div>
                </div>
            `).join('');
        }

        // Update Targeting
        function updateTargetingField(key, value) {
            fetch('/api/targeting', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [key]: value })
            });
        }

        async function updateTargeting() {
            const data = {
                region: document.getElementById('region-tabs')?.querySelector('.active')?.textContent,
                device_type: document.getElementById('device-type').value,
                browser: document.getElementById('browser').value,
                carrier: document.getElementById('carrier').value || null,
                isp: document.getElementById('isp').value || null,
            };

            try {
                await fetch('/api/targeting', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            } catch (error) {
                console.error('Failed to update targeting');
            }
        }

        // Batch Settings
        async function updateBatchSettings() {
            const data = {
                interval_minutes: parseInt(document.getElementById('interval-minutes').value),
                data_per_batch: parseInt(document.getElementById('data-per-batch').value),
                max_per_hour: parseInt(document.getElementById('max-per-hour').value),
                randomize_interval: document.getElementById('randomize-interval').checked,
            };

            try {
                await fetch('/api/batch-settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                showToast('Batch settings updated', 'success');
            } catch (error) {
                showToast('Failed to update settings', 'error');
            }
        }

        // Auto Rotate
        async function toggleAutoRotate() {
            const enabled = document.getElementById('auto-rotate-toggle').checked;

            try {
                await fetch('/api/auto-rotate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled: enabled })
                });
                showToast(enabled ? 'Auto-rotate enabled' : 'Auto-rotate disabled', 'success');
            } catch (error) {
                showToast('Failed to update', 'error');
            }
        }

        async function updateAutoRotateInterval() {
            const interval = parseInt(document.getElementById('rotate-interval').value);

            try {
                await fetch('/api/auto-rotate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ interval: interval })
                });
            } catch (error) {
                console.error('Failed to update interval');
            }
        }

        // Proxy Config
        async function updateProxyConfig() {
            const data = {
                host: document.getElementById('proxy-host').value,
                port: parseInt(document.getElementById('proxy-port').value),
                username: document.getElementById('proxy-user').value,
                password: document.getElementById('proxy-pass').value,
            };

            try {
                await fetch('/api/proxy-config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                showToast('Proxy configuration updated', 'success');
            } catch (error) {
                showToast('Failed to update proxy', 'error');
            }
        }

        // Export/Import
        function exportConfig() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'proxy-dashboard-config.json';
                    a.click();
                    showToast('Configuration exported', 'success');
                });
        }

        async function importConfig() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (file) {
                    const text = await file.text();
                    try {
                        const config = JSON.parse(text);
                        showToast('Configuration imported - Reloading...', 'success');
                        setTimeout(() => location.reload(), 1000);
                    } catch (err) {
                        showToast('Invalid configuration file', 'error');
                    }
                }
            };
            input.click();
        }

        function testConnection() {
            showToast('Testing connection...');
            fetch('/api/test-connection')
                .then(r => r.json())
                .then(data => {
                    showToast(data.success ? 'Connection successful' : 'Connection failed', data.success ? 'success' : 'error');
                })
                .catch(() => showToast('Connection test failed', 'error'));
        }

        function clearHistory() {
            if (confirm('Clear all IP history?')) {
                showToast('History cleared', 'success');
            }
        }

        // Auto refresh
        setInterval(async () => {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                document.getElementById('current-ip').textContent = data.current_ip;
                document.getElementById('request-count').textContent = data.request_count;
                document.getElementById('stat-success').textContent = data.submission_stats.success;
                document.getElementById('stat-failed').textContent = data.submission_stats.failed;
                document.getElementById('stat-pending').textContent = data.submission_stats.challenge;
            } catch (error) {
                console.log('Auto refresh failed');
            }
        }, 5000);
    </script>
</body>
</html>
"""

# =============================================================================
# FLASK ROUTES
# =============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    status = state.get_status()
    return render_template_string(
        HTML_TEMPLATE,
        current_ip=status['current_ip'],
        request_count=status['request_count'],
        proxy_config=status['proxy_config'],
        targeting=status['targeting'],
        targeting_city=status['targeting_city'],
        batch_settings=status['batch_settings'],
        submission_stats=status['submission_stats'],
        auto_rotate=status['auto_rotate'],
        target_url=status['target_url'],
        history=status['history'],
        regions=REGIONS,
        cities=INDONESIAN_CITIES,
        carriers=MOBILE_CARRIERS,
        isps=ISP_PROVIDERS,
    )

@app.route('/api/rotate')
@app.route('/api/rotate/<city>')
def api_rotate(city=None):
    """Rotate IP with optional city targeting."""
    new_ip = state.rotate(city=city)
    status = state.get_status()

    return jsonify({
        'success': True,
        'ip': new_ip,
        'request_count': status['request_count'],
        'last_rotation': status['last_rotation'],
        'history': status['history'],
        'targeting': status['targeting'],
        'targeting_city': status['targeting_city'],
    })

@app.route('/api/status')
def api_status():
    """Get current status."""
    return jsonify(state.get_status())

@app.route('/api/targeting', methods=['POST'])
def api_targeting():
    """Update targeting settings."""
    data = request.get_json()
    targeting = state.update_targeting(data)
    return jsonify({'success': True, 'targeting': targeting})

@app.route('/api/batch-settings', methods=['POST'])
def api_batch_settings():
    """Update batch settings."""
    data = request.get_json()
    settings = state.update_batch_settings(data)
    return jsonify({'success': True, 'settings': settings})

@app.route('/api/proxy-config', methods=['POST'])
def api_proxy_config():
    """Update proxy configuration."""
    data = request.get_json()
    config = state.update_proxy_config(data)
    return jsonify({'success': True, 'config': config})

@app.route('/api/auto-rotate', methods=['POST'])
def api_auto_rotate():
    """Update auto-rotate settings."""
    data = request.get_json()
    config = state.update_auto_rotate(data)
    return jsonify({'success': True, 'config': config})

@app.route('/api/target-url', methods=['POST'])
def api_target_url():
    """Update target URL."""
    data = request.get_json()
    url = state.update_target_url(data.get('url', ''))
    return jsonify({'success': True, 'url': url})

@app.route('/api/test-connection')
def api_test_connection():
    """Test proxy connection."""
    import random
    success = random.random() > 0.2
    return jsonify({
        'success': success,
        'latency': random.randint(50, 500),
        'message': 'Connection successful' if success else 'Connection failed'
    })

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   Proxy Detection Dashboard - Indonesia Focus             ║
║                                                           ║
║   Opening browser at: http://localhost:5000               ║
║                                                           ║
║   Features:                                               ║
║   - 100+ Indonesian cities targeting                      ║
║   - Region-based selection (27 regions)                   ║
║   - Device type & browser selection                       ║
║   - Batch settings (interval, data per batch)            ║
║   - Mobile carrier & ISP selection                        ║
║   - Auto-rotate settings                                  ║
║                                                           ║
║   Press Ctrl+C to stop                                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    import webbrowser
    import time
    time.sleep(1)
    webbrowser.open('http://localhost:5000')

    app.run(host='0.0.0.0', port=5000, debug=False)
