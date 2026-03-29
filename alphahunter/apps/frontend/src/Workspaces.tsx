/**
 * Workspaces — list and create analyst research workspaces.
 *
 * Sections:
 *   PageHeader      — title, new-workspace CTA
 *   Metrics grid    — total, public equity, private/deal, active (4-up)
 *   Filter bar      — search input + type/stage dropdowns
 *   Workspace grid  — 3-col card grid linking to WorkspaceDetail
 *
 * Deep link: ?create=true&symbol=INFY triggers an auto-create from opportunity
 * (redirects directly to the new workspace detail page on success).
 */
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Plus, Search, Filter, FolderOpen, TrendingUp, Building2, Briefcase } from "lucide-react";
import { api, type ApiResponse, type WorkspaceSummary, type CompanySummary } from "./api/client";
import {
  Button,
  EmptyState,
  ErrorState,
  LoadingState,
  MetricCard,
  PageHeader,
  Panel,
  StatusBadge,
} from "./components/ui";

interface WorkspaceWithCompany extends WorkspaceSummary {
  company?: CompanySummary;
}

function getWorkspaceTypeIcon(workspaceType: string) {
  switch (workspaceType) {
    case "public_equity":
      return TrendingUp;
    case "private_company":
      return Building2;
    case "deal":
      return Briefcase;
    default:
      return FolderOpen;
  }
}

function getWorkspaceTypeLabel(workspaceType: string) {
  switch (workspaceType) {
    case "public_equity":
      return "Public Equity";
    case "private_company":
      return "Private Company";
    case "deal":
      return "Deal";
    default:
      return workspaceType;
  }
}

function getStageTone(stage: string) {
  switch (stage) {
    case "active":
      return "positive" as const;
    case "completed":
      return "info" as const;
    case "archived":
      return "neutral" as const;
    default:
      return "warning" as const;
  }
}

export default function Workspaces() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [workspaces, setWorkspaces] = useState<WorkspaceWithCompany[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<{ type: string; stage: string }>({
    type: "",
    stage: "",
  });
  const [searchQuery, setSearchQuery] = useState("");

  const createFromSymbol = searchParams.get("create") === "true" ? searchParams.get("symbol") : null;

  useEffect(() => {
    let cancelled = false;

    const loadWorkspaces = async () => {
      try {
        const response = await api.getWorkspaces({
          workspace_type: filter.type || undefined,
          stage: filter.stage || undefined,
        });
        if (cancelled) return;
        setWorkspaces(response.data.workspaces || []);
        setError("");
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load workspaces");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadWorkspaces();

    return () => {
      cancelled = true;
    };
  }, [filter.type, filter.stage]);

  useEffect(() => {
    if (createFromSymbol) {
      const createWorkspace = async () => {
        try {
          const response = await api.createWorkspaceFromOpportunity({
            symbol: createFromSymbol,
            title: `${createFromSymbol} Research Workspace`,
          });
          if (response.success && response.data.id) {
            navigate(`/workspaces/${response.data.id}`);
          }
        } catch (err) {
          console.error("Failed to create workspace:", err);
        }
      };
      void createWorkspace();
    }
  }, [createFromSymbol, navigate]);

  const filteredWorkspaces = workspaces.filter((ws) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      ws.title.toLowerCase().includes(query) ||
      ws.company?.name?.toLowerCase().includes(query) ||
      ws.company?.symbol?.toLowerCase().includes(query)
    );
  });

  const stats = {
    total: workspaces.length,
    publicEquity: workspaces.filter((w) => w.workspace_type === "public_equity").length,
    privateCompany: workspaces.filter((w) => w.workspace_type === "private_company").length,
    deals: workspaces.filter((w) => w.workspace_type === "deal").length,
  };

  const handleCreateWorkspace = async () => {
    try {
      const response = await api.createWorkspace({
        title: "New Workspace",
        workspace_type: "public_equity",
      });
      if (response.success && response.data.id) {
        navigate(`/workspaces/${response.data.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create workspace");
    }
  };

  if (loading) {
    return <LoadingState label="Loading workspaces..." />;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Analyst workspaces"
        title="Research & Valuation Workspaces"
        description="Create and manage analyst workspaces for deep-dive research, valuation models, and investment memos."
        actions={
          <Button onClick={handleCreateWorkspace}>
            <Plus className="mr-2 size-4" />
            New Workspace
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Total Workspaces"
          value={stats.total}
          detail="All workspaces across the organization"
          tone="neutral"
        />
        <MetricCard
          label="Public Equity"
          value={stats.publicEquity}
          detail="Public market coverage workspaces"
          tone="info"
        />
        <MetricCard
          label="Private/Deal"
          value={stats.privateCompany + stats.deals}
          detail="Private company and deal workspaces"
          tone="positive"
        />
        <MetricCard
          label="Active"
          value={workspaces.filter((w) => w.stage === "active").length}
          detail="Workspaces with ongoing activity"
          tone="warning"
        />
      </div>

      <Panel>
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-1 items-center gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search workspaces..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-slate-900/50 px-4 py-2.5 pl-10 text-sm text-white placeholder-slate-500 focus:border-cyan-400/50 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filter.type}
              onChange={(e) => setFilter((f) => ({ ...f, type: e.target.value }))}
              className="rounded-xl border border-white/10 bg-slate-900/50 px-3 py-2 text-sm text-white focus:border-cyan-400/50 focus:outline-none"
            >
              <option value="">All Types</option>
              <option value="public_equity">Public Equity</option>
              <option value="private_company">Private Company</option>
              <option value="deal">Deal</option>
            </select>
            <select
              value={filter.stage}
              onChange={(e) => setFilter((f) => ({ ...f, stage: e.target.value }))}
              className="rounded-xl border border-white/10 bg-slate-900/50 px-3 py-2 text-sm text-white focus:border-cyan-400/50 focus:outline-none"
            >
              <option value="">All Stages</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </div>
      </Panel>

      {error && <ErrorState title="Error" description={error} />}

      {filteredWorkspaces.length === 0 && !error ? (
        <EmptyState
          title="No workspaces yet"
          description="Create your first workspace to start research and valuation work."
          action={
            <Button onClick={handleCreateWorkspace}>
              <Plus className="mr-2 size-4" />
              Create Workspace
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filteredWorkspaces.map((workspace) => {
            const TypeIcon = getWorkspaceTypeIcon(workspace.workspace_type);
            const health = workspace.health_summary as Record<string, number> | null;

            return (
              <Link
                key={workspace.id}
                to={`/workspaces/${workspace.id}`}
                className="group block"
              >
                <Panel className="h-full transition-colors hover:border-cyan-400/30">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex size-10 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-300">
                        <TypeIcon className="size-5" />
                      </div>
                      <div>
                        <h3 className="font-medium text-white group-hover:text-cyan-300">
                          {workspace.title}
                        </h3>
                        <p className="text-sm text-slate-400">
                          {workspace.company?.symbol || workspace.company?.name || "No company"}
                        </p>
                      </div>
                    </div>
                    <StatusBadge
                      label={workspace.stage}
                      tone={getStageTone(workspace.stage)}
                    />
                  </div>

                  <div className="mt-4 flex items-center gap-4 text-xs text-slate-400">
                    <span>{getWorkspaceTypeLabel(workspace.workspace_type)}</span>
                    {health && (
                      <>
                        <span>{health.documents || 0} docs</span>
                        <span>{health.open_tasks || 0} tasks</span>
                        <span>{health.outputs || 0} outputs</span>
                      </>
                    )}
                  </div>

                  {workspace.company?.sector && (
                    <p className="mt-3 text-xs text-slate-500">
                      {workspace.company.sector}
                    </p>
                  )}
                </Panel>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
