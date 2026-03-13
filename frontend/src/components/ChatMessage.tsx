"use client";

import { useState } from "react";
import {
  User,
  Bot,
  ChevronDown,
  ChevronUp,
  Code,
  Lightbulb,
  TrendingUp,
  TrendingDown,
  Clock,
  AlertTriangle,
  Target,
  Zap,
  BarChart2,
  Activity,
  DollarSign,
  CheckCircle,
  XCircle,
  AlertCircle,
  FlaskConical,
} from "lucide-react";
import { QueryResult } from "@/lib/api";
import Visualization from "./Visualization";
import clsx from "clsx";

interface Message {
  role: "user" | "assistant";
  content: string;
  result?: QueryResult;
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
  onFollowUp?: (question: string) => void;
}

export default function ChatMessage({ message, onFollowUp }: ChatMessageProps) {
  const [showSQL, setShowSQL] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activeTab, setActiveTab] = useState<string>("insights");
  const isUser = message.role === "user";

  const getHealthColor = (health?: string) => {
    switch (health) {
      case "healthy":
        return "text-green-600 bg-green-50";
      case "warning":
        return "text-yellow-600 bg-yellow-50";
      case "critical":
        return "text-red-600 bg-red-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getHealthIcon = (health?: string) => {
    switch (health) {
      case "healthy":
        return <CheckCircle className="w-5 h-5" />;
      case "warning":
        return <AlertCircle className="w-5 h-5" />;
      case "critical":
        return <XCircle className="w-5 h-5" />;
      default:
        return <Activity className="w-5 h-5" />;
    }
  };

  const getPriorityBadge = (priority?: string) => {
    const colors = {
      high: "bg-red-100 text-red-700",
      medium: "bg-yellow-100 text-yellow-700",
      low: "bg-gray-100 text-gray-700",
    };
    return colors[priority as keyof typeof colors] || colors.low;
  };

  const getCategoryIcon = (category?: string) => {
    switch (category) {
      case "trend":
        return <TrendingUp className="w-4 h-4" />;
      case "anomaly":
        return <AlertTriangle className="w-4 h-4" />;
      case "opportunity":
        return <Target className="w-4 h-4" />;
      case "risk":
        return <AlertCircle className="w-4 h-4" />;
      case "correlation":
        return <Activity className="w-4 h-4" />;
      default:
        return <Lightbulb className="w-4 h-4" />;
    }
  };

  return (
    <div
      className={clsx(
        "flex gap-4 py-6 px-4",
        isUser ? "bg-white" : "bg-gray-50"
      )}
    >
      {/* Avatar */}
      <div
        className={clsx(
          "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
          isUser ? "bg-primary-100" : "bg-gray-200"
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-primary-600" />
        ) : (
          <Bot className="w-4 h-4 text-gray-600" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* User message */}
        {isUser && <p className="text-gray-900">{message.content}</p>}

        {/* Assistant response */}
        {!isUser && message.result && (
          <div className="space-y-4">
            {/* Error state */}
            {message.result.error && (
              <div className="bg-red-50 text-red-700 rounded-lg p-4">
                <p className="font-medium">Error</p>
                <p className="text-sm mt-1">{message.result.error}</p>
              </div>
            )}

            {/* Executive Summary with Health Score */}
            {message.result.executive_summary && (
              <div className="bg-white border rounded-lg p-4 shadow-sm">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">Executive Summary</h3>
                  {message.result.performance_assessment && (
                    <div
                      className={clsx(
                        "flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium",
                        getHealthColor(message.result.performance_assessment.overall_health)
                      )}
                    >
                      {getHealthIcon(message.result.performance_assessment.overall_health)}
                      <span>
                        Score: {message.result.performance_assessment.health_score}/100
                      </span>
                    </div>
                  )}
                </div>
                <p className="text-gray-700">{message.result.executive_summary}</p>
              </div>
            )}

            {/* Performance Metrics */}
            {message.result.performance_assessment?.key_metrics &&
              message.result.performance_assessment.key_metrics.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {message.result.performance_assessment.key_metrics.slice(0, 4).map((metric, i) => (
                    <div key={i} className="bg-white border rounded-lg p-3">
                      <p className="text-xs text-gray-500 uppercase tracking-wide">
                        {metric.metric}
                      </p>
                      <p className="text-xl font-bold text-gray-900 mt-1">
                        {metric.value}
                      </p>
                      <div className="flex items-center gap-1 mt-1">
                        {metric.delta_percentage?.startsWith("+") ? (
                          <TrendingUp className="w-3 h-3 text-green-500" />
                        ) : (
                          <TrendingDown className="w-3 h-3 text-red-500" />
                        )}
                        <span
                          className={clsx(
                            "text-xs",
                            metric.delta_percentage?.startsWith("+")
                              ? "text-green-600"
                              : "text-red-600"
                          )}
                        >
                          {metric.delta_percentage} vs benchmark
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

            {/* Visualization */}
            {message.result.data && message.result.data.length > 0 && (
              <Visualization result={message.result} />
            )}

            {/* Tabbed Advanced Insights */}
            {(message.result.deep_insights?.length ||
              message.result.strategic_recommendations?.length ||
              message.result.channel_analysis?.length ||
              message.result.anomalies_detected?.length) && (
              <div className="border rounded-lg overflow-hidden">
                {/* Tab Headers */}
                <div className="flex border-b bg-gray-50 overflow-x-auto">
                  {message.result.deep_insights?.length ? (
                    <button
                      onClick={() => setActiveTab("insights")}
                      className={clsx(
                        "px-4 py-2 text-sm font-medium whitespace-nowrap",
                        activeTab === "insights"
                          ? "bg-white text-primary-600 border-b-2 border-primary-600"
                          : "text-gray-600 hover:text-gray-900"
                      )}
                    >
                      <Lightbulb className="w-4 h-4 inline mr-1" />
                      Deep Insights
                    </button>
                  ) : null}
                  {message.result.strategic_recommendations?.length ? (
                    <button
                      onClick={() => setActiveTab("recommendations")}
                      className={clsx(
                        "px-4 py-2 text-sm font-medium whitespace-nowrap",
                        activeTab === "recommendations"
                          ? "bg-white text-primary-600 border-b-2 border-primary-600"
                          : "text-gray-600 hover:text-gray-900"
                      )}
                    >
                      <Zap className="w-4 h-4 inline mr-1" />
                      Actions
                    </button>
                  ) : null}
                  {message.result.channel_analysis?.length ? (
                    <button
                      onClick={() => setActiveTab("channels")}
                      className={clsx(
                        "px-4 py-2 text-sm font-medium whitespace-nowrap",
                        activeTab === "channels"
                          ? "bg-white text-primary-600 border-b-2 border-primary-600"
                          : "text-gray-600 hover:text-gray-900"
                      )}
                    >
                      <BarChart2 className="w-4 h-4 inline mr-1" />
                      Channels
                    </button>
                  ) : null}
                  {message.result.anomalies_detected?.length ? (
                    <button
                      onClick={() => setActiveTab("anomalies")}
                      className={clsx(
                        "px-4 py-2 text-sm font-medium whitespace-nowrap",
                        activeTab === "anomalies"
                          ? "bg-white text-primary-600 border-b-2 border-primary-600"
                          : "text-gray-600 hover:text-gray-900"
                      )}
                    >
                      <AlertTriangle className="w-4 h-4 inline mr-1" />
                      Anomalies
                    </button>
                  ) : null}
                  {message.result.testing_suggestions?.length ? (
                    <button
                      onClick={() => setActiveTab("tests")}
                      className={clsx(
                        "px-4 py-2 text-sm font-medium whitespace-nowrap",
                        activeTab === "tests"
                          ? "bg-white text-primary-600 border-b-2 border-primary-600"
                          : "text-gray-600 hover:text-gray-900"
                      )}
                    >
                      <FlaskConical className="w-4 h-4 inline mr-1" />
                      Tests
                    </button>
                  ) : null}
                </div>

                {/* Tab Content */}
                <div className="p-4 bg-white">
                  {/* Deep Insights Tab */}
                  {activeTab === "insights" && message.result.deep_insights && (
                    <div className="space-y-3">
                      {message.result.deep_insights.map((insight, i) => (
                        <div
                          key={i}
                          className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
                        >
                          <div
                            className={clsx(
                              "p-2 rounded-lg",
                              insight.category === "opportunity"
                                ? "bg-green-100 text-green-600"
                                : insight.category === "risk"
                                ? "bg-red-100 text-red-600"
                                : insight.category === "anomaly"
                                ? "bg-yellow-100 text-yellow-600"
                                : "bg-blue-100 text-blue-600"
                            )}
                          >
                            {getCategoryIcon(insight.category)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-gray-900">
                                {insight.title}
                              </span>
                              <span
                                className={clsx(
                                  "text-xs px-2 py-0.5 rounded-full",
                                  insight.impact === "high"
                                    ? "bg-red-100 text-red-700"
                                    : insight.impact === "medium"
                                    ? "bg-yellow-100 text-yellow-700"
                                    : "bg-gray-100 text-gray-700"
                                )}
                              >
                                {insight.impact} impact
                              </span>
                            </div>
                            <p className="text-sm text-gray-600">{insight.insight}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Strategic Recommendations Tab */}
                  {activeTab === "recommendations" &&
                    message.result.strategic_recommendations && (
                      <div className="space-y-3">
                        {message.result.strategic_recommendations.map((rec, i) => (
                          <div
                            key={i}
                            className="border rounded-lg p-4 hover:shadow-sm transition-shadow"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <span
                                className={clsx(
                                  "text-xs px-2 py-1 rounded-full font-medium",
                                  getPriorityBadge(rec.priority)
                                )}
                              >
                                {rec.priority} priority
                              </span>
                              <span className="text-xs text-gray-500">
                                {rec.timeframe?.replace("_", " ")}
                              </span>
                            </div>
                            <p className="font-medium text-gray-900 mb-1">
                              {rec.recommendation}
                            </p>
                            <p className="text-sm text-gray-600">
                              Expected: {rec.expected_outcome}
                            </p>
                            <div className="flex gap-4 mt-2 text-xs text-gray-500">
                              <span>Effort: {rec.effort}</span>
                              <span>Impact: {rec.impact}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                  {/* Channel Analysis Tab */}
                  {activeTab === "channels" && message.result.channel_analysis && (
                    <div className="space-y-3">
                      {message.result.channel_analysis.map((channel, i) => (
                        <div key={i} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-gray-900 capitalize">
                              {channel.channel?.replace("_", " ")}
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-500">
                                {channel.role}
                              </span>
                              <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-primary-500 rounded-full"
                                  style={{
                                    width: `${channel.efficiency_score || 0}%`,
                                  }}
                                />
                              </div>
                              <span className="text-xs font-medium">
                                {channel.efficiency_score}%
                              </span>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <p className="text-xs text-gray-500 mb-1">Strengths</p>
                              <ul className="text-green-700">
                                {channel.strengths?.map((s, j) => (
                                  <li key={j} className="flex items-start gap-1">
                                    <span className="text-green-500">+</span> {s}
                                  </li>
                                ))}
                              </ul>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500 mb-1">Weaknesses</p>
                              <ul className="text-red-700">
                                {channel.weaknesses?.map((w, j) => (
                                  <li key={j} className="flex items-start gap-1">
                                    <span className="text-red-500">-</span> {w}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                          {channel.recommendation && (
                            <p className="mt-2 text-sm text-primary-600 bg-primary-50 p-2 rounded">
                              {channel.recommendation}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Anomalies Tab */}
                  {activeTab === "anomalies" && message.result.anomalies_detected && (
                    <div className="space-y-3">
                      {message.result.anomalies_detected.map((anomaly, i) => (
                        <div
                          key={i}
                          className="border-l-4 border-yellow-400 bg-yellow-50 p-4 rounded-r-lg"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <AlertTriangle className="w-4 h-4 text-yellow-600" />
                            <span className="font-medium text-yellow-800">
                              {anomaly.type?.replace("_", " ")} in {anomaly.metric}
                            </span>
                          </div>
                          <p className="text-sm text-yellow-700 mb-2">
                            {anomaly.when} - {anomaly.magnitude}
                          </p>
                          {anomaly.possible_causes?.length > 0 && (
                            <div className="text-sm">
                              <span className="text-yellow-600">Possible causes: </span>
                              {anomaly.possible_causes.join(", ")}
                            </div>
                          )}
                          {anomaly.recommended_action && (
                            <p className="mt-2 text-sm font-medium text-yellow-800">
                              Action: {anomaly.recommended_action}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Testing Suggestions Tab */}
                  {activeTab === "tests" && message.result.testing_suggestions && (
                    <div className="space-y-3">
                      {message.result.testing_suggestions.map((test, i) => (
                        <div key={i} className="border rounded-lg p-4 bg-purple-50">
                          <div className="flex items-center gap-2 mb-2">
                            <FlaskConical className="w-4 h-4 text-purple-600" />
                            <span className="font-medium text-purple-900">
                              {test.test_type}
                            </span>
                            <span className="text-xs text-purple-600 ml-auto">
                              ~{test.estimated_duration}
                            </span>
                          </div>
                          <p className="text-sm text-purple-800 mb-2">
                            <strong>Hypothesis:</strong> {test.hypothesis}
                          </p>
                          <p className="text-sm text-purple-700">
                            <strong>Variables:</strong> {test.variables?.join(", ")}
                          </p>
                          <p className="text-sm text-purple-700">
                            <strong>Success metric:</strong> {test.success_metric}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Fallback to basic insights if no deep analysis */}
            {!message.result.deep_insights?.length &&
              message.result.key_findings &&
              message.result.key_findings.length > 0 && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Lightbulb className="w-4 h-4 text-blue-600" />
                    <h4 className="font-medium text-blue-900">Key Findings</h4>
                  </div>
                  <ul className="space-y-1">
                    {message.result.key_findings.map((finding, i) => (
                      <li
                        key={i}
                        className="text-sm text-blue-800 flex items-start gap-2"
                      >
                        <span className="text-blue-400">\u2022</span>
                        {finding}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

            {/* Basic recommendations fallback */}
            {!message.result.strategic_recommendations?.length &&
              message.result.recommendations &&
              message.result.recommendations.length > 0 && (
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-4 h-4 text-green-600" />
                    <h4 className="font-medium text-green-900">Recommendations</h4>
                  </div>
                  <ul className="space-y-1">
                    {message.result.recommendations.map((rec, i) => (
                      <li
                        key={i}
                        className="text-sm text-green-800 flex items-start gap-2"
                      >
                        <span className="text-green-400">{i + 1}.</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

            {/* SQL Query toggle */}
            {message.result.sql_query && (
              <div className="border rounded-lg">
                <button
                  onClick={() => setShowSQL(!showSQL)}
                  className="w-full flex items-center justify-between px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
                >
                  <div className="flex items-center gap-2">
                    <Code className="w-4 h-4" />
                    <span>SQL Query</span>
                  </div>
                  {showSQL ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </button>
                {showSQL && (
                  <div className="px-4 py-3 bg-gray-900 text-gray-100 text-sm font-mono rounded-b-lg overflow-x-auto">
                    <pre>{message.result.sql_query}</pre>
                    {message.result.sql_explanation && (
                      <p className="text-gray-400 mt-2 text-xs">
                        {message.result.sql_explanation}
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Data Quality Notes */}
            {message.result.data_quality_notes &&
              message.result.data_quality_notes.length > 0 && (
                <div className="bg-gray-100 rounded-lg p-3 text-sm text-gray-600">
                  <p className="font-medium mb-1">Data Quality Notes:</p>
                  <ul className="list-disc list-inside">
                    {message.result.data_quality_notes.map((note, i) => (
                      <li key={i}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}

            {/* Follow-up questions */}
            {message.result.follow_up_questions &&
              message.result.follow_up_questions.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs text-gray-500 mb-2">Dig deeper:</p>
                  <div className="flex flex-wrap gap-2">
                    {message.result.follow_up_questions.map((q, i) => (
                      <button
                        key={i}
                        onClick={() => onFollowUp?.(q)}
                        className="text-sm px-3 py-1.5 bg-white border rounded-full hover:bg-gray-50 hover:border-primary-300 transition-colors text-gray-700"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

            {/* Execution time */}
            <div className="flex items-center gap-1 text-xs text-gray-400">
              <Clock className="w-3 h-3" />
              <span>
                {message.result.row_count} rows \u00B7{" "}
                {message.result.execution_time_ms}ms
                {message.result.analysis_depth === "deep" && " \u00B7 Deep Analysis"}
              </span>
            </div>
          </div>
        )}

        {/* Simple text response (no result) */}
        {!isUser && !message.result && (
          <p className="text-gray-700">{message.content}</p>
        )}
      </div>
    </div>
  );
}
