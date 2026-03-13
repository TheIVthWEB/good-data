import pandas as pd
from pathlib import Path
from typing import Optional
import uuid

from app.config import settings
from app.database import create_data_table, save_data_source


class CSVConnector:
    """Handle CSV file uploads and data loading."""

    @staticmethod
    def process_upload(file_content: bytes, filename: str, custom_name: Optional[str] = None) -> dict:
        """
        Process an uploaded CSV file.

        Returns data source metadata including schema info.
        """
        # Generate unique ID and sanitized table name
        source_id = str(uuid.uuid4())[:8]
        name = custom_name or Path(filename).stem
        table_name = f"data_{source_id}"

        # Save file to disk
        upload_path = Path(settings.upload_dir) / f"{source_id}_{filename}"
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        upload_path.write_bytes(file_content)

        # Load and analyze the data
        df = pd.read_csv(upload_path)

        # Extract schema info
        schema_info = CSVConnector._extract_schema(df)

        # Create queryable table in SQLite
        create_data_table(table_name, df)

        # Save data source metadata
        data_source = {
            "id": source_id,
            "name": name,
            "type": "csv",
            "config": {
                "file_path": str(upload_path),
                "table_name": table_name,
                "original_filename": filename
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
    def load_data(source_config: dict) -> pd.DataFrame:
        """Load data from a CSV source."""
        file_path = source_config.get("file_path")
        if file_path and Path(file_path).exists():
            return pd.read_csv(file_path)
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    @staticmethod
    def refresh_data(source_id: str, source_config: dict) -> dict:
        """Refresh data from the CSV file."""
        df = CSVConnector.load_data(source_config)
        table_name = source_config["table_name"]
        create_data_table(table_name, df)
        return {"row_count": len(df), "refreshed": True}
