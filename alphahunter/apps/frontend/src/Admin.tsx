/**
 * Admin — admin-only control surface.
 *
 * Columns:
 *   Left   — feedback inbox (10s polling) showing every thread in the org
 *   Right  — selected thread with reply box, plus resolve/reopen control
 *
 * Route-guarded by AdminRoute in App.tsx; this component still defensively
 * refuses to render if the user is not an admin.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle2, RotateCcw, Send } from "lucide-react";
import {
  api,
  type FeedbackMessage,
  type FeedbackThread,
} from "./api/client";
import { useAuth } from "./auth/auth-context";
import { Button, EmptyState, LoadingState, Panel } from "./components/ui";
import { cx } from "./lib/utils";

const MAX_BODY = 4000;

export default function Admin() {
  const { user } = useAuth();
  const [threads, setThreads] = useState<FeedbackThread[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<FeedbackMessage[]>([]);
  const [replyBody, setReplyBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [statusFilter, setStatusFilter] = useState<"all" | "open" | "resolved">("open");
  const threadPoll = useRef<number | null>(null);
  const messagePoll = useRef<number | null>(null);

  const refreshThreads = useCallback(async () => {
    try {
      const res = await api.listFeedbackThreads();
      setThreads(res.data.threads);
      setLoading(false);
    } catch (e) {
      setError((e as Error).message);
      setLoading(false);
    }
  }, []);

  const refreshMessages = useCallback(async (threadId: string) => {
    try {
      const res = await api.getFeedbackThread(threadId);
      setMessages(res.data.messages);
      setThreads((prev) =>
        prev.map((t) => (t.thread_id === threadId ? res.data.thread : t)),
      );
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    void refreshThreads();
    threadPoll.current = window.setInterval(() => void refreshThreads(), 10000);
    return () => {
      if (threadPoll.current) window.clearInterval(threadPoll.current);
    };
  }, [refreshThreads]);

  useEffect(() => {
    if (messagePoll.current) window.clearInterval(messagePoll.current);
    if (!activeThreadId) {
      setMessages([]);
      return;
    }
    void refreshMessages(activeThreadId);
    messagePoll.current = window.setInterval(() => {
      if (activeThreadId) void refreshMessages(activeThreadId);
    }, 3000);
    return () => {
      if (messagePoll.current) window.clearInterval(messagePoll.current);
    };
  }, [activeThreadId, refreshMessages]);

  const filtered = useMemo(
    () =>
      statusFilter === "all"
        ? threads
        : threads.filter((t) => t.status === statusFilter),
    [threads, statusFilter],
  );

  const activeThread = useMemo(
    () => threads.find((t) => t.thread_id === activeThreadId) ?? null,
    [threads, activeThreadId],
  );

  if (!user || user.role.toLowerCase() !== "admin") {
    return (
      <EmptyState
        title="Admin only"
        description="You need an admin role to view this page."
      />
    );
  }

  if (loading) return <LoadingState label="Loading admin console..." />;

  async function submitReply() {
    if (!replyBody.trim() || !activeThreadId) return;
    setSending(true);
    try {
      await api.postFeedbackMessage(activeThreadId, replyBody.trim().slice(0, MAX_BODY));
      setReplyBody("");
      await refreshMessages(activeThreadId);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSending(false);
    }
  }

  async function toggleStatus() {
    if (!activeThread) return;
    try {
      const next = activeThread.status === "open" ? "resolved" : "open";
      await api.setFeedbackThreadStatus(activeThread.thread_id, next);
      await refreshThreads();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Admin console</h1>
          <p className="text-sm text-slate-400">
            Feedback from every user in <span className="text-white">{user.org_slug}</span>.
          </p>
        </div>
        <div className="flex items-center gap-1 rounded-md border border-white/10 bg-slate-950/60 p-1 text-xs">
          {(["open", "resolved", "all"] as const).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setStatusFilter(s)}
              className={cx(
                "px-3 py-1 rounded capitalize",
                statusFilter === s ? "bg-emerald-500/30 text-emerald-200" : "text-slate-400",
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[18rem_minmax(0,1fr)]">
        <Panel title="Inbox" subtitle={`${filtered.length} threads`}>
          {filtered.length === 0 ? (
            <p className="py-6 text-center text-xs text-slate-500">No threads.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {filtered.map((t) => (
                <li key={t.thread_id}>
                  <button
                    type="button"
                    onClick={() => setActiveThreadId(t.thread_id)}
                    className={cx(
                      "w-full rounded-md border px-3 py-2 text-left",
                      activeThreadId === t.thread_id
                        ? "border-emerald-400/50 bg-emerald-400/10"
                        : "border-white/5 bg-slate-900/60 hover:border-white/20",
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="line-clamp-1 text-sm text-white">{t.subject}</p>
                      <span
                        className={cx(
                          "rounded-full px-2 py-0.5 text-[10px] uppercase",
                          t.status === "resolved"
                            ? "bg-slate-700/60 text-slate-300"
                            : "bg-emerald-500/20 text-emerald-300",
                        )}
                      >
                        {t.status}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-slate-500">
                      {t.last_activity_at
                        ? new Date(t.last_activity_at).toLocaleString()
                        : ""}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel
          title={activeThread?.subject ?? "Select a thread"}
          subtitle={activeThread ? `Status: ${activeThread.status}` : "Conversation view"}
          actions={
            activeThread ? (
              <Button variant="secondary" onClick={toggleStatus}>
                {activeThread.status === "open" ? (
                  <span className="flex items-center gap-1">
                    <CheckCircle2 size={14} /> Mark resolved
                  </span>
                ) : (
                  <span className="flex items-center gap-1">
                    <RotateCcw size={14} /> Reopen
                  </span>
                )}
              </Button>
            ) : null
          }
        >
          {!activeThread ? (
            <p className="py-10 text-center text-sm text-slate-500">
              Pick a thread from the inbox to read and reply.
            </p>
          ) : (
            <div className="flex flex-col gap-3">
              <div className="max-h-[24rem] overflow-y-auto pr-1">
                <ul className="flex flex-col gap-3">
                  {messages.map((m) => (
                    <li
                      key={m.message_id}
                      className={cx(
                        "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                        m.author_role === "admin"
                          ? "self-end ml-auto bg-emerald-500/20 text-emerald-50"
                          : "self-start border border-white/10 bg-slate-900/60 text-slate-100",
                      )}
                    >
                      <p className="whitespace-pre-wrap break-words">{m.body}</p>
                      <p className="mt-1 text-[10px] uppercase tracking-wide text-slate-400">
                        {m.author_role}
                        {m.created_at ? ` · ${new Date(m.created_at).toLocaleString()}` : ""}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
              {activeThread.status === "open" ? (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    void submitReply();
                  }}
                  className="flex items-end gap-2 border-t border-white/10 pt-3"
                >
                  <textarea
                    placeholder="Write a reply…"
                    value={replyBody}
                    maxLength={MAX_BODY}
                    onChange={(e) => setReplyBody(e.target.value)}
                    className="h-20 flex-1 resize-none rounded-md border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-emerald-400/60"
                  />
                  <button
                    type="submit"
                    disabled={sending || !replyBody.trim()}
                    className="rounded-md bg-emerald-500 p-2 text-slate-950 hover:bg-emerald-400 disabled:opacity-40"
                    aria-label="Send reply"
                  >
                    <Send size={16} />
                  </button>
                </form>
              ) : (
                <p className="rounded-md border border-white/10 bg-slate-950/60 px-3 py-2 text-xs text-slate-400">
                  Thread is resolved. Reopen it to continue the conversation.
                </p>
              )}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
