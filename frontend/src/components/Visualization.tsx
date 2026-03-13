"use client";

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { QueryResult } from "@/lib/api";

interface VisualizationProps {
  result: QueryResult;
}

const COLORS = [
  "#0ea5e9",
  "#8b5cf6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#ec4899",
  "#06b6d4",
  "#84cc16",
];

export default function Visualization({ result }: VisualizationProps) {
  const { data, visualization } = result;

  if (!data || data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No data to visualize
      </div>
    );
  }

  const vizType = visualization?.type || "table";
  const xAxis = visualization?.x_axis || Object.keys(data[0])[0];
  const yAxis = visualization?.y_axis || Object.keys(data[0])[1];
  const title = visualization?.title || "Query Results";

  // Format numbers for display
  const formatValue = (value: any) => {
    if (typeof value === "number") {
      if (Math.abs(value) >= 1000000) {
        return `${(value / 1000000).toFixed(1)}M`;
      }
      if (Math.abs(value) >= 1000) {
        return `${(value / 1000).toFixed(1)}K`;
      }
      return value.toFixed(2);
    }
    return value;
  };

  const renderChart = () => {
    switch (vizType) {
      case "bar":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey={xAxis}
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={formatValue} />
              <Tooltip formatter={formatValue} />
              <Legend />
              <Bar dataKey={yAxis} fill="#0ea5e9" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        );

      case "line":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey={xAxis}
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={formatValue} />
              <Tooltip formatter={formatValue} />
              <Legend />
              <Line
                type="monotone"
                dataKey={yAxis}
                stroke="#0ea5e9"
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case "pie":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={data}
                dataKey={yAxis}
                nameKey={xAxis}
                cx="50%"
                cy="50%"
                outerRadius={150}
                label={({ name, percent }) =>
                  `${name}: ${(percent * 100).toFixed(0)}%`
                }
              >
                {data.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip formatter={formatValue} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );

      case "scatter":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey={xAxis}
                name={xAxis}
                tick={{ fontSize: 12 }}
                tickFormatter={formatValue}
              />
              <YAxis
                dataKey={yAxis}
                name={yAxis}
                tick={{ fontSize: 12 }}
                tickFormatter={formatValue}
              />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} formatter={formatValue} />
              <Scatter name="Data" data={data} fill="#0ea5e9" />
            </ScatterChart>
          </ResponsiveContainer>
        );

      case "metric":
        // Single metric display
        const metricValue = data[0]?.[yAxis] ?? data[0]?.[Object.keys(data[0])[0]];
        return (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <p className="text-5xl font-bold text-primary-600">
                {formatValue(metricValue)}
              </p>
              <p className="text-gray-500 mt-2">{title}</p>
            </div>
          </div>
        );

      case "table":
      default:
        return (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {Object.keys(data[0]).map((key) => (
                    <th
                      key={key}
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.slice(0, 100).map((row, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    {Object.values(row).map((value: any, j) => (
                      <td
                        key={j}
                        className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap"
                      >
                        {typeof value === "number" ? formatValue(value) : String(value)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {data.length > 100 && (
              <p className="text-center text-sm text-gray-500 py-2">
                Showing 100 of {data.length} rows
              </p>
            )}
          </div>
        );
    }
  };

  return (
    <div className="bg-white rounded-lg border p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-4">{title}</h3>
      {renderChart()}
    </div>
  );
}
