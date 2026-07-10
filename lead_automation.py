#!/usr/bin/env python3
"""
Lead Automation Script - Google Sheets to Prulady
Indonesia-Focused with Natural Human Timing

Usage:
    python3 lead_automation.py --sheet-id "SPREADSHEET_ID" --target-url "https://prulady.com/form"

Requirements:
    pip install gspread google-auth selenium webdriver-manager
"""

import argparse
import csv
import json
import random
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# For Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("Warning: gspread not installed. Use --csv instead of --sheet-id")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Indonesian cities for geo-targeting
CITY_TO_REGION = {
    "jakarta": "jabodetabek", "bekasi": "jabodetabek", "depok": "jabodetabek",
    "bogor": "jabodetabek", "tangerang": "jabodetabek", "cilegon": "jabodetabek",
    "bandung": "jawa_barat", "cirebon": "jawa_barat", "sukabumi": "jawa_barat",
    "semarang": "jawa_tengah", "yogyakarta": "jawa_tengah", "solo": "jawa_tengah",
    "surabaya": "jawa_timur", "malang": "jawa_timur", "sidoarjo": "jawa_timur",
    "medan": "sumatera_utara", "palembang": "sumatera_selatan",
    "makassar": "sulawesi_selatan", "manado": "sulawesi_utara",
    "denpasar": "bali", "jayapura": "papua",
}

# IP Prefixes by region
IP_PREFIXES = {
    "jabodetabek": ["101.128.", "114.4.", "116.12.", "180.214.", "182.253."],
    "jawa_barat": ["125.160.", "222.124.", "180.250.", "202.62."],
    "jawa_tengah": ["180.243.", "114.125.", "125.214."],
    "jawa_timur": ["36.91.", "114.127.", "180.249."],
    "sumatera_utara": ["139.192.", "180.243.", "114.125."],
    "sumatera_selatan": ["125.160.", "180.243.", "114.125."],
    "sulawesi_selatan": ["180.214.", "114.5.", "116.58."],
    "sulawesi_utara": ["180.214.", "114.5.", "116.58."],
    "bali": ["36.84.", "114.57.", "180.248."],
    "papua": ["202.62.", "116.66.", "180.250."],
}

# Human timing patterns
TIMING_CONFIG = {
    "base_interval_minutes": 8,
    "interval_variance_minutes": 12,
    "work_hours_only": True,
    "work_start_hour": 8,
    "work_end_hour": 21,
    "night_multiplier": 0.1,
    "lunch_boost": True,
}


# =============================================================================
# FINGERPRINT GENERATOR
# =============================================================================

class FingerprintGenerator:
    """Generate browser fingerprints for anti-detection."""

    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        ]

    def get_random_ua(self) -> str:
        return random.choice(self.user_agents)

    def get_screen_resolution(self) -> tuple:
        resolutions = [
            (1920, 1080), (1366, 768), (1536, 864),
            (1440, 900), (1280, 720), (1600, 900)
        ]
        return random.choice(resolutions)

    def get_timezone(self, region: str) -> dict:
        """Return timezone based on Indonesian region."""
        timezones = {
            "jabodetabek": ("Asia/Jakarta", 420),
            "jawa_barat": ("Asia/Jakarta", 420),
            "jawa_tengah": ("Asia/Jakarta", 420),
            "jawa_timur": ("Asia/Jakarta", 420),
            "sumatera_utara": ("Asia/Jakarta", 420),
            "sumatera_selatan": ("Asia/Jakarta", 420),
            "sulawesi_selatan": ("Asia/Makassar", 480),
            "sulawesi_utara": ("Asia/Makassar", 480),
            "bali": ("Asia/Makassar", 480),
            "papua": ("Asia/Jayapura", 540),
        }
        return timezones.get(region, ("Asia/Jakarta", 420))


# =============================================================================
# BROWSER MANAGER
# =============================================================================

class BrowserManager:
    """Manage browser instances with anti-detection features."""

    def __init__(self, region: str, city: str, proxy_config: dict = None):
        self.region = region
        self.city = city
        self.proxy_config = proxy_config
        self.fingerprint = FingerprintGenerator()
        self.driver = None

    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with anti-detection."""
        options = Options()

        # Basic anti-detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # User agent
        ua = self.fingerprint.get_random_ua()
        options.add_argument(f"--user-agent={ua}")

        # Screen resolution
        width, height = self.fingerprint.get_screen_resolution()
        options.add_argument(f"--window-size={width},{height}")

        # Timezone
        tz, offset = self.fingerprint.get_timezone(self.region)
        options.add_argument(f"--timezone={tz}")

        # Language
        options.add_argument("--lang=id-ID")
        options.add_experimental_option("prefs", {
            "intl.accept_languages": "id-ID,id,en-US,en"
        })

        # Proxy (if configured)
        if self.proxy_config and self.proxy_config.get("host"):
            proxy_url = self._build_proxy_url()
            options.add_argument(f"--proxy-server={proxy_url}")

        # Additional stealth options
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")

        # Create driver
        try:
            self.driver = webdriver.Chrome(options=options)
        except Exception as e:
            logger.warning(f"Chrome driver error: {e}. Using headless mode.")
            options.add_argument("--headless")
            self.driver = webdriver.Chrome(options=options)

        # Remove webdriver痕迹
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return self.driver

    def _build_proxy_url(self) -> str:
        """Build proxy URL from config."""
        cfg = self.proxy_config
        if cfg.get("username") and cfg.get("password"):
            return f"http://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}"
        return f"http://{cfg['host']}:{cfg['port']}"

    def close(self):
        """Close browser."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


# =============================================================================
# LEAD PROCESSOR
# =============================================================================

class LeadProcessor:
    """Process leads with human-like behavior."""

    def __init__(self, target_url: str, proxy_config: dict = None):
        self.target_url = target_url
        self.proxy_config = proxy_config
        self.fingerprint = FingerprintGenerator()
        self.results = []

    def _calculate_delay(self) -> float:
        """Calculate human-like random delay."""
        now = datetime.now()
        hour = now.hour

        base = TIMING_CONFIG["base_interval_minutes"]
        variance = TIMING_CONFIG["interval_variance_minutes"]

        # Base delay with variance
        delay = base + random.uniform(-variance/2, variance/2)

        # Work hours adjustment
        if TIMING_CONFIG["work_hours_only"]:
            if hour < TIMING_CONFIG["work_start_hour"]:
                delay *= 3
            elif hour >= TIMING_CONFIG["work_end_hour"]:
                delay *= 4

        # Lunch boost
        if TIMING_CONFIG["lunch_boost"] and 12 <= hour < 13:
            delay *= 0.3

        # Night reduction
        if hour >= 22 or hour < 6:
            delay *= TIMING_CONFIG["night_multiplier"] * 10

        return max(1, delay) * 60  # Convert to seconds

    def _get_region_for_city(self, city: str) -> str:
        """Get region code for city."""
        city_lower = city.lower()
        for key, value in CITY_TO_REGION.items():
            if key in city_lower:
                return value
        return "jabodetabek"  # Default

    def _simulate_human_typing(self, element, text: str):
        """Type with human-like delays."""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))  # 50-150ms per character

    def _simulate_mouse_movement(self, driver):
        """Simulate human mouse movement."""
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(driver)

        # Random small movements
        for _ in range(random.randint(3, 8)):
            x = random.randint(100, 500)
            y = random.randint(100, 400)
            actions.move_by_offset(x, y)
            actions.pause(random.uniform(0.1, 0.3))

        actions.perform()

    def _generate_ip(self, region: str) -> str:
        """Generate realistic Indonesian IP."""
        prefixes = IP_PREFIXES.get(region, IP_PREFIXES["jabodetabek"])
        prefix = random.choice(prefixes)
        parts = prefix.rstrip(".").split(".")
        return f"{parts[0]}.{parts[1]}.{random.randint(1,255)}.{random.randint(1,254)}"

    def process_lead(self, lead: dict, index: int) -> dict:
        """Process single lead submission."""
        region = self._get_region_for_city(lead.get("kota", ""))
        simulated_ip = self._generate_ip(region)

        result = {
            "index": index,
            "nama": lead.get("nama", ""),
            "email": lead.get("email", ""),
            "phone": lead.get("phone", ""),
            "kota": lead.get("kota", ""),
            "region": region,
            "simulated_ip": simulated_ip,
            "status": "pending",
            "message": "",
            "timestamp": datetime.now().isoformat(),
        }

        browser = None

        try:
            # Setup browser
            browser = BrowserManager(region, lead.get("kota", ""), self.proxy_config)
            driver = browser.setup_driver()

            logger.info(f"[{index}] Processing: {lead.get('nama')} from {lead.get('kota')} (IP: {simulated_ip})")

            # Navigate to target
            driver.get(self.target_url)
            time.sleep(random.uniform(2, 4))  # Page load time

            # Simulate human behavior
            self._simulate_mouse_movement(driver)
            time.sleep(random.uniform(1, 2))

            # Fill form - adjust selectors based on actual website
            # This is a template - adjust based on Prulady's actual form
            form_mappings = {
                "nama": ["name", "full_name", "fullname", "nama", "//input[@name='name']"],
                "email": ["email", "//input[@type='email']", "//input[@name='email']"],
                "phone": ["phone", "mobile", "telepon", "//input[@name='phone']"],
                "kota": ["city", "kota", "location", "//select[@name='city']"],
            }

            # Try to fill fields (template - needs adjustment for actual Prulady form)
            for field_key, selectors in form_mappings.items():
                value = lead.get(field_key, "")
                if not value:
                    continue

                for selector in selectors:
                    try:
                        if selector.startswith("//"):
                            element = driver.find_element(By.XPATH, selector)
                        else:
                            element = driver.find_element(By.NAME, selector)

                        if "select" in selector.lower():
                            from selenium.webdriver.support.ui import Select
                            select = Select(element)
                            # Try to match option by text containing the value
                            for option in select.options:
                                if value.lower() in option.text.lower():
                                    select.select_by_visible_text(option.text)
                                    break
                        else:
                            self._simulate_human_typing(element, value)

                        logger.info(f"[{index}] Filled {field_key}: {value}")
                        break
                    except NoSuchElementException:
                        continue
                    except Exception as e:
                        logger.warning(f"[{index}] Error filling {field_key}: {e}")

            # Simulate more human behavior
            time.sleep(random.uniform(1, 3))
            self._simulate_mouse_movement(driver)

            # Find and click submit button
            submit_selectors = [
                "//button[@type='submit']",
                "//input[@type='submit']",
                "//button[contains(text(),'Submit')]",
                "//button[contains(text(),'Kirim')]",
                "//button[contains(text(),'Daftar')]",
                "//button[contains(text(),'Register')]",
            ]

            submitted = False
            for selector in submit_selectors:
                try:
                    submit_btn = driver.find_element(By.XPATH, selector)
                    submit_btn.click()
                    submitted = True
                    logger.info(f"[{index}] Submit button clicked")
                    break
                except NoSuchElementException:
                    continue

            if submitted:
                time.sleep(random.uniform(3, 5))  # Wait for response

                # Check for success/error
                page_source = driver.page_source.lower()
                if "success" in page_source or "terima kasih" in page_source or "thank you" in page_source:
                    result["status"] = "success"
                    result["message"] = "Submission successful"
                elif "error" in page_source or "gagal" in page_source:
                    result["status"] = "failed"
                    result["message"] = "Submission failed - error on page"
                elif "challenge" in page_source or "captcha" in page_source:
                    result["status"] = "challenge"
                    result["message"] = "Challenge/CAPTCHA detected"
                else:
                    result["status"] = "unknown"
                    result["message"] = "Response unclear - manual check needed"
            else:
                result["status"] = "failed"
                result["message"] = "Submit button not found"

            # Take screenshot
            try:
                screenshot_path = f"screenshots/lead_{index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                Path("screenshots").mkdir(exist_ok=True)
                driver.save_screenshot(screenshot_path)
                result["screenshot"] = screenshot_path
            except Exception as e:
                logger.warning(f"[{index}] Screenshot failed: {e}")

        except TimeoutException:
            result["status"] = "failed"
            result["message"] = "Page load timeout"
        except Exception as e:
            result["status"] = "failed"
            result["message"] = f"Error: {str(e)}"
            logger.error(f"[{index}] Processing error: {e}")
        finally:
            if browser:
                browser.close()

        self.results.append(result)
        return result


# =============================================================================
# DATA SOURCES
# =============================================================================

def load_from_google_sheet(sheet_id: str, worksheet_index: int = 0) -> List[Dict]:
    """Load leads from Google Sheets."""
    if not GOOGLE_SHEETS_AVAILABLE:
        raise ImportError("gspread not installed. Run: pip install gspread google-auth")

    # Setup credentials (uses service account)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scope)

    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).get_worksheet(worksheet_index)

    # Get all records
    records = sheet.get_all_records()

    # Convert to list of dicts with lowercase keys
    leads = []
    for record in records:
        lead = {k.lower().strip(): v for k, v in record.items()}
        # Normalize field names
        if "nama" not in lead and "name" in lead:
            lead["nama"] = lead.pop("name")
        if "email" not in lead and "e-mail" in lead:
            lead["email"] = lead.pop("e-mail")
        if "phone" not in lead and "telepon" in lead:
            lead["phone"] = lead.pop("telepon")
        if "kota" not in lead and "city" in lead:
            lead["kota"] = lead.pop("city")
        leads.append(lead)

    return leads


def load_from_csv(file_path: str) -> List[Dict]:
    """Load leads from CSV file."""
    leads = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append({k.lower().strip(): v.strip() for k, v in row.items()})
    return leads


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Lead Automation Script")
    parser.add_argument("--sheet-id", help="Google Sheets Spreadsheet ID")
    parser.add_argument("--csv", help="CSV file path (alternative to --sheet-id)")
    parser.add_argument("--target-url", required=True, help="Target form URL")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of leads (0 = all)")
    parser.add_argument("--proxy-host", default="", help="Proxy host")
    parser.add_argument("--proxy-port", type=int, default=0, help="Proxy port")
    parser.add_argument("--proxy-user", default="", help="Proxy username")
    parser.add_argument("--proxy-pass", default="", help="Proxy password")
    parser.add_argument("--no-delay", action="store_true", help="Skip delay between submissions")

    args = parser.parse_args()

    # Load leads
    if args.sheet_id:
        logger.info(f"Loading leads from Google Sheet: {args.sheet_id}")
        leads = load_from_google_sheet(args.sheet_id)
    elif args.csv:
        logger.info(f"Loading leads from CSV: {args.csv}")
        leads = load_from_csv(args.csv)
    else:
        print("Error: Either --sheet-id or --csv must be provided")
        return

    # Limit leads
    if args.limit > 0:
        leads = leads[:args.limit]

    logger.info(f"Loaded {len(leads)} leads")

    # Proxy config
    proxy_config = None
    if args.proxy_host:
        proxy_config = {
            "host": args.proxy_host,
            "port": args.proxy_port,
            "username": args.proxy_user,
            "password": args.proxy_pass,
        }

    # Create processor
    processor = LeadProcessor(args.target_url, proxy_config)

    # Process leads
    print("\n" + "="*60)
    print("STARTING LEAD AUTOMATION")
    print("="*60)

    for i, lead in enumerate(leads, 1):
        print(f"\n[{i}/{len(leads)}] Processing: {lead.get('nama', 'Unknown')}")

        result = processor.process_lead(lead, i)

        print(f"    Status: {result['status'].upper()}")
        print(f"    Message: {result['message']}")
        print(f"    IP: {result['simulated_ip']}")

        # Save intermediate results
        with open("results_temp.json", "w") as f:
            json.dump(processor.results, f, indent=2)

        # Calculate delay for next submission
        if not args.no_delay and i < len(leads):
            delay = processor._calculate_delay()
            print(f"\n    Waiting {delay/60:.1f} minutes before next submission...")
            time.sleep(delay)

    # Save final results
    output_file = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(processor.results, f, indent=2)

    # Print summary
    print("\n" + "="*60)
    print("AUTOMATION COMPLETE")
    print("="*60)

    success = sum(1 for r in processor.results if r["status"] == "success")
    failed = sum(1 for r in processor.results if r["status"] == "failed")
    challenge = sum(1 for r in processor.results if r["status"] == "challenge")
    unknown = sum(1 for r in processor.results if r["status"] == "unknown")

    print(f"\nResults Summary:")
    print(f"  Total:     {len(processor.results)}")
    print(f"  Success:   {success} ({success/len(processor.results)*100:.1f}%)")
    print(f"  Failed:    {failed}")
    print(f"  Challenge: {challenge}")
    print(f"  Unknown:   {unknown}")
    print(f"\nResults saved to: {output_file}")
    print("="*60)


if __name__ == "__main__":
    main()
