"""Proxy rotation manager."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProxyConfig:
    """Configuration for a single proxy."""

    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    protocol: str = "http"
    latency: Optional[float] = None
    success_rate: float = 1.0
    total_requests: int = 0
    failed_requests: int = 0
    last_used: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

    def get_url(self, include_auth: bool = True) -> str:
        """Get proxy URL."""
        if include_auth and self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"

    def is_authenticated(self) -> bool:
        """Check if proxy requires authentication."""
        return bool(self.username and self.password)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "country": self.country,
            "protocol": self.protocol,
            "latency": self.latency,
            "success_rate": self.success_rate,
            "tags": self.tags,
        }

    @classmethod
    def from_url(cls, url: str, country: Optional[str] = None) -> ProxyConfig:
        """
        Create ProxyConfig from URL.

        Supports formats:
        - http://host:port
        - http://user:pass@host:port
        - socks5://host:port
        - host:port (assumes http)
        """
        # Simple format: host:port
        if "://" not in url:
            if "@" in url:
                # user:pass@host:port
                auth, host_part = url.split("@")
                username, password = auth.split(":")
                host, port = host_part.split(":")
            else:
                # host:port
                username = None
                password = None
                host, port = url.split(":")
            return cls(
                host=host,
                port=int(port),
                username=username,
                password=password,
                country=country,
            )

        # Full URL format
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return cls(
            host=parsed.hostname or "",
            port=parsed.port or 80,
            username=parsed.username,
            password=parsed.password,
            country=country,
            protocol=parsed.scheme,
        )

    def __str__(self) -> str:
        """String representation."""
        auth = f"{self.username}:***@" if self.username else ""
        return f"{self.host}:{self.port} ({self.country or 'unknown'})"


class ProxyRotator:
    """
    Manages proxy rotation for browser sessions.

    Features:
    - Multiple proxy providers support
    - Country-based selection
    - Automatic health checking
    - Load balancing across proxies
    - Configurable rotation strategies
    """

    def __init__(
        self,
        strategy: str = "random",
        health_check_interval: int = 300,
    ):
        """
        Initialize proxy rotator.

        Args:
            strategy: Rotation strategy ('random', 'round_robin', 'weighted')
            health_check_interval: Interval between health checks in seconds
        """
        self.strategy = strategy
        self.health_check_interval = health_check_interval

        self._proxies: List[ProxyConfig] = []
        self._index = 0
        self._lock = asyncio.Lock()

        self._providers: List[Any] = []
        self._health_checker: Optional[Any] = None

        logger.info(f"ProxyRotator initialized with strategy: {strategy}")

    def add_proxy(self, proxy: ProxyConfig) -> None:
        """
        Add a proxy to the pool.

        Args:
            proxy: Proxy configuration to add
        """
        self._proxies.append(proxy)
        logger.info(f"Added proxy: {proxy}")

    def add_proxies_from_file(self, filepath: str, country: Optional[str] = None) -> int:
        """
        Add proxies from a text file.

        File format (one proxy per line):
        - host:port
        - host:port:username:password
        - protocol://host:port

        Args:
            filepath: Path to proxy file
            country: Default country code for proxies

        Returns:
            Number of proxies added
        """
        path = Path(filepath)
        if not path.exists():
            logger.error(f"Proxy file not found: {filepath}")
            return 0

        count = 0
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                try:
                    proxy = ProxyConfig.from_url(line, country=country)
                    self.add_proxy(proxy)
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to parse proxy line: {line} - {e}")

        logger.info(f"Added {count} proxies from {filepath}")
        return count

    def remove_proxy(self, host: str, port: int) -> bool:
        """
        Remove a proxy from the pool.

        Args:
            host: Proxy host
            port: Proxy port

        Returns:
            True if removed, False if not found
        """
        for i, proxy in enumerate(self._proxies):
            if proxy.host == host and proxy.port == port:
                self._proxies.pop(i)
                logger.info(f"Removed proxy: {host}:{port}")
                return True
        return False

    async def get_proxy(
        self,
        country: Optional[str] = None,
        min_success_rate: float = 0.5,
        tag: Optional[str] = None,
    ) -> Optional[ProxyConfig]:
        """
        Get a proxy based on rotation strategy.

        Args:
            country: Filter by country code
            min_success_rate: Minimum success rate required
            tag: Filter by tag

        Returns:
            Selected ProxyConfig or None
        """
        async with self._lock:
            # Filter proxies
            candidates = self._proxies.copy()

            if country:
                candidates = [p for p in candidates if p.country == country]

            if tag:
                candidates = [p for p in candidates if tag in p.tags]

            if min_success_rate > 0:
                candidates = [p for p in candidates if p.success_rate >= min_success_rate]

            if not candidates:
                logger.warning(f"No proxies available for criteria: country={country}, tag={tag}")
                return None

            # Select based on strategy
            if self.strategy == "random":
                selected = random.choice(candidates)
            elif self.strategy == "round_robin":
                # Find next valid proxy
                attempts = 0
                while attempts < len(candidates):
                    proxy = candidates[self._index % len(candidates)]
                    self._index = (self._index + 1) % len(candidates)
                    attempts += 1

                    if proxy.success_rate >= min_success_rate:
                        selected = proxy
                        break
                else:
                    selected = random.choice(candidates)
            elif self.strategy == "weighted":
                # Weighted by success rate
                weights = [p.success_rate for p in candidates]
                total = sum(weights)
                r = random.uniform(0, total)
                cumulative = 0
                selected = candidates[-1]

                for proxy, weight in zip(candidates, weights):
                    cumulative += weight
                    if r <= cumulative:
                        selected = proxy
                        break
            else:
                selected = random.choice(candidates)

            # Update usage stats
            selected.last_used = datetime.utcnow()
            selected.total_requests += 1

            logger.debug(f"Selected proxy: {selected}")
            return selected

    def record_success(self, proxy: ProxyConfig) -> None:
        """
        Record a successful request for a proxy.

        Args:
            proxy: The proxy that succeeded
        """
        proxy.success_rate = (proxy.success_rate * proxy.total_requests) / (proxy.total_requests + 1)
        # This is simplified - in production use proper running average
        if proxy.total_requests > 0:
            proxy.success_rate = (proxy.total_requests - proxy.failed_requests) / proxy.total_requests

    def record_failure(self, proxy: ProxyConfig) -> None:
        """
        Record a failed request for a proxy.

        Args:
            proxy: The proxy that failed
        """
        proxy.failed_requests += 1
        proxy.total_requests += 1
        if proxy.total_requests > 0:
            proxy.success_rate = (proxy.total_requests - proxy.failed_requests) / proxy.total_requests

        # Mark as unhealthy if success rate drops too low
        if proxy.success_rate < 0.3:
            logger.warning(f"Proxy {proxy} has low success rate: {proxy.success_rate:.2%}")

    def get_stats(self) -> Dict[str, Any]:
        """Get proxy pool statistics."""
        if not self._proxies:
            return {
                "total": 0,
                "by_country": {},
                "avg_success_rate": 0,
                "avg_latency": 0,
            }

        countries: Dict[str, int] = {}
        total_success = 0
        total_latency = 0
        latency_count = 0

        for proxy in self._proxies:
            country = proxy.country or "unknown"
            countries[country] = countries.get(country, 0) + 1
            total_success += proxy.success_rate
            if proxy.latency:
                total_latency += proxy.latency
                latency_count += 1

        return {
            "total": len(self._proxies),
            "by_country": countries,
            "avg_success_rate": total_success / len(self._proxies),
            "avg_latency": total_latency / latency_count if latency_count > 0 else 0,
            "healthy_count": sum(1 for p in self._proxies if p.success_rate >= 0.5),
            "unhealthy_count": sum(1 for p in self._proxies if p.success_rate < 0.5),
        }

    def list_proxies(
        self,
        country: Optional[str] = None,
        filter_healthy: bool = True,
    ) -> List[ProxyConfig]:
        """
        List proxies with optional filters.

        Args:
            country: Filter by country
            filter_healthy: Only return healthy proxies

        Returns:
            List of ProxyConfig
        """
        proxies = self._proxies.copy()

        if country:
            proxies = [p for p in proxies if p.country == country]

        if filter_healthy:
            proxies = [p for p in proxies if p.success_rate >= 0.5]

        return proxies

    async def health_check_all(
        self,
        timeout: int = 30,
        test_url: str = "https://www.google.com",
    ) -> Dict[str, bool]:
        """
        Perform health check on all proxies.

        Args:
            timeout: Timeout per proxy in seconds
            test_url: URL to test connectivity

        Returns:
            Dict mapping proxy to health status
        """
        from .health_checker import ProxyHealthChecker

        checker = ProxyHealthChecker(timeout=timeout)
        results: Dict[str, bool] = {}

        for proxy in self._proxies:
            is_healthy = await checker.check_proxy(proxy, test_url)
            proxy.success_rate = 0.9 if is_healthy else 0.1
            results[str(proxy)] = is_healthy

        logger.info(f"Health check complete: {sum(results.values())}/{len(results)} healthy")
        return results

    def export_to_file(self, filepath: str) -> int:
        """
        Export proxies to a file.

        Args:
            filepath: Output file path

        Returns:
            Number of proxies exported
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            for proxy in self._proxies:
                f.write(f"{proxy.get_url()}\n")

        logger.info(f"Exported {len(self._proxies)} proxies to {filepath}")
        return len(self._proxies)

    @property
    def count(self) -> int:
        """Get number of proxies in pool."""
        return len(self._proxies)
