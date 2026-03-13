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
  };
  row_count?: number;
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

export interface QueryResult {
  question: string;
  sql_query: string;
  sql_explanation?: string;
  data: Record<string, any>[];
  error?: string;
  insights: string;
  key_findings?: string[];
  recommendations: string[];
  visualization?: {
    type: string;
    title: string;
    x_axis?: string;
    y_axis?: string;
    config?: Record<string, any>;
  };
  follow_up_questions?: string[];
  execution_time_ms: number;
  row_count: number;
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
