"""Core modules for ProxyDetection."""

from .engine import LeadSubmissionEngine, SubmissionResult, SubmissionConfig
from .session import SessionManager, Session

__all__ = [
    "LeadSubmissionEngine",
    "SubmissionResult",
    "SubmissionConfig",
    "SessionManager",
    "Session",
]
