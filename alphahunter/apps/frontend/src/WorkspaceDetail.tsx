/**
 * WorkspaceDetail — full research workspace view for a single company.
 *
 * Sections (tab-switched):
 *   overview       Health summary, company info, recent agent runs
 *   documents      Upload panel + document list with parse/RAG status
 *   tasks          Checklist of workspace tasks with status/priority editing
 *   valuation      Latest valuation run result; links to Valuation Lab
 *   outputs        Draft and approved research outputs with download/review
 *
 * The workspace is loaded on mount; each tab shows data fetched as part of
 * the initial GET /api/platform/workspaces/:id response.
 */
import { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Plus,
  Upload,
  Play,
  FileText,
  CheckSquare,
  TrendingUp,
  Download,
  RefreshCw,
} from "lucide-react";
import {
  api,
  type WorkspaceDetailResponse,
  type ValuationRunSummary,
  type DocumentSummary,
  type TaskSummary,
  type OutputSummary,
  type AgentRunSummary,
} from "./api/client";
import {
  Button,
  EmptyState,
  ErrorState,
  LoadingState,
  MetricCard,
  PageHeader,
  Panel,
  SectionTabs,
  StatusBadge,
} from "./components/ui";
import { formatDateTime } from "./lib/format";

type DetailTab = "overview" | "documents" | "valuations" | "tasks" | "outputs";

function getModelTypeLabel(modelType: string) {
  switch (modelType) {
    case "dcf":
      return "DCF";
    case "lbo":
      return "LBO";
    case "comps":
      return "Comps";
    default:
      return modelType.toUpperCase();
  }
}

function getModelTone(modelType: string) {
  switch (modelType) {
    case "dcf":
      return "info" as const;
    case "lbo":
      return "positive" as const;
    case "comps":
      return "warning" as const;
    default:
      return "neutral" as const;
  }
}

export default function WorkspaceDetail() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState<WorkspaceDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<DetailTab>("overview");
  const [runningValuation, setRunningValuation] = useState(false);
  const [uploadingDocument, setUploadingDocument] = useState(false);

  useEffect(() => {
    if (!workspaceId) return;

    let cancelled = false;

    const loadWorkspace = async () => {
      try {
        const response = await api.getWorkspaceDetail(workspaceId);
        if (cancelled) return;
        setWorkspace(response.data);
        setError("");
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load workspace");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadWorkspace();

    return () => {
      cancelled = true;
    };
  }, [workspaceId]);

  const handleRunValuation = async (modelType: string) => {
    if (!workspace) return;
    setRunningValuation(true);
    try {
      const response = await api.runValuation({
        workspace_id: workspace.workspace.id,
        model_type: modelType,
        assumptions: workspace.default_valuation_inputs || {},
      });
      if (response.success) {
        const updated = await api.getWorkspaceDetail(workspace.workspace.id);
        setWorkspace(updated.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run valuation");
    } finally {
      setRunningValuation(false);
    }
  };

  const handleCreateTask = async () => {
    if (!workspace) return;
    try {
      const response = await api.createTask(workspace.workspace.id, {
        title: "New task",
        status: "todo",
        priority: "medium",
      });
      if (response.success) {
        const updated = await api.getWorkspaceDetail(workspace.workspace.id);
        setWorkspace(updated.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
    }
  };

  if (loading) {
    return <LoadingState label="Loading workspace..." />;
  }

  if (error || !workspace) {
    return (
      <ErrorState
        title="Workspace not found"
        description={error || "The workspace could not be found."}
        action={
          <Button onClick={() => navigate("/workspaces")}>
            <ArrowLeft className="mr-2 size-4" />
            Back to Workspaces
          </Button>
        }
      />
    );
  }

  const { workspace: ws, documents, valuations, tasks, outputs, default_valuation_inputs } = workspace;
  const health = ws.health_summary as Record<string, number> | null;

  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "documents", label: `Documents (${documents?.length || 0})` },
    { id: "valuations", label: `Valuations (${valuations?.length || 0})` },
    { id: "tasks", label: `Tasks (${tasks?.length || 0})` },
    { id: "outputs", label: `Outputs (${outputs?.length || 0})` },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate("/workspaces")}>
          <ArrowLeft className="mr-2 size-4" />
          Back
        </Button>
      </div>

      <PageHeader
        eyebrow="Workspace"
        title={ws.title}
        description={`${ws.workspace_type} workspace for ${ws.company?.name || "company"}`}
        actions={
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={() => navigate(`/valuation-lab?workspace=${ws.id}`)}
            >
              <TrendingUp className="mr-2 size-4" />
              Run Valuation
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Documents"
          value={health?.documents || 0}
          detail={`${health?.parsed_documents || 0} parsed`}
          tone="neutral"
        />
        <MetricCard
          label="Valuations"
          value={valuations?.length || 0}
          detail={health?.latest_valuation_status || "idle"}
          tone="info"
        />
        <MetricCard
          label="Open Tasks"
          value={health?.open_tasks || 0}
          detail={`of ${health?.open_tasks || 0} total`}
          tone="warning"
        />
        <MetricCard
          label="Outputs"
          value={health?.outputs || 0}
          detail={`${health?.approved_outputs || 0} approved`}
          tone="positive"
        />
      </div>

      <SectionTabs tabs={tabs} activeTab={tab} onTabChange={(t) => setTab(t as DetailTab)} />

      {tab === "overview" && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Panel>
            <h3 className="mb-4 text-lg font-medium text-white">Company Details</h3>
            {ws.company && (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-slate-400">Name</span>
                  <span className="text-white">{ws.company.name}</span>
                </div>
                {ws.company.symbol && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Symbol</span>
                    <span className="text-white">{ws.company.symbol}</span>
                  </div>
                )}
                {ws.company.sector && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Sector</span>
                    <span className="text-white">{ws.company.sector}</span>
                  </div>
                )}
                {ws.company.exchange && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Exchange</span>
                    <span className="text-white">{ws.company.exchange}</span>
                  </div>
                )}
                {ws.company.market_cap && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Market Cap</span>
                    <span className="text-white">₹{ws.company.market_cap.toLocaleString()} Cr</span>
                  </div>
                )}
              </div>
            )}
          </Panel>

          <Panel>
            <h3 className="mb-4 text-lg font-medium text-white">Quick Actions</h3>
            <div className="space-y-2">
              <Button
                variant="secondary"
                className="w-full justify-start"
                onClick={() => handleRunValuation("dcf")}
                disabled={runningValuation}
              >
                <TrendingUp className="mr-2 size-4" />
                Run DCF Valuation
              </Button>
              <Button
                variant="secondary"
                className="w-full justify-start"
                onClick={() => handleRunValuation("lbo")}
                disabled={runningValuation}
              >
                <TrendingUp className="mr-2 size-4" />
                Run LBO Analysis
              </Button>
              <Button
                variant="secondary"
                className="w-full justify-start"
                onClick={() => handleRunValuation("comps")}
                disabled={runningValuation}
              >
                <TrendingUp className="mr-2 size-4" />
                Run Comps Analysis
              </Button>
              <Button variant="secondary" className="w-full justify-start" onClick={handleCreateTask}>
                <CheckSquare className="mr-2 size-4" />
                Add Task
              </Button>
            </div>
          </Panel>
        </div>
      )}

      {tab === "documents" && (
        <Panel>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-medium text-white">Documents</h3>
            <Button variant="secondary" size="sm">
              <Upload className="mr-2 size-4" />
              Upload
            </Button>
          </div>
          {!documents?.length ? (
            <EmptyState
              title="No documents"
              description="Upload documents to start analysis."
              action={
                <Button variant="secondary" size="sm">
                  <Upload className="mr-2 size-4" />
                  Upload Document
                </Button>
              }
            />
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between rounded-lg bg-slate-900/50 p-3"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="size-5 text-slate-400" />
                    <div>
                      <p className="text-sm font-medium text-white">{doc.filename}</p>
                      <p className="text-xs text-slate-500">
                        {doc.file_type} • {doc.file_size_bytes} bytes • {doc.parse_status}
                      </p>
                    </div>
                  </div>
                  <StatusBadge label={doc.parse_status} tone={doc.parse_status === "parsed" ? "positive" : "warning"} />
                </div>
              ))}
            </div>
          )}
        </Panel>
      )}

      {tab === "valuations" && (
        <Panel>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-medium text-white">Valuations</h3>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => navigate(`/valuation-lab?workspace=${ws.id}`)}
            >
              <Play className="mr-2 size-4" />
              New Valuation
            </Button>
          </div>
          {!valuations?.length ? (
            <EmptyState
              title="No valuations"
              description="Run a valuation model to see results here."
              action={
                <Button variant="secondary" size="sm" onClick={() => navigate(`/valuation-lab?workspace=${ws.id}`)}>
                  <Play className="mr-2 size-4" />
                  Run Valuation
                </Button>
              }
            />
          ) : (
            <div className="space-y-2">
              {valuations.map((val) => (
                <div
                  key={val.id}
                  className="flex items-center justify-between rounded-lg bg-slate-900/50 p-3"
                >
                  <div className="flex items-center gap-3">
                    <TrendingUp className="size-5 text-slate-400" />
                    <div>
                      <p className="text-sm font-medium text-white">
                        {getModelTypeLabel(val.model_type)} Valuation
                      </p>
                      <p className="text-xs text-slate-500">
                        {formatDateTime(val.created_at)} • {val.status}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <StatusBadge
                      label={val.status}
                      tone={val.status === "completed" ? "positive" : "warning"}
                    />
                    {val.headline_value && (
                      <p className="mt-1 text-sm font-medium text-white">
                        {val.headline_metric}: {val.headline_value}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>
      )}

      {tab === "tasks" && (
        <Panel>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-medium text-white">Tasks</h3>
            <Button variant="secondary" size="sm" onClick={handleCreateTask}>
              <Plus className="mr-2 size-4" />
              Add Task
            </Button>
          </div>
          {!tasks?.length ? (
            <EmptyState
              title="No tasks"
              description="Add tasks to track your workspace progress."
              action={
                <Button variant="secondary" size="sm" onClick={handleCreateTask}>
                  <Plus className="mr-2 size-4" />
                  Add Task
                </Button>
              }
            />
          ) : (
            <div className="space-y-2">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center justify-between rounded-lg bg-slate-900/50 p-3"
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={task.status === "done"}
                      readOnly
                      className="size-4 rounded border-slate-600"
                    />
                    <div>
                      <p className={`text-sm font-medium ${task.status === "done" ? "text-slate-500 line-through" : "text-white"}`}>
                        {task.title}
                      </p>
                      <p className="text-xs text-slate-500">
                        {task.priority} • {task.owner_label}
                      </p>
                    </div>
                  </div>
                  <StatusBadge
                    label={task.status}
                    tone={task.status === "done" ? "positive" : task.status === "in_progress" ? "info" : "warning"}
                  />
                </div>
              ))}
            </div>
          )}
        </Panel>
      )}

      {tab === "outputs" && (
        <Panel>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-medium text-white">Outputs</h3>
          </div>
          {!outputs?.length ? (
            <EmptyState
              title="No outputs"
              description="Outputs from valuations and research will appear here."
            />
          ) : (
            <div className="space-y-2">
              {outputs.map((output) => (
                <div
                  key={output.id}
                  className="flex items-center justify-between rounded-lg bg-slate-900/50 p-3"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="size-5 text-slate-400" />
                    <div>
                      <p className="text-sm font-medium text-white">{output.title}</p>
                      <p className="text-xs text-slate-500">
                        {output.output_type} • v{output.version} • {formatDateTime(output.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge
                      label={output.review_status}
                      tone={
                        output.review_status === "approved"
                          ? "positive"
                          : output.review_status === "draft"
                          ? "warning"
                          : "neutral"
                      }
                    />
                    {output.review_status === "approved" && (
                      <Button variant="ghost" size="sm">
                        <Download className="size-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>
      )}
    </div>
  );
}
