import sqlite3
import json
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
import pandas as pd

from app.config import settings


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
            json.dumps(data_source.get("config", {})),
            json.dumps(data_source.get("schema_info")),
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
