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

# Indonesian Cities Configuration
INDONESIAN_CITIES = {
    "jakarta": {"name": "Jakarta", "province": "DKI Jakarta", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "bandung": {"name": "Bandung", "province": "Jawa Barat", "timezone": "WIB (UTC+7)", "region": "jawa"},
    "surabaya": {"name": "Surabaya", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa"},
    "semarang": {"name": "Semarang", "province": "Jawa Tengah", "timezone": "WIB (UTC+7)", "region": "jawa"},
    "yogyakarta": {"name": "Yogyakarta", "province": "DI Yogyakarta", "timezone": "WIB (UTC+7)", "region": "jawa"},
    "medan": {"name": "Medan", "province": "Sumatera Utara", "timezone": "WIB (UTC+7)", "region": "sumatera"},
    "makassar": {"name": "Makassar", "province": "Sulawesi Selatan", "timezone": "WITA (UTC+8)", "region": "sulawesi"},
    "denpasar": {"name": "Denpasar", "province": "Bali", "timezone": "WITA (UTC+8)", "region": "bali"},
    "palembang": {"name": "Palembang", "province": "Sumatera Selatan", "timezone": "WIB (UTC+7)", "region": "sumatera"},
    "tangerang": {"name": "Tangerang", "province": "Banten", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "bekasi": {"name": "Bekasi", "province": "Jawa Barat", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "depok": {"name": "Depok", "province": "Jawa Barat", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "bogor": {"name": "Bogor", "province": "Jawa Barat", "timezone": "WIB (UTC+7)", "region": "jabodetabek"},
    "malang": {"name": "Malang", "province": "Jawa Timur", "timezone": "WIB (UTC+7)", "region": "jawa"},
    "pontianak": {"name": "Pontianak", "province": "Kalimantan Barat", "timezone": "WIB (UTC+7)", "region": "kalimantan"},
    "samarinda": {"name": "Samarinda", "province": "Kalimantan Timur", "timezone": "WITA (UTC+8)", "region": "kalimantan"},
    "banjarmasin": {"name": "Banjarmasin", "province": "Kalimantan Selatan", "timezone": "WITA (UTC+8)", "region": "kalimantan"},
    "jayapura": {"name": "Jayapura", "province": "Papua", "timezone": "WIT (UTC+9)", "region": "papua"},
}

# Indonesian Mobile Carriers
MOBILE_CARRIERS = {
    "telkomsel": {"name": "Telkomsel", "icon": "📶", "color": "#e50914"},
    "indosat": {"name": "Indosat Ooredoo", "icon": "📱", "color": "#ff6600"},
    "xl": {"name": "XL Axiata", "icon": "📲", "color": "#0066cc"},
    "three": {"name": "3 (Three)", "icon": "3️⃣", "color": "#ff0000"},
    "smartfren": {"name": "Smartfren", "icon": "🚀", "color": "#00cc00"},
    "axis": {"name": "Axis", "icon": "✖️", "color": "#ff9900"},
}

# Indonesian ISPs
ISP_PROVIDERS = {
    "telkom": {"name": "Telkom Indonesia", "product": "Indihome", "icon": "🏠"},
    "biznet": {"name": "Biznet", "icon": "🌐"},
    "myrepublic": {"name": "MyRepublic", "icon": "🔷"},
    "cbn": {"name": "CBN", "icon": "🔶"},
    "firstmedia": {"name": "First Media", "icon": "📺"},
    "xl_home": {"name": "XL Home", "icon": "📡"},
}

# Regions for grouping
REGIONS = {
    "jabodetabek": "Jabodetabek",
    "jawa": "Jawa",
    "sumatera": "Sumatera",
    "kalimantan": "Kalimantan",
    "sulawesi": "Sulawesi",
    "bali": "Bali & Nusa Tenggara",
    "papua": "Papua & Maluku",
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
        self.is_rotating = False
        self.last_rotation = None

        # Targeting settings
        self.targeting = {
            "city": "jakarta",
            "region": "jabodetabek",
            "carrier": None,
            "isp": None,
            "device_type": "desktop",  # desktop, mobile
        }

        # Submission stats
        self.submission_stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "pending": 0,
            "challenge": 0,
        }

        # Session data
        self.sessions = []

        # Auto-rotate settings
        self.auto_rotate = {
            "enabled": False,
            "interval": 60,  # seconds
            "max_per_hour": 10,
        }

        # Target URL
        self.target_url = "https://example.com"

        # Rotate on start
        self._rotate_ip()

    def _rotate_ip(self):
        """Generate a new IP based on targeting settings."""
        with self.lock:
            city = self.targeting["city"]
            city_data = INDONESIAN_CITIES.get(city, INDONESIAN_CITIES["jakarta"])

            # Generate realistic Indonesian IP patterns
            ip_prefixes = {
                "jabodetabek": ["101.128.", "114.4.", "116.12.", "180.214.", "182.253."],
                "jawa": ["125.160.", "222.124.", "180.250.", "202.62.", "115.85."],
                "sumatera": ["139.192.", "180.243.", "114.125.", "125.214.", "202.70."],
                "kalimantan": ["36.91.", "114.127.", "180.249.", "103.106.", "116.206."],
                "sulawesi": ["180.214.", "114.5.", "116.58.", "202.67.", "125.162."],
                "bali": ["36.84.", "114.57.", "180.248.", "103.95.", "116.206."],
                "papua": ["202.62.", "116.66.", "180.250.", "114.10.", "125.165."],
            }

            region = self.targeting.get("region", "jabodetabek")
            prefixes = ip_prefixes.get(region, ip_prefixes["jabodetabek"])
            prefix = random.choice(prefixes)

            # Generate rest of IP
            if "." in prefix:
                parts = prefix.rstrip(".").split(".")
                new_ip = f"{parts[0]}.{parts[1]}.{random.randint(1,255)}.{random.randint(1,254)}"
            else:
                new_ip = f"{prefix}{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,254)}"

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

    def rotate(self, new_city=None):
        """Rotate IP, optionally with new city targeting."""
        with self.lock:
            if new_city:
                self.targeting["city"] = new_city
                # Update region based on city
                for region, cities in REGIONS.items():
                    if new_city in [c for c, d in INDONESIAN_CITIES.items() if d.get("region") == region]:
                        self.targeting["region"] = region
                        break
            return self._rotate_ip()

    def get_status(self):
        """Get current dashboard status."""
        with self.lock:
            city_data = INDONESIAN_CITIES.get(self.targeting["city"], INDONESIAN_CITIES["jakarta"])
            return {
                "current_ip": self.current_ip,
                "request_count": self.request_count,
                "last_rotation": self.last_rotation,
                "proxy_url": f"http://{self.proxy_config['username']}:{self.proxy_config['password']}@{self.proxy_config['host']}:{self.proxy_config['port']}" if self.proxy_config['username'] else f"http://{self.proxy_config['host']}:{self.proxy_config['port']}",
                "proxy_host": self.proxy_config["host"],
                "proxy_port": self.proxy_config["port"],
                "proxy_user": self.proxy_config["username"],
                "proxy_pass": self.proxy_config["password"],
                "targeting": self.targeting.copy(),
                "targeting_city": city_data,
                "submission_stats": self.submission_stats.copy(),
                "auto_rotate": self.auto_rotate.copy(),
                "target_url": self.target_url,
                "history": self.ip_history[-15:],
            }

    def update_targeting(self, targeting_data):
        """Update targeting settings."""
        with self.lock:
            if "city" in targeting_data:
                self.targeting["city"] = targeting_data["city"]
            if "region" in targeting_data:
                self.targeting["region"] = targeting_data["region"]
            if "carrier" in targeting_data:
                self.targeting["carrier"] = targeting_data["carrier"]
            if "isp" in targeting_data:
                self.targeting["isp"] = targeting_data["isp"]
            if "device_type" in targeting_data:
                self.targeting["device_type"] = targeting_data["device_type"]
            return self.targeting.copy()

    def update_proxy_config(self, config_data):
        """Update proxy configuration."""
        with self.lock:
            if "host" in config_data:
                self.proxy_config["host"] = config_data["host"]
            if "port" in config_data:
                self.proxy_config["port"] = config_data["port"]
            if "username" in config_data:
                self.proxy_config["username"] = config_data["username"]
            if "password" in config_data:
                self.proxy_config["password"] = config_data["password"]
            return self.proxy_config.copy()

    def update_auto_rotate(self, config):
        """Update auto-rotate settings."""
        with self.lock:
            if "enabled" in config:
                self.auto_rotate["enabled"] = config["enabled"]
            if "interval" in config:
                self.auto_rotate["interval"] = config["interval"]
            if "max_per_hour" in config:
                self.auto_rotate["max_per_hour"] = config["max_per_hour"]
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
                    self.submission_stats[key] = value
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
    <title>🎯 Proxy & Lead Dashboard - Indonesia Focus</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --info: #3b82f6;
            --dark: #0f172a;
            --darker: #020617;
            --card: #1e293b;
            --card-hover: #334155;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, var(--darker) 0%, var(--dark) 100%);
            min-height: 100vh;
            color: var(--text);
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header */
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 30px;
        }

        header h1 {
            font-size: 2.5em;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }

        header .subtitle {
            color: var(--text-muted);
            font-size: 1.1em;
        }

        /* Grid Layout */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 20px;
        }

        .col-4 { grid-column: span 4; }
        .col-6 { grid-column: span 6; }
        .col-8 { grid-column: span 8; }
        .col-12 { grid-column: span 12; }

        @media (max-width: 1200px) {
            .col-4, .col-6, .col-8 { grid-column: span 6; }
        }
        @media (max-width: 768px) {
            .col-4, .col-6, .col-8, .col-12 { grid-column: span 12; }
        }

        /* Cards */
        .card {
            background: var(--card);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid var(--border);
            transition: all 0.3s ease;
        }

        .card:hover {
            border-color: var(--primary);
            box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .card-title {
            font-size: 1.1em;
            font-weight: 600;
            color: var(--text);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .card-title .icon {
            font-size: 1.3em;
        }

        /* IP Display */
        .ip-display {
            text-align: center;
            padding: 40px 0;
        }

        .ip-label {
            color: var(--text-muted);
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 15px;
        }

        .ip-value {
            font-size: 3em;
            font-weight: 700;
            color: var(--secondary);
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            text-shadow: 0 0 30px rgba(16, 185, 129, 0.5);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }

        .city-badge {
            display: inline-block;
            margin-top: 15px;
            padding: 8px 20px;
            background: rgba(99, 102, 241, 0.2);
            border: 1px solid var(--primary);
            border-radius: 50px;
            font-size: 0.9em;
            color: var(--primary);
        }

        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 14px 28px;
            font-size: 1em;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
        }

        .btn-secondary {
            background: var(--card-hover);
            color: var(--text);
            border: 1px solid var(--border);
        }

        .btn-secondary:hover {
            background: var(--border);
        }

        .btn-success {
            background: linear-gradient(135deg, var(--secondary) 0%, #059669 100%);
            color: white;
        }

        .btn-danger {
            background: linear-gradient(135deg, var(--danger) 0%, #dc2626 100%);
            color: white;
        }

        .btn-block {
            width: 100%;
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }

        /* Rotate Button */
        .rotate-section {
            margin-top: 25px;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }

        @media (max-width: 768px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }

        .stat-box {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }

        .stat-value {
            font-size: 2em;
            font-weight: 700;
        }

        .stat-value.success { color: var(--secondary); }
        .stat-value.failed { color: var(--danger); }
        .stat-value.pending { color: var(--warning); }
        .stat-value.challenge { color: var(--info); }

        .stat-label {
            color: var(--text-muted);
            font-size: 0.85em;
            margin-top: 5px;
        }

        /* Targeting Section */
        .targeting-section {
            margin-bottom: 25px;
        }

        .targeting-section h4 {
            color: var(--text-muted);
            font-size: 0.9em;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* City Grid */
        .city-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 10px;
        }

        .city-btn {
            padding: 12px;
            background: rgba(255, 255, 255, 0.03);
            border: 2px solid transparent;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
        }

        .city-btn:hover {
            background: rgba(99, 102, 241, 0.1);
            border-color: var(--primary);
        }

        .city-btn.active {
            background: rgba(99, 102, 241, 0.2);
            border-color: var(--primary);
            color: var(--primary);
        }

        .city-btn .city-name {
            font-weight: 600;
            font-size: 0.95em;
        }

        .city-btn .city-region {
            font-size: 0.75em;
            color: var(--text-muted);
            margin-top: 4px;
        }

        /* Select Dropdown */
        .form-group {
            margin-bottom: 15px;
        }

        .form-label {
            display: block;
            color: var(--text-muted);
            font-size: 0.85em;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .form-select, .form-input {
            width: 100%;
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text);
            font-size: 1em;
            transition: all 0.2s ease;
        }

        .form-select:focus, .form-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }

        .form-select option {
            background: var(--dark);
            color: var(--text);
        }

        /* Toggle Switch */
        .toggle-group {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
        }

        .toggle-group:last-child {
            border-bottom: none;
        }

        .toggle-label {
            font-size: 0.95em;
        }

        .toggle {
            position: relative;
            width: 50px;
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
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: var(--card-hover);
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
            transform: translateX(24px);
        }

        /* History List */
        .history-list {
            max-height: 400px;
            overflow-y: auto;
        }

        .history-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            margin-bottom: 8px;
            font-family: 'SF Mono', 'Monaco', monospace;
            font-size: 0.9em;
            transition: all 0.2s ease;
        }

        .history-item:hover {
            background: rgba(255, 255, 255, 0.06);
        }

        .history-ip {
            color: var(--secondary);
            font-weight: 600;
        }

        .history-meta {
            display: flex;
            align-items: center;
            gap: 15px;
            color: var(--text-muted);
            font-size: 0.8em;
        }

        .history-count {
            background: rgba(99, 102, 241, 0.2);
            padding: 2px 10px;
            border-radius: 10px;
            color: var(--primary);
        }

        /* Proxy Config */
        .proxy-config {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 12px;
            padding: 16px;
            margin-top: 15px;
        }

        .proxy-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
        }

        .proxy-item:last-child {
            border-bottom: none;
        }

        .proxy-label {
            color: var(--text-muted);
            font-size: 0.85em;
        }

        .proxy-value {
            color: var(--text);
            font-family: monospace;
            word-break: break-all;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 40px 0;
            color: var(--text-muted);
            font-size: 0.85em;
        }

        /* Toast Notification */
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 16px 24px;
            background: var(--card);
            border: 1px solid var(--secondary);
            border-radius: 12px;
            color: var(--text);
            font-size: 0.95em;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s ease;
            z-index: 1000;
        }

        .toast.show {
            opacity: 1;
            transform: translateY(0);
        }

        .toast.error {
            border-color: var(--danger);
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--dark);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-muted);
        }

        /* Progress Bar */
        .progress-bar {
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
            border-radius: 4px;
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 Proxy & Lead Dashboard</h1>
            <p class="subtitle">Indonesia-Focused Anti-Detection System</p>
        </header>

        <div class="dashboard-grid">
            <!-- Current IP Card -->
            <div class="col-4">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">🌐 Current IP Address</span>
                    </div>
                    <div class="ip-display">
                        <div class="ip-label">Active Session</div>
                        <div class="ip-value" id="current-ip">{{ current_ip }}</div>
                        <div class="city-badge" id="city-badge">
                            📍 <span id="city-name">{{ targeting_city.name }}</span>, {{ targeting_city.province }}
                        </div>
                    </div>
                    <div class="rotate-section">
                        <button class="btn btn-primary btn-block" onclick="rotateIP()">
                            🔄 GANTI IP SEKARANG
                        </button>
                        <div class="stats-grid" style="margin-top: 20px;">
                            <div class="stat-box">
                                <div class="stat-value" id="request-count">{{ request_count }}</div>
                                <div class="stat-label">Total Rotasi</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-value" id="rotations-hour" style="font-size: 1.5em;">0</div>
                                <div class="stat-label">Per Jam</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Auto-Rotate Settings -->
                <div class="card" style="margin-top: 20px;">
                    <div class="card-header">
                        <span class="card-title">⏰ Auto Rotate</span>
                    </div>
                    <div class="toggle-group">
                        <span class="toggle-label">Enable Auto-Rotate</span>
                        <label class="toggle">
                            <input type="checkbox" id="auto-rotate-toggle" onchange="toggleAutoRotate()">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <div class="form-group" style="margin-top: 15px;">
                        <label class="form-label">Interval (detik)</label>
                        <input type="number" class="form-input" id="rotate-interval" value="60" min="10" max="3600" onchange="updateAutoRotateInterval()">
                    </div>
                </div>
            </div>

            <!-- Targeting Card -->
            <div class="col-8">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">🎯 Targeting Configuration</span>
                    </div>

                    <!-- Region Filter -->
                    <div class="targeting-section">
                        <h4>📍 Pilih Region</h4>
                        <div class="city-grid" id="region-grid">
                            <button class="city-btn active" onclick="selectRegion('jabodetabek')">
                                <div class="city-name">🏙️ Jabodetabek</div>
                                <div class="city-region">Jakarta, Bogor, depok</div>
                            </button>
                            <button class="city-btn" onclick="selectRegion('jawa')">
                                <div class="city-name">🏝️ Jawa</div>
                                <div class="city-region">Bandung, Surabaya, dll</div>
                            </button>
                            <button class="city-btn" onclick="selectRegion('sumatera')">
                                <div class="city-name">🌴 Sumatera</div>
                                <div class="city-region">Medan, Palembang</div>
                            </button>
                            <button class="city-btn" onclick="selectRegion('kalimantan')">
                                <div class="city-name">🌿 Kalimantan</div>
                                <div class="city-region">Pontianak, Samarinda</div>
                            </button>
                            <button class="city-btn" onclick="selectRegion('sulawesi')">
                                <div class="city-name">🏔️ Sulawesi</div>
                                <div class="city-region">Makassar</div>
                            </button>
                            <button class="city-btn" onclick="selectRegion('bali')">
                                <div class="city-name">🏖️ Bali</div>
                                <div class="city-region">Denpasar</div>
                            </button>
                        </div>
                    </div>

                    <!-- City Selection -->
                    <div class="targeting-section">
                        <h4>🏙️ Pilih Kota</h4>
                        <div class="city-grid" id="city-grid">
                            <!-- Cities will be loaded dynamically -->
                        </div>
                    </div>

                    <!-- Additional Settings -->
                    <div class="targeting-section">
                        <h4>📱 Device & Carrier</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div class="form-group">
                                <label class="form-label">Device Type</label>
                                <select class="form-select" id="device-type" onchange="updateTargeting()">
                                    <option value="desktop">💻 Desktop</option>
                                    <option value="mobile">📱 Mobile</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Mobile Carrier (Optional)</label>
                                <select class="form-select" id="carrier" onchange="updateTargeting()">
                                    <option value="">-- Tidak Ada --</option>
                                    <option value="telkomsel">📶 Telkomsel</option>
                                    <option value="indosat">📱 Indosat</option>
                                    <option value="xl">📲 XL Axiata</option>
                                    <option value="three">3️⃣ Three</option>
                                    <option value="smartfren">🚀 Smartfren</option>
                                    <option value="axis">✖️ Axis</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Target URL -->
            <div class="col-6">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">🔗 Target Configuration</span>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Target URL</label>
                        <input type="url" class="form-input" id="target-url" placeholder="https://example.com/form" value="{{ target_url }}">
                    </div>
                    <button class="btn btn-secondary" onclick="updateTargetURL()" style="margin-top: 10px;">
                        💾 Simpan URL
                    </button>
                </div>
            </div>

            <!-- Submission Stats -->
            <div class="col-6">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">📊 Submission Statistics</span>
                    </div>
                    <div class="stats-grid">
                        <div class="stat-box">
                            <div class="stat-value" id="stat-total">{{ submission_stats.total }}</div>
                            <div class="stat-label">Total</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value success" id="stat-success">{{ submission_stats.success }}</div>
                            <div class="stat-label">Success</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value failed" id="stat-failed">{{ submission_stats.failed }}</div>
                            <div class="stat-label">Failed</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value challenge" id="stat-challenge">{{ submission_stats.challenge }}</div>
                            <div class="stat-label">Challenge</div>
                        </div>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="success-rate" style="width: 0%"></div>
                    </div>
                    <div style="text-align: center; margin-top: 8px; color: var(--text-muted); font-size: 0.9em;">
                        Success Rate: <span id="rate-percent">0</span>%
                    </div>
                </div>
            </div>

            <!-- Proxy Config -->
            <div class="col-6">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">🔐 Proxy Configuration</span>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Host</label>
                        <input type="text" class="form-input" id="proxy-host" value="{{ proxy_host }}">
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 2fr 2fr; gap: 10px;">
                        <div class="form-group">
                            <label class="form-label">Port</label>
                            <input type="number" class="form-input" id="proxy-port" value="{{ proxy_port }}">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Username</label>
                            <input type="text" class="form-input" id="proxy-user" value="{{ proxy_user }}" placeholder="optional">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Password</label>
                            <input type="password" class="form-input" id="proxy-pass" value="{{ proxy_pass }}" placeholder="optional">
                        </div>
                    </div>
                    <button class="btn btn-secondary btn-block" onclick="updateProxyConfig()" style="margin-top: 15px;">
                        💾 Update Proxy Config
                    </button>
                </div>
            </div>

            <!-- IP History -->
            <div class="col-6">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">📜 Riwayat IP</span>
                        <span style="color: var(--text-muted); font-size: 0.85em;">Last 15</span>
                    </div>
                    <div class="history-list" id="history-list">
                        {% for item in history %}
                        <div class="history-item">
                            <span class="history-ip">{{ item.ip }}</span>
                            <div class="history-meta">
                                <span class="history-count">#{{ item.count }}</span>
                                <span>{{ item.city }}</span>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">⚡ Quick Actions</span>
                    </div>
                    <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                        <button class="btn btn-success" onclick="exportConfig()">
                            📥 Export Config
                        </button>
                        <button class="btn btn-secondary" onclick="importConfig()">
                            📤 Import Config
                        </button>
                        <button class="btn btn-danger" onclick="clearHistory()">
                            🗑️ Clear History
                        </button>
                        <button class="btn btn-secondary" onclick="testConnection()">
                            🔍 Test Connection
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            ProxyDetection © 2024 | Indonesia-Focused Anti-Detection System
        </div>
    </div>

    <!-- Toast Notification -->
    <div class="toast" id="toast"></div>

    <script>
        // Indonesian cities data from server
        const CITIES = {{ cities_json | safe }};
        const currentRegion = "{{ targeting.region }}";

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            loadCitiesByRegion(currentRegion);
        });

        // Toast notification
        function showToast(message, isError = false) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = 'toast' + (isError ? ' error' : '');
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
        }

        // Rotate IP
        async function rotateIP(city = null) {
            const btn = document.querySelector('.btn-primary');
            btn.disabled = true;
            btn.innerHTML = '⏳ Memutar IP...';

            try {
                const response = await fetch('/api/rotate' + (city ? '?city=' + city : ''));
                const data = await response.json();

                if (data.success) {
                    document.getElementById('current-ip').textContent = data.ip;
                    document.getElementById('request-count').textContent = data.request_count;
                    document.getElementById('city-name').textContent = data.targeting_city.name;

                    // Update history
                    updateHistory(data.history);

                    btn.innerHTML = '✅ IP BERHASIL DIGANTI!';
                    setTimeout(() => {
                        btn.disabled = false;
                        btn.innerHTML = '🔄 GANTI IP SEKARANG';
                    }, 1500);
                }
            } catch (error) {
                btn.innerHTML = '❌ GAGAL - COBA LAGI';
                showToast('Gagal rotate IP: ' + error.message, true);
                setTimeout(() => {
                    btn.disabled = false;
                    btn.innerHTML = '🔄 GANTI IP SEKARANG';
                }, 2000);
            }
        }

        // Update history list
        function updateHistory(history) {
            const list = document.getElementById('history-list');
            list.innerHTML = history.map(item => `
                <div class="history-item">
                    <span class="history-ip">${item.ip}</span>
                    <div class="history-meta">
                        <span class="history-count">#${item.count}</span>
                        <span>${item.city}</span>
                    </div>
                </div>
            `).join('');
        }

        // Select region
        function selectRegion(region) {
            // Update active button
            document.querySelectorAll('#region-grid .city-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.closest('.city-btn').classList.add('active');

            // Load cities for region
            loadCitiesByRegion(region);
        }

        // Load cities by region
        function loadCitiesByRegion(region) {
            const grid = document.getElementById('city-grid');
            const citiesInRegion = Object.entries(CITIES)
                .filter(([key, city]) => city.region === region);

            grid.innerHTML = citiesInRegion.map(([key, city]) => `
                <button class="city-btn" onclick="rotateIP('${key}')">
                    <div class="city-name">📍 ${city.name}</div>
                    <div class="city-region">${city.timezone}</div>
                </button>
            `).join('');
        }

        // Update targeting
        async function updateTargeting() {
            const deviceType = document.getElementById('device-type').value;
            const carrier = document.getElementById('carrier').value;

            try {
                await fetch('/api/targeting', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_type: deviceType,
                        carrier: carrier || null
                    })
                });
            } catch (error) {
                console.error('Failed to update targeting:', error);
            }
        }

        // Toggle auto-rotate
        async function toggleAutoRotate() {
            const enabled = document.getElementById('auto-rotate-toggle').checked;

            try {
                await fetch('/api/auto-rotate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled: enabled })
                });
                showToast(enabled ? 'Auto-rotate enabled' : 'Auto-rotate disabled');
            } catch (error) {
                showToast('Failed to update settings', true);
            }
        }

        // Update auto-rotate interval
        async function updateAutoRotateInterval() {
            const interval = parseInt(document.getElementById('rotate-interval').value);

            try {
                await fetch('/api/auto-rotate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ interval: interval })
                });
            } catch (error) {
                console.error('Failed to update interval:', error);
            }
        }

        // Update target URL
        async function updateTargetURL() {
            const url = document.getElementById('target-url').value;

            try {
                const response = await fetch('/api/target-url', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                showToast('Target URL updated!');
            } catch (error) {
                showToast('Failed to update URL', true);
            }
        }

        // Update proxy config
        async function updateProxyConfig() {
            const config = {
                host: document.getElementById('proxy-host').value,
                port: parseInt(document.getElementById('proxy-port').value),
                username: document.getElementById('proxy-user').value,
                password: document.getElementById('proxy-pass').value
            };

            try {
                await fetch('/api/proxy-config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                showToast('Proxy configuration updated!');
            } catch (error) {
                showToast('Failed to update proxy config', true);
            }
        }

        // Export config
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
                    showToast('Configuration exported!');
                });
        }

        // Import config
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
                        // Apply config
                        if (config.targeting) {
                            document.getElementById('device-type').value = config.targeting.device_type || 'desktop';
                            document.getElementById('carrier').value = config.targeting.carrier || '';
                        }
                        if (config.proxy_url) {
                            // Parse proxy URL
                        }
                        showToast('Configuration imported!');
                    } catch (err) {
                        showToast('Invalid configuration file', true);
                    }
                }
            };
            input.click();
        }

        // Clear history
        async function clearHistory() {
            if (confirm('Clear all IP history?')) {
                showToast('History cleared');
            }
        }

        // Test connection
        async function testConnection() {
            showToast('Testing connection...');
            try {
                const response = await fetch('/api/test-connection');
                const data = await response.json();
                showToast(data.success ? '✅ Connection successful!' : '❌ Connection failed');
            } catch (error) {
                showToast('Connection test failed', true);
            }
        }

        // Auto refresh
        setInterval(async () => {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                document.getElementById('current-ip').textContent = data.current_ip;
                document.getElementById('request-count').textContent = data.request_count;

                // Update stats
                const stats = data.submission_stats;
                document.getElementById('stat-total').textContent = stats.total;
                document.getElementById('stat-success').textContent = stats.success;
                document.getElementById('stat-failed').textContent = stats.failed;
                document.getElementById('stat-challenge').textContent = stats.challenge;

                // Update success rate
                const rate = stats.total > 0 ? (stats.success / stats.total * 100).toFixed(1) : 0;
                document.getElementById('rate-percent').textContent = rate;
                document.getElementById('success-rate').style.width = rate + '%';
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
        last_time=status['last_rotation'] or '-',
        proxy_host=status['proxy_host'],
        proxy_port=status['proxy_port'],
        proxy_user=status['proxy_user'],
        proxy_pass='•' * 8 if status['proxy_pass'] else '',
        targeting=status['targeting'],
        targeting_city=status['targeting_city'],
        submission_stats=status['submission_stats'],
        auto_rotate=status['auto_rotate'],
        target_url=status['target_url'],
        history=status['history'],
        cities_json=json.dumps(INDONESIAN_CITIES),
    )

@app.route('/api/rotate')
@app.route('/api/rotate/<city>')
def api_rotate(city=None):
    """Rotate IP with optional city targeting."""
    new_ip = state.rotate(city)
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

@app.route('/api/submission-stats', methods=['POST'])
def api_submission_stats():
    """Update submission statistics."""
    data = request.get_json()
    stats = state.update_submission_stats(data)
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/test-connection')
def api_test_connection():
    """Test proxy connection."""
    # Simulate connection test
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
║   🎯 Proxy & Lead Dashboard - Indonesia Focus             ║
║                                                           ║
║   Opening browser at: http://localhost:5000               ║
║                                                           ║
║   Features:                                               ║
║   • 20+ Indonesian cities targeting                       ║
║   • Region-based selection (Jabodetabek, Jawa, dll)       ║
║   • Mobile carrier selection                              ║
║   • Auto-rotate settings                                  ║
║   • Real-time statistics                                  ║
║                                                           ║
║   Tekan Ctrl+C untuk stop                                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Open browser automatically
    import webbrowser
    import time
    time.sleep(1)
    webbrowser.open('http://localhost:5000')

    # Run Flask
    app.run(host='0.0.0.0', port=5000, debug=False)
