"""DataImpulse proxy provider integration."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx

from src.utils.logger import get_logger
from .base import BaseProxyProvider
from ..rotator import ProxyConfig

logger = get_logger(__name__)


class DataImpulseProvider(BaseProxyProvider):
    """
    DataImpulse proxy provider.

    DataImpulse provides residential proxies with good coverage
    in most countries.

    API Documentation: https://dataimpulse.com/docs
    """

    BASE_URL = "https://proxy.dataimpulse.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        requests_limit: int = 1000,
    ):
        """
        Initialize DataImpulse provider.

        Args:
            api_key: DataImpulse API key
            requests_limit: Requests limit per month
        """
        super().__init__(api_key)
        self.requests_limit = requests_limit
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def fetch_proxies(
        self,
        country: Optional[str] = None,
        limit: int = 100,
    ) -> List[ProxyConfig]:
        """
        Fetch proxies from DataImpulse.

        Args:
            country: Country code (e.g., 'US', 'GB')
            limit: Maximum number of proxies to fetch

        Returns:
            List of ProxyConfig
        """
        if not self.api_key:
            logger.error("DataImpulse API key not configured")
            return []

        client = await self._get_client()

        try:
            # DataImpulse API endpoint
            response = await client.get(
                "/api/proxies",
                params={
                    "country": country or "all",
                    "limit": limit,
                },
            )
            response.raise_for_status()

            data = response.json()
            proxies = []

            for item in data.get("proxies", []):
                proxy = ProxyConfig(
                    host=item["host"],
                    port=item["port"],
                    username=item.get("username"),
                    password=item.get("password"),
                    country=item.get("country", country),
                    protocol="http",
                    latency=item.get("latency"),
                    tags=["dat_impulse", "residential"],
                )
                proxies.append(proxy)

            logger.info(f"Fetched {len(proxies)} proxies from DataImpulse")
            return proxies

        except httpx.HTTPStatusError as e:
            logger.error(f"DataImpulse API error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"DataImpulse fetch error: {e}")
            return []

    async def get_proxy_info(self, proxy_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get proxy information from DataImpulse.

        Args:
            proxy_id: Optional proxy ID

        Returns:
            Dict with proxy information
        """
        client = await self._get_client()

        try:
            response = await client.get("/api/proxy/info")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get proxy info: {e}")
            return {}

    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.

        Returns:
            Dict with usage info (requests used, remaining, etc.)
        """
        client = await self._get_client()

        try:
            response = await client.get("/api/usage")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {}

    async def test_connection(self) -> bool:
        """Test connection to DataImpulse API."""
        try:
            client = await self._get_client()
            response = await client.get("/api/status")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"DataImpulse connection test failed: {e}")
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Factory function
def create_dat_impulse_provider(api_key: Optional[str] = None) -> DataImpulseProvider:
    """Create DataImpulse provider from settings."""
    from ...utils.config import get_settings
    settings = get_settings()
    key = api_key or settings.dat_impulse_api_key
    return DataImpulseProvider(api_key=key)
