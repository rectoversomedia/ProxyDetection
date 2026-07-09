"""Input validation utilities for CLI."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import typer


def validate_url(url: str) -> bool:
    """
    Validate if string is a valid URL.

    Args:
        url: URL string to validate

    Returns:
        True if valid URL, False otherwise
    """
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(url_pattern.match(url))


def validate_file_path(path: Path, must_exist: bool = True, extensions: Optional[list] = None) -> bool:
    """
    Validate a file path.

    Args:
        path: Path to validate
        must_exist: If True, file must exist
        extensions: List of allowed extensions (e.g., ['.csv', '.json'])

    Returns:
        True if valid, False otherwise
    """
    if must_exist and not path.exists():
        return False

    if extensions:
        if path.suffix.lower() not in extensions:
            return False

    return True


def validate_country_code(code: str) -> bool:
    """
    Validate if string is a valid ISO 3166-1 alpha-2 country code.

    Args:
        code: Country code to validate

    Returns:
        True if valid, False otherwise
    """
    valid_codes = {
        "US", "GB", "CA", "AU", "DE", "FR", "JP", "CN", "IN", "BR",
        "MX", "ES", "IT", "NL", "SE", "NO", "DK", "FI", "PL", "RU",
        "KR", "SG", "MY", "TH", "ID", "PH", "VN", "NZ", "ZA", "EG",
        # Add more as needed
    }
    return code.upper() in valid_codes


def validate_proxy_format(proxy: str) -> bool:
    """
    Validate proxy string format.

    Supports:
    - host:port
    - host:port:user:pass
    - protocol://host:port
    - protocol://user:pass@host:port

    Args:
        proxy: Proxy string to validate

    Returns:
        True if valid format, False otherwise
    """
    # Simple format: host:port
    simple_pattern = re.compile(r"^[\w.-]+:\d+$")

    # With auth: host:port:user:pass
    auth_pattern = re.compile(r"^[\w.-]+:\d+:[\w.-]+:[\w.-]+$")

    # With protocol: protocol://host:port or protocol://user:pass@host:port
    protocol_pattern = re.compile(
        r"^(socks5?|https?)://"
        r"(?:[\w.-]+:[\w.-]+@)?"
        r"[\w.-]+:\d+$",
        re.IGNORECASE,
    )

    return bool(
        simple_pattern.match(proxy) or
        auth_pattern.match(proxy) or
        protocol_pattern.match(proxy)
    )


def validate_delay(delay: float) -> bool:
    """
    Validate delay value.

    Args:
        delay: Delay in seconds

    Returns:
        True if valid, False otherwise
    """
    return 0 <= delay <= 300  # 0 to 5 minutes


def validate_parallel(parallel: int) -> bool:
    """
    Validate parallel count.

    Args:
        parallel: Number of parallel operations

    Returns:
        True if valid, False otherwise
    """
    return 1 <= parallel <= 20


def validate_lead_data(data: dict, required_fields: Optional[list] = None) -> tuple[bool, list]:
    """
    Validate lead data structure.

    Args:
        data: Lead data dictionary
        required_fields: List of required field names

    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []

    if required_fields is None:
        required_fields = ["name", "email"]

    for field in required_fields:
        if field not in data or not data[field]:
            issues.append(f"Missing required field: {field}")

    # Email validation
    if "email" in data and data["email"]:
        email_pattern = re.compile(r"^[\w.-]+@[\w.-]+\.\w+$")
        if not email_pattern.match(data["email"]):
            issues.append("Invalid email format")

    return len(issues) == 0, issues
