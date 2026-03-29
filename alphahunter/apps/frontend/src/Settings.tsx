/**
 * Settings — engine configuration UI.
 *
 * Tabs: alerts | signals | scanner | pipeline
 *
 * SETTING_DEFINITIONS drives every control declaratively — add/change a setting
 * by editing the array, not by adding new JSX. Supported kinds:
 *   range    — slider with min/max/step and live % display
 *   select   — <select> from a fixed options list
 *   number   — free-form numeric input
 *   toggle   — single boolean on/off button
 *
 * Save sends only the changed keys (delta diff against originalValues).
 */
import { useEffect, useMemo, useState } from "react";
import { RotateCcw, Save } from "lucide-react";
import { api } from "./api/client";
import {
  Button,
  ErrorState,
  FieldLabel,
  LoadingState,
  PageHeader,
  Panel,
  SectionTabs,
} from "./components/ui";

type SettingsTab = "alerts" | "signals" | "scanner" | "pipeline";

interface SettingDefinition {
  key: string;
  label: string;
  description: string;
  tab: SettingsTab;
  kind: "number" | "range" | "select" | "toggle";
  unit?: string;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
}

const SETTING_DEFINITIONS: SettingDefinition[] = [
  {
    key: "default_alert_confidence_threshold",
    label: "Alert confidence threshold",
    description: "Minimum confidence required before AlphaHunter generates an in-app alert.",
    tab: "alerts",
    kind: "range",
    min: 0,
    max: 100,
    step: 5,
    unit: "%",
  },
  {
    key: "confidence_buy_threshold",
    label: "BUY threshold",
    description: "Minimum conviction required to escalate an idea into a BUY recommendation.",
    tab: "alerts",
    kind: "range",
    min: 40,
    max: 95,
    step: 5,
    unit: "%",
  },
  {
    key: "confidence_watch_threshold",
    label: "WATCH threshold",
    description: "Minimum conviction required to keep a name on the WATCH side of the book.",
    tab: "alerts",
    kind: "range",
    min: 10,
    max: 80,
    step: 5,
    unit: "%",
  },
  {
    key: "breakout_lookback_days",
    label: "Breakout lookback",
    description: "Window used to determine key resistance levels.",
    tab: "signals",
    kind: "select",
    options: ["20", "30", "45", "60"],
    unit: "days",
  },
  {
    key: "volume_spike_threshold",
    label: "Volume spike threshold",
    description: "Multiplier above average volume required before the spike signal triggers.",
    tab: "signals",
    kind: "select",
    options: ["1.5", "2.0", "2.5", "3.0"],
    unit: "x",
  },
  {
    key: "bulk_deal_lookback_days",
    label: "Bulk deal lookback",
    description: "How far back AlphaHunter should consider institutional bulk-deal activity relevant.",
    tab: "signals",
    kind: "select",
    options: ["3", "5", "7", "10"],
    unit: "days",
  },
  {
    key: "backtest_lookback_years",
    label: "Backtest lookback",
    description: "Historical window used to find prior matching signal patterns.",
    tab: "signals",
    kind: "select",
    options: ["1", "2", "3"],
    unit: "years",
  },
  {
    key: "backtest_outcome_days",
    label: "Outcome window",
    description: "How many trading days AlphaHunter uses to measure the post-signal result.",
    tab: "signals",
    kind: "select",
    options: ["3", "5", "7", "10"],
    unit: "days",
  },
  {
    key: "scan_interval_minutes",
    label: "Scan interval",
    description: "Cadence for scheduled market scans during trading hours.",
    tab: "scanner",
    kind: "select",
    options: ["5", "10", "15", "30"],
    unit: "minutes",
  },
  {
    key: "volume_avg_period",
    label: "Average volume period",
    description: "Rolling session count used to compute normal volume.",
    tab: "scanner",
    kind: "select",
    options: ["10", "20", "30", "60"],
    unit: "days",
  },
  {
    key: "tinyfish_timeout_secs",
    label: "TinyFish timeout",
    description: "Timeout budget for external web-intel fetches.",
    tab: "pipeline",
    kind: "select",
    options: ["10", "20", "30", "45"],
    unit: "seconds",
  },
  {
    key: "tinyfish_max_concurrency",
    label: "TinyFish concurrency",
    description: "Concurrent external jobs allowed in the enrichment pipeline.",
    tab: "pipeline",
    kind: "select",
    options: ["5", "10", "20", "30"],
  },
  {
    key: "tinyfish_batch_size",
    label: "TinyFish batch size",
    description: "Number of symbols grouped into one external enrichment batch.",
    tab: "pipeline",
    kind: "select",
    options: ["10", "20", "30", "50"],
  },
  {
    key: "tinyfish_fail_open",
    label: "Fail open",
    description: "Continue with fallback market-only intelligence if external enrichment fails.",
    tab: "pipeline",
    kind: "toggle",
  },
  {
    key: "data_pipeline_mode",
    label: "Pipeline mode",
    description: "Switch between legacy, shadow, and active scoring behaviour.",
    tab: "pipeline",
    kind: "select",
    options: ["legacy", "shadow", "active"],
  },
];

export default function Settings() {
  const [tab, setTab] = useState<SettingsTab>("alerts");
  const [values, setValues] = useState<Record<string, string>>({});
  const [originalValues, setOriginalValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const loadSettings = async () => {
      try {
        const response = await api.getSettings();
        if (!cancelled) {
          setValues(response.data);
          setOriginalValues(response.data);
          setError("");
        }
      } catch (settingsError) {
        if (!cancelled) {
          setError(settingsError instanceof Error ? settingsError.message : "Unable to load settings.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadSettings();

    return () => {
      cancelled = true;
    };
  }, []);

  const hasChanges = useMemo(
    () => JSON.stringify(values) !== JSON.stringify(originalValues),
    [originalValues, values],
  );

  const currentDefinitions = SETTING_DEFINITIONS.filter((definition) => definition.tab === tab);

  const updateValue = (key: string, value: string) => {
    setValues((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const changes = Object.fromEntries(
        Object.entries(values).filter(([key, value]) => originalValues[key] !== value),
      );
      await api.updateSettings(changes);
      setOriginalValues(values);
      setSaved(true);
      setError("");
      window.setTimeout(() => setSaved(false), 2200);
    } catch (settingsError) {
      setError(settingsError instanceof Error ? settingsError.message : "Unable to save settings.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <LoadingState label="Loading engine settings..." />;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Settings"
        title="Tune the AlphaHunter engine with product-grade controls."
        description="Settings are grouped around investor outcomes: alerting, signal logic, scan cadence, and web-intel pipeline behaviour."
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <SectionTabs
              value={tab}
              onChange={setTab}
              tabs={[
                { value: "alerts", label: "Alerts" },
                { value: "signals", label: "Signals" },
                { value: "scanner", label: "Scanner" },
                { value: "pipeline", label: "Pipeline" },
              ]}
            />
            <Button
              variant="secondary"
              onClick={() => setValues(originalValues)}
              disabled={!hasChanges || saving}
            >
              <RotateCcw className="size-4" />
              Reset
            </Button>
            <Button onClick={() => void handleSave()} disabled={!hasChanges || saving}>
              <Save className="size-4" />
              {saving ? "Saving..." : saved ? "Saved" : "Save changes"}
            </Button>
          </div>
        }
      />

      {error ? <ErrorState description={error} /> : null}

      <Panel
        title={
          tab === "alerts"
            ? "Alert rules"
            : tab === "signals"
              ? "Signal logic"
              : tab === "scanner"
                ? "Scanner cadence"
                : "Pipeline controls"
        }
        subtitle="Each control writes directly to the runtime settings store used by the backend."
      >
        <div className="space-y-4">
          {currentDefinitions.map((definition) => {
            const value = values[definition.key] ?? "";

            return (
              <div
                key={definition.key}
                className="grid gap-4 rounded-[28px] border border-white/8 bg-slate-950/55 p-5 lg:grid-cols-[1.2fr_1fr]"
              >
                <FieldLabel label={definition.label} hint={definition.description} />

                <div className="space-y-3">
                  {definition.kind === "range" ? (
                    <div className="rounded-[24px] border border-white/8 bg-slate-950/90 px-4 py-4">
                      <input
                        type="range"
                        min={definition.min}
                        max={definition.max}
                        step={definition.step}
                        value={Number(value || definition.min || 0)}
                        onChange={(event) => updateValue(definition.key, event.target.value)}
                        className="w-full accent-cyan-300"
                      />
                      <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                        <span>
                          {definition.min}
                          {definition.unit}
                        </span>
                        <span className="text-sm font-medium text-white">
                          {value}
                          {definition.unit}
                        </span>
                        <span>
                          {definition.max}
                          {definition.unit}
                        </span>
                      </div>
                    </div>
                  ) : null}

                  {definition.kind === "select" ? (
                    <select
                      value={value}
                      onChange={(event) => updateValue(definition.key, event.target.value)}
                      className="terminal-select"
                    >
                      {definition.options?.map((option) => (
                        <option key={option} value={option}>
                          {option}
                          {definition.unit ? ` ${definition.unit}` : ""}
                        </option>
                      ))}
                    </select>
                  ) : null}

                  {definition.kind === "number" ? (
                    <input
                      type="number"
                      value={value}
                      onChange={(event) => updateValue(definition.key, event.target.value)}
                      className="terminal-input"
                    />
                  ) : null}

                  {definition.kind === "toggle" ? (
                    <button
                      type="button"
                      onClick={() => updateValue(definition.key, value === "true" ? "false" : "true")}
                      className={`flex items-center justify-between rounded-[24px] border px-4 py-3 ${
                        value === "true"
                          ? "border-emerald-400/25 bg-emerald-400/10 text-emerald-100"
                          : "border-white/8 bg-slate-950/80 text-slate-300"
                      }`}
                    >
                      <span className="text-sm font-medium">{value === "true" ? "Enabled" : "Disabled"}</span>
                      <span className="rounded-full border border-current px-3 py-1 text-xs uppercase tracking-[0.18em]">
                        {value === "true" ? "On" : "Off"}
                      </span>
                    </button>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      </Panel>
    </div>
  );
}
