from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class DataSourceType(str, Enum):
    CSV = "csv"
    GOOGLE_SHEETS = "google_sheets"


class DataSource(BaseModel):
    id: str
    name: str
    type: DataSourceType
    config: dict
    schema_info: Optional[dict] = None
    row_count: Optional[int] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class DataSourceCreate(BaseModel):
    name: str
    type: DataSourceType
    config: dict = {}


class QueryRequest(BaseModel):
    question: str
    data_source_ids: Optional[list[str]] = None  # None = use all sources


class QueryResponse(BaseModel):
    question: str
    sql_query: str
    data: list[dict]
    insights: str
    recommendations: list[str]
    visualization: Optional[dict] = None
    execution_time_ms: int


class VisualizationType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    TABLE = "table"
    METRIC = "metric"
    FUNNEL = "funnel"
    HEATMAP = "heatmap"


class Visualization(BaseModel):
    type: VisualizationType
    title: str
    data: list[dict]
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    config: dict = {}


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = datetime.now()
    query_response: Optional[QueryResponse] = None


class MarketingMetrics(BaseModel):
    """Common marketing metrics for analysis"""
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    conversions: Optional[int] = None
    spend: Optional[float] = None
    revenue: Optional[float] = None
    ctr: Optional[float] = None  # Click-through rate
    cpc: Optional[float] = None  # Cost per click
    cpa: Optional[float] = None  # Cost per acquisition
    roas: Optional[float] = None  # Return on ad spend
    cpm: Optional[float] = None  # Cost per mille


class AdvertiserContext(BaseModel):
    """Advertiser-specific context for AI insights"""
    id: Optional[str] = None
    data_source_id: Optional[str] = None  # None = applies to all sources
    name: str  # e.g., "Acme Corp Context"

    # Business context
    industry: Optional[str] = None
    business_model: Optional[str] = None  # B2B, B2C, DTC, etc.
    sales_cycle_days: Optional[int] = None
    primary_kpi: Optional[str] = None
    secondary_kpis: Optional[list[str]] = None

    # Targets and benchmarks
    target_cpa: Optional[float] = None
    target_roas: Optional[float] = None
    target_ctr: Optional[float] = None
    industry_benchmarks: Optional[dict] = None  # {"cpa": 50, "roas": 3.0}

    # Channel-specific rules
    channel_rules: Optional[list[dict]] = None  # [{"channel": "Google Brand", "rule": "never pause"}]

    # Custom instructions
    dos: Optional[list[str]] = None  # Things Claude should do
    donts: Optional[list[str]] = None  # Things Claude should avoid
    custom_instructions: Optional[str] = None  # Free-form instructions

    # Attribution preferences
    attribution_window_days: Optional[int] = None
    preferred_attribution_model: Optional[str] = None

    # Metadata
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class AdvertiserContextCreate(BaseModel):
    """Create request for advertiser context"""
    data_source_id: Optional[str] = None
    name: str
    industry: Optional[str] = None
    business_model: Optional[str] = None
    sales_cycle_days: Optional[int] = None
    primary_kpi: Optional[str] = None
    secondary_kpis: Optional[list[str]] = None
    target_cpa: Optional[float] = None
    target_roas: Optional[float] = None
    target_ctr: Optional[float] = None
    industry_benchmarks: Optional[dict] = None
    channel_rules: Optional[list[dict]] = None
    dos: Optional[list[str]] = None
    donts: Optional[list[str]] = None
    custom_instructions: Optional[str] = None
    attribution_window_days: Optional[int] = None
    preferred_attribution_model: Optional[str] = None


class AdvertiserContextUpdate(BaseModel):
    """Update request for advertiser context"""
    name: Optional[str] = None
    industry: Optional[str] = None
    business_model: Optional[str] = None
    sales_cycle_days: Optional[int] = None
    primary_kpi: Optional[str] = None
    secondary_kpis: Optional[list[str]] = None
    target_cpa: Optional[float] = None
    target_roas: Optional[float] = None
    target_ctr: Optional[float] = None
    industry_benchmarks: Optional[dict] = None
    channel_rules: Optional[list[dict]] = None
    dos: Optional[list[str]] = None
    donts: Optional[list[str]] = None
    custom_instructions: Optional[str] = None
    attribution_window_days: Optional[int] = None
    preferred_attribution_model: Optional[str] = None
