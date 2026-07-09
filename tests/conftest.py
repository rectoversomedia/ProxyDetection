"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import Generator

from src.antidetect.fingerprint import FingerprintGenerator, FingerprintProfile
from src.antidetect.behavioral import BehavioralSimulator
from src.antidetect.profile import BrowserProfile, ProfileManager
from src.proxy.rotator import ProxyRotator, ProxyConfig


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def fingerprint_generator() -> FingerprintGenerator:
    """Create fingerprint generator."""
    return FingerprintGenerator(seed=42)


@pytest.fixture
def sample_fingerprint(fingerprint_generator) -> FingerprintProfile:
    """Create sample fingerprint."""
    return fingerprint_generator.generate(country="US", os="windows", browser="chrome")


@pytest.fixture
def behavioral_simulator() -> BehavioralSimulator:
    """Create behavioral simulator."""
    return BehavioralSimulator(seed=42)


@pytest.fixture
def browser_profile() -> BrowserProfile:
    """Create browser profile."""
    return BrowserProfile(
        name="test_profile",
        os="windows",
        browser="chrome",
        headless=True,
    )


@pytest.fixture
def proxy_rotator() -> ProxyRotator:
    """Create proxy rotator."""
    return ProxyRotator(strategy="random")


@pytest.fixture
def sample_proxy() -> ProxyConfig:
    """Create sample proxy."""
    return ProxyConfig(
        host="proxy.example.com",
        port=8080,
        username="user",
        password="pass",
        country="US",
    )


@pytest.fixture
def sample_lead() -> dict:
    """Create sample lead data."""
    return {
        "id": "test-lead-001",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "age": 30,
        "country": "US",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001",
    }


@pytest.fixture
def sample_leads() -> list:
    """Create multiple sample leads."""
    return [
        {
            "id": f"lead-{i:03d}",
            "name": f"User {i}",
            "email": f"user{i}@example.com",
            "phone": f"+1-555-000-{i:04d}",
        }
        for i in range(10)
    ]
