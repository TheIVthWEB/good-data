"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  FileSpreadsheet,
  Table2,
  Trash2,
  RefreshCw,
  X,
  Plus,
  Database,
} from "lucide-react";
import { DataSource, uploadCSV, deleteSource, refreshSource } from "@/lib/api";
import clsx from "clsx";

interface DataSourcePanelProps {
  sources: DataSource[];
  onSourcesChange: () => void;
  isOpen: boolean;
  onClose: () => void;
}

export default function DataSourcePanel({
  sources,
  onSourcesChange,
  isOpen,
  onClose,
}: DataSourcePanelProps) {
  const [uploading, setUploading] = useState(false);
  const [refreshingId, setRefreshingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setUploading(true);
      setError(null);

      try {
        await uploadCSV(file);
        onSourcesChange();
      } catch (e: any) {
        setError(e.message);
      } finally {
        setUploading(false);
      }
    },
    [onSourcesChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    multiple: false,
  });

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to remove this data source?")) return;
    try {
      await deleteSource(id);
      onSourcesChange();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleRefresh = async (id: string) => {
    setRefreshingId(id);
    try {
      await refreshSource(id);
      onSourcesChange();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setRefreshingId(null);
    }
  };

  const getSourceIcon = (type: string) => {
    if (type === "google_sheets") {
      return <FileSpreadsheet className="w-5 h-5 text-green-600" />;
    }
    return <Table2 className="w-5 h-5 text-blue-600" />;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/20"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="relative w-full max-w-md bg-white shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-primary-600" />
            <h2 className="text-lg font-semibold">Data Sources</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Error */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
              {error}
              <button
                onClick={() => setError(null)}
                className="ml-2 underline"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Upload Zone */}
          <div
            {...getRootProps()}
            className={clsx(
              "border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors",
              isDragActive
                ? "border-primary-500 bg-primary-50"
                : "border-gray-300 hover:border-primary-400 hover:bg-gray-50"
            )}
          >
            <input {...getInputProps()} />
            <Upload
              className={clsx(
                "w-8 h-8 mx-auto mb-2",
                isDragActive ? "text-primary-500" : "text-gray-400"
              )}
            />
            {uploading ? (
              <p className="text-sm text-gray-600">Uploading...</p>
            ) : isDragActive ? (
              <p className="text-sm text-primary-600">Drop your CSV here</p>
            ) : (
              <>
                <p className="text-sm text-gray-600">
                  Drag & drop a CSV file, or click to select
                </p>
                <p className="text-xs text-gray-400 mt-1">Max 50MB</p>
              </>
            )}
          </div>

          {/* Sources List */}
          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              Connected Sources ({sources.length})
            </h3>

            {sources.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                No data sources connected yet
              </p>
            ) : (
              <div className="space-y-3">
                {sources.map((source) => (
                  <div
                    key={source.id}
                    className="border rounded-lg p-4 bg-white hover:shadow-sm transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        {getSourceIcon(source.type)}
                        <div>
                          <h4 className="font-medium text-gray-900">
                            {source.name}
                          </h4>
                          <p className="text-xs text-gray-500 mt-0.5">
                            {source.row_count?.toLocaleString()} rows
                            {source.schema_info?.column_count &&
                              ` \u00B7 ${source.schema_info.column_count} columns`}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleRefresh(source.id)}
                          disabled={refreshingId === source.id}
                          className="p-1.5 hover:bg-gray-100 rounded text-gray-500 hover:text-gray-700"
                          title="Refresh data"
                        >
                          <RefreshCw
                            className={clsx(
                              "w-4 h-4",
                              refreshingId === source.id && "animate-spin"
                            )}
                          />
                        </button>
                        <button
                          onClick={() => handleDelete(source.id)}
                          className="p-1.5 hover:bg-red-50 rounded text-gray-500 hover:text-red-600"
                          title="Remove source"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Schema preview */}
                    {source.schema_info?.columns && (
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-xs text-gray-500 mb-1.5">Columns:</p>
                        <div className="flex flex-wrap gap-1.5">
                          {source.schema_info.columns.slice(0, 6).map((col) => (
                            <span
                              key={col.name}
                              className={clsx(
                                "text-xs px-2 py-0.5 rounded-full",
                                col.semantic_type === "monetary"
                                  ? "bg-green-100 text-green-700"
                                  : col.semantic_type === "metric"
                                  ? "bg-blue-100 text-blue-700"
                                  : col.semantic_type === "temporal"
                                  ? "bg-purple-100 text-purple-700"
                                  : col.semantic_type === "dimension"
                                  ? "bg-orange-100 text-orange-700"
                                  : "bg-gray-100 text-gray-700"
                              )}
                            >
                              {col.name}
                            </span>
                          ))}
                          {source.schema_info.columns.length > 6 && (
                            <span className="text-xs text-gray-400">
                              +{source.schema_info.columns.length - 6} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
