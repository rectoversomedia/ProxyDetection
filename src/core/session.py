"""Session management for browser sessions."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Session:
    """Represents a browser session."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proxy_host: Optional[str] = None
    proxy_country: Optional[str] = None
    fingerprint_id: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    success_count: int = 0
    fail_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Check if session is still active."""
        return self.ended_at is None

    @property
    def total_count(self) -> int:
        """Get total submission count."""
        return self.success_count + self.fail_count

    @property
    def success_rate(self) -> float:
        """Get success rate."""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "proxy_host": self.proxy_host,
            "proxy_country": self.proxy_country,
            "fingerprint_id": self.fingerprint_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "metadata": self.metadata,
        }

    def record_success(self) -> None:
        """Record a successful action."""
        self.success_count += 1
        logger.debug(f"Session {self.id}: success recorded, total: {self.success_count}")

    def record_failure(self) -> None:
        """Record a failed action."""
        self.fail_count += 1
        logger.debug(f"Session {self.id}: failure recorded, total: {self.fail_count}")

    def end(self) -> None:
        """End the session."""
        self.ended_at = datetime.utcnow()
        logger.info(
            f"Session {self.id} ended. "
            f"Success: {self.success_count}, Fail: {self.fail_count}"
        )


class SessionManager:
    """
    Manages browser sessions.

    Handles session lifecycle, tracking, and cleanup.
    """

    def __init__(self, max_concurrent: int = 5):
        """
        Initialize session manager.

        Args:
            max_concurrent: Maximum number of concurrent sessions
        """
        self.max_concurrent = max_concurrent
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()
        logger.info(f"SessionManager initialized (max concurrent: {max_concurrent})")

    async def create_session(
        self,
        proxy_host: Optional[str] = None,
        proxy_country: Optional[str] = None,
        fingerprint_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """
        Create a new session.

        Args:
            proxy_host: Proxy host for this session
            proxy_country: Proxy country
            fingerprint_id: Fingerprint ID used
            metadata: Additional metadata

        Returns:
            Created Session instance
        """
        async with self._lock:
            # Check concurrent limit
            active_count = sum(1 for s in self._sessions.values() if s.is_active)
            if active_count >= self.max_concurrent:
                logger.warning(
                    f"Max concurrent sessions reached ({self.max_concurrent}). "
                    "Waiting for available slot..."
                )

            session = Session(
                proxy_host=proxy_host,
                proxy_country=proxy_country,
                fingerprint_id=fingerprint_id,
                metadata=metadata or {},
            )

            self._sessions[session.id] = session
            logger.info(f"Created session {session.id}")

            return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session or None
        """
        return self._sessions.get(session_id)

    async def end_session(self, session_id: str) -> Optional[Session]:
        """
        End a session.

        Args:
            session_id: Session ID

        Returns:
            Ended Session or None
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session and session.is_active:
                session.end()
                return session
            return None

    async def end_all(self) -> int:
        """
        End all active sessions.

        Returns:
            Number of sessions ended
        """
        async with self._lock:
            count = 0
            for session in self._sessions.values():
                if session.is_active:
                    session.end()
                    count += 1
            logger.info(f"Ended {count} sessions")
            return count

    async def get_active_sessions(self) -> List[Session]:
        """
        Get all active sessions.

        Returns:
            List of active Session instances
        """
        return [s for s in self._sessions.values() if s.is_active]

    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics.

        Returns:
            Dict with session stats
        """
        active = [s for s in self._sessions.values() if s.is_active]
        ended = [s for s in self._sessions.values() if not s.is_active]

        total_success = sum(s.success_count for s in self._sessions.values())
        total_fail = sum(s.fail_count for s in self._sessions.values())
        total = total_success + total_fail

        return {
            "total_sessions": len(self._sessions),
            "active_sessions": len(active),
            "ended_sessions": len(ended),
            "total_success": total_success,
            "total_fail": total_fail,
            "overall_success_rate": total_success / total if total > 0 else 0,
        }

    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Remove old ended sessions from memory.

        Args:
            max_age_hours: Maximum age for ended sessions

        Returns:
            Number of sessions removed
        """
        async with self._lock:
            now = datetime.utcnow()
            to_remove = []

            for session_id, session in self._sessions.items():
                if not session.is_active and session.ended_at:
                    age = (now - session.ended_at).total_seconds() / 3600
                    if age > max_age_hours:
                        to_remove.append(session_id)

            for session_id in to_remove:
                del self._sessions[session_id]

            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old sessions")

            return len(to_remove)
