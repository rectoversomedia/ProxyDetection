"""Custom exceptions for ProxyDetection."""


class ProxyDetectionError(Exception):
    """Base exception for ProxyDetection."""
    pass


class BrowserError(ProxyDetectionError):
    """Browser-related errors."""
    pass


class BrowserLaunchError(BrowserError):
    """Failed to launch browser."""
    pass


class BrowserConnectionError(BrowserError):
    """Lost connection to browser."""
    pass


class ProxyError(ProxyDetectionError):
    """Proxy-related errors."""
    pass


class ProxyNotAvailableError(ProxyError):
    """No proxy available."""
    pass


class ProxyAuthenticationError(ProxyError):
    """Proxy authentication failed."""
    pass


class LeadError(ProxyDetectionError):
    """Lead-related errors."""
    pass


class LeadValidationError(LeadError):
    """Lead validation failed."""
    pass


class LeadNotFoundError(LeadError):
    """Lead not found."""
    pass


class SubmissionError(ProxyDetectionError):
    """Submission-related errors."""
    pass


class ChallengeDetectedError(SubmissionError):
    """Challenge/CAPTCHA detected during submission."""

    def __init__(self, challenge_type: str, message: str = None):
        self.challenge_type = challenge_type
        self.message = message or f"Challenge detected: {challenge_type}"
        super().__init__(self.message)


class DetectionError(SubmissionError):
    """Bot detection triggered."""
    pass


class NetworkError(ProxyDetectionError):
    """Network-related errors."""
    pass


class TimeoutError(ProxyDetectionError):
    """Operation timeout."""
    pass


class ConfigurationError(ProxyDetectionError):
    """Configuration error."""
    pass


class DatabaseError(ProxyDetectionError):
    """Database operation error."""
    pass
