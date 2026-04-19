/**
 * FeedbackWidget — floating button + drawer for posting and reading feedback.
 *
 * Views:
 *   list    — user's existing threads + "Start new thread" CTA
 *   thread  — open conversation, polls GET /feedback/threads/:id/messages
 *             every 3s; body compose box at the bottom
 *   new     — subject + body form that calls POST /feedback/threads
 *
 * The widget hides itself when unauthenticated.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { MessageSquarePlus, X, ArrowLeft, Send } from "lucide-react";
import {
  api,
  type FeedbackMessage,
  type FeedbackThread,
} from "../api/client";
import { useAuth } from "../auth/auth-context";
import { Button } from "./ui";
import { cx } from "../lib/utils";

type View = "list" | "thread" | "new";

const MAX_BODY = 4000;
const MAX_SUBJECT = 200;

export default function FeedbackWidget() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [view, setView] = useState<View>("list");
  const [threads, setThreads] = useState<FeedbackThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<FeedbackMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [replyBody, setReplyBody] = useState("");
  const pollRef = useRef<number | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const activeThread = useMemo(
    () => threads.find((t) => t.thread_id === activeThreadId) ?? null,
    [threads, activeThreadId],
  );

  const refreshThreads = useCallback(async () => {
    try {
      const res = await api.listFeedbackThreads();
      setThreads(res.data.threads);
    } catch (e) {
      setError((e as Error).message);
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
    if (!open || !user) return;
    if (view === "list") void refreshThreads();
  }, [open, user, view, refreshThreads]);

  useEffect(() => {
    if (pollRef.current) window.clearInterval(pollRef.current);
    if (!open || view !== "thread" || !activeThreadId) return;
    void refreshMessages(activeThreadId);
    pollRef.current = window.setInterval(() => {
      void refreshMessages(activeThreadId);
    }, 3000);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [open, view, activeThreadId, refreshMessages]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length]);

  if (!user) return null;

  async function submitNewThread() {
    if (!subject.trim() || !body.trim()) return;
    setSending(true);
    setError(null);
    try {
      const res = await api.createFeedbackThread({
        subject: subject.trim().slice(0, MAX_SUBJECT),
        body: body.trim().slice(0, MAX_BODY),
      });
      setSubject("");
      setBody("");
      setActiveThreadId(res.data.thread.thread_id);
      setView("thread");
      await refreshThreads();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSending(false);
    }
  }

  async function submitReply() {
    if (!replyBody.trim() || !activeThreadId) return;
    setSending(true);
    setError(null);
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

  return (
    <>
      <button
        type="button"
        onClick={() => {
          setOpen((v) => !v);
          setView("list");
        }}
        className="fixed bottom-5 right-5 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/30 transition hover:bg-emerald-400"
        aria-label="Open feedback"
      >
        {open ? <X size={20} /> : <MessageSquarePlus size={20} />}
      </button>

      {open ? (
        <div className="fixed bottom-20 right-5 z-40 flex h-[32rem] w-[22rem] flex-col overflow-hidden rounded-2xl border border-white/10 bg-slate-950 shadow-xl shadow-black/40">
          <header className="flex items-center justify-between border-b border-white/10 px-4 py-3">
            <div className="flex items-center gap-2">
              {view !== "list" ? (
                <button
                  type="button"
                  onClick={() => {
                    setView("list");
                    setActiveThreadId(null);
                  }}
                  className="rounded-md p-1 text-slate-300 hover:bg-white/5"
                  aria-label="Back"
                >
                  <ArrowLeft size={16} />
                </button>
              ) : null}
              <div>
                <p className="text-sm font-semibold text-white">Support & feedback</p>
                <p className="text-[11px] text-slate-400">
                  {view === "thread" && activeThread
                    ? activeThread.subject
                    : view === "new"
                    ? "Start a new conversation"
                    : "Your threads"}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-md p-1 text-slate-400 hover:bg-white/5"
              aria-label="Close"
            >
              <X size={16} />
            </button>
          </header>

          {error ? (
            <div className="border-b border-red-500/20 bg-red-500/10 px-3 py-2 text-xs text-red-300">
              {error}
            </div>
          ) : null}

          {view === "list" ? (
            <div className="flex flex-1 flex-col overflow-hidden">
              <div className="flex-1 overflow-y-auto px-3 py-3">
                {threads.length === 0 ? (
                  <p className="px-2 py-8 text-center text-xs text-slate-500">
                    No threads yet. Start the first one.
                  </p>
                ) : (
                  <ul className="flex flex-col gap-2">
                    {threads.map((t) => (
                      <li key={t.thread_id}>
                        <button
                          type="button"
                          onClick={() => {
                            setActiveThreadId(t.thread_id);
                            setView("thread");
                          }}
                          className="w-full rounded-md border border-white/5 bg-slate-900/60 px-3 py-2 text-left hover:border-emerald-400/40"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <p className="line-clamp-1 text-sm text-white">{t.subject}</p>
                            <span
                              className={cx(
                                "rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide",
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
              </div>
              <div className="border-t border-white/10 p-3">
                <Button onClick={() => setView("new")} className="w-full">
                  Start new thread
                </Button>
              </div>
            </div>
          ) : null}

          {view === "new" ? (
            <div className="flex flex-1 flex-col gap-3 overflow-y-auto p-3">
              <input
                type="text"
                placeholder="Subject"
                value={subject}
                maxLength={MAX_SUBJECT}
                onChange={(e) => setSubject(e.target.value)}
                className="rounded-md border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-emerald-400/60"
              />
              <textarea
                placeholder="How can we help?"
                value={body}
                maxLength={MAX_BODY}
                onChange={(e) => setBody(e.target.value)}
                className="h-40 flex-1 resize-none rounded-md border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-emerald-400/60"
              />
              <Button
                onClick={submitNewThread}
                disabled={sending || !subject.trim() || !body.trim()}
                className="w-full"
              >
                {sending ? "Sending..." : "Send"}
              </Button>
            </div>
          ) : null}

          {view === "thread" ? (
            <div className="flex flex-1 flex-col overflow-hidden">
              <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-3">
                <ul className="flex flex-col gap-3">
                  {messages.map((m) => (
                    <li
                      key={m.message_id}
                      className={cx(
                        "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                        m.author_role === "admin"
                          ? "self-start border border-white/10 bg-slate-900/60 text-slate-100"
                          : "self-end bg-emerald-500/20 text-emerald-50",
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
              {activeThread && activeThread.status === "open" ? (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    void submitReply();
                  }}
                  className="flex items-end gap-2 border-t border-white/10 p-3"
                >
                  <textarea
                    placeholder="Write a reply…"
                    value={replyBody}
                    maxLength={MAX_BODY}
                    onChange={(e) => setReplyBody(e.target.value)}
                    className="h-16 flex-1 resize-none rounded-md border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-emerald-400/60"
                  />
                  <button
                    type="submit"
                    disabled={sending || !replyBody.trim()}
                    className="rounded-md bg-emerald-500 p-2 text-slate-950 hover:bg-emerald-400 disabled:opacity-40"
                    aria-label="Send"
                  >
                    <Send size={16} />
                  </button>
                </form>
              ) : (
                <div className="border-t border-white/10 bg-slate-950/60 px-3 py-3 text-xs text-slate-400">
                  This thread is resolved. An admin can reopen it.
                </div>
              )}
            </div>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
