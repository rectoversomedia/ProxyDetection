"""Lead data validation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationError:
    """Represents a validation error."""
    field: str
    message: str
    code: str
    severity: str = "error"  # error, warning

    def __str__(self) -> str:
        return f"{self.field}: {self.message}"


@dataclass
class ValidationResult:
    """Result of validation."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    @property
    def error_messages(self) -> List[str]:
        """Get simple error messages."""
        return [str(e) for e in self.errors]

    @property
    def warning_messages(self) -> List[str]:
        """Get simple warning messages."""
        return [str(e) for e in self.warnings]

    def add_error(self, field: str, message: str, code: str = "invalid") -> None:
        """Add an error."""
        self.errors.append(ValidationError(field, message, code))
        self.is_valid = False

    def add_warning(self, field: str, message: str, code: str = "warning") -> None:
        """Add a warning."""
        self.warnings.append(ValidationError(field, message, code, "warning"))

    def merge(self, other: "ValidationResult") -> None:
        """Merge another validation result."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False


class LeadValidator:
    """
    Validator for lead data.

    Validates:
    - Email format
    - Phone numbers
    - URLs
    - Required fields
    - Data consistency
    """

    # Common email providers to flag disposable emails
    DISPOSABLE_DOMAINS: Set[str] = {
        "tempmail.com", "guerrillamail.com", "mailinator.com",
        "throwaway.email", "temp-mail.org", "fakeinbox.com",
        "sharklasers.com", "grr.la", "guerrillamailblock.com",
    }

    def __init__(
        self,
        require_email: bool = True,
        require_name: bool = False,
        strict_phone: bool = False,
        allow_disposable_email: bool = False,
    ):
        """
        Initialize validator.

        Args:
            require_email: Email field is required
            require_name: Name field is required
            strict_phone: Use strict phone validation
            allow_disposable_email: Allow disposable email domains
        """
        self.require_email = require_email
        self.require_name = require_name
        self.strict_phone = strict_phone
        self.allow_disposable_email = allow_disposable_email

    def validate(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate lead data.

        Args:
            data: Lead data dictionary

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        result = self.validate_full(data)
        return result.is_valid, result.error_messages

    def validate_full(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate lead data with full result.

        Args:
            data: Lead data dictionary

        Returns:
            ValidationResult with all errors and warnings
        """
        result = ValidationResult(is_valid=True)

        # Email validation
        email = data.get("email") or data.get("e-mail") or data.get("email_address")
        if email:
            self._validate_email(email, result)
        elif self.require_email:
            result.add_error("email", "Email is required", "required")

        # Name validation
        name = data.get("name") or data.get("full_name") or data.get("fullname")
        if name:
            self._validate_name(name, result)
        elif self.require_name:
            result.add_error("name", "Name is required", "required")

        # Phone validation
        phone = data.get("phone") or data.get("phone_number") or data.get("mobile")
        if phone:
            self._validate_phone(phone, result)

        # URL validation
        url = data.get("url") or data.get("website") or data.get("link")
        if url:
            self._validate_url(url, result)

        # Age validation
        age = data.get("age") or data.get("date_of_birth") or data.get("dob")
        if age:
            self._validate_age(age, result)

        # Country validation
        country = data.get("country") or data.get("country_code")
        if country:
            self._validate_country(country, result)

        # Check for empty data
        if not any(data.values()):
            result.add_error("data", "Lead data is empty", "empty")

        return result

    def _validate_email(self, email: str, result: ValidationResult) -> None:
        """Validate email format."""
        if not email or not isinstance(email, str):
            result.add_error("email", "Invalid email format", "invalid_type")
            return

        email = email.strip().lower()

        # Basic format check
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            result.add_error("email", f"Invalid email format: {email}", "invalid_format")
            return

        # Extract domain
        domain = email.split("@")[1] if "@" in email else ""

        # Check disposable domain
        if not self.allow_disposable_email:
            if domain in self.DISPOSABLE_DOMAINS:
                result.add_warning(
                    "email",
                    f"Disposable email domain detected: {domain}",
                    "disposable",
                )

        # Check for suspicious patterns
        if "test" in domain.lower():
            result.add_warning("email", "Test email domain detected", "test")

        if len(email) > 254:
            result.add_error("email", "Email address too long", "too_long")

    def _validate_name(self, name: str, result: ValidationResult) -> None:
        """Validate name field."""
        if not name or not isinstance(name, str):
            result.add_error("name", "Invalid name format", "invalid_type")
            return

        name = name.strip()

        if len(name) < 2:
            result.add_warning("name", "Name seems too short", "too_short")

        if len(name) > 100:
            result.add_warning("name", "Name seems too long", "too_long")

        # Check for numbers
        if any(c.isdigit() for c in name):
            result.add_warning("name", "Name contains numbers", "suspicious")

    def _validate_phone(
        self,
        phone: str,
        result: ValidationResult,
    ) -> None:
        """Validate phone number."""
        if not phone or not isinstance(phone, str):
            result.add_error("phone", "Invalid phone format", "invalid_type")
            return

        phone = re.sub(r"[^\d+]", "", phone)  # Remove non-digits except +

        if self.strict_phone:
            # Strict validation
            if len(phone) < 10 or len(phone) > 15:
                result.add_error(
                    "phone",
                    f"Invalid phone length: {len(phone)} digits",
                    "invalid_length",
                )
        else:
            # Lenient validation
            if len(phone) < 7:
                result.add_warning(
                    "phone",
                    f"Phone number seems too short: {phone}",
                    "too_short",
                )

            if len(phone) > 15:
                result.add_warning(
                    "phone",
                    f"Phone number seems too long: {phone}",
                    "too_long",
                )

    def _validate_url(self, url: str, result: ValidationResult) -> None:
        """Validate URL."""
        if not url or not isinstance(url, str):
            result.add_error("url", "Invalid URL format", "invalid_type")
            return

        url = url.strip()

        # Add protocol if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                result.add_error("url", f"Invalid URL: {url}", "invalid_format")
                return

            # Check for localhost/private IPs
            if any(x in parsed.netloc for x in ["localhost", "127.0.0.1", "0.0.0.0"]):
                result.add_warning("url", "Localhost URL detected", "private")

        except Exception as e:
            result.add_error("url", f"Invalid URL: {e}", "parse_error")

    def _validate_age(self, age: Any, result: ValidationResult) -> None:
        """Validate age."""
        if isinstance(age, str):
            age = age.strip()

            # Try to parse date of birth
            if "/" in age or "-" in age:
                result.add_warning("age", "Date of birth should be in YYYY-MM-DD format", "format")
                return

            try:
                age = int(age)
            except ValueError:
                result.add_error("age", f"Invalid age value: {age}", "invalid_type")
                return

        if not isinstance(age, (int, float)):
            result.add_error("age", "Age must be a number", "invalid_type")
            return

        if age < 0:
            result.add_error("age", "Age cannot be negative", "invalid_range")

        if age < 13:
            result.add_warning("age", f"Age {age} is under 13 - may require parental consent", "minor")

        if age > 120:
            result.add_warning("age", f"Age {age} seems unrealistic", "unrealistic")

    def _validate_country(
        self,
        country: str,
        result: ValidationResult,
    ) -> None:
        """Validate country code."""
        if not country:
            return

        country = country.strip().upper()

        # Common country codes
        valid_codes = {
            "US", "GB", "CA", "AU", "DE", "FR", "JP", "CN", "IN", "BR",
            "MX", "ES", "IT", "NL", "SE", "NO", "DK", "FI", "PL", "RU",
            "KR", "SG", "MY", "TH", "ID", "PH", "VN", "NZ", "ZA", "EG",
            "AE", "SA", "AR", "CO", "CL", "PE", "VE", "PT", "BE", "CH",
            "AT", "IE", "CZ", "HU", "RO", "UA", "TR", "IL", "PK", "BD",
            "LK", "NP", "MM", "KH", "LA", "BN", "TW", "HK", "MO",
        }

        if len(country) == 2:
            if country not in valid_codes:
                result.add_warning(
                    "country",
                    f"Unusual country code: {country}",
                    "unusual",
                )
        elif len(country) == 3:
            # ISO 3166-1 alpha-3
            if country.lower() not in ["usa", "gbr", "can", "aus", "deu", "fra"]:
                result.add_warning(
                    "country",
                    f"Alpha-3 country code detected: {country}",
                    "alpha3",
                )

    def validate_batch(
        self,
        data_list: List[Dict[str, Any]],
    ) -> List[ValidationResult]:
        """
        Validate multiple leads.

        Args:
            data_list: List of lead data dictionaries

        Returns:
            List of ValidationResult, one per lead
        """
        results = []
        for i, data in enumerate(data_list):
            try:
                result = self.validate_full(data)
                results.append(result)
            except Exception as e:
                logger.error(f"Validation error for lead {i}: {e}")
                error_result = ValidationResult(is_valid=False)
                error_result.add_error("data", str(e), "exception")
                results.append(error_result)

        return results

    def get_summary(
        self,
        results: List[ValidationResult],
    ) -> Dict[str, Any]:
        """
        Get summary statistics from validation results.

        Args:
            results: List of ValidationResult

        Returns:
            Summary statistics
        """
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid

        error_counts: Dict[str, int] = {}
        warning_counts: Dict[str, int] = {}

        for result in results:
            for error in result.errors:
                error_counts[error.code] = error_counts.get(error.code, 0) + 1

            for warning in result.warnings:
                warning_counts[warning.code] = warning_counts.get(warning.code, 0) + 1

        return {
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "validity_rate": valid / total if total > 0 else 0,
            "error_counts": error_counts,
            "warning_counts": warning_counts,
        }
