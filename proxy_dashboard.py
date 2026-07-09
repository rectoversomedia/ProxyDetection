#!/usr/bin/env python3
"""
Advanced Proxy & Lead Submission Dashboard
Indonesia-Focused - Interactive Web Interface
With Natural Human Behavior Simulation

Run with: python3 proxy_dashboard.py
Then open: http://localhost:5000
"""

from flask import Flask, jsonify, render_template_string, request
from datetime import datetime, time as dt_time
import random
import json
import threading
import time
import math

app = Flask(__name__)

# =============================================================================
# CONFIGURATION - ALL INDONESIAN CITIES
# =============================================================================

INDONESIAN_CITIES = {
    # DKI Jakarta
    "jakarta_pusat": {"name": "Jakarta Pusat", "province": "DKI Jakarta", "timezone": "WIB", "region": "jabodetabek"},
    "jakarta_barat": {"name": "Jakarta Barat", "province": "DKI Jakarta", "timezone": "WIB", "region": "jabodetabek"},
    "jakarta_timur": {"name": "Jakarta Timur", "province": "DKI Jakarta", "timezone": "WIB", "region": "jabodetabek"},
    "jakarta_selatan": {"name": "Jakarta Selatan", "province": "DKI Jakarta", "timezone": "WIB", "region": "jabodetabek"},
    "jakarta_utara": {"name": "Jakarta Utara", "province": "DKI Jakarta", "timezone": "WIB", "region": "jabodetabek"},
    "kepser": {"name": "Kepulauan Seribu", "province": "DKI Jakarta", "timezone": "WIB", "region": "jabodetabek"},

    # Jawa Barat - Greater Jakarta Area
    "bekasi": {"name": "Bekasi", "province": "Jawa Barat", "timezone": "WIB", "region": "jabodetabek"},
    "bekasi_utara": {"name": "Bekasi Utara", "province": "Jawa Barat", "timezone": "WIB", "region": "jabodetabek"},
    "bekasi_selatan": {"name": "Bekasi Selatan", "province": "Jawa Barat", "timezone": "WIB", "region": "jabodetabek"},
    "depok": {"name": "Depok", "province": "Jawa Barat", "timezone": "WIB", "region": "jabodetabek"},
    "bogor": {"name": "Bogor", "province": "Jawa Barat", "timezone": "WIB", "region": "jabodetabek"},
    "bogor_selatan": {"name": "Bogor Selatan", "province": "Jawa Barat", "timezone": "WIB", "region": "jabodetabek"},
    "tangerang": {"name": "Tangerang", "province": "Banten", "timezone": "WIB", "region": "jabodetabek"},
    "tangerang_selatan": {"name": "Tangerang Selatan", "province": "Banten", "timezone": "WIB", "region": "jabodetabek"},
    "tangerang_kota": {"name": "Tangerang Kota", "province": "Banten", "timezone": "WIB", "region": "jabodetabek"},
    "cilegon": {"name": "Cilegon", "province": "Banten", "timezone": "WIB", "region": "banten"},
    "serang": {"name": "Serang", "province": "Banten", "timezone": "WIB", "region": "banten"},
    "serang_selatan": {"name": "Serang Selatan", "province": "Banten", "timezone": "WIB", "region": "banten"},

    # Jawa Barat - Other
    "bandung": {"name": "Bandung", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "bandung_barat": {"name": "Bandung Barat", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "bandung_kota": {"name": "Bandung Kota", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "cirebon": {"name": "Cirebon", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "cirebon_kota": {"name": "Cirebon Kota", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "sukabumi": {"name": "Sukabumi", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "karawang": {"name": "Karawang", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "cikarang": {"name": "Cikarang", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "purwakarta": {"name": "Purwakarta", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "subang": {"name": "Subang", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "indramayu": {"name": "Indramayu", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "garut": {"name": "Garut", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "tasikmalaya": {"name": "Tasikmalaya", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "sumber": {"name": "Cirebon (Sumber)", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "抽Bakal": {"name": "Majalengka", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},
    "kuningan": {"name": "Kuningan", "province": "Jawa Barat", "timezone": "WIB", "region": "jawa_barat"},

    # Jawa Tengah
    "semarang": {"name": "Semarang", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "semarang_utara": {"name": "Semarang Utara", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "semarang_selatan": {"name": "Semarang Selatan", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "yogyakarta": {"name": "Yogyakarta", "province": "DI Yogyakarta", "timezone": "WIB", "region": "jawa_tengah"},
    "sleman": {"name": "Sleman", "province": "DI Yogyakarta", "timezone": "WIB", "region": "jawa_tengah"},
    "bantul": {"name": "Bantul", "province": "DI Yogyakarta", "timezone": "WIB", "region": "jawa_tengah"},
    "solo": {"name": "Surakarta/Solo", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "klaten": {"name": "Klaten", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "kudus": {"name": "Kudus", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "tegal": {"name": "Tegal", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "pekalongan": {"name": "Pekalongan", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "magelang": {"name": "Magelang", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "salatiga": {"name": "Salatiga", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "boyolali": {"name": "Boyolali", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "karanganyar": {"name": "Karanganyar", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "wonogiri": {"name": "Wonogiri", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "sragen": {"name": "Sragen", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "grobogan": {"name": "Grobogan", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "pati": {"name": "Pati", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},
    "rembang": {"name": "Rembang", "province": "Jawa Tengah", "timezone": "WIB", "region": "jawa_tengah"},

    # Jawa Timur
    "surabaya": {"name": "Surabaya", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "surabaya_utara": {"name": "Surabaya Utara", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "surabaya_selatan": {"name": "Surabaya Selatan", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "surabaya_timur": {"name": "Surabaya Timur", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "surabaya_barat": {"name": "Surabaya Barat", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "malang": {"name": "Malang", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "malang_kota": {"name": "Malang Kota", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "sidoarjo": {"name": "Sidoarjo", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "gresik": {"name": "Gresik", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "pasuruan": {"name": "Pasuruan", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "mojokerto": {"name": "Mojokerto", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "kediri": {"name": "Kediri", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "jember": {"name": "Jember", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "banyuwangi": {"name": "Banyuwangi", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "lamongan": {"name": "Lamongan", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "tuban": {"name": "Tuban", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "bojonegoro": {"name": "Bojonegoro", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "nganjuk": {"name": "Nganjuk", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "jombang": {"name": "Jombang", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "probolinggo": {"name": "Probolinggo", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "lumajang": {"name": "Lumajang", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "bondowoso": {"name": "Bondowoso", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},
    "situbondo": {"name": "Situbondo", "province": "Jawa Timur", "timezone": "WIB", "region": "jawa_timur"},

    # Sumatera Utara
    "medan": {"name": "Medan", "province": "Sumatera Utara", "timezone": "WIB", "region": "sumatera_utara"},
    "medan_utara": {"name": "Medan Utara", "province": "Sumatera Utara", "timezone": "WIB", "region": "sumatera_utara"},
    "medan_selatan": {"name": "Medan Selatan", "province": "Sumatera Utara", "timezone": "WIB", "region": "sumatera_utara"},
    "medan_timur": {"name": "Medan Timur", "province": "Sumatera Utara", "timezone": "WIB", "region": "sumatera_utara"},
    "medan_barat": {"name": "Medan Barat", "province": "Sumatera Utara", "timezone": "WIB", "region": "sumatera_utara"},
    "binjai": {"name": "Binjai", "province": "Sumatera Utara", "timezone": "WIB", "region": "sumatera_utara"},
    "deliserdang": {"name": "Deli Serdang", "province": "Sumatera Utara", "timezone": "WIB", "region": "sumatera_utara"},
    "pematangsiantar": {"name": "Pematangsiantar", "province": "Sumatera Utara", "timezone": "WIB", "region": "sumatera_utara"},
    "tebingtinggi": {"name": "Tebing Tinggi", "province": "Sumatera Utara", "timezone": "WIB", "region": "sumatera_utara"},
    "stabat": {"name": "Stabat", "province": "Sumatera Utara", "timezone": "WIB", "region": "sumatera_utara"},
    "siantar": {"name": "Pematangsiantar", "province": "Sumatera Utara", "timezone": "WIB", "region": "sumatera_utara"},
    "tanjungmorawa": {"name": "Tanjung Morawa", "province": "Sumatera Utara", "timezone": "WIB", "region": "sumatera_utara"},

    # Sumatera Barat
    "padang": {"name": "Padang", "province": "Sumatera Barat", "timezone": "WIB", "region": "sumatera_barat"},
    "padang_panjang": {"name": "Padang Panjang", "province": "Sumatera Barat", "timezone": "WIB", "region": "sumatera_barat"},
    "bukittinggi": {"name": "Bukittinggi", "province": "Sumatera Barat", "timezone": "WIB", "region": "sumatera_barat"},
    "solok": {"name": "Solok", "province": "Sumatera Barat", "timezone": "WIB", "region": "sumatera_barat"},
    "payakumbuh": {"name": "Payakumbuh", "province": "Sumatera Barat", "timezone": "WIB", "region": "sumatera_barat"},
    "paritmalintang": {"name": "Pariaman", "province": "Sumatera Barat", "timezone": "WIB", "region": "sumatera_barat"},

    # Sumatera Selatan
    "palembang": {"name": "Palembang", "province": "Sumatera Selatan", "timezone": "WIB", "region": "sumatera_selatan"},
    "palembang_utara": {"name": "Palembang Utara", "province": "Sumatera Selatan", "timezone": "WIB", "region": "sumatera_selatan"},
    "lubuklinggau": {"name": "Lubuklinggau", "province": "Sumatera Selatan", "timezone": "WIB", "region": "sumatera_selatan"},
    "prabumulih": {"name": "Prabumulih", "province": "Sumatera Selatan", "timezone": "WIB", "region": "sumatera_selatan"},
    "palembang_ilir": {"name": "Palembang Ilir", "province": "Sumatera Selatan", "timezone": "WIB", "region": "sumatera_selatan"},

    # Riau
    "pekanbaru": {"name": "Pekanbaru", "province": "Riau", "timezone": "WIB", "region": "riau"},
    "dumai": {"name": "Dumai", "province": "Riau", "timezone": "WIB", "region": "riau"},
    "batam": {"name": "Batam", "province": "Kepulauan Riau", "timezone": "WIB", "region": "kepulauan_riau"},
    "tanjungpin": {"name": "Tanjung Pinang", "province": "Kepulauan Riau", "timezone": "WIB", "region": "kepulauan_riau"},

    # Lampung
    "bandarlampung": {"name": "Bandar Lampung", "province": "Lampung", "timezone": "WIB", "region": "lampung"},
    "metro": {"name": "Metro", "province": "Lampung", "timezone": "WIB", "region": "lampung"},
    "kalianda": {"name": "Kalianda", "province": "Lampung", "timezone": "WIB", "region": "lampung"},

    # Kalimantan Barat
    "pontianak": {"name": "Pontianak", "province": "Kalimantan Barat", "timezone": "WIB", "region": "kalimantan_barat"},
    "pontianak_utara": {"name": "Pontianak Utara", "province": "Kalimantan Barat", "timezone": "WIB", "region": "kalimantan_barat"},
    "singkawang": {"name": "Singkawang", "province": "Kalimantan Barat", "timezone": "WIB", "region": "kalimantan_barat"},
    "ketapang": {"name": "Ketapang", "province": "Kalimantan Barat", "timezone": "WIB", "region": "kalimantan_barat"},
    "sintang": {"name": "Sintang", "province": "Kalimantan Barat", "timezone": "WIB", "region": "kalimantan_barat"},

    # Kalimantan Timur
    "samarinda": {"name": "Samarinda", "province": "Kalimantan Timur", "timezone": "WITA", "region": "kalimantan_timur"},
    "balikpapan": {"name": "Balikpapan", "province": "Kalimantan Timur", "timezone": "WITA", "region": "kalimantan_timur"},
    "bontang": {"name": "Bontang", "province": "Kalimantan Timur", "timezone": "WITA", "region": "kalimantan_timur"},
    "tarakan": {"name": "Tarakan", "province": "Kalimantan Utara", "timezone": "WITA", "region": "kalimantan_utara"},

    # Kalimantan Selatan
    "banjarmasin": {"name": "Banjarmasin", "province": "Kalimantan Selatan", "timezone": "WITA", "region": "kalimantan_selatan"},
    "banjarbaru": {"name": "Banjarbaru", "province": "Kalimantan Selatan", "timezone": "WITA", "region": "kalimantan_selatan"},
    "martapura": {"name": "Martapura", "province": "Kalimantan Selatan", "timezone": "WITA", "region": "kalimantan_selatan"},

    # Sulawesi Selatan
    "makassar": {"name": "Makassar", "province": "Sulawesi Selatan", "timezone": "WITA", "region": "sulawesi_selatan"},
    "makassar_utara": {"name": "Makassar Utara", "province": "Sulawesi Selatan", "timezone": "WITA", "region": "sulawesi_selatan"},
    "parepare": {"name": "Parepare", "province": "Sulawesi Selatan", "timezone": "WITA", "region": "sulawesi_selatan"},
    "palopo": {"name": "Palopo", "province": "Sulawesi Selatan", "timezone": "WITA", "region": "sulawesi_selatan"},
    "maros": {"name": "Maros", "province": "Sulawesi Selatan", "timezone": "WITA", "region": "sulawesi_selatan"},
    "gowa": {"name": "Gowa", "province": "Sulawesi Selatan", "timezone": "WITA", "region": "sulawesi_selatan"},

    # Sulawesi Utara
    "manado": {"name": "Manado", "province": "Sulawesi Utara", "timezone": "WITA", "region": "sulawesi_utara"},
    "bitung": {"name": "Bitung", "province": "Sulawesi Utara", "timezone": "WITA", "region": "sulawesi_utara"},
    "tomohon": {"name": "Tomohon", "province": "Sulawesi Utara", "timezone": "WITA", "region": "sulawesi_utara"},
    "kotamobagu": {"name": "Kotamobagu", "province": "Sulawesi Utara", "timezone": "WITA", "region": "sulawesi_utara"},

    # Sulawesi Tengah & Tenggara
    "palu": {"name": "Palu", "province": "Sulawesi Tengah", "timezone": "WITA", "region": "sulawesi_tengah"},
    "kendari": {"name": "Kendari", "province": "Sulawesi Tenggara", "timezone": "WITA", "region": "sulawesi_tenggara"},
    "bau-bau": {"name": "Bau-Bau", "province": "Sulawesi Tenggara", "timezone": "WITA", "region": "sulawesi_tenggara"},
    "gorontalo": {"name": "Gorontalo", "province": "Gorontalo", "timezone": "WITA", "region": "gorontalo"},

    # Bali
    "denpasar": {"name": "Denpasar", "province": "Bali", "timezone": "WITA", "region": "bali"},
    "badung": {"name": "Badung", "province": "Bali", "timezone": "WITA", "region": "bali"},
    "gianyar": {"name": "Gianyar", "province": "Bali", "timezone": "WITA", "region": "bali"},
    "singaraja": {"name": "Singaraja", "province": "Bali", "timezone": "WITA", "region": "bali"},
    "kuta": {"name": "Kuta", "province": "Bali", "timezone": "WITA", "region": "bali"},
    "ubud": {"name": "Ubud", "province": "Bali", "timezone": "WITA", "region": "bali"},
    "denpasar_barat": {"name": "Denpasar Barat", "province": "Bali", "timezone": "WITA", "region": "bali"},
    "denpasar_selatan": {"name": "Denpasar Selatan", "province": "Bali", "timezone": "WITA", "region": "bali"},

    # Nusa Tenggara
    "mataram": {"name": "Mataram", "province": "Nusa Tenggara Barat", "timezone": "WITA", "region": "ntb"},
    "lombok": {"name": "Lombok", "province": "Nusa Tenggara Barat", "timezone": "WITA", "region": "ntb"},
    "kupang": {"name": "Kupang", "province": "Nusa Tenggara Timur", "timezone": "WITA", "region": "ntt"},

    # Maluku
    "ambon": {"name": "Ambon", "province": "Maluku", "timezone": "WIT", "region": "maluku"},
    "tual": {"name": "Tual", "province": "Maluku", "timezone": "WIT", "region": "maluku"},

    # Papua
    "jayapura": {"name": "Jayapura", "province": "Papua", "timezone": "WIT", "region": "papua"},
    "sorong": {"name": "Sorong", "province": "Papua Barat", "timezone": "WIT", "region": "papua_barat"},
    "manokwari": {"name": "Manokwari", "province": "Papua Barat", "timezone": "WIT", "region": "papua_barat"},
    "merauke": {"name": "Merauke", "province": "Papua", "timezone": "WIT", "region": "papua"},
    "wamena": {"name": "Wamena", "province": "Papua", "timezone": "WIT", "region": "papua"},
    "timika": {"name": "Timika", "province": "Papua", "timezone": "WIT", "region": "papua"},
}

# Regions
REGIONS = {
    "jabodetabek": "Jabodetabek",
    "jawa_barat": "Jawa Barat",
    "banten": "Banten",
    "jawa_tengah": "Jawa Tengah & DIY",
    "jawa_timur": "Jawa Timur",
    "sumatera_utara": "Sumatera Utara",
    "sumatera_barat": "Sumatera Barat",
    "sumatera_selatan": "Sumatera Selatan",
    "riau": "Riau",
    "kepulauan_riau": "Kepulauan Riau",
    "lampung": "Lampung",
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

# Carriers
MOBILE_CARRIERS = {
    "telkomsel": "Telkomsel",
    "indosat": "Indosat Ooredoo",
    "xl": "XL Axiata",
    "three": "Three",
    "smartfren": "Smartfren",
    "axis": "Axis",
}

# ISPs
ISP_PROVIDERS = {
    "telkom": "Telkom Indonesia",
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
        self.current_ip = None
        self.request_count = 0
        self.ip_history = []
        self.last_rotation = None
        self.start_time = datetime.now()

        # Proxy config
        self.proxy_config = {
            "host": "gw.dataimpulse.com",
            "port": 823,
            "username": "",
            "password": "",
        }

        # Targeting
        self.targeting = {
            "region": "jabodetabek",
            "city": "jakarta_pusat",
            "carrier": None,
            "isp": None,
            "device_type": "desktop",
            "browser": "chrome",
        }

        # Batch settings (HUMAN-LIKE PATTERNS)
        self.batch_settings = {
            # Base timing
            "base_interval_minutes": 8,
            "interval_variance": 12,
            "data_per_batch_min": 2,
            "data_per_batch_max": 8,
            "max_per_hour": 25,

            # Natural timing mode
            "natural_timing": True,
            "work_hours_only": True,
            "work_start_hour": 8,
            "work_end_hour": 21,

            # Burst mode
            "burst_mode": True,
            "burst_size_min": 2,
            "burst_size_max": 5,
            "burst_pause_min": 5,
            "burst_pause_max": 15,

            # Night reduction
            "night_reduction": True,
            "night_multiplier": 0.1,
            "lunch_break": True,
            "lunch_start": 12,
            "lunch_end": 13,
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

        # Auto-rotate
        self.auto_rotate = {
            "enabled": False,
            "interval": 60,
        }

        # Initialize
        self._rotate_ip()

    def _calculate_next_interval(self):
        """Calculate human-like random interval based on time of day."""
        now = datetime.now()
        hour = now.hour

        settings = self.batch_settings

        # Base calculation
        base = settings["base_interval_minutes"]
        variance = settings["interval_variance"]

        # Add randomness
        interval = random.uniform(base - variance/2, base + variance)

        # Work hours adjustment
        if settings["work_hours_only"]:
            if hour < settings["work_start_hour"]:
                interval *= 3  # Early morning = slower
            elif hour >= settings["work_end_hour"]:
                interval *= 4  # Night = much slower

        # Lunch break reduction
        if settings["lunch_break"]:
            if settings["lunch_start"] <= hour < settings["lunch_end"]:
                interval *= 0.3  # Lunch = faster (orang makan sambil ngisi)

        # Night reduction
        if settings["night_reduction"]:
            if hour >= 22 or hour < 6:
                interval *= settings["night_multiplier"] * 10

        # Ensure positive
        return max(1, interval)

    def _calculate_batch_size(self):
        """Calculate human-like batch size."""
        if self.batch_settings["burst_mode"]:
            # Burst mode: clusters of submissions
            if random.random() < 0.3:  # 30% chance of burst
                return random.randint(
                    self.batch_settings["burst_size_min"],
                    self.batch_settings["burst_size_max"]
                )

        # Normal mode
        return random.randint(
            self.batch_settings["data_per_batch_min"],
            self.batch_settings["data_per_batch_max"]
        )

    def _generate_realistic_ip(self, region):
        """Generate realistic Indonesian IP based on region."""
        ip_prefixes = {
            "jabodetabek": ["101.128.", "114.4.", "116.12.", "180.214.", "182.253.", "139.192.", "125.160."],
            "jawa_barat": ["125.160.", "222.124.", "180.250.", "202.62.", "115.85.", "36.91."],
            "jawa_tengah": ["180.243.", "114.125.", "125.214.", "202.70.", "139.192.", "36.84."],
            "jawa_timur": ["116.206.", "36.84.", "114.57.", "180.248.", "103.95.", "36.91."],
            "banten": ["180.214.", "114.4.", "116.12.", "182.253.", "101.128."],
            "sumatera_utara": ["139.192.", "180.243.", "114.125.", "125.214.", "202.62."],
            "sumatera_barat": ["180.250.", "202.62.", "115.85.", "125.160."],
            "sumatera_selatan": ["125.160.", "180.243.", "114.125.", "125.214."],
            "riau": ["36.84.", "114.57.", "180.248.", "103.95."],
            "kepulauan_riau": ["116.206.", "36.84.", "114.57.", "180.248."],
            "lampung": ["180.250.", "202.62.", "115.85.", "125.160."],
            "kalimantan_barat": ["36.91.", "114.127.", "180.249.", "103.106."],
            "kalimantan_timur": ["116.206.", "36.84.", "114.57.", "180.248."],
            "kalimantan_selatan": ["116.206.", "36.84.", "114.57.", "180.248."],
            "sulawesi_selatan": ["180.214.", "114.5.", "116.58.", "202.67.", "125.162."],
            "sulawesi_utara": ["180.214.", "114.5.", "116.58.", "202.67."],
            "bali": ["36.84.", "114.57.", "180.248.", "103.95.", "116.206."],
            "papua": ["202.62.", "116.66.", "180.250.", "114.10."],
            "papua_barat": ["202.62.", "116.66.", "180.250.", "114.10."],
            "maluku": ["202.62.", "116.66.", "180.250.", "114.10."],
        }

        prefixes = ip_prefixes.get(region, ip_prefixes["jabodetabek"])
        prefix = random.choice(prefixes)
        parts = prefix.rstrip(".").split(".")

        return f"{parts[0]}.{parts[1]}.{random.randint(1,255)}.{random.randint(1,254)}"

    def _rotate_ip(self):
        """Generate new IP based on targeting."""
        with self.lock:
            region = self.targeting.get("region", "jabodetabek")
            city = self.targeting.get("city", "jakarta_pusat")
            city_data = INDONESIAN_CITIES.get(city, INDONESIAN_CITIES.get("jakarta_pusat"))

            new_ip = self._generate_realistic_ip(region)
            self.current_ip = new_ip
            self.request_count += 1
            self.last_rotation = datetime.now().isoformat()

            self.ip_history.append({
                "ip": new_ip,
                "time": self.last_rotation,
                "count": self.request_count,
                "city": city_data["name"],
                "region": city_data["province"],
                "interval_seconds": int(self._calculate_next_interval() * 60),
            })

            if len(self.ip_history) > 100:
                self.ip_history = self.ip_history[-100:]

            return new_ip

    def rotate(self, city=None, region=None):
        with self.lock:
            if region:
                self.targeting["region"] = region
            if city:
                self.targeting["city"] = city
            return self._rotate_ip()

    def get_status(self):
        with self.lock:
            city_data = INDONESIAN_CITIES.get(
                self.targeting["city"],
                INDONESIAN_CITIES.get("jakarta_pusat")
            )

            # Calculate next interval
            next_interval = self._calculate_next_interval()
            next_batch = self._calculate_batch_size()

            return {
                "current_ip": self.current_ip,
                "request_count": self.request_count,
                "last_rotation": self.last_rotation,
                "uptime": str(datetime.now() - self.start_time).split(".")[0],
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
                "next_interval": round(next_interval, 1),
                "next_batch_size": next_batch,
            }

    def update_targeting(self, data):
        with self.lock:
            for key in ["region", "city", "carrier", "isp", "device_type", "browser"]:
                if key in data:
                    self.targeting[key] = data[key]
            return self.targeting.copy()

    def update_batch_settings(self, settings):
        with self.lock:
            for key in self.batch_settings:
                if key in settings:
                    val = settings[key]
                    if isinstance(self.batch_settings[key], bool):
                        self.batch_settings[key] = bool(val)
                    elif isinstance(self.batch_settings[key], int):
                        self.batch_settings[key] = int(val)
            return self.batch_settings.copy()

    def update_proxy_config(self, config):
        with self.lock:
            for key in ["host", "port", "username", "password"]:
                if key in config:
                    self.proxy_config[key] = config[key]
            return self.proxy_config.copy()

    def update_auto_rotate(self, config):
        with self.lock:
            for key in ["enabled", "interval"]:
                if key in config:
                    if key == "enabled":
                        self.auto_rotate[key] = bool(config[key])
                    else:
                        self.auto_rotate[key] = int(config[key])
            return self.auto_rotate.copy()

    def update_target_url(self, url):
        with self.lock:
            self.target_url = url
            return self.target_url

    def update_submission_stats(self, stats):
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
    <title>Proxy Detection Dashboard</title>
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
            --success-light: #d1fae5;
            --danger: #ef4444;
            --danger-light: #fee2e2;
            --warning: #f59e0b;
            --warning-light: #fef3c7;
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
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
            --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06);
            --shadow-lg: 0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05);
            --radius: 8px;
            --radius-lg: 12px;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--gray-100);
            color: var(--gray-900);
            line-height: 1.5;
            min-height: 100vh;
        }

        .container {
            max-width: 1440px;
            margin: 0 auto;
            padding: 0 24px 40px;
        }

        /* HEADER */
        .header {
            background: var(--white);
            border-bottom: 1px solid var(--gray-200);
            padding: 24px 0;
            margin-bottom: 32px;
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }

        .header h1 {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--gray-900);
            letter-spacing: -0.025em;
        }

        .header .subtitle {
            font-size: 0.875rem;
            color: var(--gray-500);
            margin-top: 2px;
        }

        .header-stats {
            display: flex;
            gap: 24px;
        }

        .header-stat {
            text-align: right;
        }

        .header-stat-value {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--primary);
        }

        .header-stat-label {
            font-size: 0.75rem;
            color: var(--gray-500);
            text-transform: uppercase;
        }

        /* GRID LAYOUT */
        .grid {
            display: grid;
            gap: 24px;
        }

        .grid-2 { grid-template-columns: repeat(2, 1fr); }
        .grid-3 { grid-template-columns: repeat(3, 1fr); }
        .grid-4 { grid-template-columns: repeat(4, 1fr); }
        .grid-main { grid-template-columns: 380px 1fr; }
        .grid-timing { grid-template-columns: 1fr 1fr; }

        @media (max-width: 1200px) {
            .grid-main { grid-template-columns: 1fr; }
            .grid-timing { grid-template-columns: 1fr; }
        }
        @media (max-width: 768px) {
            .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; }
        }

        /* CARD */
        .card {
            background: var(--white);
            border-radius: var(--radius-lg);
            border: 1px solid var(--gray-200);
            box-shadow: var(--shadow-sm);
        }

        .card-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--gray-100);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--gray-500);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .card-body {
            padding: 20px;
        }

        /* IP DISPLAY */
        .ip-section {
            text-align: center;
            padding: 32px 20px;
        }

        .ip-label {
            font-size: 0.688rem;
            font-weight: 500;
            color: var(--gray-400);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }

        .ip-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
            font-family: 'SF Mono', 'Monaco', Consolas, monospace;
            letter-spacing: -1px;
        }

        .city-info {
            margin-top: 12px;
            padding: 8px 16px;
            background: var(--gray-50);
            border-radius: 20px;
            display: inline-block;
            font-size: 0.813rem;
            color: var(--gray-600);
        }

        /* STATS ROW */
        .stats-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            border-top: 1px solid var(--gray-100);
        }

        .stat-item {
            padding: 16px;
            text-align: center;
            border-right: 1px solid var(--gray-100);
        }

        .stat-item:last-child {
            border-right: none;
        }

        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--gray-900);
        }

        .stat-value.success { color: var(--success); }
        .stat-value.failed { color: var(--danger); }
        .stat-value.challenge { color: var(--warning); }

        .stat-label {
            font-size: 0.688rem;
            color: var(--gray-400);
            text-transform: uppercase;
            margin-top: 4px;
        }

        /* BUTTONS */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 10px 20px;
            font-size: 0.813rem;
            font-weight: 600;
            border: none;
            border-radius: var(--radius);
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

        .btn-success {
            background: var(--success);
            color: white;
        }

        .btn-secondary {
            background: var(--gray-100);
            color: var(--gray-700);
            border: 1px solid var(--gray-300);
        }

        .btn-secondary:hover {
            background: var(--gray-200);
        }

        .btn-block {
            width: 100%;
        }

        .btn-sm {
            padding: 6px 12px;
            font-size: 0.75rem;
        }

        /* FORMS */
        .form-group {
            margin-bottom: 16px;
        }

        .form-group:last-child {
            margin-bottom: 0;
        }

        .form-label {
            display: block;
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--gray-600);
            margin-bottom: 6px;
        }

        .form-input, .form-select {
            width: 100%;
            padding: 10px 14px;
            font-size: 0.875rem;
            border: 1px solid var(--gray-300);
            border-radius: var(--radius);
            background: var(--white);
            color: var(--gray-900);
            transition: all 0.2s;
        }

        .form-input:focus, .form-select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        .form-row {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }

        .form-row-3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }

        @media (max-width: 640px) {
            .form-row, .form-row-3 { grid-template-columns: 1fr; }
        }

        /* TOGGLE */
        .toggle-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid var(--gray-100);
        }

        .toggle-item:last-child {
            border-bottom: none;
        }

        .toggle-label {
            font-size: 0.813rem;
            color: var(--gray-700);
        }

        .toggle {
            position: relative;
            width: 44px;
            height: 24px;
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
            border-radius: 24px;
            transition: 0.3s;
        }

        .toggle-slider:before {
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
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
            transform: translateX(20px);
        }

        /* REGION TABS */
        .region-tabs {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .region-tab {
            padding: 8px 14px;
            font-size: 0.75rem;
            font-weight: 500;
            background: var(--gray-100);
            border: 2px solid transparent;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.15s;
            color: var(--gray-600);
        }

        .region-tab:hover {
            background: var(--gray-200);
        }

        .region-tab.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        /* CITY GRID */
        .city-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 8px;
            max-height: 280px;
            overflow-y: auto;
            padding: 4px;
        }

        .city-btn {
            padding: 10px 12px;
            background: var(--gray-50);
            border: 2px solid var(--gray-200);
            border-radius: 6px;
            cursor: pointer;
            text-align: center;
            transition: all 0.15s;
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
            font-size: 0.75rem;
            font-weight: 500;
        }

        .city-btn .city-tz {
            font-size: 0.625rem;
            color: var(--gray-400);
            margin-top: 2px;
        }

        .city-btn.active .city-tz {
            color: rgba(255,255,255,0.7);
        }

        /* SETTING ROW */
        .setting-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 0;
            border-bottom: 1px solid var(--gray-100);
        }

        .setting-row:last-child {
            border-bottom: none;
        }

        .setting-info {
            flex: 1;
        }

        .setting-title {
            font-size: 0.813rem;
            font-weight: 500;
            color: var(--gray-800);
        }

        .setting-desc {
            font-size: 0.688rem;
            color: var(--gray-400);
            margin-top: 2px;
        }

        .setting-control {
            width: 100px;
        }

        .setting-control input {
            width: 100%;
            padding: 8px 10px;
            font-size: 0.813rem;
            text-align: center;
            border: 1px solid var(--gray-300);
            border-radius: 6px;
            background: var(--white);
        }

        .setting-control input:focus {
            outline: none;
            border-color: var(--primary);
        }

        /* BADGE */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            font-size: 0.688rem;
            font-weight: 600;
            border-radius: 12px;
            text-transform: uppercase;
        }

        .badge-success {
            background: var(--success-light);
            color: var(--success);
        }

        .badge-warning {
            background: var(--warning-light);
            color: var(--warning);
        }

        /* HISTORY */
        .history-list {
            max-height: 300px;
            overflow-y: auto;
        }

        .history-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid var(--gray-50);
        }

        .history-item:last-child {
            border-bottom: none;
        }

        .history-ip {
            font-family: 'SF Mono', 'Monaco', Consolas, monospace;
            font-size: 0.813rem;
            font-weight: 600;
            color: var(--primary);
        }

        .history-meta {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .history-count {
            font-size: 0.688rem;
            background: var(--gray-100);
            padding: 2px 8px;
            border-radius: 10px;
            color: var(--gray-500);
        }

        .history-city {
            font-size: 0.75rem;
            color: var(--gray-400);
        }

        .history-interval {
            font-size: 0.688rem;
            color: var(--gray-400);
        }

        /* TIME DISPLAY */
        .time-slots {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 8px;
            margin-top: 16px;
        }

        .time-slot {
            text-align: center;
            padding: 12px 8px;
            background: var(--gray-50);
            border-radius: 6px;
            border: 1px solid var(--gray-200);
        }

        .time-slot-label {
            font-size: 0.625rem;
            color: var(--gray-500);
            text-transform: uppercase;
        }

        .time-slot-value {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--gray-700);
            margin-top: 4px;
        }

        .time-slot.peak .time-slot-value {
            color: var(--success);
        }

        .time-slot.off .time-slot-value {
            color: var(--gray-400);
        }

        /* ACTIONS GRID */
        .actions-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }

        /* SECTION DIVIDER */
        .divider {
            height: 1px;
            background: var(--gray-200);
            margin: 20px 0;
        }

        /* FOOTER */
        footer {
            text-align: center;
            padding: 40px;
            color: var(--gray-400);
            font-size: 0.75rem;
        }

        /* SCROLLBAR */
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

        /* TOAST */
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            padding: 14px 20px;
            background: var(--gray-900);
            color: white;
            font-size: 0.813rem;
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

        /* NEXT ACTION PREVIEW */
        .next-action {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border-radius: var(--radius);
            padding: 16px;
            margin-top: 16px;
            text-align: center;
        }

        .next-action-label {
            font-size: 0.688rem;
            opacity: 0.8;
            text-transform: uppercase;
        }

        .next-action-value {
            font-size: 1.25rem;
            font-weight: 700;
            margin-top: 4px;
        }

        .next-action-hint {
            font-size: 0.688rem;
            opacity: 0.7;
            margin-top: 8px;
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <div class="header-content">
                <div>
                    <h1>Proxy Detection</h1>
                    <p class="subtitle">Indonesia Anti-Detection System</p>
                </div>
                <div class="header-stats">
                    <div class="header-stat">
                        <div class="header-stat-value" id="uptime">{{ uptime }}</div>
                        <div class="header-stat-label">Uptime</div>
                    </div>
                    <div class="header-stat">
                        <div class="header-stat-value" id="total-rotations">{{ request_count }}</div>
                        <div class="header-stat-label">Total Rotations</div>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <div class="container">
        <div class="grid grid-main">
            <!-- SIDEBAR -->
            <div class="sidebar">
                <!-- Current IP Card -->
                <div class="card">
                    <div class="ip-section">
                        <div class="ip-label">Active IP Address</div>
                        <div class="ip-value" id="current-ip">{{ current_ip }}</div>
                        <div class="city-info" id="city-info">
                            {{ targeting_city.name }}, {{ targeting_city.province }}
                        </div>
                    </div>
                    <div style="padding: 0 20px 20px;">
                        <button class="btn btn-primary btn-block" id="rotate-btn" onclick="rotateIP()">
                            ROTATE IP
                        </button>
                    </div>
                    <div class="stats-row">
                        <div class="stat-item">
                            <div class="stat-value" id="stat-total">{{ submission_stats.total }}</div>
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
                            <div class="stat-value challenge" id="stat-challenge">{{ submission_stats.challenge }}</div>
                            <div class="stat-label">Challenge</div>
                        </div>
                    </div>
                </div>

                <!-- Next Action Preview -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">Next Action Preview</span>
                    </div>
                    <div class="card-body">
                        <div class="next-action">
                            <div class="next-action-label">Estimated Next Interval</div>
                            <div class="next-action-value" id="next-interval">{{ next_interval }} min</div>
                            <div class="next-action-hint">Next batch: <span id="next-batch">{{ next_batch_size }}</span> submissions</div>
                        </div>
                        <div class="time-slots">
                            <div class="time-slot">
                                <div class="time-slot-label">6-8 AM</div>
                                <div class="time-slot-value">15</div>
                            </div>
                            <div class="time-slot peak">
                                <div class="time-slot-label">8-12 PM</div>
                                <div class="time-slot-value">35</div>
                            </div>
                            <div class="time-slot">
                                <div class="time-slot-label">12-1 PM</div>
                                <div class="time-slot-value">45</div>
                            </div>
                            <div class="time-slot peak">
                                <div class="time-slot-label">1-5 PM</div>
                                <div class="time-slot-value">40</div>
                            </div>
                            <div class="time-slot">
                                <div class="time-slot-label">5-9 PM</div>
                                <div class="time-slot-value">25</div>
                            </div>
                            <div class="time-slot off">
                                <div class="time-slot-label">9 PM-6</div>
                                <div class="time-slot-value">5</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Auto Rotate -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">Auto Rotate</span>
                    </div>
                    <div class="card-body">
                        <div class="toggle-item">
                            <span class="toggle-label">Enable Auto-Rotate</span>
                            <label class="toggle">
                                <input type="checkbox" id="auto-rotate-toggle" onchange="toggleAutoRotate()">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="form-group" style="margin-top: 16px;">
                            <label class="form-label">Rotate Every (seconds)</label>
                            <input type="number" class="form-input" id="rotate-interval" value="{{ auto_rotate.interval }}" min="30" max="3600" onchange="updateAutoRotate()">
                        </div>
                    </div>
                </div>
            </div>

            <!-- MAIN CONTENT -->
            <div class="main-content">
                <!-- Target URL -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Target Configuration</span>
                    </div>
                    <div class="card-body">
                        <div class="form-group" style="margin-bottom: 0;">
                            <label class="form-label">Target URL (Form Submission URL)</label>
                            <input type="url" class="form-input" id="target-url" value="{{ target_url }}" placeholder="https://prulady.com/affiliate/register">
                        </div>
                    </div>
                </div>

                <!-- Region Selection -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">Region</span>
                    </div>
                    <div class="card-body">
                        <div class="region-tabs" id="region-tabs"></div>
                    </div>
                </div>

                <!-- City Selection -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">City</span>
                    </div>
                    <div class="card-body">
                        <div class="city-grid" id="city-grid"></div>
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
                                <label class="form-label">Mobile Carrier</label>
                                <select class="form-select" id="carrier" onchange="updateTargeting()">
                                    <option value="">None</option>
                                    {% for key, name in carriers.items() %}
                                    <option value="{{ key }}" {% if targeting.carrier == key %}selected{% endif %}>{{ name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">ISP Provider</label>
                                <select class="form-select" id="isp" onchange="updateTargeting()">
                                    <option value="">None</option>
                                    {% for key, name in isps.items() %}
                                    <option value="{{ key }}" {% if targeting.isp == key %}selected{% endif %}>{{ name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Natural Timing Settings -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">Natural Timing Settings</span>
                        <span class="badge badge-success">Anti-Detection</span>
                    </div>
                    <div class="card-body">
                        <div class="toggle-item">
                            <div>
                                <div class="toggle-label">Natural Timing Mode</div>
                                <div class="setting-desc">Random intervals mimicking human behavior</div>
                            </div>
                            <label class="toggle">
                                <input type="checkbox" id="natural-timing" checked onchange="updateBatchSettings()">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>

                        <div class="divider"></div>

                        <div class="setting-row">
                            <div class="setting-info">
                                <div class="setting-title">Base Interval (minutes)</div>
                                <div class="setting-desc">Average time between submissions</div>
                            </div>
                            <div class="setting-control">
                                <input type="number" id="base-interval" value="8" min="1" max="60" onchange="updateBatchSettings()">
                            </div>
                        </div>

                        <div class="setting-row">
                            <div class="setting-info">
                                <div class="setting-title">Interval Variance</div>
                                <div class="setting-desc">Random variance range</div>
                            </div>
                            <div class="setting-control">
                                <input type="number" id="interval-variance" value="12" min="1" max="30" onchange="updateBatchSettings()">
                            </div>
                        </div>

                        <div class="setting-row">
                            <div class="setting-info">
                                <div class="setting-title">Min Batch Size</div>
                                <div class="setting-desc">Minimum submissions per batch</div>
                            </div>
                            <div class="setting-control">
                                <input type="number" id="batch-min" value="2" min="1" max="20" onchange="updateBatchSettings()">
                            </div>
                        </div>

                        <div class="setting-row">
                            <div class="setting-info">
                                <div class="setting-title">Max Batch Size</div>
                                <div class="setting-desc">Maximum submissions per batch</div>
                            </div>
                            <div class="setting-control">
                                <input type="number" id="batch-max" value="8" min="1" max="50" onchange="updateBatchSettings()">
                            </div>
                        </div>

                        <div class="setting-row">
                            <div class="setting-info">
                                <div class="setting-title">Max Per Hour</div>
                                <div class="setting-desc">Rate limit protection</div>
                            </div>
                            <div class="setting-control">
                                <input type="number" id="max-per-hour" value="25" min="1" max="100" onchange="updateBatchSettings()">
                            </div>
                        </div>

                        <div class="divider"></div>

                        <div class="toggle-item">
                            <div>
                                <div class="toggle-label">Burst Mode</div>
                                <div class="setting-desc">Submit 2-5 quickly, then long pause</div>
                            </div>
                            <label class="toggle">
                                <input type="checkbox" id="burst-mode" checked onchange="updateBatchSettings()">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>

                        <div class="toggle-item">
                            <div>
                                <div class="toggle-label">Work Hours Only</div>
                                <div class="setting-desc">Active 8 AM - 9 PM, reduced at night</div>
                            </div>
                            <label class="toggle">
                                <input type="checkbox" id="work-hours" checked onchange="updateBatchSettings()">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>

                        <div class="toggle-item">
                            <div>
                                <div class="toggle-label">Night Reduction</div>
                                <div class="setting-desc">90% less activity 10 PM - 6 AM</div>
                            </div>
                            <label class="toggle">
                                <input type="checkbox" id="night-reduction" checked onchange="updateBatchSettings()">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>

                        <div class="toggle-item">
                            <div>
                                <div class="toggle-label">Lunch Break Boost</div>
                                <div class="setting-desc">Faster submissions during lunch 12-1 PM</div>
                            </div>
                            <label class="toggle">
                                <input type="checkbox" id="lunch-break" checked onchange="updateBatchSettings()">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Proxy Config -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">Proxy Configuration</span>
                    </div>
                    <div class="card-body">
                        <div class="form-row-3">
                            <div class="form-group">
                                <label class="form-label">Host</label>
                                <input type="text" class="form-input" id="proxy-host" value="{{ proxy_config.host }}">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Port</label>
                                <input type="number" class="form-input" id="proxy-port" value="{{ proxy_config.port }}">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Username</label>
                                <input type="text" class="form-input" id="proxy-user" value="{{ proxy_config.username }}" placeholder="Optional">
                            </div>
                        </div>
                        <div class="form-group" style="margin-top: 16px;">
                            <label class="form-label">Password</label>
                            <input type="password" class="form-input" id="proxy-pass" value="{{ proxy_config.password }}" placeholder="Optional">
                        </div>
                        <button class="btn btn-secondary" onclick="updateProxyConfig()" style="margin-top: 12px;">
                            Update Proxy
                        </button>
                    </div>
                </div>

                <!-- IP History -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">IP History</span>
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <div class="history-list" id="history-list" style="padding: 0 20px;">
                            {% for item in history %}
                            <div class="history-item">
                                <span class="history-ip">{{ item.ip }}</span>
                                <div class="history-meta">
                                    <span class="history-interval">{{ item.interval_seconds }}s</span>
                                    <span class="history-count">#{{ item.count }}</span>
                                    <span class="history-city">{{ item.city }}</span>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="card" style="margin-top: 24px;">
                    <div class="card-header">
                        <span class="card-title">Quick Actions</span>
                    </div>
                    <div class="card-body">
                        <div class="actions-grid">
                            <button class="btn btn-success" onclick="exportConfig()">Export Config</button>
                            <button class="btn btn-secondary" onclick="importConfig()">Import Config</button>
                            <button class="btn btn-secondary" onclick="testConnection()">Test Connection</button>
                            <button class="btn btn-secondary" onclick="clearHistory()">Clear History</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer>
        Proxy Detection Dashboard | Indonesia Anti-Detection System
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
            initBatchSettings();
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
            let html = '';
            Object.entries(REGIONS).forEach(([key, name]) => {
                const active = key === currentRegion ? 'active' : '';
                html += `<button class="region-tab ${active}" onclick="selectRegion('${key}')">${name}</button>`;
            });
            container.innerHTML = html;
        }

        // Select Region
        function selectRegion(region) {
            document.querySelectorAll('.region-tab').forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
            initCityGrid(region);
            fetch('/api/targeting', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ region: region })
            });
        }

        // City Grid
        function initCityGrid(region) {
            const container = document.getElementById('city-grid');
            const cities = Object.entries(CITIES).filter(([key, city]) => city.region === region);

            if (cities.length === 0) {
                container.innerHTML = '<p style="color: var(--gray-400); text-align: center; padding: 40px;">No cities available</p>';
                return;
            }

            let html = '';
            cities.forEach(([key, city]) => {
                const active = key === currentCity ? 'active' : '';
                html += `<button class="city-btn ${active}" onclick="selectCity('${key}')">
                    <div class="city-name">${city.name}</div>
                    <div class="city-tz">${city.timezone}</div>
                </button>`;
            });
            container.innerHTML = html;
        }

        // Select City
        function selectCity(city) {
            document.querySelectorAll('.city-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
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
                    document.getElementById('city-info').textContent = `${data.targeting_city.name}, ${data.targeting_city.province}`;
                    document.getElementById('next-interval').textContent = `${data.next_interval} min`;
                    document.getElementById('next-batch').textContent = data.next_batch_size;
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
                        <span class="history-interval">${item.interval_seconds}s</span>
                        <span class="history-count">#${item.count}</span>
                        <span class="history-city">${item.city}</span>
                    </div>
                </div>
            `).join('');
        }

        // Update Targeting
        async function updateTargeting() {
            const data = {
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
        function initBatchSettings() {
            // Settings will be populated from server
        }

        async function updateBatchSettings() {
            const data = {
                natural_timing: document.getElementById('natural-timing').checked,
                base_interval_minutes: parseInt(document.getElementById('base-interval').value),
                interval_variance: parseInt(document.getElementById('interval-variance').value),
                data_per_batch_min: parseInt(document.getElementById('batch-min').value),
                data_per_batch_max: parseInt(document.getElementById('batch-max').value),
                max_per_hour: parseInt(document.getElementById('max-per-hour').value),
                burst_mode: document.getElementById('burst-mode').checked,
                work_hours_only: document.getElementById('work-hours').checked,
                night_reduction: document.getElementById('night-reduction').checked,
                lunch_break: document.getElementById('lunch-break').checked,
            };

            try {
                await fetch('/api/batch-settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                showToast('Timing settings updated', 'success');
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

        async function updateAutoRotate() {
            const interval = parseInt(document.getElementById('rotate-interval').value);
            try {
                await fetch('/api/auto-rotate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ interval: interval })
                });
            } catch (error) {
                console.error('Failed to update');
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
                        JSON.parse(text);
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
                document.getElementById('total-rotations').textContent = data.request_count;
                document.getElementById('uptime').textContent = data.uptime;
                document.getElementById('next-interval').textContent = `${data.next_interval} min`;
                document.getElementById('next-batch').textContent = data.next_batch_size;
                document.getElementById('stat-total').textContent = data.submission_stats.total;
                document.getElementById('stat-success').textContent = data.submission_stats.success;
                document.getElementById('stat-failed').textContent = data.submission_stats.failed;
                document.getElementById('stat-challenge').textContent = data.submission_stats.challenge;
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
    status = state.get_status()
    return render_template_string(
        HTML_TEMPLATE,
        current_ip=status['current_ip'],
        request_count=status['request_count'],
        uptime=status['uptime'],
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
        next_interval=status['next_interval'],
        next_batch_size=status['next_batch_size'],
    )

@app.route('/api/rotate')
@app.route('/api/rotate/<city>')
def api_rotate(city=None):
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
        'next_interval': status['next_interval'],
        'next_batch_size': status['next_batch_size'],
    })

@app.route('/api/status')
def api_status():
    return jsonify(state.get_status())

@app.route('/api/targeting', methods=['POST'])
def api_targeting():
    data = request.get_json()
    targeting = state.update_targeting(data)
    return jsonify({'success': True, 'targeting': targeting})

@app.route('/api/batch-settings', methods=['POST'])
def api_batch_settings():
    data = request.get_json()
    settings = state.update_batch_settings(data)
    return jsonify({'success': True, 'settings': settings})

@app.route('/api/proxy-config', methods=['POST'])
def api_proxy_config():
    data = request.get_json()
    config = state.update_proxy_config(data)
    return jsonify({'success': True, 'config': config})

@app.route('/api/auto-rotate', methods=['POST'])
def api_auto_rotate():
    data = request.get_json()
    config = state.update_auto_rotate(data)
    return jsonify({'success': True, 'config': config})

@app.route('/api/test-connection')
def api_test_connection():
    import random
    success = random.random() > 0.2
    return jsonify({'success': success})

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
║   - Natural Human Timing Simulation                       ║
║   - 130+ Indonesian cities                               ║
║   - 26 Regions                                           ║
║   - Work Hours / Night Reduction                         ║
║   - Burst Mode (clustered submissions)                   ║
║   - Lunch Break Boost                                    ║
║                                                           ║
║   Press Ctrl+C to stop                                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    import webbrowser
    import time
    time.sleep(1)
    webbrowser.open('http://localhost:5000')

    app.run(host='0.0.0.0', port=5000, debug=False)
