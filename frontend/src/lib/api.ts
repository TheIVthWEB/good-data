const API_BASE = "/api";

export interface DataSource {
  id: string;
  name: string;
  type: "csv" | "google_sheets";
  config: Record<string, any>;
  schema_info?: {
    columns: Column[];
    row_count: number;
    column_count: number;
    cleaning_report?: CleaningReport;
  };
  row_count?: number;
  cleaning_applied?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Column {
  name: string;
  dtype: string;
  nullable: boolean;
  unique_count: number;
  sample_values: any[];
  semantic_type?: string;
}

export interface CleaningReport {
  original_shape: [number, number];
  cleaned_shape: [number, number];
  actions_taken: string[];
  outliers_detected: Record<string, any>;
  columns_mapped: string[];
}

export interface PerformanceAssessment {
  overall_health: "healthy" | "warning" | "critical";
  health_score: number;
  key_metrics: Array<{
    metric: string;
    value: string;
    benchmark: string;
    assessment: string;
    delta_percentage: string;
  }>;
}

export interface DeepInsight {
  category: "trend" | "anomaly" | "opportunity" | "risk" | "correlation";
  title: string;
  insight: string;
  confidence: "high" | "medium" | "low";
  impact: "high" | "medium" | "low";
}

export interface ChannelAnalysis {
  channel: string;
  role: string;
  efficiency_score: number;
  strengths: string[];
  weaknesses: string[];
  recommendation: string;
}

export interface StrategicRecommendation {
  priority: "high" | "medium" | "low";
  timeframe: "immediate" | "short_term" | "long_term";
  recommendation: string;
  expected_outcome: string;
  effort: "low" | "medium" | "high";
  impact: "low" | "medium" | "high";
}

export interface Anomaly {
  type: string;
  metric: string;
  when: string;
  magnitude: string;
  possible_causes: string[];
  recommended_action: string;
}

export interface QueryResult {
  question: string;
  sql_query: string;
  sql_explanation?: string;
  data: Record<string, any>[];
  error?: string;

  // Deep marketing intelligence
  executive_summary?: string;
  performance_assessment?: PerformanceAssessment;
  deep_insights?: DeepInsight[];
  funnel_analysis?: Record<string, any>;
  channel_analysis?: ChannelAnalysis[];
  budget_recommendations?: Record<string, any>;
  anomalies_detected?: Anomaly[];
  strategic_recommendations?: StrategicRecommendation[];
  testing_suggestions?: Array<{
    test_type: string;
    hypothesis: string;
    variables: string[];
    success_metric: string;
    estimated_duration: string;
  }>;

  // Legacy fields
  insights: string;
  key_findings?: string[];
  recommendations: string[];

  // Advanced analytics
  analytics?: {
    time_series?: Record<string, any>;
    anomalies?: Array<Record<string, any>>;
    attribution?: Record<string, any>;
    correlations?: Record<string, any>;
    [key: string]: any;
  };

  // Visualization
  visualization?: {
    type: string;
    title: string;
    x_axis?: string;
    y_axis?: string;
    config?: Record<string, any>;
  };

  follow_up_questions?: string[];
  data_quality_notes?: string[];
  execution_time_ms: number;
  row_count: number;
  analysis_depth?: "deep" | "basic";
}

export async function fetchSources(): Promise<DataSource[]> {
  const res = await fetch(`${API_BASE}/sources`);
  if (!res.ok) throw new Error("Failed to fetch sources");
  const data = await res.json();
  return data.sources;
}

export async function uploadCSV(
  file: File,
  name?: string
): Promise<{ success: boolean; source: DataSource; message: string }> {
  const formData = new FormData();
  formData.append("file", file);
  if (name) formData.append("name", name);

  const res = await fetch(`${API_BASE}/upload/csv`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Upload failed");
  }

  return res.json();
}

export async function connectGoogleSheet(
  sheetUrl: string,
  worksheetName?: string,
  name?: string
): Promise<{ success: boolean; source: DataSource; message: string }> {
  const formData = new FormData();
  formData.append("sheet_url", sheetUrl);
  if (worksheetName) formData.append("worksheet_name", worksheetName);
  if (name) formData.append("name", name);

  const res = await fetch(`${API_BASE}/connect/sheets`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Connection failed");
  }

  return res.json();
}

export async function deleteSource(sourceId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/sources/${sourceId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete source");
}

export async function refreshSource(
  sourceId: string
): Promise<{ refreshed: boolean; row_count: number }> {
  const res = await fetch(`${API_BASE}/sources/${sourceId}/refresh`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to refresh source");
  return res.json();
}

export async function submitQuery(
  question: string,
  dataSourceIds?: string[]
): Promise<QueryResult> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      data_source_ids: dataSourceIds,
    }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Query failed");
  }

  return res.json();
}

export async function getSchema(): Promise<{
  sources: Array<{
    id: string;
    name: string;
    type: string;
    columns: Column[];
    row_count: number;
  }>;
  total_columns: number;
  total_rows: number;
}> {
  const res = await fetch(`${API_BASE}/schema`);
  if (!res.ok) throw new Error("Failed to fetch schema");
  return res.json();
}

// ============ Advertiser Context ============

export interface ChannelRule {
  channel: string;
  rule: string;
}

export interface AdvertiserContext {
  id?: string;
  data_source_id?: string | null;
  name: string;
  industry?: string;
  business_model?: string;
  sales_cycle_days?: number;
  primary_kpi?: string;
  secondary_kpis?: string[];
  target_cpa?: number;
  target_roas?: number;
  target_ctr?: number;
  industry_benchmarks?: Record<string, number>;
  channel_rules?: ChannelRule[];
  dos?: string[];
  donts?: string[];
  custom_instructions?: string;
  attribution_window_days?: number;
  preferred_attribution_model?: string;
  created_at?: string;
  updated_at?: string;
}

export async function fetchContexts(dataSourceId?: string): Promise<AdvertiserContext[]> {
  const url = dataSourceId
    ? `${API_BASE}/context?data_source_id=${dataSourceId}`
    : `${API_BASE}/context`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch contexts");
  const data = await res.json();
  return data.contexts;
}

export async function fetchContext(contextId: string): Promise<AdvertiserContext> {
  const res = await fetch(`${API_BASE}/context/${contextId}`);
  if (!res.ok) throw new Error("Failed to fetch context");
  return res.json();
}

export async function createContext(
  context: Omit<AdvertiserContext, "id" | "created_at" | "updated_at">
): Promise<{ id: string; message: string }> {
  const res = await fetch(`${API_BASE}/context`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(context),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to create context");
  }
  return res.json();
}

export async function updateContext(
  contextId: string,
  context: Partial<AdvertiserContext>
): Promise<{ id: string; message: string }> {
  const res = await fetch(`${API_BASE}/context/${contextId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(context),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to update context");
  }
  return res.json();
}

export async function deleteContext(contextId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/context/${contextId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete context");
}

export async function getSourceContext(
  sourceId: string
): Promise<{ context: AdvertiserContext | null; message?: string }> {
  const res = await fetch(`${API_BASE}/sources/${sourceId}/context`);
  if (!res.ok) throw new Error("Failed to fetch source context");
  return res.json();
}
