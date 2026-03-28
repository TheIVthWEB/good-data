"use client";

import { useState, useEffect } from "react";
import {
  AdvertiserContext,
  ChannelRule,
  fetchContexts,
  createContext,
  updateContext,
  deleteContext,
} from "@/lib/api";
import { Settings, Plus, Trash2, Save, X, ChevronDown, ChevronUp } from "lucide-react";

interface ContextPanelProps {
  dataSourceId?: string;
  onClose?: () => void;
}

export default function ContextPanel({ dataSourceId, onClose }: ContextPanelProps) {
  const [contexts, setContexts] = useState<AdvertiserContext[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<AdvertiserContext | null>(null);
  const [isNew, setIsNew] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadContexts();
  }, [dataSourceId]);

  const loadContexts = async () => {
    try {
      setLoading(true);
      const data = await fetchContexts(dataSourceId);
      setContexts(data);
    } catch (err) {
      setError("Failed to load contexts");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setIsNew(true);
    setEditing({
      name: "",
      data_source_id: dataSourceId || null,
      dos: [],
      donts: [],
      channel_rules: [],
    });
  };

  const handleEdit = (ctx: AdvertiserContext) => {
    setIsNew(false);
    setEditing({ ...ctx });
  };

  const handleSave = async () => {
    if (!editing || !editing.name.trim()) {
      setError("Name is required");
      return;
    }

    try {
      setSaving(true);
      setError(null);

      if (isNew) {
        await createContext(editing);
      } else if (editing.id) {
        await updateContext(editing.id, editing);
      }

      await loadContexts();
      setEditing(null);
      setIsNew(false);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (contextId: string) => {
    if (!confirm("Delete this context? This cannot be undone.")) return;

    try {
      await deleteContext(contextId);
      await loadContexts();
    } catch (err) {
      setError("Failed to delete context");
    }
  };

  const handleCancel = () => {
    setEditing(null);
    setIsNew(false);
    setError(null);
  };

  // Helper to update nested fields
  const updateField = (field: keyof AdvertiserContext, value: any) => {
    if (!editing) return;
    setEditing({ ...editing, [field]: value });
  };

  const addChannelRule = () => {
    if (!editing) return;
    const rules = editing.channel_rules || [];
    setEditing({
      ...editing,
      channel_rules: [...rules, { channel: "", rule: "" }],
    });
  };

  const updateChannelRule = (index: number, field: keyof ChannelRule, value: string) => {
    if (!editing) return;
    const rules = [...(editing.channel_rules || [])];
    rules[index] = { ...rules[index], [field]: value };
    setEditing({ ...editing, channel_rules: rules });
  };

  const removeChannelRule = (index: number) => {
    if (!editing) return;
    const rules = (editing.channel_rules || []).filter((_, i) => i !== index);
    setEditing({ ...editing, channel_rules: rules });
  };

  const addListItem = (field: "dos" | "donts") => {
    if (!editing) return;
    const list = editing[field] || [];
    setEditing({ ...editing, [field]: [...list, ""] });
  };

  const updateListItem = (field: "dos" | "donts", index: number, value: string) => {
    if (!editing) return;
    const list = [...(editing[field] || [])];
    list[index] = value;
    setEditing({ ...editing, [field]: list });
  };

  const removeListItem = (field: "dos" | "donts", index: number) => {
    if (!editing) return;
    const list = (editing[field] || []).filter((_, i) => i !== index);
    setEditing({ ...editing, [field]: list });
  };

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-500">
        Loading contexts...
      </div>
    );
  }

  // Editing mode
  if (editing) {
    return (
      <div className="bg-white border rounded-lg p-4 space-y-4 max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b pb-2">
          <h3 className="font-semibold text-lg">
            {isNew ? "New Advertiser Context" : "Edit Context"}
          </h3>
          <button onClick={handleCancel} className="text-gray-500 hover:text-gray-700">
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-2 rounded text-sm">{error}</div>
        )}

        {/* Basic Info */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-gray-700">Basic Info</h4>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Name *</label>
            <input
              type="text"
              value={editing.name}
              onChange={(e) => updateField("name", e.target.value)}
              className="w-full px-3 py-2 border rounded text-sm"
              placeholder="e.g., Acme Corp"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Industry</label>
              <input
                type="text"
                value={editing.industry || ""}
                onChange={(e) => updateField("industry", e.target.value)}
                className="w-full px-3 py-2 border rounded text-sm"
                placeholder="e.g., B2B SaaS"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Business Model</label>
              <select
                value={editing.business_model || ""}
                onChange={(e) => updateField("business_model", e.target.value)}
                className="w-full px-3 py-2 border rounded text-sm"
              >
                <option value="">Select...</option>
                <option value="B2B">B2B</option>
                <option value="B2C">B2C</option>
                <option value="DTC">DTC</option>
                <option value="Marketplace">Marketplace</option>
                <option value="SaaS">SaaS</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Primary KPI</label>
              <input
                type="text"
                value={editing.primary_kpi || ""}
                onChange={(e) => updateField("primary_kpi", e.target.value)}
                className="w-full px-3 py-2 border rounded text-sm"
                placeholder="e.g., Qualified Leads"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Sales Cycle (days)</label>
              <input
                type="number"
                value={editing.sales_cycle_days || ""}
                onChange={(e) => updateField("sales_cycle_days", parseInt(e.target.value) || undefined)}
                className="w-full px-3 py-2 border rounded text-sm"
                placeholder="e.g., 45"
              />
            </div>
          </div>
        </div>

        {/* Targets */}
        <div className="space-y-3 border-t pt-3">
          <h4 className="font-medium text-sm text-gray-700">Targets</h4>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Target CPA ($)</label>
              <input
                type="number"
                value={editing.target_cpa || ""}
                onChange={(e) => updateField("target_cpa", parseFloat(e.target.value) || undefined)}
                className="w-full px-3 py-2 border rounded text-sm"
                placeholder="150"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Target ROAS (x)</label>
              <input
                type="number"
                step="0.1"
                value={editing.target_roas || ""}
                onChange={(e) => updateField("target_roas", parseFloat(e.target.value) || undefined)}
                className="w-full px-3 py-2 border rounded text-sm"
                placeholder="3.0"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Target CTR (%)</label>
              <input
                type="number"
                step="0.1"
                value={editing.target_ctr || ""}
                onChange={(e) => updateField("target_ctr", parseFloat(e.target.value) || undefined)}
                className="w-full px-3 py-2 border rounded text-sm"
                placeholder="2.5"
              />
            </div>
          </div>
        </div>

        {/* Channel Rules */}
        <div className="space-y-3 border-t pt-3">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-sm text-gray-700">Channel Rules</h4>
            <button
              onClick={addChannelRule}
              className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <Plus size={14} /> Add Rule
            </button>
          </div>
          {(editing.channel_rules || []).map((rule, i) => (
            <div key={i} className="flex gap-2 items-start">
              <input
                type="text"
                value={rule.channel}
                onChange={(e) => updateChannelRule(i, "channel", e.target.value)}
                className="w-1/3 px-2 py-1.5 border rounded text-sm"
                placeholder="Channel"
              />
              <input
                type="text"
                value={rule.rule}
                onChange={(e) => updateChannelRule(i, "rule", e.target.value)}
                className="flex-1 px-2 py-1.5 border rounded text-sm"
                placeholder="Rule (e.g., Never pause, expect high CPA)"
              />
              <button
                onClick={() => removeChannelRule(i)}
                className="text-red-500 hover:text-red-600 p-1"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>

        {/* Do's */}
        <div className="space-y-3 border-t pt-3">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-sm text-gray-700">Do's (Required Behaviors)</h4>
            <button
              onClick={() => addListItem("dos")}
              className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <Plus size={14} /> Add
            </button>
          </div>
          {(editing.dos || []).map((item, i) => (
            <div key={i} className="flex gap-2">
              <input
                type="text"
                value={item}
                onChange={(e) => updateListItem("dos", i, e.target.value)}
                className="flex-1 px-2 py-1.5 border rounded text-sm"
                placeholder="e.g., Weight MQLs higher than raw form fills"
              />
              <button
                onClick={() => removeListItem("dos", i)}
                className="text-red-500 hover:text-red-600 p-1"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>

        {/* Don'ts */}
        <div className="space-y-3 border-t pt-3">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-sm text-gray-700">Don'ts (Forbidden Recommendations)</h4>
            <button
              onClick={() => addListItem("donts")}
              className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <Plus size={14} /> Add
            </button>
          </div>
          {(editing.donts || []).map((item, i) => (
            <div key={i} className="flex gap-2">
              <input
                type="text"
                value={item}
                onChange={(e) => updateListItem("donts", i, e.target.value)}
                className="flex-1 px-2 py-1.5 border rounded text-sm"
                placeholder="e.g., Don't recommend pausing brand campaigns"
              />
              <button
                onClick={() => removeListItem("donts", i)}
                className="text-red-500 hover:text-red-600 p-1"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>

        {/* Custom Instructions */}
        <div className="space-y-3 border-t pt-3">
          <h4 className="font-medium text-sm text-gray-700">Custom Instructions</h4>
          <textarea
            value={editing.custom_instructions || ""}
            onChange={(e) => updateField("custom_instructions", e.target.value)}
            className="w-full px-3 py-2 border rounded text-sm"
            rows={3}
            placeholder="Any additional context or instructions for the AI..."
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 border-t pt-3">
          <button
            onClick={handleCancel}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            <Save size={16} />
            {saving ? "Saving..." : "Save Context"}
          </button>
        </div>
      </div>
    );
  }

  // List mode
  return (
    <div className="bg-white border rounded-lg">
      <div className="flex items-center justify-between p-3 border-b">
        <div className="flex items-center gap-2">
          <Settings size={18} className="text-gray-500" />
          <h3 className="font-semibold">Advertiser Context</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCreate}
            className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <Plus size={16} /> Add Context
          </button>
          {onClose && (
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X size={18} />
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 p-2 text-sm">{error}</div>
      )}

      {contexts.length === 0 ? (
        <div className="p-4 text-center text-gray-500 text-sm">
          <p>No advertiser context configured.</p>
          <p className="mt-1">Add context to customize AI insights for your data.</p>
        </div>
      ) : (
        <div className="divide-y">
          {contexts.map((ctx) => (
            <div key={ctx.id} className="p-3">
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpanded(expanded === ctx.id ? null : ctx.id!)}
              >
                <div>
                  <div className="font-medium">{ctx.name}</div>
                  <div className="text-xs text-gray-500">
                    {[ctx.industry, ctx.business_model].filter(Boolean).join(" | ") || "No details"}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {expanded === ctx.id ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </div>
              </div>

              {expanded === ctx.id && (
                <div className="mt-3 pt-3 border-t text-sm space-y-2">
                  {ctx.primary_kpi && (
                    <div><span className="text-gray-500">Primary KPI:</span> {ctx.primary_kpi}</div>
                  )}
                  {ctx.target_cpa && (
                    <div><span className="text-gray-500">Target CPA:</span> ${ctx.target_cpa}</div>
                  )}
                  {ctx.target_roas && (
                    <div><span className="text-gray-500">Target ROAS:</span> {ctx.target_roas}x</div>
                  )}
                  {ctx.channel_rules && ctx.channel_rules.length > 0 && (
                    <div>
                      <span className="text-gray-500">Channel Rules:</span>
                      <ul className="ml-4 list-disc">
                        {ctx.channel_rules.map((r, i) => (
                          <li key={i}><strong>{r.channel}:</strong> {r.rule}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {ctx.dos && ctx.dos.length > 0 && (
                    <div>
                      <span className="text-gray-500">Do's:</span>
                      <ul className="ml-4 list-disc">
                        {ctx.dos.map((d, i) => <li key={i}>{d}</li>)}
                      </ul>
                    </div>
                  )}
                  {ctx.donts && ctx.donts.length > 0 && (
                    <div>
                      <span className="text-gray-500">Don'ts:</span>
                      <ul className="ml-4 list-disc">
                        {ctx.donts.map((d, i) => <li key={i}>{d}</li>)}
                      </ul>
                    </div>
                  )}

                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => handleEdit(ctx)}
                      className="text-blue-600 hover:text-blue-700 text-xs"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => ctx.id && handleDelete(ctx.id)}
                      className="text-red-600 hover:text-red-700 text-xs"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
