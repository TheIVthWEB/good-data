"use client";

import { useState, useEffect, useRef } from "react";
import {
  Send,
  Database,
  Sparkles,
  Loader2,
  BarChart3,
  PieChart,
  TrendingUp,
  DollarSign,
} from "lucide-react";
import ChatMessage from "@/components/ChatMessage";
import DataSourcePanel from "@/components/DataSourcePanel";
import { DataSource, fetchSources, submitQuery, QueryResult } from "@/lib/api";
import clsx from "clsx";

interface Message {
  role: "user" | "assistant";
  content: string;
  result?: QueryResult;
  timestamp: Date;
}

const EXAMPLE_QUESTIONS = [
  {
    icon: <DollarSign className="w-4 h-4" />,
    text: "What's my total ad spend by campaign?",
  },
  {
    icon: <TrendingUp className="w-4 h-4" />,
    text: "Which channels have the best ROAS?",
  },
  {
    icon: <BarChart3 className="w-4 h-4" />,
    text: "Show me daily conversions for the last 30 days",
  },
  {
    icon: <PieChart className="w-4 h-4" />,
    text: "What's the breakdown of spend by source/medium?",
  },
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<DataSource[]>([]);
  const [showSourcePanel, setShowSourcePanel] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load data sources on mount
  useEffect(() => {
    loadSources();
  }, []);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadSources = async () => {
    try {
      const data = await fetchSources();
      setSources(data);
    } catch (e) {
      console.error("Failed to load sources:", e);
    }
  };

  const handleSubmit = async (question: string) => {
    if (!question.trim() || loading) return;

    const userMessage: Message = {
      role: "user",
      content: question,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const result = await submitQuery(question);
      const assistantMessage: Message = {
        role: "assistant",
        content: result.insights || "Here are your results:",
        result,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (e: any) {
      const errorMessage: Message = {
        role: "assistant",
        content: `Sorry, I encountered an error: ${e.message}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(input);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Good Data</h1>
              <p className="text-xs text-gray-500">Marketing Analytics AI</p>
            </div>
          </div>

          <button
            onClick={() => setShowSourcePanel(true)}
            className={clsx(
              "flex items-center gap-2 px-4 py-2 rounded-lg transition-colors",
              sources.length > 0
                ? "bg-green-50 text-green-700 hover:bg-green-100"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            )}
          >
            <Database className="w-4 h-4" />
            <span className="text-sm font-medium">
              {sources.length > 0
                ? `${sources.length} source${sources.length > 1 ? "s" : ""}`
                : "Add Data"}
            </span>
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col max-w-5xl mx-auto w-full">
        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-6">
          {messages.length === 0 ? (
            // Empty state
            <div className="h-full flex flex-col items-center justify-center py-12">
              <div className="w-16 h-16 bg-gradient-to-br from-primary-100 to-primary-200 rounded-2xl flex items-center justify-center mb-6">
                <Sparkles className="w-8 h-8 text-primary-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Ask questions about your marketing data
              </h2>
              <p className="text-gray-500 mb-8 text-center max-w-md">
                {sources.length === 0
                  ? "Start by adding a data source, then ask questions in plain English."
                  : "Ask anything about your campaigns, spend, conversions, and more."}
              </p>

              {sources.length === 0 ? (
                <button
                  onClick={() => setShowSourcePanel(true)}
                  className="px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors flex items-center gap-2"
                >
                  <Database className="w-5 h-5" />
                  Add Your First Data Source
                </button>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
                  {EXAMPLE_QUESTIONS.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => handleSubmit(q.text)}
                      className="flex items-center gap-3 p-4 bg-white border rounded-lg hover:border-primary-300 hover:shadow-sm transition-all text-left"
                    >
                      <div className="w-8 h-8 bg-primary-50 rounded-lg flex items-center justify-center text-primary-600">
                        {q.icon}
                      </div>
                      <span className="text-sm text-gray-700">{q.text}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            // Chat messages
            <div className="py-4">
              {messages.map((message, i) => (
                <ChatMessage
                  key={i}
                  message={message}
                  onFollowUp={handleSubmit}
                />
              ))}
              {loading && (
                <div className="flex gap-4 py-6 bg-gray-50">
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                    <Loader2 className="w-4 h-4 text-gray-600 animate-spin" />
                  </div>
                  <div className="flex items-center text-gray-500">
                    Analyzing your data...
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="border-t bg-white px-6 py-4">
          <div className="max-w-3xl mx-auto">
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    sources.length === 0
                      ? "Add a data source to start asking questions..."
                      : "Ask a question about your marketing data..."
                  }
                  disabled={loading || sources.length === 0}
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-400"
                />
              </div>
              <button
                onClick={() => handleSubmit(input)}
                disabled={!input.trim() || loading || sources.length === 0}
                className="px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-2 text-center">
              Powered by Claude AI \u00B7 Press Enter to send
            </p>
          </div>
        </div>
      </main>

      {/* Data Source Panel */}
      <DataSourcePanel
        sources={sources}
        onSourcesChange={loadSources}
        isOpen={showSourcePanel}
        onClose={() => setShowSourcePanel(false)}
      />
    </div>
  );
}
