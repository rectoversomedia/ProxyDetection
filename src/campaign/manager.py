"""Campaign management system.

Manages multiple campaigns with different:
- Google Sheets data sources
- Target URLs
- Form field mappings
"""

from __future__ import annotations

import json
import csv
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger(__name__)


class CampaignStatus(str, Enum):
    """Campaign status."""
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FieldMapping:
    """Maps Google Sheet columns to form fields."""
    sheet_column: str  # Column name in Google Sheet
    form_selector: str  # CSS selector in the form
    field_type: str = "input"  # input, select, textarea, checkbox
    required: bool = False
    transform: Optional[str] = None  # Transform function name

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FieldMapping":
        return cls(**data)


@dataclass
class CampaignConfig:
    """Configuration for a single campaign."""
    id: str
    name: str
    description: str = ""

    # Data source
    sheet_url: str = ""
    sheet_range: str = "A1:Z"  # Default range
    has_header: bool = True

    # Target
    target_url: str = ""
    form_selectors: Dict[str, str] = field(default_factory=lambda: {
        "submit": 'button[type="submit"]',
    })

    # Field mappings
    field_mappings: List[FieldMapping] = field(default_factory=list)

    # Submission settings
    delay_between: float = 5.0
    max_retries: int = 3
    parallel: int = 1
    headless: bool = False

    # Proxy settings
    use_proxy: bool = True
    proxy_country: Optional[str] = None  # Filter proxies by country

    # Success/failure selectors
    success_selectors: List[str] = field(default_factory=lambda: [
        ".success", ".thank-you", "[class*='success']", "#success"
    ])
    failure_selectors: List[str] = field(default_factory=lambda: [
        ".error", ".validation-error", "[class*='error']"
    ])

    # Status
    status: CampaignStatus = CampaignStatus.DRAFT
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Stats
    total_leads: int = 0
    success_count: int = 0
    failed_count: int = 0
    last_run: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["field_mappings"] = [fm.to_dict() for fm in self.field_mappings]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampaignConfig":
        if "field_mappings" in data and data["field_mappings"]:
            data["field_mappings"] = [
                FieldMapping.from_dict(fm) if isinstance(fm, dict) else fm
                for fm in data["field_mappings"]
            ]
        if "status" in data and isinstance(data["status"], str):
            data["status"] = CampaignStatus(data["status"])
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "CampaignConfig":
        return cls.from_dict(json.loads(json_str))

    def save(self, directory: Path) -> Path:
        """Save campaign to file."""
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.id}.json"
        with open(path, "w") as f:
            f.write(self.to_json())
        logger.info(f"Campaign saved: {path}")
        return path

    @classmethod
    def load(cls, campaign_id: str, directory: Path) -> Optional["CampaignConfig"]:
        """Load campaign from file."""
        path = directory / f"{campaign_id}.json"
        if path.exists():
            with open(path) as f:
                return cls.from_json(f.read())
        return None


@dataclass
class CampaignResult:
    """Result of a campaign run."""
    campaign_id: str
    start_time: str
    end_time: Optional[str] = None
    total: int = 0
    success: int = 0
    failed: int = 0
    challenges: int = 0
    duration_seconds: float = 0
    results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CampaignManager:
    """
    Manages multiple campaigns.

    Handles:
    - CRUD operations for campaigns
    - Loading data from Google Sheets
    - Running campaigns
    - Tracking results
    """

    def __init__(self, campaigns_dir: Optional[Path] = None):
        """
        Initialize campaign manager.

        Args:
            campaigns_dir: Directory to store campaign configs
        """
        if campaigns_dir is None:
            campaigns_dir = Path("data/campaigns")

        self.campaigns_dir = campaigns_dir
        self.campaigns_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self._campaigns: Dict[str, CampaignConfig] = {}

        logger.info(f"CampaignManager initialized: {campaigns_dir}")

    def create_campaign(
        self,
        name: str,
        sheet_url: str,
        target_url: str,
        field_mappings: List[Dict[str, Any]],
        description: str = "",
        **kwargs,
    ) -> CampaignConfig:
        """
        Create a new campaign.

        Args:
            name: Campaign name
            sheet_url: Google Sheets URL
            target_url: Target form URL
            field_mappings: List of field mappings
            description: Campaign description

        Returns:
            Created CampaignConfig
        """
        # Generate ID from name
        import re
        campaign_id = re.sub(r"[^a-zA-Z0-9]", "_", name.lower())
        campaign_id = f"{campaign_id}_{datetime.utcnow().strftime('%Y%m%d')}"

        # Create field mappings
        mappings = [
            FieldMapping(**fm) for fm in field_mappings
        ]

        # Create campaign
        campaign = CampaignConfig(
            id=campaign_id,
            name=name,
            description=description,
            sheet_url=sheet_url,
            target_url=target_url,
            field_mappings=mappings,
            status=CampaignStatus.DRAFT,
            **kwargs,
        )

        # Save to file
        campaign.save(self.campaigns_dir)

        # Cache
        self._campaigns[campaign_id] = campaign

        logger.info(f"Created campaign: {name} ({campaign_id})")
        return campaign

    def get_campaign(self, campaign_id: str) -> Optional[CampaignConfig]:
        """Get a campaign by ID."""
        # Check cache
        if campaign_id in self._campaigns:
            return self._campaigns[campaign_id]

        # Try to load from file
        campaign = CampaignConfig.load(campaign_id, self.campaigns_dir)
        if campaign:
            self._campaigns[campaign_id] = campaign

        return campaign

    def list_campaigns(self) -> List[CampaignConfig]:
        """List all campaigns."""
        campaigns = []

        for path in self.campaigns_dir.glob("*.json"):
            try:
                with open(path) as f:
                    campaign = CampaignConfig.from_json(f.read())
                    campaigns.append(campaign)
                    self._campaigns[campaign.id] = campaign
            except Exception as e:
                logger.warning(f"Failed to load campaign {path}: {e}")

        return sorted(campaigns, key=lambda c: c.created_at, reverse=True)

    def update_campaign(self, campaign: CampaignConfig) -> None:
        """Update a campaign."""
        campaign.updated_at = datetime.utcnow().isoformat()
        campaign.save(self.campaigns_dir)
        self._campaigns[campaign.id] = campaign
        logger.info(f"Updated campaign: {campaign.name}")

    def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign."""
        path = self.campaigns_dir / f"{campaign_id}.json"
        if path.exists():
            path.unlink()
            if campaign_id in self._campaigns:
                del self._campaigns[campaign_id]
            logger.info(f"Deleted campaign: {campaign_id}")
            return True
        return False

    def import_csv(
        self,
        campaign_id: str,
        csv_path: Path,
    ) -> List[Dict[str, Any]]:
        """
        Import leads from CSV file for a campaign.

        Args:
            campaign_id: Campaign ID
            csv_path: Path to CSV file

        Returns:
            List of lead data dictionaries
        """
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        leads = []

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                leads.append(dict(row))

        logger.info(f"Imported {len(leads)} leads from CSV")
        return leads


# =============================================================================
# Pre-built Campaign Templates
# =============================================================================

def create_prulady_campaign(
    name: str,
    sheet_url: str,
) -> CampaignConfig:
    """
    Create a standard Prulady campaign template.

    Args:
        name: Campaign name
        sheet_url: Google Sheets URL

    Returns:
        CampaignConfig for Prulady
    """
    return CampaignConfig(
        id=name.lower().replace(" ", "_"),
        name=name,
        description="Prulady VCBL Campaign",
        sheet_url=sheet_url,
        target_url="https://prulady.vcbl.co.id/form",
        field_mappings=[
            FieldMapping(sheet_column="name", form_selector='input[name="name"]', field_type="input", required=True),
            FieldMapping(sheet_column="email", form_selector='input[name="email"]', field_type="input", required=True),
            FieldMapping(sheet_column="phone", form_selector='input[name="phone"]', field_type="input", required=True),
            FieldMapping(sheet_column="age", form_selector='input[name="age"]', field_type="input"),
            FieldMapping(sheet_column="gender", form_selector='select[name="gender"]', field_type="select"),
            FieldMapping(sheet_column="city", form_selector='input[name="city"]', field_type="input"),
            FieldMapping(sheet_column="state", form_selector='select[name="state"]', field_type="select"),
            FieldMapping(sheet_column="zip", form_selector='input[name="zip"]', field_type="input"),
        ],
        success_selectors=[
            ".success-message",
            ".thank-you",
            "[data-success]",
        ],
        delay_between=5.0,
        max_retries=3,
    )


def create_generic_campaign(
    name: str,
    sheet_url: str,
    target_url: str,
) -> CampaignConfig:
    """
    Create a generic campaign template.

    Args:
        name: Campaign name
        sheet_url: Google Sheets URL
        target_url: Target form URL

    Returns:
        CampaignConfig
    """
    return CampaignConfig(
        id=name.lower().replace(" ", "_"),
        name=name,
        description="Generic Lead Campaign",
        sheet_url=sheet_url,
        target_url=target_url,
        field_mappings=[
            FieldMapping(sheet_column="name", form_selector='input[name="name"]', field_type="input", required=True),
            FieldMapping(sheet_column="email", form_selector='input[name="email"]', field_type="input", required=True),
            FieldMapping(sheet_column="phone", form_selector='input[name="phone"]', field_type="input"),
        ],
    )
