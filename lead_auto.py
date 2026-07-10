#!/usr/bin/env python3
"""
Lead Automation - Full Anti-Detection System
IP + Fingerprint Rotate per Submission

Usage:
    python3 lead_auto.py --sheet-id "SPREADSHEET_ID" --limit 10 --test

Requirements:
    pip install selenium undetected-chromedriver gspread google-auth
"""

import argparse
import csv
import json
import random
import time
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Selenium with undetected-chromedriver for anti-detection
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("Warning: Google Sheets not available. Use --csv instead.")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Indonesian Cities with geo data
CITIES = [
    {"name": "Jakarta", "region": "jabodetabek", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Bandung", "region": "jawa_barat", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Surabaya", "region": "jawa_timur", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Semarang", "region": "jawa_tengah", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Yogyakarta", "region": "jawa_tengah", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Medan", "region": "sumatera_utara", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Palembang", "region": "sumatera_selatan", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Makassar", "region": "sulawesi_selatan", "tz": "Asia/Makassar", "offset": 8},
    {"name": "Denpasar", "region": "bali", "tz": "Asia/Makassar", "offset": 8},
    {"name": "Jayapura", "region": "papua", "tz": "Asia/Jayapura", "offset": 9},
    {"name": "Bogor", "region": "jabodetabek", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Depok", "region": "jabodetabek", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Tangerang", "region": "jabodetabek", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Bekasi", "region": "jabodetabek", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Malang", "region": "jawa_timur", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Sidoarjo", "region": "jawa_timur", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Kediri", "region": "jawa_timur", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Solo", "region": "jawa_tengah", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Kudus", "region": "jawa_tengah", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Cirebon", "region": "jawa_barat", "tz": "Asia/Jakarta", "offset": 7},
    {"name": "Sukabumi", "region": "jawa_barat", "tz": "Asia/Jakarta", "offset": 7},
]

# Proxy Configuration
PROXY_HOST = "gw.dataimpulse.com"
PROXY_PORT = 823
PROXY_USER = "1598b06c2cd2aea9c80b"  # Replace with your DataImpulse username
PROXY_PASS = "4ffb48b7789c69a7"  # Replace with your DataImpulse password

# Human timing settings
TIMING = {
    "min_interval": 180,  # 3 minutes minimum between submissions
    "max_interval": 600,  # 10 minutes maximum
    "work_hours_only": True,
    "work_start": 8,
    "work_end": 22,
}

# User Agents (Chrome versions)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

# Screen resolutions
SCREEN_RESOLUTIONS = [
    (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
    (1600, 900), (1280, 720), (1280, 800)
]

# =============================================================================
# FINGERPRINT GENERATOR
# =============================================================================

class FingerprintGenerator:
    """Generate unique fingerprints per session."""

    def __init__(self):
        self.ua = random.choice(USER_AGENTS)
        self.screen = random.choice(SCREEN_RESOLUTIONS)
        self.city = random.choice(CITIES)
        self.canvas_seed = random.randint(100000, 999999)
        self.webgl_seed = random.randint(100000, 999999)

    def get_ua(self) -> str:
        return self.ua

    def get_screen(self) -> tuple:
        return self.screen

    def get_city(self) -> dict:
        return self.city

    def get_timezone(self) -> dict:
        return {
            "id": self.city["tz"],
            "offset": self.city["offset"]
        }

    def get_proxy(self) -> str:
        return f"{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

    def __str__(self) -> str:
        return f"FP[UA:{self.ua[:50]}... | City:{self.city['name']} | Screen:{self.screen}]"


# =============================================================================
# BROWSER MANAGER
# =============================================================================

class BrowserManager:
    """Manage browser with anti-detection measures."""

    def __init__(self, fingerprint: FingerprintGenerator):
        self.fingerprint = fingerprint
        self.driver = None

    def setup(self):
        """Setup undetected Chrome with unique fingerprint."""

        # Chrome options
        options = uc.ChromeOptions()

        # Basic stealth
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")

        # Screen resolution
        width, height = self.fingerprint.get_screen()
        options.add_argument(f"--window-size={width},{height}")
        options.add_argument(f"--start-maximized")

        # Proxy
        proxy = self.fingerprint.get_proxy()
        options.add_argument(f"--proxy-server=http://{proxy}")

        # Languages (Indonesia)
        options.add_argument("--lang=id-ID")
        options.add_experimental_option("prefs", {
            "intl.accept_languages": "id-ID,id,en-US,en",
            "profile.default_content_setting_values.notifications": 2,
        })

        # Create driver (undetected)
        self.driver = uc.Chrome(options=options, version_main=None)

        # Additional stealth - remove webdriver property
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        # Set timezone via CDP
        try:
            tz = self.fingerprint.get_timezone()
            self.driver.execute_cdp_cmd(
                "Emulation.setTimezoneOverride",
                {"timezoneId": tz["id"]}
            )
        except:
            pass

        logger.info(f"Browser setup: {self.fingerprint}")
        return self.driver

    def close(self):
        """Close browser."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


# =============================================================================
# HUMAN BEHAVIOR SIMULATOR
# =============================================================================

class HumanSimulator:
    """Simulate human-like behavior."""

    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)

    def human_delay(self, min_ms=100, max_ms=500):
        """Random delay simulating human thinking."""
        delay = random.uniform(min_ms, max_ms) / 1000
        time.sleep(delay)

    def type_like_human(self, element, text: str):
        """Type with random delays between keystrokes."""
        element.clear()
        for char in text:
            element.send_keys(char)
            # Random delay 50-150ms per character
            time.sleep(random.uniform(0.05, 0.15))

    def mouse_move_human(self, element):
        """Move mouse naturally to element."""
        # Random starting position
        start_x = random.randint(100, 500)
        start_y = random.randint(100, 400)

        # Move with bezier-like curve
        self.actions.move_by_offset(start_x, start_y)
        self.human_delay(100, 300)
        self.actions.move_to_element(element)
        self.human_delay(50, 150)
        self.actions.click()
        self.actions.perform()

    def scroll_naturally(self):
        """Scroll with human-like pattern."""
        for _ in range(random.randint(1, 3)):
            scroll_amount = random.randint(200, 500)
            self.driver.execute_script(
                f"window.scrollBy(0, {scroll_amount});"
            )
            self.human_delay(300, 800)

    def click_random_position(self):
        """Click at random position on element."""
        action = ActionChains(self.driver)
        action.move_by_offset(
            random.randint(5, 50),
            random.randint(5, 20)
        )
        action.click()
        action.perform()


# =============================================================================
# LEAD PROCESSOR
# =============================================================================

class LeadProcessor:
    """Process and submit leads."""

    def __init__(self, target_url: str):
        self.target_url = target_url
        self.results = []

    def submit(self, lead: dict, index: int) -> dict:
        """Submit single lead with unique fingerprint."""

        # Generate unique fingerprint
        fp = FingerprintGenerator()

        result = {
            "index": index,
            "nama": lead.get("nama", ""),
            "email": lead.get("email", ""),
            "phone": lead.get("phone", ""),
            "kota": lead.get("kota", ""),
            "city": fp.get_city()["name"],
            "ua": fp.get_ua()[:60] + "...",
            "screen": fp.get_screen(),
            "status": "pending",
            "message": "",
            "timestamp": datetime.now().isoformat(),
        }

        browser = BrowserManager(fp)
        simulator = None

        try:
            # Setup browser with unique fingerprint
            driver = browser.setup()
            simulator = HumanSimulator(driver)

            logger.info(f"[{index}] Submitting: {lead.get('nama')} from {lead.get('kota')}")
            logger.info(f"    Fingerprint: {fp}")

            # Navigate to target
            driver.get(self.target_url)
            simulator.human_delay(2000, 4000)  # Page load

            # Simulate human behavior
            simulator.mouse_move_human(driver.find_element(By.TAG_NAME, "body"))
            simulator.scroll_naturally()

            # Fill form fields (adjust selectors based on actual site)
            # This is a template - modify based on VCBL form structure

            form_mapping = {
                "nama": ["input[name*='name']", "input[id*='name']", "#fullname", "//input[contains(@placeholder,'Nama')]"],
                "email": ["input[name*='email']", "input[type='email']", "#email"],
                "phone": ["input[name*='phone']", "input[name*='hp']", "#phone", "//input[contains(@placeholder,'08')]"],
                "kota": ["select[name*='city']", "select[name*='kota']", "#city"],
            }

            for field, selectors in form_mapping.items():
                value = lead.get(field, "")
                if not value:
                    continue

                for selector in selectors:
                    try:
                        if selector.startswith("//"):
                            elem = driver.find_element(By.XPATH, selector)
                        else:
                            elem = driver.find_element(By.CSS_SELECTOR, selector)

                        simulator.human_delay(300, 600)
                        simulator.type_like_human(elem, str(value))
                        logger.info(f"    Filled: {field} = {value}")
                        break
                    except NoSuchElementException:
                        continue
                    except Exception as e:
                        logger.warning(f"    Error filling {field}: {e}")

            # Additional fields from sheet
            if lead.get("birth"):
                birth_selectors = ["input[name*='birth']", "input[name*='tanggal']", "//input[contains(@placeholder,'Tanggal')]"]
                for selector in birth_selectors:
                    try:
                        elem = driver.find_element(By.XPATH, selector)
                        simulator.type_like_human(elem, lead.get("birth"))
                        break
                    except:
                        continue

            # Submit
            simulator.human_delay(1000, 2000)
            simulator.scroll_naturally()

            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "//button[contains(text(),'Submit')]",
                "//button[contains(text(),'Daftar')]",
                "//button[contains(text(),'Kirim')]",
                ".btn-submit",
                "#submit",
            ]

            submitted = False
            for selector in submit_selectors:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, selector)
                    simulator.mouse_move_human(btn)
                    btn.click()
                    submitted = True
                    logger.info(f"    Submitted!")
                    break
                except:
                    try:
                        btn = driver.find_element(By.XPATH, selector)
                        btn.click()
                        submitted = True
                        logger.info(f"    Submitted!")
                        break
                    except:
                        continue

            if submitted:
                simulator.human_delay(3000, 5000)

                # Check result
                page = driver.page_source.lower()
                if any(x in page for x in ["success", "terima kasih", "thank you", "selamat"]):
                    result["status"] = "success"
                    result["message"] = "Submitted successfully"
                elif any(x in page for x in ["error", "gagal", "failed"]):
                    result["status"] = "failed"
                    result["message"] = "Error on page"
                elif any(x in page for x in ["captcha", "challenge", "verifikasi"]):
                    result["status"] = "challenge"
                    result["message"] = "CAPTCHA/Challenge detected"
                else:
                    result["status"] = "unknown"
                    result["message"] = "Check manually"

            else:
                result["status"] = "failed"
                result["message"] = "Submit button not found"

            # Screenshot
            try:
                Path("screenshots").mkdir(exist_ok=True)
                screenshot_file = f"screenshots/lead_{index}_{datetime.now().strftime('%H%M%S')}.png"
                driver.save_screenshot(screenshot_file)
                result["screenshot"] = screenshot_file
            except:
                pass

        except TimeoutException:
            result["status"] = "failed"
            result["message"] = "Page load timeout"
        except Exception as e:
            result["status"] = "failed"
            result["message"] = str(e)
            logger.error(f"[{index}] Error: {e}")
        finally:
            browser.close()

        self.results.append(result)
        return result


# =============================================================================
# DATA LOADERS
# =============================================================================

def load_from_sheet(sheet_id: str) -> List[Dict]:
    """Load leads from Google Sheets."""
    if not GOOGLE_AVAILABLE:
        raise ImportError("Install gspread: pip install gspread google-auth")

    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(sheet_id).sheet1
    records = sheet.get_all_records()

    leads = []
    for row in records:
        # Normalize keys
        lead = {}
        for k, v in row.items():
            key = k.lower().strip()
            if "nama" in key or "name" in key:
                lead["nama"] = v
            elif "email" in key or "e-mail" in key:
                lead["email"] = v
            elif "phone" in key or "hp" in key or "telp" in key:
                lead["phone"] = v
            elif "kota" in key or "city" in key or "domisili" in key:
                lead["kota"] = v
            elif "birth" in key or "lahir" in key:
                lead["birth"] = v
        if lead.get("nama"):
            leads.append(lead)

    return leads


def load_from_csv(filepath: str) -> List[Dict]:
    """Load leads from CSV file."""
    leads = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append({k.lower().strip(): v.strip() for k, v in row.items()})
    return leads


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Lead Automation - Full Anti-Detection")
    parser.add_argument("--sheet-id", help="Google Sheets Spreadsheet ID")
    parser.add_argument("--csv", help="CSV file path")
    parser.add_argument("--target-url", required=True, help="Target form URL")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of leads (0=all)")
    parser.add_argument("--test", action="store_true", help="Test mode - no actual submission")
    parser.add_argument("--headless", action="store_true", help="Run headless")

    args = parser.parse_args()

    # Load leads
    if args.sheet_id:
        logger.info(f"Loading from Google Sheet: {args.sheet_id}")
        leads = load_from_sheet(args.sheet_id)
    elif args.csv:
        logger.info(f"Loading from CSV: {args.csv}")
        leads = load_from_csv(args.csv)
    else:
        print("Error: Use --sheet-id or --csv")
        return

    if args.limit > 0:
        leads = leads[:args.limit]

    logger.info(f"Loaded {len(leads)} leads")

    # Processor
    processor = LeadProcessor(args.target_url)

    print("\n" + "="*60)
    print("LEAD AUTOMATION - FULL ANTI-DETECTION")
    print("="*60)
    print(f"Target: {args.target_url}")
    print(f"Leads: {len(leads)}")
    print("="*60)

    for i, lead in enumerate(leads, 1):
        print(f"\n[{i}/{len(leads)}] Processing: {lead.get('nama', 'Unknown')}")

        if args.test:
            # Test mode - just show what would happen
            fp = FingerprintGenerator()
            print(f"    IP: Would rotate to {PROXY_HOST}")
            print(f"    UA: {fp.get_ua()[:50]}...")
            print(f"    City: {fp.get_city()['name']}")
            print(f"    Screen: {fp.get_screen()}")
            result = {"status": "test", "message": "Test mode"}
            processor.results.append(result)
        else:
            result = processor.submit(lead, i)

        print(f"    Status: {result['status'].upper()}")
        print(f"    Message: {result['message']}")
        if "city" in result:
            print(f"    City: {result['city']}")

        # Save progress
        with open("results_temp.json", "w") as f:
            json.dump(processor.results, f, indent=2)

        # Random delay between submissions
        if i < len(leads):
            delay = random.randint(TIMING["min_interval"], TIMING["max_interval"])
            print(f"\n    Waiting {delay//60}m {delay%60}s before next...")
            time.sleep(delay)

    # Save final results
    output_file = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(processor.results, f, indent=2)

    # Summary
    print("\n" + "="*60)
    print("AUTOMATION COMPLETE")
    print("="*60)

    success = sum(1 for r in processor.results if r["status"] == "success")
    failed = sum(1 for r in processor.results if r["status"] == "failed")
    challenge = sum(1 for r in processor.results if r["status"] == "challenge")
    test = sum(1 for r in processor.results if r["status"] == "test")

    print(f"\nResults:")
    print(f"  Total:    {len(processor.results)}")
    if test > 0:
        print(f"  Test:     {test}")
    print(f"  Success:  {success} ({success/max(1,len(processor.results)-test)*100:.0f}%)")
    print(f"  Failed:   {failed}")
    print(f"  Challenge:{challenge}")
    print(f"\nResults saved: {output_file}")
    print("="*60)


if __name__ == "__main__":
    main()
