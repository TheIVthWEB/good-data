from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os

from app.config import settings
from app.database import init_db, get_data_sources, get_data_source, delete_data_source
from app.connectors import CSVConnector, GoogleSheetsConnector
from app.services import QueryService
from app.models import QueryRequest, DataSourceType

# Initialize app
app = FastAPI(
    title="Good Data - Marketing Analytics AI",
    description="Ask questions about your marketing data in plain English",
    version="0.1.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
query_service = QueryService()


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


# ============ Data Sources ============

@app.get("/api/sources")
async def list_sources():
    """List all connected data sources."""
    sources = get_data_sources()
    return {"sources": sources}


@app.get("/api/sources/{source_id}")
async def get_source(source_id: str):
    """Get details about a specific data source."""
    source = get_data_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return source


@app.delete("/api/sources/{source_id}")
async def remove_source(source_id: str):
    """Delete a data source."""
    source = get_data_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    delete_data_source(source_id)
    return {"deleted": True, "id": source_id}


@app.post("/api/sources/{source_id}/refresh")
async def refresh_source(source_id: str):
    """Refresh data from the source."""
    source = get_data_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    try:
        if source["type"] == DataSourceType.CSV:
            result = CSVConnector.refresh_data(source_id, source["config"])
        elif source["type"] == DataSourceType.GOOGLE_SHEETS:
            result = GoogleSheetsConnector.refresh_data(source_id, source["config"])
        else:
            raise HTTPException(status_code=400, detail=f"Unknown source type: {source['type']}")

        return {"refreshed": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ CSV Upload ============

@app.post("/api/upload/csv")
async def upload_csv(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None)
):
    """Upload a CSV file as a data source."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    if file.size and file.size > settings.max_upload_size:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    try:
        content = await file.read()
        source = CSVConnector.process_upload(content, file.filename, name)
        return {
            "success": True,
            "source": source,
            "message": f"Successfully imported {source['row_count']} rows"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Google Sheets ============

@app.post("/api/connect/sheets")
async def connect_google_sheet(
    sheet_url: str = Form(...),
    worksheet_name: Optional[str] = Form(None),
    name: Optional[str] = Form(None)
):
    """Connect to a Google Sheet."""
    try:
        source = GoogleSheetsConnector.connect(sheet_url, worksheet_name, name)
        return {
            "success": True,
            "source": source,
            "message": f"Successfully imported {source['row_count']} rows from Google Sheets"
        }
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=400,
            detail="Google credentials not configured. Please add credentials.json file."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sheets/worksheets")
async def list_worksheets(sheet_url: str):
    """List worksheets in a Google Sheet."""
    try:
        worksheets = GoogleSheetsConnector.list_worksheets(sheet_url)
        return {"worksheets": worksheets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Query ============

@app.post("/api/query")
async def query_data(request: QueryRequest):
    """
    Process a natural language query against your data.

    Ask questions like:
    - "What's my total ad spend by campaign?"
    - "Which channels have the best ROAS?"
    - "Show me daily conversions for the last 30 days"
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    result = query_service.process_query(
        request.question,
        request.data_source_ids
    )

    if result.get("error") and not result.get("data"):
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# ============ Schema ============

@app.get("/api/schema")
async def get_combined_schema():
    """Get the combined schema of all data sources."""
    sources = get_data_sources()
    combined = {
        "sources": [],
        "total_columns": 0,
        "total_rows": 0
    }

    for source in sources:
        schema = source.get("schema_info", {})
        combined["sources"].append({
            "id": source["id"],
            "name": source["name"],
            "type": source["type"],
            "columns": schema.get("columns", []),
            "row_count": source.get("row_count", 0)
        })
        combined["total_columns"] += len(schema.get("columns", []))
        combined["total_rows"] += source.get("row_count", 0)

    return combined


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
