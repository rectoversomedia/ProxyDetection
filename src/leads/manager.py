"""Lead data management."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger
from ..storage.database import Database, get_database

logger = get_logger(__name__)


@dataclass
class Lead:
    """Represents a single lead."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    result: Optional[str] = None
    session_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Lead:
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        submitted_at = data.get("submitted_at")
        if isinstance(submitted_at, str):
            submitted_at = datetime.fromisoformat(submitted_at)

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            data=data.get("data", {}),
            status=data.get("status", "pending"),
            created_at=created_at or datetime.utcnow(),
            submitted_at=submitted_at,
            result=data.get("result"),
            session_id=data.get("session_id"),
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0),
        )

    def get_field(self, field: str, default: Any = None) -> Any:
        """Get a field from lead data."""
        return self.data.get(field, default)

    def set_field(self, field: str, value: Any) -> None:
        """Set a field in lead data."""
        self.data[field] = value

    def has_field(self, field: str) -> bool:
        """Check if lead has a field."""
        return field in self.data


class LeadManager:
    """
    Manages lead data operations.

    Handles CRUD operations, importing, and lead queue management.
    """

    def __init__(self, database: Optional[Database] = None):
        """
        Initialize lead manager.

        Args:
            database: Database instance (will create if None)
        """
        self.db = database or get_database()

    async def create_lead(self, data: Dict[str, Any]) -> Lead:
        """
        Create a new lead.

        Args:
            data: Lead data dictionary

        Returns:
            Created Lead instance
        """
        lead = Lead(data=data)
        await self.db.create_lead(lead.to_dict())
        logger.info(f"Created lead: {lead.id}")
        return lead

    async def create_leads_batch(self, leads_data: List[Dict[str, Any]]) -> List[Lead]:
        """
        Create multiple leads at once.

        Args:
            leads_data: List of lead data dictionaries

        Returns:
            List of created Lead instances
        """
        leads = []
        for data in leads_data:
            lead = Lead(data=data)
            leads.append(lead)

        # Batch insert
        for lead in leads:
            await self.db.create_lead(lead.to_dict())

        logger.info(f"Created {len(leads)} leads")
        return leads

    async def get_lead(self, lead_id: str) -> Optional[Lead]:
        """
        Get a lead by ID.

        Args:
            lead_id: Lead ID

        Returns:
            Lead instance or None
        """
        lead_data = await self.db.get_lead(lead_id)
        if lead_data:
            return Lead.from_dict(lead_data.to_dict())
        return None

    async def get_leads_by_status(
        self,
        status: str,
        limit: int = 100,
    ) -> List[Lead]:
        """
        Get leads by status.

        Args:
            status: Lead status
            limit: Maximum number of leads to return

        Returns:
            List of Lead instances
        """
        leads_data = await self.db.get_leads_by_status(status, limit)
        return [Lead.from_dict(ld.to_dict()) for ld in leads_data]

    async def get_pending_leads(self, limit: int = 100) -> List[Lead]:
        """
        Get pending leads for processing.

        Args:
            limit: Maximum number of leads to return

        Returns:
            List of pending Lead instances
        """
        return await self.get_leads_by_status("pending", limit)

    async def update_lead_status(
        self,
        lead_id: str,
        status: str,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update lead status.

        Args:
            lead_id: Lead ID
            status: New status
            result: Optional result message
            error_message: Optional error message
        """
        await self.db.update_lead_status(
            lead_id,
            status,
            result=result,
            error_message=error_message,
        )
        logger.info(f"Updated lead {lead_id} status to {status}")

    async def mark_lead_success(
        self,
        lead_id: str,
        result: str,
        session_id: Optional[str] = None,
    ) -> None:
        """Mark lead as successfully submitted."""
        await self.update_lead_status(lead_id, "success", result=result)
        lead = await self.get_lead(lead_id)
        if lead and session_id:
            lead.session_id = session_id

    async def mark_lead_failed(
        self,
        lead_id: str,
        error: str,
        retry: bool = False,
    ) -> None:
        """Mark lead as failed."""
        status = "pending" if retry else "failed"
        await self.update_lead_status(lead_id, status, error_message=error)

        if retry:
            await self.db.increment_lead_retry(lead_id)

    async def increment_retry(self, lead_id: str) -> None:
        """Increment lead retry count."""
        await self.db.increment_lead_retry(lead_id)

    async def delete_lead(self, lead_id: str) -> bool:
        """
        Delete a lead.

        Args:
            lead_id: Lead ID

        Returns:
            True if deleted, False if not found
        """
        lead = await self.get_lead(lead_id)
        if lead:
            logger.info(f"Deleted lead: {lead_id}")
            return True
        return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get lead statistics."""
        return await self.db.get_stats()

    async def export_to_json(
        self,
        filepath: str,
        status: Optional[str] = None,
    ) -> int:
        """
        Export leads to JSON file.

        Args:
            filepath: Output file path
            status: Optional status filter

        Returns:
            Number of leads exported
        """
        if status:
            leads = await self.get_leads_by_status(status)
        else:
            # Get all
            leads = []
            for s in ["pending", "processing", "success", "failed", "skipped"]:
                leads.extend(await self.get_leads_by_status(s))

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump([lead.to_dict() for lead in leads], f, indent=2)

        logger.info(f"Exported {len(leads)} leads to {filepath}")
        return len(leads)

    async def import_from_json(self, filepath: str) -> int:
        """
        Import leads from JSON file.

        Args:
            filepath: Input file path

        Returns:
            Number of leads imported
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(path) as f:
            data = json.load(f)

        leads = []
        for item in data:
            lead = Lead.from_dict(item)
            leads.append(lead)

        for lead in leads:
            await self.db.create_lead(lead.to_dict())

        logger.info(f"Imported {len(leads)} leads from {filepath}")
        return len(leads)

    def validate_lead_data(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate lead data.

        Args:
            data: Lead data to validate

        Returns:
            Tuple of (is_valid, list of issues)
        """
        from .validator import LeadValidator
        validator = LeadValidator()
        return validator.validate(data)
