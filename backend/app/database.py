import sqlite3
import json
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from datetime import datetime
import pandas as pd
import numpy as np

from app.config import settings


class CustomJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles pandas/numpy types."""
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def json_dumps(obj):
    """JSON dumps with custom encoder for pandas/numpy types."""
    return json.dumps(obj, cls=CustomJSONEncoder)


DATABASE_PATH = Path(settings.database_url.replace("sqlite:///", ""))


def init_db():
    """Initialize the database with required tables."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        cursor = conn.cursor()

        # Data sources metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                config TEXT NOT NULL,
                schema_info TEXT,
                row_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Query history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                sql_query TEXT,
                result_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Chat sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                messages TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Advertiser context table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS advertiser_context (
                id TEXT PRIMARY KEY,
                data_source_id TEXT,
                name TEXT NOT NULL,
                industry TEXT,
                business_model TEXT,
                sales_cycle_days INTEGER,
                primary_kpi TEXT,
                secondary_kpis TEXT,
                target_cpa REAL,
                target_roas REAL,
                target_ctr REAL,
                industry_benchmarks TEXT,
                channel_rules TEXT,
                dos TEXT,
                donts TEXT,
                custom_instructions TEXT,
                attribution_window_days INTEGER,
                preferred_attribution_model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (data_source_id) REFERENCES data_sources(id) ON DELETE CASCADE
            )
        """)

        conn.commit()


@contextmanager
def get_connection():
    """Get a database connection context manager."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def save_data_source(data_source: dict):
    """Save or update a data source."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO data_sources
            (id, name, type, config, schema_info, row_count, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            data_source["id"],
            data_source["name"],
            data_source["type"],
            json_dumps(data_source.get("config", {})),
            json_dumps(data_source.get("schema_info")),
            data_source.get("row_count")
        ))
        conn.commit()


def get_data_sources() -> list[dict]:
    """Get all data sources."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data_sources ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "type": row["type"],
                "config": json.loads(row["config"]),
                "schema_info": json.loads(row["schema_info"]) if row["schema_info"] else None,
                "row_count": row["row_count"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            for row in rows
        ]


def get_data_source(source_id: str) -> Optional[dict]:
    """Get a specific data source."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data_sources WHERE id = ?", (source_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "name": row["name"],
                "type": row["type"],
                "config": json.loads(row["config"]),
                "schema_info": json.loads(row["schema_info"]) if row["schema_info"] else None,
                "row_count": row["row_count"]
            }
        return None


def delete_data_source(source_id: str):
    """Delete a data source."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM data_sources WHERE id = ?", (source_id,))
        conn.commit()


def save_query_history(question: str, sql_query: str, result_summary: str):
    """Save a query to history."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO query_history (question, sql_query, result_summary)
            VALUES (?, ?, ?)
        """, (question, sql_query, result_summary))
        conn.commit()


def create_data_table(table_name: str, df: pd.DataFrame):
    """Create a table from a pandas DataFrame for querying."""
    with get_connection() as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)


def query_data(sql: str) -> pd.DataFrame:
    """Execute a SQL query and return results as DataFrame."""
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn)


# ============ Advertiser Context Functions ============

def save_advertiser_context(context: dict) -> str:
    """Save or update advertiser context."""
    import uuid

    context_id = context.get("id") or str(uuid.uuid4())[:8]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO advertiser_context
            (id, data_source_id, name, industry, business_model, sales_cycle_days,
             primary_kpi, secondary_kpis, target_cpa, target_roas, target_ctr,
             industry_benchmarks, channel_rules, dos, donts, custom_instructions,
             attribution_window_days, preferred_attribution_model, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            context_id,
            context.get("data_source_id"),
            context["name"],
            context.get("industry"),
            context.get("business_model"),
            context.get("sales_cycle_days"),
            context.get("primary_kpi"),
            json_dumps(context.get("secondary_kpis")) if context.get("secondary_kpis") else None,
            context.get("target_cpa"),
            context.get("target_roas"),
            context.get("target_ctr"),
            json_dumps(context.get("industry_benchmarks")) if context.get("industry_benchmarks") else None,
            json_dumps(context.get("channel_rules")) if context.get("channel_rules") else None,
            json_dumps(context.get("dos")) if context.get("dos") else None,
            json_dumps(context.get("donts")) if context.get("donts") else None,
            context.get("custom_instructions"),
            context.get("attribution_window_days"),
            context.get("preferred_attribution_model"),
        ))
        conn.commit()

    return context_id


def get_advertiser_contexts(data_source_id: Optional[str] = None) -> list[dict]:
    """Get all advertiser contexts, optionally filtered by data source."""
    with get_connection() as conn:
        cursor = conn.cursor()

        if data_source_id:
            cursor.execute("""
                SELECT * FROM advertiser_context
                WHERE data_source_id = ? OR data_source_id IS NULL
                ORDER BY created_at DESC
            """, (data_source_id,))
        else:
            cursor.execute("SELECT * FROM advertiser_context ORDER BY created_at DESC")

        rows = cursor.fetchall()
        return [_parse_context_row(row) for row in rows]


def get_advertiser_context(context_id: str) -> Optional[dict]:
    """Get a specific advertiser context."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM advertiser_context WHERE id = ?", (context_id,))
        row = cursor.fetchone()
        if row:
            return _parse_context_row(row)
        return None


def delete_advertiser_context(context_id: str):
    """Delete an advertiser context."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM advertiser_context WHERE id = ?", (context_id,))
        conn.commit()


def get_context_for_source(data_source_id: str) -> Optional[dict]:
    """Get the most relevant context for a data source (specific or global)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        # First try to get source-specific context
        cursor.execute("""
            SELECT * FROM advertiser_context
            WHERE data_source_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
        """, (data_source_id,))
        row = cursor.fetchone()

        if row:
            return _parse_context_row(row)

        # Fall back to global context (no data_source_id)
        cursor.execute("""
            SELECT * FROM advertiser_context
            WHERE data_source_id IS NULL
            ORDER BY updated_at DESC
            LIMIT 1
        """)
        row = cursor.fetchone()

        if row:
            return _parse_context_row(row)

        return None


def _parse_context_row(row) -> dict:
    """Parse a database row into a context dict."""
    return {
        "id": row["id"],
        "data_source_id": row["data_source_id"],
        "name": row["name"],
        "industry": row["industry"],
        "business_model": row["business_model"],
        "sales_cycle_days": row["sales_cycle_days"],
        "primary_kpi": row["primary_kpi"],
        "secondary_kpis": json.loads(row["secondary_kpis"]) if row["secondary_kpis"] else None,
        "target_cpa": row["target_cpa"],
        "target_roas": row["target_roas"],
        "target_ctr": row["target_ctr"],
        "industry_benchmarks": json.loads(row["industry_benchmarks"]) if row["industry_benchmarks"] else None,
        "channel_rules": json.loads(row["channel_rules"]) if row["channel_rules"] else None,
        "dos": json.loads(row["dos"]) if row["dos"] else None,
        "donts": json.loads(row["donts"]) if row["donts"] else None,
        "custom_instructions": row["custom_instructions"],
        "attribution_window_days": row["attribution_window_days"],
        "preferred_attribution_model": row["preferred_attribution_model"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
