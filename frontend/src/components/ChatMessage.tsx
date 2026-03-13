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
  Clock,
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
  const isUser = message.role === "user";

  return (
    <div
      className={clsx(
        "flex gap-4 py-6",
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
        {isUser && (
          <p className="text-gray-900">{message.content}</p>
        )}

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

            {/* Insights */}
            {message.result.insights && (
              <div className="prose prose-sm max-w-none">
                <p className="text-gray-700 whitespace-pre-wrap">
                  {message.result.insights}
                </p>
              </div>
            )}

            {/* Key Findings */}
            {message.result.key_findings && message.result.key_findings.length > 0 && (
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Lightbulb className="w-4 h-4 text-blue-600" />
                  <h4 className="font-medium text-blue-900">Key Findings</h4>
                </div>
                <ul className="space-y-1">
                  {message.result.key_findings.map((finding, i) => (
                    <li key={i} className="text-sm text-blue-800 flex items-start gap-2">
                      <span className="text-blue-400">\u2022</span>
                      {finding}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Visualization */}
            {message.result.data && message.result.data.length > 0 && (
              <Visualization result={message.result} />
            )}

            {/* Recommendations */}
            {message.result.recommendations && message.result.recommendations.length > 0 && (
              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-4 h-4 text-green-600" />
                  <h4 className="font-medium text-green-900">Recommendations</h4>
                </div>
                <ul className="space-y-1">
                  {message.result.recommendations.map((rec, i) => (
                    <li key={i} className="text-sm text-green-800 flex items-start gap-2">
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

            {/* Follow-up questions */}
            {message.result.follow_up_questions && message.result.follow_up_questions.length > 0 && (
              <div className="mt-4">
                <p className="text-xs text-gray-500 mb-2">Suggested follow-ups:</p>
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
                {message.result.row_count} rows \u00B7 {message.result.execution_time_ms}ms
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
