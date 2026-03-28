from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os

from app.config import settings
from app.database import (
    init_db, get_data_sources, get_data_source, delete_data_source, query_data as db_query,
    save_advertiser_context, get_advertiser_contexts, get_advertiser_context,
    delete_advertiser_context, get_context_for_source
)
from app.connectors import CSVConnector, GoogleSheetsConnector
from app.services import QueryService, ConversionAnalytics, IncrementalityAnalyzer, AttributionModels
from app.models import QueryRequest, DataSourceType, AdvertiserContextCreate, AdvertiserContextUpdate
import pandas as pd

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
conversion_analytics = ConversionAnalytics()
incrementality_analyzer = IncrementalityAnalyzer()
attribution_models = AttributionModels()


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


# ============ Conversion Analytics ============

@app.get("/api/analytics/funnel")
async def analyze_funnel():
    """Analyze the full conversion funnel across all data."""
    sources = get_data_sources()
    if not sources:
        raise HTTPException(status_code=400, detail="No data sources available")

    try:
        # Get all data
        table_names = [s["config"]["table_name"] for s in sources]
        dfs = [db_query(f"SELECT * FROM {t}") for t in table_names]
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

        if df.empty:
            raise HTTPException(status_code=400, detail="No data available")

        result = conversion_analytics.analyze_conversion_funnel(df)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/conversion-by-segment/{segment}")
async def conversion_by_segment(segment: str):
    """Analyze conversion rates by segment with statistical comparison."""
    sources = get_data_sources()
    if not sources:
        raise HTTPException(status_code=400, detail="No data sources available")

    try:
        table_names = [s["config"]["table_name"] for s in sources]
        dfs = [db_query(f"SELECT * FROM {t}") for t in table_names]
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

        if df.empty:
            raise HTTPException(status_code=400, detail="No data available")

        result = conversion_analytics.conversion_rate_by_segment(df, segment)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/conversion-trends")
async def conversion_trends():
    """Analyze conversion rate trends over time."""
    sources = get_data_sources()
    if not sources:
        raise HTTPException(status_code=400, detail="No data sources available")

    try:
        table_names = [s["config"]["table_name"] for s in sources]
        dfs = [db_query(f"SELECT * FROM {t}") for t in table_names]
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

        if df.empty:
            raise HTTPException(status_code=400, detail="No data available")

        result = conversion_analytics.conversion_trend_analysis(df)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analytics/ab-test")
async def analyze_ab_test(
    variant_a_name: str = Form(...),
    variant_a_visitors: int = Form(...),
    variant_a_conversions: int = Form(...),
    variant_b_name: str = Form(...),
    variant_b_visitors: int = Form(...),
    variant_b_conversions: int = Form(...)
):
    """Analyze A/B test results for statistical significance."""
    variant_a = {
        "name": variant_a_name,
        "visitors": variant_a_visitors,
        "conversions": variant_a_conversions
    }
    variant_b = {
        "name": variant_b_name,
        "visitors": variant_b_visitors,
        "conversions": variant_b_conversions
    }

    result = conversion_analytics.ab_test_analysis(variant_a, variant_b)
    return result


@app.get("/api/analytics/sample-size")
async def calculate_sample_size(
    baseline_rate: float,
    minimum_effect: float = 0.1,
    confidence: float = 0.95,
    power: float = 0.8
):
    """Calculate required sample size for A/B test."""
    result = conversion_analytics.sample_size_calculator(
        baseline_rate, minimum_effect, confidence, power
    )
    return result


# ============ Incrementality Analytics ============

@app.get("/api/analytics/incrementality")
async def estimate_incrementality():
    """Estimate channel incrementality using statistical methods."""
    sources = get_data_sources()
    if not sources:
        raise HTTPException(status_code=400, detail="No data sources available")

    try:
        table_names = [s["config"]["table_name"] for s in sources]
        dfs = [db_query(f"SELECT * FROM {t}") for t in table_names]
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

        if df.empty:
            raise HTTPException(status_code=400, detail="No data available")

        result = incrementality_analyzer.estimate_channel_incrementality(df)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/incrementality/time-based")
async def time_based_incrementality(treatment_start: Optional[str] = None):
    """Estimate incrementality using before/after analysis."""
    sources = get_data_sources()
    if not sources:
        raise HTTPException(status_code=400, detail="No data sources available")

    try:
        table_names = [s["config"]["table_name"] for s in sources]
        dfs = [db_query(f"SELECT * FROM {t}") for t in table_names]
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

        if df.empty:
            raise HTTPException(status_code=400, detail="No data available")

        result = incrementality_analyzer.time_based_incrementality(df, treatment_start=treatment_start)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/incrementality/holdout-design")
async def design_holdout_test(
    daily_conversions: float,
    minimum_lift: float = 0.1,
    confidence: float = 0.95,
    power: float = 0.8
):
    """Design a holdout test to measure true incrementality."""
    result = incrementality_analyzer.design_holdout_test(
        daily_conversions, minimum_lift, confidence, power
    )
    return result


# ============ Attribution Analytics ============

@app.get("/api/analytics/attribution")
async def attribution_analysis():
    """
    Run attribution analysis on aggregated channel data.

    For multi-touch attribution models, upload user journey data with columns:
    user_id, timestamp, channel, converted
    """
    sources = get_data_sources()
    if not sources:
        raise HTTPException(status_code=400, detail="No data sources available")

    try:
        table_names = [s["config"]["table_name"] for s in sources]
        dfs = [db_query(f"SELECT * FROM {t}") for t in table_names]
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

        if df.empty:
            raise HTTPException(status_code=400, detail="No data available")

        # Check if this is journey data or aggregated data
        journey_cols = ['user_id', 'timestamp', 'channel', 'converted']
        has_journey_data = all(col in df.columns for col in journey_cols)

        if has_journey_data:
            result = attribution_models.attribute_journeys(df)
        else:
            result = attribution_models.attribute_aggregated_data(df)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analytics/attribution/journeys")
async def multi_touch_attribution(
    user_col: str = Form(default="user_id"),
    timestamp_col: str = Form(default="timestamp"),
    channel_col: str = Form(default="channel"),
    conversion_col: str = Form(default="converted"),
    revenue_col: Optional[str] = Form(default=None)
):
    """
    Run multi-touch attribution on user journey data.

    Requires data with: user_id, timestamp, channel, converted columns.
    Runs all attribution models: last-touch, first-touch, linear,
    position-based, time-decay, and W-shaped.
    """
    sources = get_data_sources()
    if not sources:
        raise HTTPException(status_code=400, detail="No data sources available")

    try:
        table_names = [s["config"]["table_name"] for s in sources]
        dfs = [db_query(f"SELECT * FROM {t}") for t in table_names]
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

        if df.empty:
            raise HTTPException(status_code=400, detail="No data available")

        result = attribution_models.attribute_journeys(
            df,
            user_col=user_col,
            timestamp_col=timestamp_col,
            channel_col=channel_col,
            conversion_col=conversion_col,
            revenue_col=revenue_col
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/attribution/compare")
async def compare_attribution_models():
    """
    Compare all attribution models side-by-side.

    Shows how credit differs across models and identifies channels
    with the biggest discrepancies between models.
    """
    sources = get_data_sources()
    if not sources:
        raise HTTPException(status_code=400, detail="No data sources available")

    try:
        table_names = [s["config"]["table_name"] for s in sources]
        dfs = [db_query(f"SELECT * FROM {t}") for t in table_names]
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

        if df.empty:
            raise HTTPException(status_code=400, detail="No data available")

        # Check for journey data
        journey_cols = ['user_id', 'timestamp', 'channel', 'converted']
        if not all(col in df.columns for col in journey_cols):
            return {
                "error": "Multi-touch model comparison requires user journey data",
                "required_columns": journey_cols,
                "your_columns": list(df.columns),
                "suggestion": "Upload data with user_id, timestamp, channel, and converted columns"
            }

        result = attribution_models.attribute_journeys(df)

        # Return just the comparison
        return {
            "model_comparison": result.get("model_comparison"),
            "channel_insights": result.get("channel_insights"),
            "journey_stats": result.get("journey_stats")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Advertiser Context ============

@app.get("/api/context")
async def list_contexts(data_source_id: Optional[str] = None):
    """List all advertiser contexts, optionally filtered by data source."""
    contexts = get_advertiser_contexts(data_source_id)
    return {"contexts": contexts}


@app.get("/api/context/{context_id}")
async def get_context(context_id: str):
    """Get a specific advertiser context."""
    context = get_advertiser_context(context_id)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    return context


@app.post("/api/context")
async def create_context(context: AdvertiserContextCreate):
    """
    Create a new advertiser context.

    This context will be used by Claude when generating insights for the
    associated data source (or all sources if data_source_id is None).

    Example:
    {
        "name": "Acme Corp",
        "data_source_id": "abc123",  // optional, null = applies to all
        "industry": "B2B SaaS",
        "business_model": "B2B",
        "sales_cycle_days": 45,
        "primary_kpi": "Qualified Leads",
        "target_cpa": 150,
        "target_roas": 3.0,
        "channel_rules": [
            {"channel": "Google Brand", "rule": "Never pause, always maintain"},
            {"channel": "LinkedIn", "rule": "Expect high CPA ($200+), focus on quality"}
        ],
        "dos": [
            "Weight MQLs higher than raw form fills",
            "Consider 30-day attribution window"
        ],
        "donts": [
            "Don't recommend pausing brand campaigns",
            "Don't compare B2B CPAs to B2C benchmarks"
        ],
        "custom_instructions": "This client is very sensitive about brand safety."
    }
    """
    context_dict = context.model_dump()
    context_id = save_advertiser_context(context_dict)
    return {"id": context_id, "message": "Context created successfully"}


@app.put("/api/context/{context_id}")
async def update_context(context_id: str, context: AdvertiserContextUpdate):
    """Update an existing advertiser context."""
    existing = get_advertiser_context(context_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Context not found")

    # Merge updates with existing
    update_data = context.model_dump(exclude_unset=True)
    updated_context = {**existing, **update_data, "id": context_id}

    save_advertiser_context(updated_context)
    return {"id": context_id, "message": "Context updated successfully"}


@app.delete("/api/context/{context_id}")
async def remove_context(context_id: str):
    """Delete an advertiser context."""
    existing = get_advertiser_context(context_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Context not found")

    delete_advertiser_context(context_id)
    return {"deleted": True, "id": context_id}


@app.get("/api/sources/{source_id}/context")
async def get_source_context(source_id: str):
    """Get the effective context for a specific data source."""
    source = get_data_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    context = get_context_for_source(source_id)
    if not context:
        return {"context": None, "message": "No context configured for this source"}

    return {"context": context}


@app.post("/api/context/quick-setup")
async def quick_context_setup(
    name: str = Form(...),
    data_source_id: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    business_model: Optional[str] = Form(None),
    primary_kpi: Optional[str] = Form(None),
    target_cpa: Optional[float] = Form(None),
    target_roas: Optional[float] = Form(None),
    dos: Optional[str] = Form(None),  # Comma-separated
    donts: Optional[str] = Form(None),  # Comma-separated
    custom_instructions: Optional[str] = Form(None)
):
    """
    Quick setup for advertiser context using form data.

    For dos/donts, provide comma-separated values:
    dos: "Focus on lead quality, Consider 30-day window"
    """
    context = {
        "name": name,
        "data_source_id": data_source_id,
        "industry": industry,
        "business_model": business_model,
        "primary_kpi": primary_kpi,
        "target_cpa": target_cpa,
        "target_roas": target_roas,
        "dos": [d.strip() for d in dos.split(",")] if dos else None,
        "donts": [d.strip() for d in donts.split(",")] if donts else None,
        "custom_instructions": custom_instructions,
    }

    context_id = save_advertiser_context(context)
    return {"id": context_id, "message": "Context created successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
