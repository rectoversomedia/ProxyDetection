"""Database models for ProxyDetection."""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class LeadStatus(str, Enum):
    """Status of a lead."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class SubmissionStatus(str, Enum):
    """Status of a submission log entry."""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    SKIPPED = "skipped"


class Lead(Base):
    """Lead data model."""

    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=LeadStatus.PENDING.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "data": self.data,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "result": self.result,
            "session_id": self.session_id,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }


class Session(Base):
    """Session tracking model."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    proxy_host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    proxy_country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    fingerprint_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

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


class ProxyHealth(Base):
    """Proxy health monitoring model."""

    __tablename__ = "proxy_health"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proxy: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    last_checked: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_healthy: Mapped[bool] = mapped_column(Boolean, default=True)
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    failed_requests: Mapped[int] = mapped_column(Integer, default=0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "proxy": self.proxy,
            "country": self.country,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "success_rate": self.success_rate,
            "avg_latency": self.avg_latency,
            "is_healthy": self.is_healthy,
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
        }


class Fingerprint(Base):
    """Browser fingerprint model."""

    __tablename__ = "fingerprints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    os: Mapped[str] = mapped_column(String(50), nullable=False)
    browser: Mapped[str] = mapped_column(String(50), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    canvas_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    webgl_vendor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    webgl_renderer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    screen_resolution: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "os": self.os,
            "browser": self.browser,
            "user_agent": self.user_agent,
            "canvas_hash": self.canvas_hash,
            "webgl_vendor": self.webgl_vendor,
            "webgl_renderer": self.webgl_renderer,
            "timezone": self.timezone,
            "screen_resolution": self.screen_resolution,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
        }


class SubmissionLog(Base):
    """Submission log model."""

    __tablename__ = "submission_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    lead_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "lead_id": self.lead_id,
            "action": self.action,
            "status": self.status,
            "message": self.message,
            "screenshot_path": self.screenshot_path,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata,
        }
