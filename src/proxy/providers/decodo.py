"""Decodo proxy provider integration."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx

from src.utils.logger import get_logger
from .base import BaseProxyProvider
from ..rotator import ProxyConfig

logger = get_logger(__name__)


class DecodoProvider(BaseProxyProvider):
    """
    Decodo proxy provider.

    Decodo provides residential and datacenter proxies
    with good global coverage.

    API Documentation: https://decodo.com/docs
    """

    BASE_URL = "https://api.decodo.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ):
        """
        Initialize Decodo provider.

        Args:
            api_key: Decodo API key
            workspace_id: Decodo workspace ID
        """
        super().__init__(api_key)
        self.workspace_id = workspace_id
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "X-Workspace-ID": self.workspace_id or "",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def fetch_proxies(
        self,
        country: Optional[str] = None,
        limit: int = 100,
        proxy_type: str = "residential",
    ) -> List[ProxyConfig]:
        """
        Fetch proxies from Decodo.

        Args:
            country: Country code (e.g., 'US', 'GB')
            limit: Maximum number of proxies to fetch
            proxy_type: Type of proxies ('residential', 'datacenter', 'mobile')

        Returns:
            List of ProxyConfig
        """
        if not self.api_key:
            logger.error("Decodo API key not configured")
            return []

        client = await self._get_client()

        try:
            response = await client.get(
                "/v2/proxies",
                params={
                    "country": country or "all",
                    "limit": limit,
                    "type": proxy_type,
                },
            )
            response.raise_for_status()

            data = response.json()
            proxies = []

            for item in data.get("data", []):
                proxy = ProxyConfig(
                    host=item["host"],
                    port=item["port"],
                    username=item.get("username"),
                    password=item.get("password"),
                    country=item.get("country", country),
                    protocol="http",
                    latency=item.get("latency"),
                    tags=["decodo", proxy_type],
                )
                proxies.append(proxy)

            logger.info(f"Fetched {len(proxies)} proxies from Decodo")
            return proxies

        except httpx.HTTPStatusError as e:
            logger.error(f"Decodo API error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Decodo fetch error: {e}")
            return []

    async def get_proxy_info(self, proxy_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get proxy information from Decodo.

        Args:
            proxy_id: Optional proxy ID

        Returns:
            Dict with proxy information
        """
        client = await self._get_client()

        try:
            response = await client.get(f"/v2/proxies/{proxy_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get proxy info: {e}")
            return {}

    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.

        Returns:
            Dict with usage info
        """
        client = await self._get_client()

        try:
            response = await client.get("/v2/usage")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {}

    async def create_proxy(
        self,
        country: str,
        proxy_type: str = "residential",
        quantity: int = 1,
    ) -> List[ProxyConfig]:
        """
        Create new proxies via Decodo.

        Args:
            country: Country code
            proxy_type: Type of proxies
            quantity: Number of proxies to create

        Returns:
            List of created ProxyConfig
        """
        client = await self._get_client()

        try:
            response = await client.post(
                "/v2/proxies",
                json={
                    "country": country,
                    "type": proxy_type,
                    "quantity": quantity,
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
                    country=country,
                    protocol="http",
                    tags=["decodo", proxy_type],
                )
                proxies.append(proxy)

            logger.info(f"Created {len(proxies)} proxies via Decodo")
            return proxies

        except Exception as e:
            logger.error(f"Failed to create proxies: {e}")
            return []

    async def test_connection(self) -> bool:
        """Test connection to Decodo API."""
        try:
            client = await self._get_client()
            response = await client.get("/v2/status")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Decodo connection test failed: {e}")
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Factory function
def create_decodo_provider(api_key: Optional[str] = None) -> DecodoProvider:
    """Create Decodo provider from settings."""
    from ...utils.config import get_settings
    settings = get_settings()
    key = api_key or settings.decodo_api_key
    return DecodoProvider(api_key=key)
