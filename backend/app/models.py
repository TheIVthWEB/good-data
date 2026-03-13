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
