"""Tests for fingerprint generation."""

import pytest
from src.antidetect.fingerprint import FingerprintGenerator, FingerprintProfile


class TestFingerprintGenerator:
    """Tests for FingerprintGenerator."""

    def test_generator_initialization(self):
        """Test generator can be initialized."""
        gen = FingerprintGenerator()
        assert gen is not None

    def test_generator_with_seed(self):
        """Test generator with seed produces reproducible results."""
        gen1 = FingerprintGenerator(seed=12345)
        gen2 = FingerprintGenerator(seed=12345)

        fp1 = gen1.generate(country="US")
        fp2 = gen2.generate(country="US")

        assert fp1.user_agent == fp2.user_agent
        assert fp1.canvas_hash == fp2.canvas_hash

    def test_generate_fingerprint(self, fingerprint_generator):
        """Test basic fingerprint generation."""
        fp = fingerprint_generator.generate()

        assert fp is not None
        assert fp.os in ["windows", "mac", "linux"]
        assert fp.browser in ["chrome", "firefox", "safari"]
        assert fp.user_agent is not None
        assert len(fp.user_agent) > 0

    def test_generate_with_country(self, fingerprint_generator):
        """Test fingerprint generation with country."""
        fp = fingerprint_generator.generate(country="JP")

        assert fp.country == "JP"
        assert fp.language is not None

    def test_generate_with_os(self, fingerprint_generator):
        """Test fingerprint generation with specific OS."""
        fp = fingerprint_generator.generate(os="mac")

        assert fp.os == "mac"

    def test_generate_with_browser(self, fingerprint_generator):
        """Test fingerprint generation with specific browser."""
        fp = fingerprint_generator.generate(browser="firefox")

        assert fp.browser == "firefox"

    def test_generate_batch(self, fingerprint_generator):
        """Test batch fingerprint generation."""
        profiles = fingerprint_generator.generate_batch(count=5)

        assert len(profiles) == 5
        assert len(set(p.id for p in profiles)) == 5  # All unique IDs

    def test_fingerprint_profile_to_dict(self, sample_fingerprint):
        """Test fingerprint serialization to dict."""
        d = sample_fingerprint.to_dict()

        assert isinstance(d, dict)
        assert "user_agent" in d
        assert "os" in d
        assert "browser" in d

    def test_fingerprint_profile_to_json(self, sample_fingerprint):
        """Test fingerprint serialization to JSON."""
        json_str = sample_fingerprint.to_json()

        assert isinstance(json_str, str)
        assert "user_agent" in json_str

    def test_fingerprint_profile_from_dict(self, sample_fingerprint):
        """Test fingerprint deserialization from dict."""
        d = sample_fingerprint.to_dict()
        fp2 = FingerprintProfile.from_dict(d)

        assert fp2.user_agent == sample_fingerprint.user_agent
        assert fp2.os == sample_fingerprint.os

    def test_user_agent_format(self, fingerprint_generator):
        """Test user agent string format."""
        ua = fingerprint_generator.get_realistic_user_agent(os="windows", browser="chrome")

        assert "Chrome" in ua or "chrome" in ua.lower()
        assert "Windows" in ua

    def test_timezone_offset(self, fingerprint_generator):
        """Test timezone offset calculation."""
        offset = fingerprint_generator._get_timezone_offset("America/New_York")

        assert offset == -300  # EST in minutes


class TestFingerprintConsistency:
    """Tests for fingerprint consistency."""

    def test_fingerprint_has_required_fields(self, sample_fingerprint):
        """Test fingerprint has all required fields."""
        assert sample_fingerprint.user_agent
        assert sample_fingerprint.canvas_hash
        assert sample_fingerprint.webgl_vendor
        assert sample_fingerprint.webgl_renderer
        assert sample_fingerprint.timezone
        assert sample_fingerprint.fonts

    def test_screen_resolution_reasonable(self, sample_fingerprint):
        """Test screen resolution is reasonable."""
        assert 800 <= sample_fingerprint.screen_width <= 3840
        assert 600 <= sample_fingerprint.screen_height <= 2160

    def test_hardware_concurrency_reasonable(self, sample_fingerprint):
        """Test hardware concurrency is reasonable."""
        assert 1 <= sample_fingerprint.hardware_concurrency <= 128

    def test_languages_list(self, sample_fingerprint):
        """Test languages list is populated."""
        assert len(sample_fingerprint.languages) > 0
        assert sample_fingerprint.language in sample_fingerprint.languages
