#!/usr/bin/env python3
"""
Prulady Lead Submission Automation
=================================
Target: https://www.vcbl.id/leads/register/prudential?product=prulady&source=cuanpintar

Usage:
    python prulady_submit.py --leads data/leads.csv --parallel 3
"""

import asyncio
import csv
import argparse
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

from src.antidetect import (
    TLSFingerprintGenerator,
    HTTP2FingerprintGenerator,
    CanvasSpoofGenerator,
    WebGLSpoofGenerator,
    AudioSpoofGenerator,
    MLResistantBehavioralSimulator,
    NetworkLayer,
    CaptchaSolver,
)
from src.proxy import ProxyRotator, ProxyConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LeadData:
    """Lead data structure."""
    nama: str
    tanggal_lahir: str  # dd/mm/yyyy
    phone: str
    email: str
    kota: str
    persetujuan: str = "Ya, Janji Temu Tatap Muka"
    meeting_day: str = "Weekday"
    meeting_time: str = "Siang Hari"


# Indonesian cities for dropdown
KOTA_OPTIONS = [
    "Jakarta", "Bandung", "Surabaya", "Medan", "Semarang",
    "Yogyakarta", "Malang", "Palembang", "Makassar", "Denpasar",
    "Bogor", "Depok", "Tangerang", "Bekasi", "Batam",
    "Pontianak", "Samarinda", "Banjarmasin", "Manado", "Lampung"
]


class PruladySubmitter:
    """Prulady form submission automation."""

    def __init__(
        self,
        parallel: int = 3,
        delay: int = 5,
        use_proxy: bool = False,
        solve_captcha: bool = True,
    ):
        self.parallel = parallel
        self.delay = delay
        self.use_proxy = use_proxy
        self.solve_captcha = solve_captcha

        # Initialize anti-detection modules
        self.tls_gen = TLSFingerprintGenerator()
        self.http2_gen = HTTP2FingerprintGenerator()
        self.canvas_gen = CanvasSpoofGenerator()
        self.webgl_gen = WebGLSpoofGenerator()
        self.audio_gen = AudioSpoofGenerator()
        self.behavior = MLResistantBehavioralSimulator()
        self.network = NetworkLayer()

        if solve_captcha:
            self.captcha_solver = CaptchaSolver()

        if use_proxy:
            self.proxy_rotator = ProxyRotator()

        logger.info(f"PruladySubmitter initialized (parallel={parallel}, delay={delay}s)")

    async def submit_lead(self, lead: LeadData, session_id: int) -> dict:
        """
        Submit a single lead to Prulady form.

        Args:
            lead: Lead data
            session_id: Session identifier for logging

        Returns:
            Dict with submission result
        """
        result = {
            "success": False,
            "name": lead.nama,
            "email": lead.email,
            "error": None,
        }

        try:
            # Get proxy if enabled
            proxy = None
            if self.use_proxy:
                proxy = self.proxy_rotator.get_next()
                logger.info(f"Session {session_id}: Using proxy {proxy.host}:{proxy.port}")

            # Generate fresh fingerprints
            tls_fp = self.tls_gen.generate()
            http2_fp = self.http2_gen.generate()
            canvas_fp = self.canvas_gen.generate()
            webgl_fp = self.webgl_gen.generate()
            audio_fp = self.audio_gen.generate()

            # Create network layer with fingerprints
            browser = await self.network.create_browser(
                fingerprints={
                    "tls": tls_fp,
                    "http2": http2_fp,
                    "canvas": canvas_fp,
                    "webgl": webgl_fp,
                    "audio": audio_fp,
                },
                proxy=proxy,
            )

            page = browser.new_page()

            # Navigate to form
            form_url = "https://www.vcbl.id/leads/register/prudential?product=prulady&source=cuanpintar"
            await page.goto(form_url)
            await asyncio.sleep(2)

            # === PAGE 1: Basic Info ===
            logger.info(f"Session {session_id}: Filling Page 1 for {lead.nama}")

            # Step 1: Gender (must be female)
            await self.behavior.click(page, selector='input[value="Ya, Saya Perempuan"]')
            await asyncio.sleep(0.5)

            # Step 2: Full Name
            name_input = await page.query_selector('input[name*="nama" i], input[placeholder*="Nama"]')
            if name_input:
                await self.behavior.type_text(page, lead.nama)
            await asyncio.sleep(0.3)

            # Step 3: Date of Birth
            dob_input = await page.query_selector('input[placeholder*="dd/mm/yyyy"], input[name*="tanggal" i]')
            if dob_input:
                await self.behavior.type_text(page, lead.tanggal_lahir)
            await asyncio.sleep(0.3)

            # Step 4: Phone Number
            phone_input = await page.query_selector('input[name*="phone" i], input[placeholder*="Handphone"]')
            if phone_input:
                await self.behavior.type_text(page, lead.phone)
            await asyncio.sleep(0.3)

            # Step 5: Email
            email_input = await page.query_selector('input[name*="email" i], input[placeholder*="Email"]')
            if email_input:
                await self.behavior.type_text(page, lead.email)
            await asyncio.sleep(0.3)

            # Step 6: City (dropdown)
            city_select = await page.query_selector('select[name*="kota" i], select')
            if city_select:
                await city_select.select(lead.kota)
            await asyncio.sleep(0.3)

            # Step 7: Consent
            persetujuan_map = {
                "Ya, Janji Temu Tatap Muka": 'input[value*="Janji Temu"]',
                "Ya, WhatsApp": 'input[value*="WhatsApp"]',
            }
            consent_selector = persetujuan_map.get(lead.persetujuan, persetujuan_map["Ya, Janji Temu Tatap Muka"])
            await self.behavior.click(page, selector=consent_selector)
            await asyncio.sleep(0.5)

            # Click NEXT
            next_btn = await page.query_selector('button:has-text("NEXT"), input[value="NEXT"]')
            if next_btn:
                await self.behavior.click(page, selector='button:has-text("NEXT")')
                await asyncio.sleep(2)

            # === PAGE 2: Meeting Preferences ===
            logger.info(f"Session {session_id}: Filling Page 2")

            # Meeting Day
            day_selector = 'input[value*="Weekday"], input[value*="Weekend"]'
            if lead.meeting_day == "Weekend":
                day_selector = 'input[value*="Weekend"]'
            await self.behavior.click(page, selector=day_selector)
            await asyncio.sleep(0.3)

            # Meeting Time
            time_selector = 'input[value*="Siang"]'
            if lead.meeting_time == "Pagi":
                time_selector = 'input[value*="Pagi"]'
            elif lead.meeting_time == "Sore":
                time_selector = 'input[value*="Sore"]'
            await self.behavior.click(page, selector=time_selector)
            await asyncio.sleep(0.5)

            # Check for CAPTCHA
            captcha_detected = await page.query_selector('[class*="captcha"], #captcha, .g-recaptcha')
            if captcha_detected and self.solve_captcha:
                logger.info(f"Session {session_id}: CAPTCHA detected, solving...")
                captcha_image = await page.screenshot()
                captcha_solution = await self.captcha_solver.solve_image(captcha_image)
                # Enter captcha solution...

            # Click SUBMIT
            submit_btn = await page.query_selector('button:has-text("SUBMIT"), input[value="SUBMIT"]')
            if submit_btn:
                await self.behavior.click(page, selector='button:has-text("SUBMIT")')
                await asyncio.sleep(3)

            # Check result
            success_indicators = [
                "terima kasih",
                "thank you",
                "success",
                "berhasil",
            ]
            page_text = await page.content()
            if any(ind in page_text.lower() for ind in success_indicators):
                result["success"] = True
                logger.info(f"Session {session_id}: ✓ Lead {lead.nama} submitted successfully!")
            else:
                result["error"] = "Unknown - check screenshot"
                logger.warning(f"Session {session_id}: Unknown result for {lead.nama}")

            await page.screenshot(f"logs/screenshots/{lead.nama}_{session_id}.png")
            await browser.close()

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Session {session_id}: Error submitting {lead.nama}: {e}")

        return result

    async def submit_batch(self, leads: List[LeadData]) -> List[dict]:
        """
        Submit multiple leads with parallel processing.

        Args:
            leads: List of lead data

        Returns:
            List of submission results
        """
        results = []

        # Process in batches
        for i in range(0, len(leads), self.parallel):
            batch = leads[i:i + self.parallel]
            tasks = [
                self.submit_lead(lead, session_id=i + j)
                for j, lead in enumerate(batch)
            ]

            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            # Delay between batches
            if i + self.parallel < len(leads):
                logger.info(f"Sleeping {self.delay}s before next batch...")
                await asyncio.sleep(self.delay)

        return results


def load_leads_from_csv(csv_path: str) -> List[LeadData]:
    """Load leads from CSV file."""
    leads = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(LeadData(
                nama=row.get('nama', ''),
                tanggal_lahir=row.get('tanggal_lahir', row.get('dob', '')),
                phone=row.get('phone', row.get('no_hp', '')),
                email=row.get('email', ''),
                kota=row.get('kota', row.get('kota_domisili', 'Jakarta')),
            ))
    return leads


async def main():
    parser = argparse.ArgumentParser(description="Prulady Lead Submission")
    parser.add_argument("--leads", required=True, help="Path to leads CSV file")
    parser.add_argument("--parallel", type=int, default=3, help="Parallel submissions")
    parser.add_argument("--delay", type=int, default=5, help="Delay between batches (seconds)")
    parser.add_argument("--use-proxy", action="store_true", help="Use proxy rotation")
    parser.add_argument("--no-captcha", action="store_true", help="Skip CAPTCHA solving")
    args = parser.parse_args()

    # Load leads
    leads = load_leads_from_csv(args.leads)
    logger.info(f"Loaded {len(leads)} leads from {args.leads}")

    # Create submitter
    submitter = PruladySubmitter(
        parallel=args.parallel,
        delay=args.delay,
        use_proxy=args.use_proxy,
        solve_captcha=not args.no_captcha,
    )

    # Submit all leads
    results = await submitter.submit_batch(leads)

    # Summary
    success = sum(1 for r in results if r["success"])
    failed = len(results) - success

    logger.info("=" * 50)
    logger.info(f"Submission Complete!")
    logger.info(f"Total: {len(results)}")
    logger.info(f"Success: {success}")
    logger.info(f"Failed: {failed}")
    logger.info("=" * 50)

    # Save results
    with open("logs/submission_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["success", "name", "email", "error"])
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    asyncio.run(main())
