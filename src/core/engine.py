"""Main lead submission engine."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..utils.logger import get_logger
from ..utils.config import get_settings
from ..utils.screenshot import save_screenshot

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

logger = get_logger(__name__)


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
    form_selectors: Dict[str, str] = field(default_factory=lambda: {})

    # Custom submit script
    submit_script: Optional[Callable] = None


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
        """
        Initialize the submission engine.

        Args:
            config: Submission configuration
            proxy_rotator: Proxy rotator instance
            session_manager: Session manager instance
            lead_manager: Lead manager instance
        """
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

        while retry_count <= cfg.max_retries:
            try:
                # Get proxy
                proxy = await self.proxy_rotator.get_proxy()
                if not proxy:
                    return SubmissionResult(
                        lead_id=lead_id,
                        success=False,
                        message="No proxy available",
                    )

                # Generate fingerprint
                fingerprint = self.fingerprint_gen.generate(
                    country=proxy.country,
                )

                # Create session
                session = await self.session_manager.create_session(
                    proxy_host=proxy.host,
                    proxy_country=proxy.country,
                    fingerprint_id=fingerprint.id,
                )
                self._current_session = session

                # Build browser config
                browser_config = BrowserConfig(
                    fingerprint=fingerprint,
                    proxy_host=proxy.host,
                    proxy_port=proxy.port,
                    proxy_username=proxy.username,
                    proxy_password=proxy.password,
                    headless=cfg.headless,
                    window_width=fingerprint.screen_width,
                    window_height=fingerprint.screen_height,
                    use_stealth=True,
                    behavioral_simulator=True,
                )

                # Launch browser
                browser = await self.browser_launcher.launch(browser_config)

                try:
                    # Navigate to target
                    await browser.goto(cfg.target_url)
                    await asyncio.sleep(2)  # Wait for page load

                    # Check for challenges
                    challenge = await browser.check_for_challenge()
                    if challenge["has_challenge"]:
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

                    # Take success screenshot
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

                    duration = time.time() - start_time

                    return SubmissionResult(
                        lead_id=lead_id,
                        success=True,
                        message="Submission successful",
                        session_id=session.id,
                        screenshot_path=screenshot,
                        duration_seconds=duration,
                    )

                finally:
                    await browser.close()

            except ChallengeDetectedError as e:
                duration = time.time() - start_time
                return SubmissionResult(
                    lead_id=lead_id,
                    success=False,
                    message=str(e),
                    session_id=self._current_session.id if self._current_session else None,
                    challenge_type=e.challenge_type,
                    retry_count=retry_count,
                    duration_seconds=duration,
                )

            except Exception as e:
                logger.error(f"Submission error for {lead_id}: {e}")
                retry_count += 1

                if self._current_session:
                    self._current_session.record_failure()
                if proxy:
                    self.proxy_rotator.record_failure(proxy)

                if retry_count <= cfg.max_retries:
                    logger.info(f"Retrying in {cfg.retry_delay}s...")
                    await asyncio.sleep(cfg.retry_delay)

        # All retries exhausted
        duration = time.time() - start_time
        return SubmissionResult(
            lead_id=lead_id,
            success=False,
            message=f"Failed after {cfg.max_retries} retries",
            session_id=self._current_session.id if self._current_session else None,
            retry_count=retry_count,
            duration_seconds=duration,
        )

    async def _submit_form(
        self,
        browser,
        lead_data: Dict[str, Any],
        config: SubmissionConfig,
    ) -> None:
        """
        Submit form with lead data.

        Override this method for custom form handling.

        Args:
            browser: Browser instance
            lead_data: Lead data
            config: Submission config
        """
        page = browser.get_page()

        # Map lead fields to form selectors
        field_mappings = config.form_selectors or {
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
        }

        # Fill form fields
        for field_name, selector in field_mappings.items():
            if field_name == "submit":
                continue

            value = lead_data.get(field_name)
            if value:
                try:
                    # Check if it's a select
                    if "select" in selector.lower():
                        await browser.select_option(selector, str(value))
                    else:
                        await browser.fill(selector, str(value))

                    await asyncio.sleep(0.1)  # Small delay between fields

                except Exception as e:
                    logger.debug(f"Could not fill {field_name}: {e}")

        # Submit
        submit_selector = field_mappings.get("submit")
        if submit_selector:
            await browser.click(submit_selector)
            await asyncio.sleep(2)  # Wait for submission

    async def submit_batch(
        self,
        leads: List[Dict[str, Any]],
        config: Optional[SubmissionConfig] = None,
        progress_callback: Optional[Callable[[int, int, SubmissionResult], None]] = None,
    ) -> List[SubmissionResult]:
        """
        Submit multiple leads.

        Args:
            leads: List of lead data dictionaries
            config: Submission configuration
            progress_callback: Callback for progress updates

        Returns:
            List of SubmissionResult
        """
        cfg = config or self.config
        if not cfg:
            raise ValueError("No submission config provided")

        results = []
        total = len(leads)

        logger.info(f"Starting batch submission of {total} leads")

        for i, lead_data in enumerate(leads):
            if not self._running:
                logger.info("Submission stopped by user")
                break

            logger.info(f"Submitting lead {i + 1}/{total}: {lead_data.get('id', 'unknown')}")

            result = await self.submit_lead(lead_data, config)
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, total, result)

            # Delay between submissions
            if i < total - 1 and cfg.delay_between > 0:
                logger.debug(f"Waiting {cfg.delay_between}s before next submission...")
                await asyncio.sleep(cfg.delay_between)

        # End session
        if self._current_session:
            await self.session_manager.end_session(self._current_session.id)
            self._current_session = None

        # Summary
        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count

        logger.info(
            f"Batch submission complete: {success_count} success, {fail_count} failed "
            f"({success_count / len(results) * 100:.1f}% success rate)"
        )

        return results

    async def submit_from_file(
        self,
        filepath: str,
        config: Optional[SubmissionConfig] = None,
    ) -> List[SubmissionResult]:
        """
        Submit leads from a file.

        Args:
            filepath: Path to leads file
            config: Submission configuration

        Returns:
            List of SubmissionResult
        """
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

    async def get_stats(self) -> Dict[str, Any]:
        """Get submission statistics."""
        session_stats = await self.session_manager.get_session_stats()
        proxy_stats = self.proxy_rotator.get_stats()

        return {
            "sessions": session_stats,
            "proxies": proxy_stats,
            "engine_status": "running" if self._running else "stopped",
        }

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.session_manager.end_all()
        logger.info("Engine cleanup complete")
