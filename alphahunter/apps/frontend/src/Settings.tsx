import { useState, useEffect } from "react";
import { api } from "./api/client";
import { Settings as SettingsIcon, Save, RotateCcw } from "lucide-react";

interface SettingDef {
  key: string;
  label: string;
  description: string;
  type: "number" | "text";
  unit?: string;
  group: string;
}

const SETTING_DEFS: SettingDef[] = [
  {
    key: "scan_interval_minutes",
    label: "Scan Interval",
    description: "Minutes between automatic scans during market hours",
    type: "number",
    unit: "min",
    group: "Scanning",
  },
  {
    key: "confidence_buy_threshold",
    label: "BUY Threshold",
    description: "Minimum confidence to recommend BUY",
    type: "number",
    unit: "%",
    group: "Decision Engine",
  },
  {
    key: "confidence_watch_threshold",
    label: "WATCH Threshold",
    description: "Minimum confidence for WATCH recommendation",
    type: "number",
    unit: "%",
    group: "Decision Engine",
  },
  {
    key: "breakout_lookback_days",
    label: "Breakout Lookback",
    description: "Days to look back for resistance level",
    type: "number",
    unit: "days",
    group: "Signal Parameters",
  },
  {
    key: "volume_spike_threshold",
    label: "Volume Spike Threshold",
    description: "Multiplier above 20-day average for spike detection",
    type: "number",
    unit: "x",
    group: "Signal Parameters",
  },
  {
    key: "volume_avg_period",
    label: "Volume Avg Period",
    description: "Days for calculating average volume",
    type: "number",
    unit: "days",
    group: "Signal Parameters",
  },
  {
    key: "bulk_deal_lookback_days",
    label: "Bulk Deal Lookback",
    description: "Days to look back for bulk/block deals",
    type: "number",
    unit: "days",
    group: "Signal Parameters",
  },
  {
    key: "backtest_lookback_years",
    label: "Backtest Lookback",
    description: "Years of historical data for backtesting",
    type: "number",
    unit: "years",
    group: "Backtesting",
  },
  {
    key: "backtest_outcome_days",
    label: "Outcome Measurement",
    description: "Trading days after signal to measure outcome",
    type: "number",
    unit: "days",
    group: "Backtesting",
  },
  {
    key: "default_alert_confidence_threshold",
    label: "Alert Confidence Threshold",
    description: "Minimum confidence to generate an alert",
    type: "number",
    unit: "%",
    group: "Alerts",
  },
];

export default function Settings() {
  const [values, setValues] = useState<Record<string, string>>({});
  const [originalValues, setOriginalValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api
      .getSettings()
      .then((res) => {
        setValues(res.data);
        setOriginalValues(res.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const hasChanges = JSON.stringify(values) !== JSON.stringify(originalValues);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const changed: Record<string, string> = {};
      for (const key of Object.keys(values)) {
        if (values[key] !== originalValues[key]) {
          changed[key] = values[key];
        }
      }
      await api.updateSettings(changed);
      setOriginalValues({ ...values });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      console.error(e);
    }
    setSaving(false);
  };

  const handleReset = () => {
    setValues({ ...originalValues });
  };

  const groups = [...new Set(SETTING_DEFS.map((s) => s.group))];

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-black text-white flex items-center gap-2">
          <SettingsIcon className="text-gray-400" size={24} />
          Settings
        </h1>
        <div className="flex gap-2">
          {hasChanges && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 px-4 py-2 rounded-lg text-sm transition-colors"
            >
              <RotateCcw size={14} />
              Reset
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={!hasChanges || saving}
            className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-5 py-2 rounded-lg text-sm transition-all disabled:opacity-50"
          >
            <Save size={14} />
            {saving ? "Saving..." : saved ? "Saved!" : "Save Changes"}
          </button>
        </div>
      </div>

      {groups.map((group) => (
        <div
          key={group}
          className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden"
        >
          <div className="bg-gray-900 px-5 py-3 border-b border-gray-700">
            <h2 className="text-sm font-bold text-gray-300 uppercase tracking-wider">
              {group}
            </h2>
          </div>
          <div className="divide-y divide-gray-700/50">
            {SETTING_DEFS.filter((s) => s.group === group).map((def) => (
              <div
                key={def.key}
                className="px-5 py-4 flex items-center justify-between gap-4"
              >
                <div className="flex-1">
                  <label className="text-white font-medium text-sm">
                    {def.label}
                  </label>
                  <p className="text-gray-500 text-xs mt-0.5">
                    {def.description}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type={def.type}
                    value={values[def.key] || ""}
                    onChange={(e) =>
                      setValues((prev) => ({
                        ...prev,
                        [def.key]: e.target.value,
                      }))
                    }
                    className="w-24 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm font-mono text-right focus:outline-none focus:border-blue-500"
                  />
                  {def.unit && (
                    <span className="text-gray-500 text-xs w-8">
                      {def.unit}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
