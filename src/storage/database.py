"""SQLite database operations."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Type

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models import Base, Lead, Session, ProxyHealth, Fingerprint, SubmissionLog
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Database:
    """Async SQLite database manager."""

    def __init__(self, database_url: str):
        """
        Initialize database connection.

        Args:
            database_url: SQLite database URL (e.g., sqlite+aiosqlite:///path/to/db)
        """
        if not database_url.startswith("sqlite+aiosqlite://"):
            database_url = f"sqlite+aiosqlite:///{database_url}"

        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info(f"Database initialized: {database_url}")

    async def initialize(self) -> None:
        """Create all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

    async def close(self) -> None:
        """Close database connection."""
        await self.engine.dispose()
        logger.info("Database connection closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session context manager."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # =====================================================================
    # Lead Operations
    # =====================================================================

    async def create_lead(self, data: Dict[str, Any]) -> Lead:
        """Create a new lead."""
        async with self.session() as session:
            lead = Lead(data=data)
            session.add(lead)
            await session.flush()
            await session.refresh(lead)
            return lead

    async def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Get a lead by ID."""
        async with self.session() as session:
            result = await session.execute(
                select(Lead).where(Lead.id == lead_id)
            )
            return result.scalar_one_or_none()

    async def get_leads_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> List[Lead]:
        """Get leads by status."""
        async with self.session() as session:
            result = await session.execute(
                select(Lead)
                .where(Lead.status == status)
                .limit(limit)
            )
            return list(result.scalars().all())

    async def update_lead_status(
        self,
        lead_id: str,
        status: str,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update lead status."""
        async with self.session() as session:
            updates: Dict[str, Any] = {"status": status}

            if status in ("success", "failed"):
                updates["submitted_at"] = datetime.utcnow()

            if result:
                updates["result"] = result

            if error_message:
                updates["error_message"] = error_message

            await session.execute(
                update(Lead).where(Lead.id == lead_id).values(**updates)
            )

    async def increment_lead_retry(self, lead_id: str) -> None:
        """Increment lead retry count."""
        async with self.session() as session:
            await session.execute(
                update(Lead).where(Lead.id == lead_id).values(
                    retry_count=Lead.retry_count + 1
                )
            )

    async def get_pending_leads(self, limit: int = 100) -> List[Lead]:
        """Get pending leads for processing."""
        return await self.get_leads_by_status("pending", limit)

    # =====================================================================
    # Session Operations
    # =====================================================================

    async def create_session(
        self,
        proxy_host: Optional[str] = None,
        proxy_country: Optional[str] = None,
        fingerprint_id: Optional[str] = None,
    ) -> Session:
        """Create a new session."""
        async with self.session() as session:
            session_obj = Session(
                proxy_host=proxy_host,
                proxy_country=proxy_country,
                fingerprint_id=fingerprint_id,
            )
            session.add(session_obj)
            await session.flush()
            await session.refresh(session_obj)
            return session_obj

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        async with self.session() as session:
            result = await session.execute(
                select(Session).where(Session.id == session_id)
            )
            return result.scalar_one_or_none()

    async def end_session(self, session_id: str) -> None:
        """End a session."""
        async with self.session() as session:
            await session.execute(
                update(Session)
                .where(Session.id == session_id)
                .values(ended_at=datetime.utcnow())
            )

    async def increment_session_success(self, session_id: str) -> None:
        """Increment session success count."""
        async with self.session() as session:
            await session.execute(
                update(Session).where(Session.id == session_id).values(
                    success_count=Session.success_count + 1
                )
            )

    async def increment_session_fail(self, session_id: str) -> None:
        """Increment session fail count."""
        async with self.session() as session:
            await session.execute(
                update(Session).where(Session.id == session_id).values(
                    fail_count=Session.fail_count + 1
                )
            )

    # =====================================================================
    # Proxy Health Operations
    # =====================================================================

    async def upsert_proxy_health(
        self,
        proxy: str,
        country: Optional[str] = None,
        success_rate: Optional[float] = None,
        latency: Optional[float] = None,
        is_healthy: bool = True,
    ) -> ProxyHealth:
        """Insert or update proxy health record."""
        async with self.session() as session:
            result = await session.execute(
                select(ProxyHealth).where(ProxyHealth.proxy == proxy)
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.last_checked = datetime.utcnow()
                if success_rate is not None:
                    existing.success_rate = success_rate
                if latency is not None:
                    existing.avg_latency = latency
                existing.is_healthy = is_healthy
                await session.flush()
                await session.refresh(existing)
                return existing
            else:
                health = ProxyHealth(
                    proxy=proxy,
                    country=country,
                    success_rate=success_rate,
                    avg_latency=latency,
                    is_healthy=is_healthy,
                )
                session.add(health)
                await session.flush()
                await session.refresh(health)
                return health

    async def get_healthy_proxies(
        self,
        country: Optional[str] = None,
        limit: int = 10,
    ) -> List[ProxyHealth]:
        """Get healthy proxies, optionally filtered by country."""
        async with self.session() as session:
            query = select(ProxyHealth).where(ProxyHealth.is_healthy == True)

            if country:
                query = query.where(ProxyHealth.country == country)

            query = query.order_by(ProxyHealth.success_rate.desc()).limit(limit)

            result = await session.execute(query)
            return list(result.scalars().all())

    async def mark_proxy_unhealthy(self, proxy: str) -> None:
        """Mark a proxy as unhealthy."""
        async with self.session() as session:
            await session.execute(
                update(ProxyHealth)
                .where(ProxyHealth.proxy == proxy)
                .values(is_healthy=False)
            )

    async def increment_proxy_requests(self, proxy: str, success: bool) -> None:
        """Increment proxy request counters."""
        async with self.session() as session:
            result = await session.execute(
                select(ProxyHealth).where(ProxyHealth.proxy == proxy)
            )
            proxy_health = result.scalar_one_or_none()

            if proxy_health:
                proxy_health.total_requests += 1
                if not success:
                    proxy_health.failed_requests += 1

                # Recalculate success rate
                if proxy_health.total_requests > 0:
                    proxy_health.success_rate = (
                        (proxy_health.total_requests - proxy_health.failed_requests)
                        / proxy_health.total_requests
                    )

                # Mark unhealthy if success rate drops below 50%
                if proxy_health.success_rate < 0.5:
                    proxy_health.is_healthy = False

    # =====================================================================
    # Fingerprint Operations
    # =====================================================================

    async def create_fingerprint(
        self,
        os: str,
        browser: str,
        user_agent: Optional[str] = None,
        canvas_hash: Optional[str] = None,
        webgl_vendor: Optional[str] = None,
        webgl_renderer: Optional[str] = None,
        timezone: Optional[str] = None,
        screen_resolution: Optional[str] = None,
        language: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Fingerprint:
        """Create a new fingerprint record."""
        async with self.session() as session:
            fingerprint = Fingerprint(
                os=os,
                browser=browser,
                user_agent=user_agent,
                canvas_hash=canvas_hash,
                webgl_vendor=webgl_vendor,
                webgl_renderer=webgl_renderer,
                timezone=timezone,
                screen_resolution=screen_resolution,
                language=language,
                metadata=metadata,
            )
            session.add(fingerprint)
            await session.flush()
            await session.refresh(fingerprint)
            return fingerprint

    async def get_fingerprint(self, fingerprint_id: str) -> Optional[Fingerprint]:
        """Get a fingerprint by ID."""
        async with self.session() as session:
            result = await session.execute(
                select(Fingerprint).where(Fingerprint.id == fingerprint_id)
            )
            return result.scalar_one_or_none()

    # =====================================================================
    # Log Operations
    # =====================================================================

    async def create_log(
        self,
        action: str,
        status: str,
        session_id: Optional[str] = None,
        lead_id: Optional[str] = None,
        message: Optional[str] = None,
        screenshot_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SubmissionLog:
        """Create a new submission log entry."""
        async with self.session() as session:
            log = SubmissionLog(
                session_id=session_id,
                lead_id=lead_id,
                action=action,
                status=status,
                message=message,
                screenshot_path=screenshot_path,
                metadata=metadata,
            )
            session.add(log)
            await session.flush()
            await session.refresh(log)
            return log

    async def get_logs_by_lead(self, lead_id: str) -> List[SubmissionLog]:
        """Get all logs for a lead."""
        async with self.session() as session:
            result = await session.execute(
                select(SubmissionLog)
                .where(SubmissionLog.lead_id == lead_id)
                .order_by(SubmissionLog.timestamp)
            )
            return list(result.scalars().all())

    # =====================================================================
    # Statistics
    # =====================================================================

    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        async with self.session() as session:
            lead_stats = await session.execute(
                select(
                    Lead.status,
                    func.count(Lead.id).label("count")
                ).group_by(Lead.status)
            )

            proxy_count = await session.execute(
                select(func.count(ProxyHealth.id))
            )

            healthy_proxy_count = await session.execute(
                select(func.count(ProxyHealth.id))
                .where(ProxyHealth.is_healthy == True)
            )

            return {
                "leads": {row.status: row.count for row in lead_stats},
                "total_proxies": proxy_count.scalar() or 0,
                "healthy_proxies": healthy_proxy_count.scalar() or 0,
            }


# Global database instance
_db: Optional[Database] = None


def get_database(database_url: Optional[str] = None) -> Database:
    """Get or create database instance."""
    global _db
    if _db is None:
        from ..utils.config import get_settings
        settings = get_settings()
        url = database_url or settings.database_path
        _db = Database(url)
    return _db
