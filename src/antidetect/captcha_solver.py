"""Captcha solver integration module.

This module provides integration with external captcha solving services:
- 2Captcha (primary)
- CapSolver (fallback)

Supported captcha types:
- reCAPTCHA v2/v2 Invisible
- reCAPTCHA v3
- hCaptcha
- Cloudflare Turnstile
- Image captchas
"""

from __future__ import annotations

import asyncio
import base64
import json
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from ..utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# PROVIDER CONFIGURATION
# =============================================================================

PROVIDERS = {
    "2captcha": {
        "name": "2Captcha",
        "solve_url": "https://2captcha.com/in.php",
        "result_url": "https://2captcha.com/res.php",
        "api_param": "key",
        "supports_recaptcha_v2": True,
        "supports_recaptcha_v3": True,
        "supports_hcaptcha": True,
        "supports_turnstile": True,
        "supports_image": True,
    },
    "capsolver": {
        "name": "CapSolver",
        "solve_url": "https://api.capsolver.com/createTask",
        "result_url": "https://api.capsolver.com/getTaskResult",
        "api_param": "clientKey",
        "supports_recaptcha_v2": True,
        "supports_recaptcha_v3": True,
        "supports_hcaptcha": True,
        "supports_turnstile": True,
        "supports_image": True,
    },
}


# =============================================================================
# CAPTCH RESPONSE MODEL
# =============================================================================

@dataclass
class CaptchaResponse:
    """Response from captcha solving."""

    success: bool
    token: Optional[str] = None
    provider: str = ""
    captcha_type: str = ""
    error: Optional[str] = None
    solve_time: float = 0
    cost: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "token": self.token,
            "provider": self.provider,
            "captcha_type": self.captcha_type,
            "error": self.error,
            "solve_time": self.solve_time,
            "cost": self.cost,
        }


# =============================================================================
# CAPTCHA SOLVER BASE
# =============================================================================

class BaseCaptchaSolver:
    """Base class for captcha solver providers."""

    def __init__(self, api_key: str):
        """
        Initialize solver.

        Args:
            api_key: API key for the service
        """
        self.api_key = api_key

    async def solve(
        self,
        captcha_type: str,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """
        Solve a captcha.

        Args:
            captcha_type: Type of captcha
            site_key: Site key from the target website
            url: URL where captcha appears
            **kwargs: Additional provider-specific parameters

        Returns:
            CaptchaResponse with solution
        """
        raise NotImplementedError

    async def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """Make HTTP request."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=data)
                else:
                    response = await client.post(url, data=data, headers=headers)

                return response.json()

        except ImportError:
            logger.error("httpx not installed")
            return {"status": "error", "error": "httpx not installed"}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"status": "error", "error": str(e)}


# =============================================================================
# 2CAPTCHA SOLVER
# =============================================================================

class TwoCaptchaSolver(BaseCaptchaSolver):
    """
    2Captcha solver implementation.

    Documentation: https://2captcha.com/2captcha-api
    """

    def __init__(self, api_key: str):
        """Initialize 2Captcha solver."""
        super().__init__(api_key)
        self.provider = "2captcha"
        self._base_url = PROVIDERS["2captcha"]["solve_url"]
        self._result_url = PROVIDERS["2captcha"]["result_url"]

    async def solve(
        self,
        captcha_type: str,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """
        Solve captcha using 2Captcha.

        Args:
            captcha_type: Type of captcha
            site_key: Site key
            url: Page URL
            **kwargs: Additional parameters

        Returns:
            CaptchaResponse
        """
        start_time = time.time()

        try:
            if captcha_type == "recaptcha_v2":
                return await self._solve_recaptcha_v2(site_key, url, **kwargs)
            elif captcha_type == "recaptcha_v3":
                return await self._solve_recaptcha_v3(site_key, url, **kwargs)
            elif captcha_type == "hcaptcha":
                return await self._solve_hcaptcha(site_key, url, **kwargs)
            elif captcha_type == "turnstile":
                return await self._solve_turnstile(site_key, url, **kwargs)
            elif captcha_type == "image":
                return await self._solve_image(site_key, **kwargs)
            else:
                return CaptchaResponse(
                    success=False,
                    provider=self.provider,
                    captcha_type=captcha_type,
                    error=f"Unknown captcha type: {captcha_type}",
                )

        except Exception as e:
            return CaptchaResponse(
                success=False,
                provider=self.provider,
                captcha_type=captcha_type,
                error=str(e),
                solve_time=time.time() - start_time,
            )

    async def _solve_recaptcha_v2(
        self,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """Solve reCAPTCHA v2."""
        data = {
            "key": self.api_key,
            "method": "userrecaptcha",
            "googlekey": site_key,
            "pageurl": url,
            "json": 1,
        }

        # Submit
        result = await self._make_request("POST", self._base_url, data=data)

        if result.get("status") != 1:
            return CaptchaResponse(
                success=False,
                provider=self.provider,
                captcha_type="recaptcha_v2",
                error=result.get("request", "Unknown error"),
            )

        captcha_id = result.get("request")

        # Poll for result
        return await self._poll_result(captcha_id, "recaptcha_v2")

    async def _solve_recaptcha_v3(
        self,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """Solve reCAPTCHA v3."""
        action = kwargs.get("action", "verify")
        min_score = kwargs.get("min_score", 0.3)

        data = {
            "key": self.api_key,
            "method": "userrecaptcha",
            "googlekey": site_key,
            "pageurl": url,
            "version": "v3",
            "action": action,
            "min_score": min_score,
            "json": 1,
        }

        result = await self._make_request("POST", self._base_url, data=data)

        if result.get("status") != 1:
            return CaptchaResponse(
                success=False,
                provider=self.provider,
                captcha_type="recaptcha_v3",
                error=result.get("request", "Unknown error"),
            )

        captcha_id = result.get("request")
        return await self._poll_result(captcha_id, "recaptcha_v3")

    async def _solve_hcaptcha(
        self,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """Solve hCaptcha."""
        data = {
            "key": self.api_key,
            "method": "hcaptcha",
            "sitekey": site_key,
            "pageurl": url,
            "json": 1,
        }

        result = await self._make_request("POST", self._base_url, data=data)

        if result.get("status") != 1:
            return CaptchaResponse(
                success=False,
                provider=self.provider,
                captcha_type="hcaptcha",
                error=result.get("request", "Unknown error"),
            )

        captcha_id = result.get("request")
        return await self._poll_result(captcha_id, "hcaptcha")

    async def _solve_turnstile(
        self,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """Solve Cloudflare Turnstile."""
        data = {
            "key": self.api_key,
            "method": "turnstile",
            "sitekey": site_key,
            "pageurl": url,
            "json": 1,
        }

        result = await self._make_request("POST", self._base_url, data=data)

        if result.get("status") != 1:
            return CaptchaResponse(
                success=False,
                provider=self.provider,
                captcha_type="turnstile",
                error=result.get("request", "Unknown error"),
            )

        captcha_id = result.get("request")
        return await self._poll_result(captcha_id, "turnstile")

    async def _solve_image(self, image_data: str, **kwargs) -> CaptchaResponse:
        """Solve image captcha."""
        data = {
            "key": self.api_key,
            "method": "base64",
            "body": image_data,
            "json": 1,
        }

        result = await self._make_request("POST", self._base_url, data=data)

        if result.get("status") != 1:
            return CaptchaResponse(
                success=False,
                provider=self.provider,
                captcha_type="image",
                error=result.get("request", "Unknown error"),
            )

        captcha_id = result.get("request")
        return await self._poll_result(captcha_id, "image")

    async def _poll_result(
        self,
        captcha_id: str,
        captcha_type: str,
        max_wait: int = 120,
    ) -> CaptchaResponse:
        """Poll for captcha result."""
        start_time = time.time()

        while time.time() - start_time < max_wait:
            await asyncio.sleep(5)

            result = await self._make_request(
                "GET",
                self._result_url,
                data={"key": self.api_key, "action": "get", "id": captcha_id, "json": 1},
            )

            if result.get("status") == 1:
                return CaptchaResponse(
                    success=True,
                    token=result.get("request"),
                    provider=self.provider,
                    captcha_type=captcha_type,
                    solve_time=time.time() - start_time,
                )

            if result.get("request") == "CAPCHA_NOT_READY":
                continue

            return CaptchaResponse(
                success=False,
                provider=self.provider,
                captcha_type=captcha_type,
                error=result.get("request", "Unknown error"),
                solve_time=time.time() - start_time,
            )

        return CaptchaResponse(
            success=False,
            provider=self.provider,
            captcha_type=captcha_type,
            error="Timeout waiting for solution",
            solve_time=time.time() - start_time,
        )


# =============================================================================
# CAPSOLVER
# =============================================================================

class CapSolver(BaseCaptchaSolver):
    """
    CapSolver implementation.

    Documentation: https://docs.capsolver.com
    """

    def __init__(self, api_key: str):
        """Initialize CapSolver."""
        super().__init__(api_key)
        self.provider = "capsolver"
        self._base_url = PROVIDERS["capsolver"]["solve_url"]
        self._result_url = PROVIDERS["capsolver"]["result_url"]

    async def solve(
        self,
        captcha_type: str,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """
        Solve captcha using CapSolver.

        Args:
            captcha_type: Type of captcha
            site_key: Site key
            url: Page URL
            **kwargs: Additional parameters

        Returns:
            CaptchaResponse
        """
        start_time = time.time()

        try:
            if captcha_type == "recaptcha_v2":
                return await self._solve_recaptcha_v2(site_key, url, **kwargs)
            elif captcha_type == "recaptcha_v3":
                return await self._solve_recaptcha_v3(site_key, url, **kwargs)
            elif captcha_type == "hcaptcha":
                return await self._solve_hcaptcha(site_key, url, **kwargs)
            elif captcha_type == "turnstile":
                return await self._solve_turnstile(site_key, url, **kwargs)
            elif captcha_type == "image":
                return await self._solve_image(site_key, **kwargs)
            else:
                return CaptchaResponse(
                    success=False,
                    provider=self.provider,
                    captcha_type=captcha_type,
                    error=f"Unknown captcha type: {captcha_type}",
                )

        except Exception as e:
            return CaptchaResponse(
                success=False,
                provider=self.provider,
                captcha_type=captcha_type,
                error=str(e),
                solve_time=time.time() - start_time,
            )

    def _get_task_type(self, captcha_type: str) -> str:
        """Map captcha type to CapSolver task type."""
        mapping = {
            "recaptcha_v2": "ReCaptchaV2Task",
            "recaptcha_v3": "ReCaptchaV3Task",
            "hcaptcha": "HCaptchaTask",
            "turnstile": "AntiCloudflareTask",
        }
        return mapping.get(captcha_type, "ReCaptchaV2Task")

    async def _solve_recaptcha_v2(
        self,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """Solve reCAPTCHA v2."""
        return await self._submit_and_poll(
            task_type="ReCaptchaV2Task",
            task_data={
                "type": "ReCaptchaV2Task",
                "websiteURL": url,
                "websiteKey": site_key,
            },
            captcha_type="recaptcha_v2",
        )

    async def _solve_recaptcha_v3(
        self,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """Solve reCAPTCHA v3."""
        action = kwargs.get("action", "verify")
        min_score = kwargs.get("min_score", 0.3)

        return await self._submit_and_poll(
            task_type="ReCaptchaV3Task",
            task_data={
                "type": "ReCaptchaV3Task",
                "websiteURL": url,
                "websiteKey": site_key,
                "pageAction": action,
                "minScore": min_score,
            },
            captcha_type="recaptcha_v3",
        )

    async def _solve_hcaptcha(
        self,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """Solve hCaptcha."""
        return await self._submit_and_poll(
            task_type="HCaptchaTask",
            task_data={
                "type": "HCaptchaTask",
                "websiteURL": url,
                "websiteKey": site_key,
            },
            captcha_type="hcaptcha",
        )

    async def _solve_turnstile(
        self,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """Solve Cloudflare Turnstile."""
        return await self._submit_and_poll(
            task_type="AntiCloudflareTask",
            task_data={
                "type": "AntiCloudflareTask",
                "websiteURL": url,
                "websiteKey": site_key,
            },
            captcha_type="turnstile",
        )

    async def _solve_image(self, image_data: str, **kwargs) -> CaptchaResponse:
        """Solve image captcha."""
        return await self._submit_and_poll(
            task_type="ImageToTextTask",
            task_data={
                "type": "ImageToTextTask",
                "body": image_data,
            },
            captcha_type="image",
        )

    async def _submit_and_poll(
        self,
        task_type: str,
        task_data: Dict,
        captcha_type: str,
        max_wait: int = 120,
    ) -> CaptchaResponse:
        """Submit task and poll for result."""
        start_time = time.time()

        # Submit task
        submit_data = {
            "clientKey": self.api_key,
            "task": task_data,
        }

        result = await self._make_request("POST", self._base_url, data=submit_data)

        if result.get("errorCode"):
            return CaptchaResponse(
                success=False,
                provider=self.provider,
                captcha_type=captcha_type,
                error=result.get("errorDescription", result.get("errorCode")),
                solve_time=time.time() - start_time,
            )

        task_id = result.get("taskId")
        if not task_id:
            return CaptchaResponse(
                success=False,
                provider=self.provider,
                captcha_type=captcha_type,
                error="No task ID returned",
                solve_time=time.time() - start_time,
            )

        # Poll for result
        return await self._poll_result(task_id, captcha_type, max_wait)

    async def _poll_result(
        self,
        task_id: str,
        captcha_type: str,
        max_wait: int = 120,
    ) -> CaptchaResponse:
        """Poll for task result."""
        start_time = time.time()

        while time.time() - start_time < max_wait:
            await asyncio.sleep(3)

            result = await self._make_request(
                "POST",
                self._result_url,
                data={"clientKey": self.api_key, "taskId": task_id},
            )

            if result.get("status") == "ready":
                solution = result.get("solution", {})
                token = solution.get("gRecaptchaResponse") or solution.get("token") or solution.get("text")

                return CaptchaResponse(
                    success=True,
                    token=token,
                    provider=self.provider,
                    captcha_type=captcha_type,
                    solve_time=time.time() - start_time,
                )

            if result.get("status") == "failed":
                return CaptchaResponse(
                    success=False,
                    provider=self.provider,
                    captcha_type=captcha_type,
                    error=result.get("errorDescription", "Task failed"),
                    solve_time=time.time() - start_time,
                )

        return CaptchaResponse(
            success=False,
            provider=self.provider,
            captcha_type=captcha_type,
            error="Timeout waiting for solution",
            solve_time=time.time() - start_time,
        )


# =============================================================================
# UNIFIED CAPTCHA SOLVER
# =============================================================================

class CaptchaSolver:
    """
    Unified captcha solver with provider fallback.

    This class provides:
    - Multiple provider support (2Captcha, CapSolver)
    - Automatic fallback between providers
    - Rate limiting
    - Cost tracking
    """

    def __init__(
        self,
        primary_provider: str = "2captcha",
        fallback_provider: Optional[str] = "capsolver",
    ):
        """
        Initialize captcha solver.

        Args:
            primary_provider: Primary provider name
            fallback_provider: Fallback provider name (optional)
        """
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider

        self._solvers: Dict[str, BaseCaptchaSolver] = {}
        self._api_keys: Dict[str, str] = {}

        # Statistics
        self._stats = {
            "total_solved": 0,
            "total_failed": 0,
            "by_provider": {},
            "by_type": {},
            "total_cost": 0,
        }

    def set_api_key(self, provider: str, api_key: str) -> None:
        """
        Set API key for a provider.

        Args:
            provider: Provider name
            api_key: API key
        """
        self._api_keys[provider] = api_key

        # Create solver instance
        if provider == "2captcha":
            self._solvers[provider] = TwoCaptchaSolver(api_key)
        elif provider == "capsolver":
            self._solvers[provider] = CapSolver(api_key)

    def _get_solver(self, provider: str) -> Optional[BaseCaptchaSolver]:
        """Get solver instance for provider."""
        if provider not in self._solvers and provider in self._api_keys:
            self.set_api_key(provider, self._api_keys[provider])

        return self._solvers.get(provider)

    async def solve(
        self,
        captcha_type: str,
        site_key: str,
        url: str,
        providers: Optional[List[str]] = None,
        **kwargs,
    ) -> CaptchaResponse:
        """
        Solve captcha with automatic fallback.

        Args:
            captcha_type: Type of captcha
            site_key: Site key
            url: Page URL
            providers: List of providers to try (in order)
            **kwargs: Additional parameters

        Returns:
            CaptchaResponse with solution
        """
        if providers is None:
            providers = [self.primary_provider]
            if self.fallback_provider:
                providers.append(self.fallback_provider)

        last_error = None

        for provider in providers:
            solver = self._get_solver(provider)
            if not solver:
                logger.warning(f"No solver configured for {provider}")
                continue

            logger.info(f"Trying {provider} for {captcha_type}")

            response = await solver.solve(captcha_type, site_key, url, **kwargs)

            if response.success:
                logger.info(f"Solved {captcha_type} with {provider} in {response.solve_time:.1f}s")
                self._update_stats(provider, captcha_type, response, success=True)
                return response

            last_error = response.error
            logger.warning(f"{provider} failed: {last_error}")
            self._update_stats(provider, captcha_type, response, success=False)

        # All providers failed
        return CaptchaResponse(
            success=False,
            provider=",".join(providers),
            captcha_type=captcha_type,
            error=last_error or "All providers failed",
        )

    async def solve_recaptcha_v2(
        self,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """Solve reCAPTCHA v2."""
        return await self.solve("recaptcha_v2", site_key, url, **kwargs)

    async def solve_recaptcha_v3(
        self,
        site_key: str,
        url: str,
        action: str = "verify",
        min_score: float = 0.3,
        **kwargs,
    ) -> CaptchaResponse:
        """Solve reCAPTCHA v3."""
        return await self.solve(
            "recaptcha_v3",
            site_key,
            url,
            action=action,
            min_score=min_score,
            **kwargs,
        )

    async def solve_hcaptcha(
        self,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """Solve hCaptcha."""
        return await self.solve("hcaptcha", site_key, url, **kwargs)

    async def solve_turnstile(
        self,
        site_key: str,
        url: str,
        **kwargs,
    ) -> CaptchaResponse:
        """Solve Cloudflare Turnstile."""
        return await self.solve("turnstile", site_key, url, **kwargs)

    async def solve_image(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        **kwargs,
    ) -> CaptchaResponse:
        """
        Solve image captcha.

        Args:
            image_path: Path to image file
            image_base64: Base64 encoded image

        Returns:
            CaptchaResponse
        """
        if image_path:
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode()
        elif not image_base64:
            return CaptchaResponse(
                success=False,
                captcha_type="image",
                error="No image provided",
            )

        return await self.solve("image", image_base64, "", **kwargs)

    def _update_stats(
        self,
        provider: str,
        captcha_type: str,
        response: CaptchaResponse,
        success: bool,
    ) -> None:
        """Update statistics."""
        if success:
            self._stats["total_solved"] += 1
        else:
            self._stats["total_failed"] += 1

        if provider not in self._stats["by_provider"]:
            self._stats["by_provider"][provider] = {"solved": 0, "failed": 0}

        if success:
            self._stats["by_provider"][provider]["solved"] += 1
        else:
            self._stats["by_provider"][provider]["failed"] += 1

        if captcha_type not in self._stats["by_type"]:
            self._stats["by_type"][captcha_type] = {"solved": 0, "failed": 0}

        if success:
            self._stats["by_type"][captcha_type]["solved"] += 1
        else:
            self._stats["by_type"][captcha_type]["failed"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get solver statistics."""
        stats = self._stats.copy()

        # Calculate success rate
        total = stats["total_solved"] + stats["total_failed"]
        if total > 0:
            stats["success_rate"] = stats["total_solved"] / total
        else:
            stats["success_rate"] = 0

        return stats

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            "total_solved": 0,
            "total_failed": 0,
            "by_provider": {},
            "by_type": {},
            "total_cost": 0,
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_captcha_solver: Optional[CaptchaSolver] = None


def get_captcha_solver(
    primary_provider: str = "2captcha",
    fallback_provider: str = "capsolver",
) -> CaptchaSolver:
    """
    Get or create global captcha solver.

    Args:
        primary_provider: Primary provider
        fallback_provider: Fallback provider

    Returns:
        CaptchaSolver instance
    """
    global _captcha_solver
    if _captcha_solver is None:
        _captcha_solver = CaptchaSolver(primary_provider, fallback_provider)
    return _captcha_solver
