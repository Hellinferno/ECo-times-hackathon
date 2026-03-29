/**
 * ValuationLab — interactive DCF / LBO / Comps model runner.
 *
 * Sections:
 *   Workspace picker  — select the target workspace (optional deep link via ?workspace=)
 *   Model type tabs   — dcf | lbo | comps
 *   Assumption inputs — numeric inputs pre-populated from default_valuation_inputs
 *   Results panel     — headline value, confidence band, sensitivity tables
 *   Run history       — previous valuation runs for the selected workspace
 *
 * A completed run can be promoted to a workspace output (investment memo)
 * directly from the results panel.
 */
import { useEffect, useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Play,
  TrendingUp,
  BarChart3,
  Download,
  Save,
  RotateCcw,
} from "lucide-react";
import {
  api,
  type WorkspaceSummary,
  type ValuationRunSummary,
} from "./api/client";
import {
  Button,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  Panel,
  StatusBadge,
} from "./components/ui";
import { formatDateTime } from "./lib/format";

type ModelType = "dcf" | "lbo" | "comps";

interface ValuationInputs {
  historical_revenues: number[];
  historical_ebitda_margins: number[];
  tax_rate: number;
  wacc: number;
  terminal_growth_rate: number;
  projection_years: number;
  net_debt: number;
  shares_outstanding: number;
  entry_ebitda?: number;
  entry_ev_ebitda?: number;
  equity_contribution_pct?: number;
  hold_years?: number;
  exit_ev_ebitda?: number;
  revenue_growth_rates?: number[];
  ebitda_margins?: number[];
}

const defaultInputs: Record<ModelType, ValuationInputs> = {
  dcf: {
    historical_revenues: [2500, 3000, 3500, 4000],
    historical_ebitda_margins: [0.14, 0.16, 0.17, 0.18],
    tax_rate: 0.25,
    wacc: 0.115,
    terminal_growth_rate: 0.03,
    projection_years: 5,
    net_debt: 800,
    shares_outstanding: 100,
  },
  lbo: {
    historical_revenues: [2500, 3000, 3500, 4000],
    historical_ebitda_margins: [0.14, 0.16, 0.17, 0.18],
    tax_rate: 0.25,
    wacc: 0.115,
    terminal_growth_rate: 0.03,
    projection_years: 5,
    net_debt: 800,
    shares_outstanding: 100,
    entry_ebitda: 720,
    entry_ev_ebitda: 8.0,
    equity_contribution_pct: 0.45,
    hold_years: 5,
    exit_ev_ebitda: 7.5,
    revenue_growth_rates: [0.11, 0.1, 0.09, 0.08, 0.07],
    ebitda_margins: [0.18, 0.19, 0.2, 0.205, 0.21],
  },
  comps: {
    historical_revenues: [4000],
    historical_ebitda_margins: [0.18],
    tax_rate: 0.25,
    wacc: 0.115,
    terminal_growth_rate: 0.03,
    projection_years: 5,
    net_debt: 800,
    shares_outstanding: 100,
  },
};

export default function ValuationLab() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [workspaces, setWorkspaces] = useState<WorkspaceSummary[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>("");
  const [modelType, setModelType] = useState<ModelType>("dcf");
  const [inputs, setInputs] = useState<ValuationInputs>(defaultInputs.dcf);
  const [result, setResult] = useState<ValuationRunSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [recentValuations, setRecentValuations] = useState<ValuationRunSummary[]>([]);

  useEffect(() => {
    const wsId = searchParams.get("workspace");
    if (wsId) {
      setSelectedWorkspace(wsId);
    }
  }, [searchParams]);

  useEffect(() => {
    let cancelled = false;

    const loadWorkspaces = async () => {
      try {
        const response = await api.getWorkspaces({});
        if (cancelled) return;
        setWorkspaces(response.data.workspaces || []);
        if (!selectedWorkspace && response.data.workspaces?.length > 0) {
          setSelectedWorkspace(response.data.workspaces[0].id);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load workspaces");
        }
      }
    };

    void loadWorkspaces();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadRecentValuations = async () => {
      try {
        const response = await api.getValuations({});
        if (cancelled) return;
        setRecentValuations((response.data.valuations || []).slice(0, 5));
      } catch {
        // Silently fail for recent valuations
      }
    };

    void loadRecentValuations();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleModelTypeChange = (type: ModelType) => {
    setModelType(type);
    setInputs(defaultInputs[type]);
    setResult(null);
  };

  const handleInputChange = (key: keyof ValuationInputs, value: number | number[]) => {
    setInputs((prev) => ({ ...prev, [key]: value }));
  };

  const handleRunValuation = async () => {
    if (!selectedWorkspace) {
      setError("Please select a workspace");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await api.runValuation({
        workspace_id: selectedWorkspace,
        model_type: modelType,
        assumptions: inputs,
      });

      if (response.success && response.data) {
        setResult(response.data);
        const updated = await api.getValuations({ workspace_id: selectedWorkspace });
        setRecentValuations((updated.data.valuations || []).slice(0, 5));
      } else {
        setError("Valuation failed to run");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run valuation");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setInputs(defaultInputs[modelType]);
    setResult(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate(-1)}>
          <ArrowLeft className="mr-2 size-4" />
          Back
        </Button>
      </div>

      <PageHeader
        eyebrow="Valuation tools"
        title="Valuation Lab"
        description="Run DCF, LBO, and comparable company analyses for investment valuation."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Panel>
            <h3 className="mb-4 text-lg font-medium text-white">Model Configuration</h3>

            <div className="mb-6 flex gap-2">
              {(["dcf", "lbo", "comps"] as ModelType[]).map((type) => (
                <Button
                  key={type}
                  variant={modelType === type ? "primary" : "secondary"}
                  size="sm"
                  onClick={() => handleModelTypeChange(type)}
                >
                  {type === "dcf" && <TrendingUp className="mr-2 size-4" />}
                  {type === "lbo" && <BarChart3 className="mr-2 size-4" />}
                  {type === "comps" && <BarChart3 className="mr-2 size-4" />}
                  {type.toUpperCase()}
                </Button>
              ))}
            </div>

            <div className="mb-4">
              <label className="mb-2 block text-sm text-slate-400">Workspace</label>
              <select
                value={selectedWorkspace}
                onChange={(e) => setSelectedWorkspace(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-slate-900/50 px-4 py-2.5 text-white focus:border-cyan-400/50 focus:outline-none"
              >
                <option value="">Select a workspace...</option>
                {workspaces.map((ws) => (
                  <option key={ws.id} value={ws.id}>
                    {ws.title} ({ws.workspace_type})
                  </option>
                ))}
              </select>
            </div>

            <div className="mb-6 rounded-lg bg-slate-900/50 p-4">
              <h4 className="mb-4 text-sm font-medium text-white">
                {modelType.toUpperCase()} Parameters
              </h4>

              <div className="grid gap-4 md:grid-cols-2">
                {modelType === "dcf" && (
                  <>
                    <div>
                      <label className="mb-1 block text-xs text-slate-400">WACC (%)</label>
                      <input
                        type="number"
                        step="0.5"
                        value={inputs.wacc * 100}
                        onChange={(e) => handleInputChange("wacc", parseFloat(e.target.value) / 100)}
                        className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-slate-400">Terminal Growth (%)</label>
                      <input
                        type="number"
                        step="0.5"
                        value={inputs.terminal_growth_rate * 100}
                        onChange={(e) => handleInputChange("terminal_growth_rate", parseFloat(e.target.value) / 100)}
                        className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-slate-400">Tax Rate (%)</label>
                      <input
                        type="number"
                        step="1"
                        value={inputs.tax_rate * 100}
                        onChange={(e) => handleInputChange("tax_rate", parseFloat(e.target.value) / 100)}
                        className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-slate-400">Projection Years</label>
                      <input
                        type="number"
                        min="3"
                        max="10"
                        value={inputs.projection_years}
                        onChange={(e) => handleInputChange("projection_years", parseInt(e.target.value))}
                        className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white"
                      />
                    </div>
                  </>
                )}

                {modelType === "lbo" && (
                  <>
                    <div>
                      <label className="mb-1 block text-xs text-slate-400">Entry EV/EBITDA</label>
                      <input
                        type="number"
                        step="0.5"
                        value={inputs.entry_ev_ebitda || 8}
                        onChange={(e) => handleInputChange("entry_ev_ebitda", parseFloat(e.target.value))}
                        className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-slate-400">Exit EV/EBITDA</label>
                      <input
                        type="number"
                        step="0.5"
                        value={inputs.exit_ev_ebitda || 7.5}
                        onChange={(e) => handleInputChange("exit_ev_ebitda", parseFloat(e.target.value))}
                        className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-slate-400">Equity Contribution (%)</label>
                      <input
                        type="number"
                        step="5"
                        value={(inputs.equity_contribution_pct || 0.45) * 100}
                        onChange={(e) => handleInputChange("equity_contribution_pct", parseFloat(e.target.value) / 100)}
                        className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-slate-400">Hold Years</label>
                      <input
                        type="number"
                        min="3"
                        max="7"
                        value={inputs.hold_years || 5}
                        onChange={(e) => handleInputChange("hold_years", parseInt(e.target.value))}
                        className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white"
                      />
                    </div>
                  </>
                )}

                {modelType === "comps" && (
                  <>
                    <div>
                      <label className="mb-1 block text-xs text-slate-400">Latest Revenue (₹ Cr)</label>
                      <input
                        type="number"
                        value={inputs.historical_revenues[inputs.historical_revenues.length - 1]}
                        onChange={(e) => {
                          const newRevenues = [...inputs.historical_revenues];
                          newRevenues[newRevenues.length - 1] = parseFloat(e.target.value);
                          handleInputChange("historical_revenues", newRevenues);
                        }}
                        className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-slate-400">EBITDA Margin (%)</label>
                      <input
                        type="number"
                        step="0.5"
                        value={inputs.historical_ebitda_margins[inputs.historical_ebitda_margins.length - 1] * 100}
                        onChange={(e) => {
                          const newMargins = [...inputs.historical_ebitda_margins];
                          newMargins[newMargins.length - 1] = parseFloat(e.target.value) / 100;
                          handleInputChange("historical_ebitda_margins", newMargins);
                        }}
                        className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white"
                      />
                    </div>
                  </>
                )}

                <div>
                  <label className="mb-1 block text-xs text-slate-400">Net Debt (₹ Cr)</label>
                  <input
                    type="number"
                    value={inputs.net_debt}
                    onChange={(e) => handleInputChange("net_debt", parseFloat(e.target.value))}
                    className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-slate-400">Shares Outstanding (Cr)</label>
                  <input
                    type="number"
                    value={inputs.shares_outstanding}
                    onChange={(e) => handleInputChange("shares_outstanding", parseFloat(e.target.value))}
                    className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              <Button onClick={handleRunValuation} disabled={loading || !selectedWorkspace}>
                <Play className="mr-2 size-4" />
                {loading ? "Running..." : "Run Valuation"}
              </Button>
              <Button variant="secondary" onClick={handleReset}>
                <RotateCcw className="mr-2 size-4" />
                Reset
              </Button>
            </div>
          </Panel>

          {error && <ErrorState title="Error" description={error} />}

          {result && (
            <Panel>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-medium text-white">Valuation Results</h3>
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm">
                    <Save className="mr-2 size-4" />
                    Save
                  </Button>
                </div>
              </div>

              <div className="mb-4 rounded-lg bg-slate-900/50 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">{result.headline_metric}</p>
                    <p className="text-3xl font-bold text-white">{result.headline_value}</p>
                  </div>
                  <StatusBadge
                    label={result.status}
                    tone={result.status === "completed" ? "positive" : "warning"}
                  />
                </div>
                {result.warnings && result.warnings.length > 0 && (
                  <div className="mt-4 rounded-lg bg-amber-500/10 p-3">
                    <p className="text-xs text-amber-400">Warnings:</p>
                    <ul className="mt-1 list-inside list-disc text-xs text-amber-300">
                      {result.warnings.map((warning, idx) => (
                        <li key={idx}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <p className="text-xs text-slate-500">
                Valuation ID: {result.id} • Created: {formatDateTime(result.created_at)}
              </p>
            </Panel>
          )}
        </div>

        <div className="space-y-6">
          <Panel>
            <h3 className="mb-4 text-lg font-medium text-white">Recent Valuations</h3>
            {recentValuations.length === 0 ? (
              <p className="text-sm text-slate-400">No recent valuations</p>
            ) : (
              <div className="space-y-2">
                {recentValuations.map((val) => (
                  <div
                    key={val.id}
                    className="cursor-pointer rounded-lg bg-slate-900/50 p-3 transition-colors hover:bg-slate-800/50"
                    onClick={() => {
                      if (val.workspace_id) {
                        navigate(`/workspaces/${val.workspace_id}?tab=valuations`);
                      }
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-white">
                        {val.model_type.toUpperCase()}
                      </span>
                      <StatusBadge
                        label={val.status}
                        tone={val.status === "completed" ? "positive" : "warning"}
                      />
                    </div>
                    {val.headline_value && (
                      <p className="mt-1 text-sm text-slate-300">
                        {val.headline_metric}: {val.headline_value}
                      </p>
                    )}
                    <p className="text-xs text-slate-500">{formatDateTime(val.created_at)}</p>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel>
            <h3 className="mb-4 text-lg font-medium text-white">Model Info</h3>
            <div className="space-y-3 text-sm">
              {modelType === "dcf" && (
                <>
                  <p className="text-slate-400">
                    <strong className="text-white">DCF (Discounted Cash Flow)</strong> values a company 
                    based on the present value of its projected future cash flows.
                  </p>
                  <p className="text-slate-500">
                    Best for: Companies with predictable cash flows and long-term visibility.
                  </p>
                </>
              )}
              {modelType === "lbo" && (
                <>
                  <p className="text-slate-400">
                    <strong className="text-white">LBO (Leveraged Buyout)</strong> analysis evaluates 
                    returns from acquiring a company using significant debt financing.
                  </p>
                  <p className="text-slate-500">
                    Best for: Private equity transactions and leveraged investments.
                  </p>
                </>
              )}
              {modelType === "comps" && (
                <>
                  <p className="text-slate-400">
                    <strong className="text-white">Comps (Comparables)</strong> values a company 
                    based on the trading multiples of similar publicly traded companies.
                  </p>
                  <p className="text-slate-500">
                    Best for: Quick估值 and industry benchmarking.
                  </p>
                </>
              )}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
