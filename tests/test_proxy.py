"""Tests for proxy management."""

import pytest
from src.proxy.rotator import ProxyRotator, ProxyConfig
from src.proxy.health_checker import ProxyHealthChecker


class TestProxyConfig:
    """Tests for ProxyConfig."""

    def test_proxy_config_creation(self):
        """Test proxy config creation."""
        proxy = ProxyConfig(
            host="proxy.example.com",
            port=8080,
        )

        assert proxy.host == "proxy.example.com"
        assert proxy.port == 8080

    def test_proxy_config_with_auth(self):
        """Test proxy config with authentication."""
        proxy = ProxyConfig(
            host="proxy.example.com",
            port=8080,
            username="user",
            password="pass",
        )

        assert proxy.is_authenticated()
        assert "user:pass@" in proxy.get_url()

    def test_proxy_config_from_url_simple(self):
        """Test proxy config from simple URL."""
        proxy = ProxyConfig.from_url("proxy.example.com:8080")

        assert proxy.host == "proxy.example.com"
        assert proxy.port == 8080

    def test_proxy_config_from_url_with_auth(self):
        """Test proxy config from URL with auth."""
        proxy = ProxyConfig.from_url("user:pass@proxy.example.com:8080")

        assert proxy.host == "proxy.example.com"
        assert proxy.port == 8080
        assert proxy.username == "user"
        assert proxy.password == "pass"

    def test_proxy_config_from_url_with_protocol(self):
        """Test proxy config from URL with protocol."""
        proxy = ProxyConfig.from_url("http://proxy.example.com:8080")

        assert proxy.host == "proxy.example.com"
        assert proxy.port == 8080
        assert proxy.protocol == "http"

    def test_proxy_to_dict(self, sample_proxy):
        """Test proxy serialization."""
        d = sample_proxy.to_dict()

        assert d["host"] == "proxy.example.com"
        assert d["port"] == 8080


class TestProxyRotator:
    """Tests for ProxyRotator."""

    def test_rotator_initialization(self):
        """Test rotator initialization."""
        rotator = ProxyRotator()
        assert rotator is not None
        assert rotator.count == 0

    def test_rotator_with_strategy(self):
        """Test rotator with different strategies."""
        for strategy in ["random", "round_robin", "weighted"]:
            rotator = ProxyRotator(strategy=strategy)
            assert rotator.strategy == strategy

    def test_add_proxy(self, proxy_rotator, sample_proxy):
        """Test adding proxy to rotator."""
        proxy_rotator.add_proxy(sample_proxy)
        assert proxy_rotator.count == 1

    def test_add_multiple_proxies(self, proxy_rotator):
        """Test adding multiple proxies."""
        for i in range(5):
            proxy = ProxyConfig(host=f"proxy{i}.example.com", port=8080)
            proxy_rotator.add_proxy(proxy)

        assert proxy_rotator.count == 5

    def test_remove_proxy(self, proxy_rotator, sample_proxy):
        """Test removing proxy."""
        proxy_rotator.add_proxy(sample_proxy)
        assert proxy_rotator.count == 1

        result = proxy_rotator.remove_proxy("proxy.example.com", 8080)
        assert result is True
        assert proxy_rotator.count == 0

    def test_remove_nonexistent_proxy(self, proxy_rotator):
        """Test removing proxy that doesn't exist."""
        result = proxy_rotator.remove_proxy("nonexistent.com", 8080)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_proxy(self, proxy_rotator, sample_proxy):
        """Test getting a proxy."""
        proxy_rotator.add_proxy(sample_proxy)

        proxy = await proxy_rotator.get_proxy()
        assert proxy is not None
        assert proxy.host == "proxy.example.com"

    @pytest.mark.asyncio
    async def test_get_proxy_with_country_filter(self, proxy_rotator):
        """Test getting proxy with country filter."""
        proxy1 = ProxyConfig(host="us.proxy.com", port=8080, country="US")
        proxy2 = ProxyConfig(host="uk.proxy.com", port=8080, country="GB")

        proxy_rotator.add_proxy(proxy1)
        proxy_rotator.add_proxy(proxy2)

        proxy = await proxy_rotator.get_proxy(country="US")
        assert proxy.country == "US"

    @pytest.mark.asyncio
    async def test_get_proxy_no_available(self, proxy_rotator):
        """Test getting proxy when none available."""
        proxy = await proxy_rotator.get_proxy()
        assert proxy is None

    def test_record_success(self, proxy_rotator, sample_proxy):
        """Test recording success."""
        proxy_rotator.add_proxy(sample_proxy)
        proxy_rotator.record_success(sample_proxy)

        # Success rate should remain high
        assert sample_proxy.success_rate >= 0.9

    def test_record_failure(self, proxy_rotator, sample_proxy):
        """Test recording failure."""
        proxy_rotator.add_proxy(sample_proxy)
        proxy_rotator.record_failure(sample_proxy)

        assert sample_proxy.failed_requests == 1

    def test_get_stats(self, proxy_rotator):
        """Test getting statistics."""
        stats = proxy_rotator.get_stats()

        assert "total" in stats
        assert stats["total"] == 0


class TestProxyHealthChecker:
    """Tests for ProxyHealthChecker."""

    def test_health_checker_initialization(self):
        """Test health checker initialization."""
        checker = ProxyHealthChecker()
        assert checker is not None
        assert checker.timeout == 30

    def test_health_checker_custom_timeout(self):
        """Test health checker with custom timeout."""
        checker = ProxyHealthChecker(timeout=60)
        assert checker.timeout == 60

    def test_calculate_success_rate(self, sample_proxy):
        """Test success rate calculation."""
        checker = ProxyHealthChecker()
        sample_proxy.total_requests = 10
        sample_proxy.failed_requests = 2

        rate = checker.calculate_success_rate(sample_proxy)
        assert rate == 0.8

    def test_calculate_success_rate_no_requests(self, sample_proxy):
        """Test success rate with no requests."""
        checker = ProxyHealthChecker()

        rate = checker.calculate_success_rate(sample_proxy)
        assert rate == 1.0  # Default to 100%

    def test_is_healthy(self, sample_proxy):
        """Test health check."""
        checker = ProxyHealthChecker(min_success_rate=0.5)
        sample_proxy.success_rate = 0.8

        assert checker.is_healthy(sample_proxy)

    def test_is_unhealthy(self, sample_proxy):
        """Test unhealthy detection."""
        checker = ProxyHealthChecker(min_success_rate=0.5)
        sample_proxy.success_rate = 0.3

        assert not checker.is_healthy(sample_proxy)
