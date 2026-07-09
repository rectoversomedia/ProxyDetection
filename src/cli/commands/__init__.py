"""CLI commands module."""

from .submit import submit_app
from .config import config_app
from .proxy import proxy_app
from .leads import leads_app
from .profile import profile_app

__all__ = [
    "submit_app",
    "config_app",
    "proxy_app",
    "leads_app",
    "profile_app",
]
