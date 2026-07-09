"""Google Sheets data source integration."""

from __future__ import annotations

import csv
import io
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from ..utils.logger import get_logger

logger = get_logger(__name__)


class GoogleSheetsReader:
    """
    Read data from Google Sheets.

    Supports:
    - Public sheets (anyone with link)
    - Shared sheets (need email access)
    - Export as CSV
    """

    EXPORT_URL_TEMPLATE = "https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    def __init__(self, timeout: int = 30):
        """
        Initialize Google Sheets reader.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    def parse_sheet_url(self, url: str) -> tuple[str, str]:
        """
        Parse Google Sheets URL to get sheet ID and gid.

        Args:
            url: Google Sheets URL

        Returns:
            Tuple of (sheet_id, gid)

        Supported URL formats:
        - https://docs.google.com/spreadsheets/d/SHEET_ID/edit
        - https://docs.google.com/spreadsheets/d/SHEET_ID/edit#gid=GID
        - https://docs.google.com/spreadsheets/d/SHEET_ID/ccc?key=KEY
        """
        # Extract sheet ID
        # Pattern: /spreadsheets/d/SHEET_ID/
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
        if not match:
            raise ValueError(f"Invalid Google Sheets URL: {url}")

        sheet_id = match.group(1)

        # Extract gid
        gid_match = re.search(r"gid=([0-9]+)", url)
        gid = gid_match.group(1) if gid_match else "0"

        return sheet_id, gid

    async def fetch_as_csv(
        self,
        sheet_url: str,
        range: str = "A1:Z",
        use_export: bool = True,
    ) -> str:
        """
        Fetch sheet data as CSV.

        Args:
            sheet_url: Google Sheets URL
            range: Cell range (default: A1:Z)
            use_export: Use CSV export endpoint (faster)

        Returns:
            CSV data as string
        """
        client = await self._get_client()
        sheet_id, gid = self.parse_sheet_url(sheet_url)

        if use_export:
            # Use CSV export - fastest method
            url = self.EXPORT_URL_TEMPLATE.format(sheet_id=sheet_id, gid=gid)

            if range != "A1:Z":
                # Add range parameter
                url += f"&range={range}"

            logger.debug(f"Fetching Google Sheet: {url}")

            response = await client.get(url)
            response.raise_for_status()

            return response.text
        else:
            # Use Sheets API
            # This requires API key and is slower but more flexible
            raise NotImplementedError("Sheets API not implemented yet. Use CSV export.")

    async def read(
        self,
        sheet_url: str,
        range: str = "A1:Z",
        has_header: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Read sheet data and return as list of dictionaries.

        Args:
            sheet_url: Google Sheets URL
            range: Cell range
            has_header: First row is header

        Returns:
            List of row dictionaries
        """
        csv_data = await self.fetch_as_csv(sheet_url, range)

        return self.parse_csv(csv_data, has_header=has_header)

    def parse_csv(
        self,
        csv_data: str,
        has_header: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Parse CSV data into list of dictionaries.

        Args:
            csv_data: CSV string
            has_header: First row is header

        Returns:
            List of row dictionaries
        """
        rows = []
        reader = csv.DictReader(io.StringIO(csv_data))

        for row in reader:
            # Clean up values
            cleaned_row = {}
            for key, value in row.items():
                # Skip empty columns
                if key and key.strip():
                    cleaned_key = key.strip()
                    cleaned_value = value.strip() if value else ""
                    cleaned_row[cleaned_key] = cleaned_value

            if cleaned_row and any(cleaned_row.values()):
                rows.append(cleaned_row)

        logger.info(f"Parsed {len(rows)} rows from CSV")
        return rows

    async def get_sheet_info(self, sheet_url: str) -> Dict[str, Any]:
        """
        Get information about the sheet.

        Args:
            sheet_url: Google Sheets URL

        Returns:
            Dict with sheet info
        """
        csv_data = await self.fetch_as_csv(sheet_url)
        rows = self.parse_csv(csv_data)

        info = {
            "url": sheet_url,
            "total_rows": len(rows),
            "columns": list(rows[0].keys()) if rows else [],
            "first_row": rows[0] if rows else {},
        }

        return info

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# =============================================================================
# Sheet Data Transformer
# =============================================================================

class SheetDataTransformer:
    """
    Transform Google Sheet data to match campaign field mappings.
    """

    def __init__(self, field_mappings: List[Dict[str, Any]]):
        """
        Initialize transformer.

        Args:
            field_mappings: List of field mapping dicts
        """
        self.field_mappings = field_mappings

    def transform_row(
        self,
        row: Dict[str, Any],
        include_unmapped: bool = True,
    ) -> Dict[str, Any]:
        """
        Transform a row according to field mappings.

        Args:
            row: Raw row data from sheet
            include_unmapped: Include columns not in mappings

        Returns:
            Transformed row data
        """
        transformed = {}

        for mapping in self.field_mappings:
            sheet_column = mapping.get("sheet_column", "")
            form_selector = mapping.get("form_selector", "")
            transform = mapping.get("transform")

            # Get value from sheet
            value = row.get(sheet_column, "")

            # Apply transform if specified
            if transform and value:
                value = self._apply_transform(value, transform)

            # Use selector as key (cleaned)
            key = self._clean_key(form_selector)

            transformed[key] = value

        # Add unmapped columns if requested
        if include_unmapped:
            mapped_columns = {m.get("sheet_column") for m in self.field_mappings}
            for column, value in row.items():
                if column not in mapped_columns and value:
                    transformed[column] = value

        return transformed

    def transform_batch(
        self,
        rows: List[Dict[str, Any]],
        include_unmapped: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Transform multiple rows.

        Args:
            rows: List of raw row data
            include_unmapped: Include unmapped columns

        Returns:
            List of transformed rows
        """
        return [
            self.transform_row(row, include_unmapped=include_unmapped)
            for row in rows
        ]

    def _clean_key(self, selector: str) -> str:
        """Extract clean key name from CSS selector."""
        # Extract name attribute
        name_match = re.search(r'name=["\']?([^"\']+)["\']?', selector)
        if name_match:
            return name_match.group(1)

        # Extract id
        id_match = re.search(r'id=["\']?([^"\']+)["\']?', selector)
        if id_match:
            return id_match.group(1)

        # Clean selector path
        selector = selector.split("=")[1] if "=" in selector else selector
        selector = selector.replace('"', "").replace("'", "")
        return selector

    def _apply_transform(self, value: str, transform: str) -> Any:
        """
        Apply transform to value.

        Supported transforms:
        - strip: Remove whitespace
        - lower: Convert to lowercase
        - upper: Convert to uppercase
        - phone: Format phone number
        - date: Parse date
        """
        if transform == "strip":
            return value.strip()
        elif transform == "lower":
            return value.lower().strip()
        elif transform == "upper":
            return value.upper().strip()
        elif transform == "phone":
            # Keep only digits
            return re.sub(r"\D", "", value)
        elif transform == "date":
            # Parse date string
            try:
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                    try:
                        return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
                    except ValueError:
                        continue
                return value
            except Exception:
                return value
        else:
            return value
