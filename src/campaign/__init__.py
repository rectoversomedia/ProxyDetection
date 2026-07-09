"""Campaign module for ProxyDetection."""

from .manager import (
    CampaignManager,
    CampaignConfig,
    CampaignStatus,
    FieldMapping,
    CampaignResult,
    create_prulady_campaign,
    create_generic_campaign,
)
from .sheets import GoogleSheetsReader, SheetDataTransformer

__all__ = [
    "CampaignManager",
    "CampaignConfig",
    "CampaignStatus",
    "FieldMapping",
    "CampaignResult",
    "create_prulady_campaign",
    "create_generic_campaign",
    "GoogleSheetsReader",
    "SheetDataTransformer",
]
