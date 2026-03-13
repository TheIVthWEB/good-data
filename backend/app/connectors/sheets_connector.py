import pandas as pd
from pathlib import Path
from typing import Optional
import uuid
import re

from app.config import settings
from app.database import create_data_table, save_data_source


class GoogleSheetsConnector:
    """Handle Google Sheets connections and data loading."""

    @staticmethod
    def _get_client():
        """Get authenticated Google Sheets client."""
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError:
            raise ImportError("Google Sheets libraries not installed. Run: pip install gspread google-auth")

        creds_path = Path(settings.google_sheets_credentials_path)
        if not creds_path.exists():
            raise FileNotFoundError(
                f"Google credentials file not found at {creds_path}. "
                "Download from Google Cloud Console and save as credentials.json"
            )

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]
        creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
        return gspread.authorize(creds)

    @staticmethod
    def extract_sheet_id(url_or_id: str) -> str:
        """Extract sheet ID from URL or return as-is if already an ID."""
        # Match Google Sheets URL pattern
        pattern = r"/spreadsheets/d/([a-zA-Z0-9-_]+)"
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
        return url_or_id

    @staticmethod
    def connect(sheet_url: str, worksheet_name: Optional[str] = None, custom_name: Optional[str] = None) -> dict:
        """
        Connect to a Google Sheet and import data.

        Args:
            sheet_url: Google Sheets URL or ID
            worksheet_name: Specific worksheet to import (defaults to first)
            custom_name: Custom name for the data source
        """
        client = GoogleSheetsConnector._get_client()
        sheet_id = GoogleSheetsConnector.extract_sheet_id(sheet_url)

        # Open the spreadsheet
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name) if worksheet_name else spreadsheet.sheet1

        # Get all data as DataFrame
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        if df.empty:
            raise ValueError("The worksheet is empty or has no data")

        # Generate unique ID
        source_id = str(uuid.uuid4())[:8]
        name = custom_name or spreadsheet.title
        table_name = f"data_{source_id}"

        # Extract schema
        schema_info = GoogleSheetsConnector._extract_schema(df)

        # Create queryable table
        create_data_table(table_name, df)

        # Save data source metadata
        data_source = {
            "id": source_id,
            "name": name,
            "type": "google_sheets",
            "config": {
                "sheet_id": sheet_id,
                "sheet_url": sheet_url,
                "worksheet_name": worksheet.title,
                "spreadsheet_title": spreadsheet.title,
                "table_name": table_name
            },
            "schema_info": schema_info,
            "row_count": len(df)
        }
        save_data_source(data_source)

        return data_source

    @staticmethod
    def _extract_schema(df: pd.DataFrame) -> dict:
        """Extract schema information from a DataFrame."""
        columns = []
        for col in df.columns:
            col_info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "nullable": df[col].isnull().any(),
                "unique_count": df[col].nunique(),
                "sample_values": df[col].dropna().head(3).tolist()
            }

            # Detect marketing-specific column types
            col_lower = col.lower()
            if any(term in col_lower for term in ["spend", "cost", "budget", "revenue", "price"]):
                col_info["semantic_type"] = "monetary"
            elif any(term in col_lower for term in ["click", "impression", "view", "conversion"]):
                col_info["semantic_type"] = "metric"
            elif any(term in col_lower for term in ["date", "time", "day", "month", "year"]):
                col_info["semantic_type"] = "temporal"
            elif any(term in col_lower for term in ["campaign", "ad_group", "ad", "channel", "source", "medium"]):
                col_info["semantic_type"] = "dimension"
            elif any(term in col_lower for term in ["ctr", "cpc", "cpa", "roas", "cpm", "rate"]):
                col_info["semantic_type"] = "rate"

            columns.append(col_info)

        return {
            "columns": columns,
            "row_count": len(df),
            "column_count": len(df.columns)
        }

    @staticmethod
    def refresh_data(source_id: str, source_config: dict) -> dict:
        """Refresh data from Google Sheets."""
        client = GoogleSheetsConnector._get_client()
        sheet_id = source_config["sheet_id"]
        worksheet_name = source_config.get("worksheet_name")

        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name) if worksheet_name else spreadsheet.sheet1

        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        table_name = source_config["table_name"]
        create_data_table(table_name, df)

        return {"row_count": len(df), "refreshed": True}

    @staticmethod
    def list_worksheets(sheet_url: str) -> list[str]:
        """List all worksheets in a spreadsheet."""
        client = GoogleSheetsConnector._get_client()
        sheet_id = GoogleSheetsConnector.extract_sheet_id(sheet_url)
        spreadsheet = client.open_by_key(sheet_id)
        return [ws.title for ws in spreadsheet.worksheets()]
