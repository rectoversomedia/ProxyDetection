"""Base proxy provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..rotator import ProxyConfig


class BaseProxyProvider(ABC):
    """
    Abstract base class for proxy providers.

    Proxy providers are responsible for fetching and managing
    proxies from various sources (API, file, custom).
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize provider.

        Args:
            api_key: API key for the provider
        """
        self.api_key = api_key

    @abstractmethod
    async def fetch_proxies(
        self,
        country: Optional[str] = None,
        limit: int = 100,
    ) -> List[ProxyConfig]:
        """
        Fetch proxies from the provider.

        Args:
            country: Filter by country code
            limit: Maximum number of proxies to fetch

        Returns:
            List of ProxyConfig
        """
        pass

    @abstractmethod
    async def get_proxy_info(self, proxy_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about proxies from the provider.

        Args:
            proxy_id: Optional specific proxy ID

        Returns:
            Dict with proxy information
        """
        pass

    async def test_connection(self) -> bool:
        """
        Test connection to the provider API.

        Returns:
            True if connection successful, False otherwise
        """
        return True

    def get_name(self) -> str:
        """Get provider name."""
        return self.__class__.__name__.replace("Provider", "").lower()

    def supports_country_filter(self) -> bool:
        """Check if provider supports country filtering."""
        return True

    def get_available_countries(self) -> List[str]:
        """
        Get list of available countries.

        Returns:
            List of ISO country codes
        """
        return [
            "US", "GB", "CA", "AU", "DE", "FR", "JP", "SG", "MY",
            "TH", "ID", "VN", "PH", "IN", "BR", "MX", "ES", "IT",
            "NL", "SE", "NO", "DK", "FI", "PL", "RU", "KR", "CN",
            "NZ", "ZA", "EG", "AE", "SA",
        ]
