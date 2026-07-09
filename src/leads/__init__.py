"""Lead management modules for ProxyDetection."""

from .manager import LeadManager
from .parser import LeadParser
from .validator import LeadValidator
from .generator import LeadGenerator

__all__ = [
    "LeadManager",
    "LeadParser",
    "LeadValidator",
    "LeadGenerator",
]
