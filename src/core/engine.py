"""Main lead submission engine."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from ..utils.config import get_settings
from ..utils.screenshot import save_screenshot
from ..utils.retry import async_retry_with_backoff

from ..antidetect.fingerprint import FingerprintGenerator
from ..antidetect.profile import BrowserProfile, ProfileManager
from ..antidetect.behavioral import BehavioralSimulator
from ..browser.launcher import BrowserLauncher, BrowserConfig
from ..proxy.rotator import ProxyRotator, ProxyConfig
from ..leads.manager import LeadManager, Lead
from .session import SessionManager, Session
from .exceptions import (
    ChallengeDetectedError,
    DetectionError,
    SubmissionError,
    TimeoutError,
)


@dataclass
class SubmissionResult:
    """Result of a lead submission."""

    lead_id: str
    success: bool
    message: str
    session_id: Optional[str] = None
    screenshot_path: Optional[str] = None
    challenge_type: Optional[str] = None
    retry_count: int = 0
    duration_seconds: float = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "lead_id": self.lead_id,
            "success": self.success,
            "message": self.message,
            "session_id": self.session_id,
            "screenshot_path": self.screenshot_path,
            "challenge_type": self.challenge_type,
            "retry_count": self.retry_count,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class SubmissionConfig:
    """Configuration for lead submission."""

    target_url: str
    parallel: int = 1
    delay_between: float = 5.0
    max_retries: int = 3
    retry_delay: float = 30.0
    timeout: int = 120
    headless: bool = False
    save_screenshots: bool = True
    screenshot_dir: str = "logs/screenshots"
    stop_on_challenge: bool = True
    stop_on_detection: bool = True
    validate_before_submit: bool = True

    # Selector mappings (customizable per target)
    form_selectors: Dict[str, str] = field(default_factory=lambda: {
        "name": 'input[name="name"]',
        "first_name": 'input[name="first_name"]',
        "last_name": 'input[name="last_name"]',
        "email": 'input[name="email"]',
        "phone": 'input[name="phone"]',
        "age": 'input[name="age"]',
        "city": 'input[name="city"]',
        "state": 'input[name="state"]',
        "zip_code": 'input[name="zip"]',
        "country": 'select[name="country"]',
        "submit": 'button[type="submit"]',
    })

    # Custom submit script
    submit_script: Optional[Callable] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "target_url": self.target_url,
            "parallel": self.parallel,
            "delay_between": self.delay_between,
            "max_retries": self.max_retries,
            "headless": self.headless,
            "stop_on_challenge": self.stop_on_challenge,
        }


class LeadSubmissionEngine:
    """
    Main engine for lead submission automation.

    Orchestrates:
    - Proxy rotation
    - Fingerprint generation
    - Browser launching
    - Lead submission
    - Result logging
    """

    def __init__(
        self,
        config: Optional[SubmissionConfig] = None,
        proxy_rotator: Optional[ProxyRotator] = None,
        session_manager: Optional[SessionManager] = None,
        lead_manager: Optional[LeadManager] = None,
    ):
        """Initialize the submission engine."""
        self.config = config
        self.settings = get_settings()

        self.proxy_rotator = proxy_rotator or ProxyRotator()
        self.session_manager = session_manager or SessionManager()
        self.lead_manager = lead_manager or LeadManager()

        self.fingerprint_gen = FingerprintGenerator()
        self.profile_manager = ProfileManager()
        self.browser_launcher = BrowserLauncher()

        self._running = False
        self._current_session: Optional[Session] = None
        self._current_proxy: Optional[ProxyConfig] = None

        # Progress tracking
        self._progress = {
            "total": 0,
            "completed": 0,
            "success": 0,
            "failed": 0,
            "challenges": 0,
        }

        logger.info("LeadSubmissionEngine initialized")

    async def submit_lead(
        self,
        lead_data: Dict[str, Any],
        config: Optional[SubmissionConfig] = None,
    ) -> SubmissionResult:
        """
        Submit a single lead.

        Args:
            lead_data: Lead data dictionary
            config: Optional submission config override

        Returns:
            SubmissionResult
        """
        start_time = time.time()
        cfg = config or self.config

        if not cfg:
            raise ValueError("No submission config provided")

        lead_id = lead_data.get("id", str(datetime.utcnow().timestamp()))
        retry_count = 0
        proxy = None

        while retry_count <= cfg.max_retries:
            try:
                # Get proxy
                proxy = await self.proxy_rotator.get_proxy(
                    country=lead_data.get("country")
                )

                if not proxy:
                    return SubmissionResult(
                        lead_id=lead_id,
                        success=False,
                        message="No proxy available",
                        retry_count=retry_count,
                        duration_seconds=time.time() - start_time,
                    )

                self._current_proxy = proxy
                logger.debug(f"Using proxy: {proxy.host}:{proxy.port}")

                # Generate fingerprint
                fingerprint = self.fingerprint_gen.generate(
                    country=proxy.country,
                )

                # Create session
                session = await self.session_manager.create_session(
                    proxy_host=proxy.host,
                    proxy_country=proxy.country,
                    fingerprint_id=fingerprint.id,
                    metadata={
                        "lead_id": lead_id,
                        "browser": cfg.headless and "headless" or "normal",
                    }
                )
                self._current_session = session

                # Build browser config
                browser_config = self._build_browser_config(
                    fingerprint=fingerprint,
                    proxy=proxy,
                    headless=cfg.headless,
                )

                # Launch browser
                browser = await self.browser_launcher.launch(browser_config)

                try:
                    # Navigate to target
                    logger.debug(f"Navigating to {cfg.target_url}")
                    await browser.goto(cfg.target_url)

                    # Wait for page to stabilize
                    await asyncio.sleep(2)

                    # Check for challenges
                    challenge = await browser.check_for_challenge()
                    if challenge["has_challenge"]:
                        screenshot = None
                        if cfg.save_screenshots:
                            screenshot = await save_screenshot(
                                browser.get_page(),
                                f"challenge_{lead_id}",
                                cfg.screenshot_dir,
                            )

                        if cfg.stop_on_challenge:
                            raise ChallengeDetectedError(
                                challenge["challenge_type"],
                                challenge["message"],
                            )

                    # Submit form
                    if cfg.submit_script:
                        await cfg.submit_script(browser, lead_data)
                    else:
                        await self._submit_form(browser, lead_data, cfg)

                    # Success!
                    screenshot = None
                    if cfg.save_screenshots:
                        screenshot = await save_screenshot(
                            browser.get_page(),
                            f"success_{lead_id}",
                            cfg.screenshot_dir,
                        )

                    # Record success
                    session.record_success()
                    self.proxy_rotator.record_success(proxy)
                    self._progress["success"] += 1

                    duration = time.time() - start_time
                    self._progress["completed"] += 1

                    logger.info(f"Successfully submitted lead {lead_id} in {duration:.2f}s")

                    return SubmissionResult(
                        lead_id=lead_id,
                        success=True,
                        message="Submission successful",
                        session_id=session.id,
                        screenshot_path=screenshot,
                        duration_seconds=duration,
                        metadata={
                            "proxy": proxy.host,
                            "country": proxy.country,
                        }
                    )

                finally:
                    await browser.close()

            except ChallengeDetectedError as e:
                logger.warning(f"Challenge detected for lead {lead_id}: {e.challenge_type}")
                self._progress["challenges"] += 1

                duration = time.time() - start_time
                self._progress["completed"] += 1

                return SubmissionResult(
                    lead_id=lead_id,
                    success=False,
                    message=str(e),
                    session_id=self._current_session.id if self._current_session else None,
                    challenge_type=e.challenge_type,
                    retry_count=retry_count,
                    duration_seconds=duration,
                )

            except asyncio.TimeoutError:
                logger.error(f"Timeout for lead {lead_id}")
                retry_count += 1
                duration = time.time() - start_time

                if retry_count <= cfg.max_retries:
                    logger.info(f"Retrying lead {lead_id} in {cfg.retry_delay}s...")
                    await asyncio.sleep(cfg.retry_delay)
                else:
                    self._record_failure(session, proxy)
                    return SubmissionResult(
                        lead_id=lead_id,
                        success=False,
                        message=f"Timeout after {cfg.max_retries} retries",
                        session_id=self._current_session.id if self._current_session else None,
                        retry_count=retry_count,
                        duration_seconds=duration,
                    )

            except Exception as e:
                logger.error(f"Submission error for {lead_id}: {type(e).__name__}: {e}")
                retry_count += 1

                self._record_failure(session, proxy)

                if retry_count <= cfg.max_retries:
                    logger.info(f"Retrying lead {lead_id} in {cfg.retry_delay}s...")
                    await asyncio.sleep(cfg.retry_delay)
                else:
                    duration = time.time() - start_time
                    self._progress["failed"] += 1
                    self._progress["completed"] += 1

                    return SubmissionResult(
                        lead_id=lead_id,
                        success=False,
                        message=f"Failed after {cfg.max_retries} retries: {str(e)}",
                        session_id=self._current_session.id if self._current_session else None,
                        retry_count=retry_count,
                        duration_seconds=duration,
                    )

        # Final failure
        duration = time.time() - start_time
        return SubmissionResult(
            lead_id=lead_id,
            success=False,
            message=f"Failed after {cfg.max_retries} retries",
            retry_count=retry_count,
            duration_seconds=duration,
        )

    def _build_browser_config(
        self,
        fingerprint,
        proxy: ProxyConfig,
        headless: bool = False,
    ) -> BrowserConfig:
        """Build browser configuration from fingerprint and proxy."""
        return BrowserConfig(
            fingerprint=fingerprint,
            proxy_host=proxy.host,
            proxy_port=proxy.port,
            proxy_username=proxy.username,
            proxy_password=proxy.password,
            headless=headless,
            window_width=fingerprint.screen_width,
            window_height=fingerprint.screen_height,
            use_stealth=True,
            behavioral_simulator=True,
        )

    async def _submit_form(
        self,
        browser,
        lead_data: Dict[str, Any],
        config: SubmissionConfig,
    ) -> None:
        """Submit form with lead data."""
        page = browser.get_page()

        # Map lead fields to form selectors
        field_mappings = config.form_selectors

        # Get behavioral simulator
        behavior = BehavioralSimulator()

        # Fill form fields with human-like behavior
        for field_name, selector in field_mappings.items():
            if field_name == "submit":
                continue

            value = lead_data.get(field_name)
            if value:
                try:
                    # Check if selector exists
                    element = await page.query_selector(selector)
                    if not element:
                        logger.debug(f"Selector not found: {selector}")
                        continue

                    # Get element position for human-like movement
                    box = await element.bounding_box()
                    if box:
                        # Move mouse to element
                        cx = box["x"] + box["width"] / 2
                        cy = box["y"] + box["height"] / 2
                        await behavior.move_mouse(browser, (cx - 50, cy - 50), (cx, cy))

                    # Clear existing value
                    await element.click()

                    # Type with human-like behavior
                    if "select" in selector.lower():
                        await browser.select_option(selector, str(value))
                    else:
                        await behavior.type_with_log_normal(browser, str(value))

                    # Small random delay
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.debug(f"Could not fill {field_name}: {e}")

        # Submit form
        submit_selector = field_mappings.get("submit")
        if submit_selector:
            try:
                element = await page.query_selector(submit_selector)
                if element:
                    box = await element.bounding_box()
                    if box:
                        cx = box["x"] + box["width"] / 2
                        cy = box["y"] + box["height"] / 2
                        await behavior.move_mouse(browser, (cx - 20, cy - 20), (cx, cy))
                        await asyncio.sleep(0.1)
                        await behavior.click(browser, cx, cy)

                await asyncio.sleep(2)  # Wait for submission
            except Exception as e:
                logger.debug(f"Could not submit: {e}")

    def _record_failure(
        self,
        session: Optional[Session],
        proxy: Optional[ProxyConfig],
    ) -> None:
        """Record a failed submission."""
        if session:
            session.record_failure()
        if proxy:
            self.proxy_rotator.record_failure(proxy)
        self._progress["failed"] += 1
        self._progress["completed"] += 1

    async def submit_batch(
        self,
        leads: List[Dict[str, Any]],
        config: Optional[SubmissionConfig] = None,
        progress_callback: Optional[Callable[[int, int, SubmissionResult], None]] = None,
    ) -> List[SubmissionResult]:
        """Submit multiple leads."""
        cfg = config or self.config
        if not cfg:
            raise ValueError("No submission config provided")

        results = []
        total = len(leads)
        self._progress["total"] = total
        self._running = True

        logger.info(f"Starting batch submission of {total} leads")

        for i, lead_data in enumerate(leads):
            if not self._running:
                logger.info("Submission stopped by user")
                break

            lead_id = lead_data.get("id", f"lead_{i}")
            logger.info(f"Submitting lead {i + 1}/{total}: {lead_id}")

            result = await self.submit_lead(lead_data, config)
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, total, result)

            # Delay between submissions
            if i < total - 1 and cfg.delay_between > 0 and self._running:
                logger.debug(f"Waiting {cfg.delay_between}s before next submission...")
                await asyncio.sleep(cfg.delay_between)

        # End session
        if self._current_session:
            await self.session_manager.end_session(self._current_session.id)
            self._current_session = None

        # Summary
        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count
        challenge_count = sum(1 for r in results if r.challenge_type)

        logger.info(
            f"Batch submission complete: "
            f"{success_count} success, {fail_count} failed, "
            f"{challenge_count} challenges "
            f"({success_count / len(results) * 100:.1f}% success rate)"
        )

        return results

    async def submit_from_file(
        self,
        filepath: str,
        config: Optional[SubmissionConfig] = None,
    ) -> List[SubmissionResult]:
        """Submit leads from a file."""
        from ..leads.parser import LeadParser

        parser = LeadParser()
        result = parser.parse_file(filepath)

        if result.errors:
            logger.warning(f"Parse errors: {result.errors[:5]}")

        logger.info(f"Loaded {len(result.leads)} leads from {filepath}")

        return await self.submit_batch(result.leads, config)

    def stop(self) -> None:
        """Stop the submission engine."""
        self._running = False
        logger.info("Submission engine stopped")

    def get_progress(self) -> Dict[str, Any]:
        """Get current progress."""
        progress = self._progress.copy()
        if progress["total"] > 0:
            progress["percent"] = progress["completed"] / progress["total"] * 100
        else:
            progress["percent"] = 0
        return progress

    async def get_stats(self) -> Dict[str, Any]:
        """Get submission statistics."""
        session_stats = await self.session_manager.get_session_stats()
        proxy_stats = self.proxy_rotator.get_stats()

        return {
            "sessions": session_stats,
            "proxies": proxy_stats,
            "progress": self.get_progress(),
            "engine_status": "running" if self._running else "stopped",
        }

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.session_manager.end_all()
        logger.info("Engine cleanup complete")
