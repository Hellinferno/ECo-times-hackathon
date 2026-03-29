/**
 * Outputs — cross-workspace research output review board.
 *
 * Sections:
 *   PageHeader    — title and filter/search controls
 *   Metrics grid  — total, approved, draft, in-review counts (4-up)
 *   Filter bar    — search input + review_status filter
 *   Output grid   — cards with preview, workspace link, review action, download
 *
 * Only approved outputs allow download (enforced by the backend /download endpoint).
 * Managers and admins can change review_status via PATCH /outputs/:id/review.
 */
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FileText, Download, Eye, Filter, Search, CheckCircle, Clock, Edit3 } from "lucide-react";
import { api, type OutputSummary, type WorkspaceSummary } from "./api/client";
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

function getReviewTone(status: string) {
  switch (status) {
    case "approved":
      return "positive" as const;
    case "draft":
      return "warning" as const;
    case "pending_review":
      return "info" as const;
    case "rejected":
      return "danger" as const;
    default:
      return "neutral" as const;
  }
}

function getReviewIcon(status: string) {
  switch (status) {
    case "approved":
      return CheckCircle;
    case "draft":
      return Edit3;
    case "pending_review":
      return Clock;
    default:
      return FileText;
  }
}

export default function Outputs() {
  const navigate = useNavigate();
  const [outputs, setOutputs] = useState<OutputSummary[]>([]);
  const [workspaces, setWorkspaces] = useState<WorkspaceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<{ status: string; type: string }>({
    status: "",
    type: "",
  });
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadData = async () => {
      try {
        const [outputsRes, workspacesRes] = await Promise.all([
          api.getOutputs(),
          api.getWorkspaces({}),
        ]);

        if (cancelled) return;

        setOutputs(outputsRes.data.outputs || []);
        setWorkspaces(workspacesRes.data.workspaces || []);
        setError("");
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load outputs");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadData();

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredOutputs = outputs.filter((output) => {
    if (filter.status && output.review_status !== filter.status) return false;
    if (filter.type && output.output_type !== filter.type) return false;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        output.title.toLowerCase().includes(query) ||
        output.output_type.toLowerCase().includes(query)
      );
    }
    return true;
  });

  const stats = {
    total: outputs.length,
    drafts: outputs.filter((o) => o.review_status === "draft").length,
    pending: outputs.filter((o) => o.review_status === "pending_review").length,
    approved: outputs.filter((o) => o.review_status === "approved").length,
  };

  const handleDownload = async (output: OutputSummary) => {
    if (output.workspace_id) {
      try {
        const blob = await api.downloadOutput(output.workspace_id, output.id);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${output.title.replace(/\s+/g, "_")}.md`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (err) {
        console.error("Download failed:", err);
      }
    }
  };

  if (loading) {
    return <LoadingState label="Loading outputs..." />;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Investment outputs"
        title="Outputs & Reports"
        description="View and manage investment memos, valuation reports, and other analytical outputs."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border border-white/8 bg-slate-900/50 p-4">
          <p className="text-sm text-slate-400">Total Outputs</p>
          <p className="mt-1 text-2xl font-bold text-white">{stats.total}</p>
        </div>
        <div className="rounded-xl border border-white/8 bg-slate-900/50 p-4">
          <p className="text-sm text-slate-400">Drafts</p>
          <p className="mt-1 text-2xl font-bold text-amber-400">{stats.drafts}</p>
        </div>
        <div className="rounded-xl border border-white/8 bg-slate-900/50 p-4">
          <p className="text-sm text-slate-400">Pending Review</p>
          <p className="mt-1 text-2xl font-bold text-cyan-400">{stats.pending}</p>
        </div>
        <div className="rounded-xl border border-white/8 bg-slate-900/50 p-4">
          <p className="text-sm text-slate-400">Approved</p>
          <p className="mt-1 text-2xl font-bold text-emerald-400">{stats.approved}</p>
        </div>
      </div>

      <Panel>
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-1 items-center gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search outputs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-slate-900/50 px-4 py-2.5 pl-10 text-sm text-white placeholder-slate-500 focus:border-cyan-400/50 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filter.status}
              onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value }))}
              className="rounded-xl border border-white/10 bg-slate-900/50 px-3 py-2 text-sm text-white focus:border-cyan-400/50 focus:outline-none"
            >
              <option value="">All Status</option>
              <option value="draft">Draft</option>
              <option value="pending_review">Pending Review</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
            <select
              value={filter.type}
              onChange={(e) => setFilter((f) => ({ ...f, type: e.target.value }))}
              className="rounded-xl border border-white/10 bg-slate-900/50 px-3 py-2 text-sm text-white focus:border-cyan-400/50 focus:outline-none"
            >
              <option value="">All Types</option>
              <option value="investment_memo">Investment Memo</option>
              <option value="valuation_report">Valuation Report</option>
              <option value="research_brief">Research Brief</option>
              <option value="due_diligence">Due Diligence</option>
            </select>
          </div>
        </div>
      </Panel>

      {error && <ErrorState title="Error" description={error} />}

      {filteredOutputs.length === 0 && !error ? (
        <EmptyState
          title="No outputs yet"
          description="Outputs from valuations and research will appear here."
        />
      ) : (
        <div className="space-y-3">
          {filteredOutputs.map((output) => {
            const workspace = workspaces.find((w) => w.id === output.workspace_id);
            const StatusIcon = getReviewIcon(output.review_status);

            return (
              <Panel key={output.id} className="transition-colors hover:border-cyan-400/30">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="flex size-10 items-center justify-center rounded-xl bg-slate-800 text-slate-400">
                      <FileText className="size-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-white">{output.title}</h3>
                        <StatusBadge
                          label={output.review_status.replace("_", " ")}
                          tone={getReviewTone(output.review_status)}
                        />
                      </div>
                      <p className="mt-1 text-sm text-slate-400">
                        {output.output_type.replace("_", " ")} • v{output.version}
                        {workspace && (
                          <span className="text-slate-500"> • {workspace.title}</span>
                        )}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        Created {formatDateTime(output.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="sm">
                      <Eye className="size-4" />
                    </Button>
                    {output.review_status === "approved" && (
                      <Button variant="ghost" size="sm" onClick={() => handleDownload(output)}>
                        <Download className="size-4" />
                      </Button>
                    )}
                  </div>
                </div>

                {output.preview_markdown && (
                  <div className="mt-4 rounded-lg bg-slate-900/50 p-3">
                    <p className="line-clamp-3 text-sm text-slate-400">
                      {output.preview_markdown.slice(0, 300)}...
                    </p>
                  </div>
                )}
              </Panel>
            );
          })}
        </div>
      )}
    </div>
  );
}
