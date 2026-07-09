"""Proxy health checking."""

from __future__ import annotations

import asyncio
import time
from typing import Dict, Optional

import httpx

from ..utils.logger import get_logger
from .rotator import ProxyConfig

logger = get_logger(__name__)


class ProxyHealthChecker:
    """
    Health checker for proxy validation.

    Performs connectivity and latency tests on proxies
    to ensure they are working properly.
    """

    def __init__(
        self,
        timeout: int = 30,
        test_url: str = "https://www.google.com",
        success_codes: tuple = (200, 201, 204),
    ):
        """
        Initialize health checker.

        Args:
            timeout: Timeout for each check in seconds
            test_url: URL to test proxy connectivity
            success_codes: HTTP status codes considered successful
        """
        self.timeout = timeout
        self.test_url = test_url
        self.success_codes = success_codes

    async def check_proxy(
        self,
        proxy: ProxyConfig,
        test_url: Optional[str] = None,
    ) -> bool:
        """
        Check if a proxy is healthy.

        Args:
            proxy: Proxy to check
            test_url: Optional custom test URL

        Returns:
            True if proxy is healthy, False otherwise
        """
        url = test_url or self.test_url

        try:
            # Configure proxy
            proxy_dict = {
                "http://": f"http://{proxy.host}:{proxy.port}",
                "https://": f"http://{proxy.host}:{proxy.port}",
            }

            if proxy.username and proxy.password:
                proxy_dict = {
                    "http://": f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}",
                    "https://": f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}",
                }

            # Make test request
            start_time = time.time()

            async with httpx.AsyncClient(
                proxies=proxy_dict,
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                latency = time.time() - start_time

                # Update proxy stats
                proxy.latency = latency
                proxy.total_requests += 1

                if response.status_code in self.success_codes:
                    logger.debug(f"Proxy {proxy} is healthy (latency: {latency:.2f}s)")
                    return True
                else:
                    logger.debug(f"Proxy {proxy} returned status {response.status_code}")
                    proxy.failed_requests += 1
                    return False

        except asyncio.TimeoutError:
            logger.debug(f"Proxy {proxy} timed out")
            proxy.failed_requests += 1
            proxy.total_requests += 1
            return False
        except httpx.ProxyError as e:
            logger.debug(f"Proxy {proxy} connection error: {e}")
            proxy.failed_requests += 1
            proxy.total_requests += 1
            return False
        except Exception as e:
            logger.debug(f"Proxy {proxy} check failed: {e}")
            proxy.failed_requests += 1
            proxy.total_requests += 1
            return False

    async def check_proxy_latency(
        self,
        proxy: ProxyConfig,
        test_url: Optional[str] = None,
    ) -> Optional[float]:
        """
        Measure proxy latency.

        Args:
            proxy: Proxy to check
            test_url: Optional custom test URL

        Returns:
            Latency in seconds, or None if failed
        """
        url = test_url or self.test_url

        try:
            proxy_dict = {
                "http://": f"http://{proxy.host}:{proxy.port}",
                "https://": f"http://{proxy.host}:{proxy.port}",
            }

            if proxy.username and proxy.password:
                proxy_dict = {
                    "http://": f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}",
                    "https://": f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}",
                }

            start_time = time.time()

            async with httpx.AsyncClient(
                proxies=proxy_dict,
                timeout=self.timeout,
            ) as client:
                await client.get(url)
                latency = time.time() - start_time
                proxy.latency = latency
                return latency

        except Exception as e:
            logger.debug(f"Latency check failed for {proxy}: {e}")
            return None

    async def check_batch(
        self,
        proxies: list[ProxyConfig],
        test_url: Optional[str] = None,
        max_concurrent: int = 10,
    ) -> Dict[str, bool]:
        """
        Check multiple proxies concurrently.

        Args:
            proxies: List of proxies to check
            test_url: Optional custom test URL
            max_concurrent: Maximum concurrent checks

        Returns:
            Dict mapping proxy string to health status
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def check_with_semaphore(proxy: ProxyConfig) -> tuple[str, bool]:
            async with semaphore:
                is_healthy = await self.check_proxy(proxy, test_url)
                return (str(proxy), is_healthy)

        tasks = [check_with_semaphore(p) for p in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        result_dict = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Check failed: {result}")
                result_dict[str(proxies[i])] = False
            else:
                result_dict[result[0]] = result[1]

        healthy_count = sum(1 for v in result_dict.values() if v)
        logger.info(f"Batch check: {healthy_count}/{len(proxies)} healthy")

        return result_dict

    def calculate_success_rate(self, proxy: ProxyConfig) -> float:
        """
        Calculate success rate for a proxy.

        Args:
            proxy: Proxy to calculate for

        Returns:
            Success rate as float between 0 and 1
        """
        if proxy.total_requests == 0:
            return 1.0
        return (proxy.total_requests - proxy.failed_requests) / proxy.total_requests

    def is_healthy(
        self,
        proxy: ProxyConfig,
        min_success_rate: float = 0.5,
        max_latency: Optional[float] = None,
    ) -> bool:
        """
        Check if proxy meets health criteria.

        Args:
            proxy: Proxy to check
            min_success_rate: Minimum required success rate
            max_latency: Optional maximum latency in seconds

        Returns:
            True if proxy is healthy
        """
        success_rate = self.calculate_success_rate(proxy)

        if success_rate < min_success_rate:
            return False

        if max_latency is not None and proxy.latency and proxy.latency > max_latency:
            return False

        return True
