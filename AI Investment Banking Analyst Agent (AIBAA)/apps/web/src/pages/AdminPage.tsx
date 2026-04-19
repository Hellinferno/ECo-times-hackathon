import { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Send, CheckCircle2, RotateCcw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../components/auth/AuthContext';
import {
  fetchFeedbackMessages,
  fetchFeedbackThreads,
  postFeedbackMessage,
  setFeedbackThreadStatus,
  api,
  type FeedbackMessage,
  type FeedbackThread,
} from '../lib/api';

type Tab = 'feedback' | 'audit' | 'models';

const POLL_LIST_MS = 10_000;
const POLL_THREAD_MS = 3_000;

export default function AdminPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [tab, setTab] = useState<Tab>('feedback');

  if (!isAdmin) {
    return (
      <div className="p-8 max-w-2xl mx-auto text-center">
        <h1 className="text-xl font-semibold mb-2">Admin access required</h1>
        <p className="opacity-70 text-sm mb-4">
          This area is restricted to users with the <code>admin</code> role.
        </p>
        <Link to="/" className="text-sm text-blue-400 hover:text-blue-300">← Back to dashboard</Link>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-10 max-w-6xl mx-auto">
      <Link
        to="/"
        className="inline-flex items-center gap-2 mb-6 text-xs opacity-70 hover:opacity-100"
      >
        <ArrowLeft size={14} /> Back
      </Link>

      <h1 className="text-2xl font-semibold mb-2">Admin</h1>
      <p className="text-sm opacity-70 mb-6">Tenant: <code>{user?.tenant_id}</code></p>

      <div className="flex gap-1 border-b mb-6" style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}>
        {(['feedback', 'audit', 'models'] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm capitalize border-b-2 ${
              tab === t ? 'border-blue-500 text-white' : 'border-transparent opacity-70 hover:opacity-100'
            }`}
          >
            {t === 'feedback' ? 'Feedback' : t === 'audit' ? 'Audit log' : 'Model registry'}
          </button>
        ))}
      </div>

      {tab === 'feedback' && <FeedbackInbox />}
      {tab === 'audit' && <AuditLogView />}
      {tab === 'models' && <ModelRegistryView />}
    </div>
  );
}

function FeedbackInbox() {
  const [threads, setThreads] = useState<FeedbackThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [activeThread, setActiveThread] = useState<FeedbackThread | null>(null);
  const [messages, setMessages] = useState<FeedbackMessage[]>([]);
  const [replyBody, setReplyBody] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  const loadThreads = useCallback(async () => {
    try {
      const list = await fetchFeedbackThreads();
      setThreads(list);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load threads');
    }
  }, []);

  const loadMessages = useCallback(async (id: string) => {
    try {
      const data = await fetchFeedbackMessages(id);
      setActiveThread(data.thread);
      setMessages(data.messages);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load thread');
    }
  }, []);

  useEffect(() => {
    loadThreads();
    const interval = window.setInterval(loadThreads, POLL_LIST_MS);
    return () => window.clearInterval(interval);
  }, [loadThreads]);

  useEffect(() => {
    if (!activeThreadId) return;
    loadMessages(activeThreadId);
    const interval = window.setInterval(() => loadMessages(activeThreadId), POLL_THREAD_MS);
    return () => window.clearInterval(interval);
  }, [activeThreadId, loadMessages]);

  const handleReply = async () => {
    if (!activeThreadId || !replyBody.trim()) return;
    setSending(true);
    setError(null);
    try {
      const msg = await postFeedbackMessage(activeThreadId, replyBody.trim());
      setMessages((prev) => [...prev, msg]);
      setReplyBody('');
      await loadThreads();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to send');
    } finally {
      setSending(false);
    }
  };

  const handleStatusToggle = async () => {
    if (!activeThread || !activeThreadId) return;
    const next = activeThread.status === 'open' ? 'resolved' : 'open';
    try {
      const updated = await setFeedbackThreadStatus(activeThreadId, next);
      setActiveThread(updated);
      await loadThreads();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to update status');
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-[320px_1fr] gap-4 h-[640px]">
      <aside className="border rounded overflow-y-auto" style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}>
        <div className="px-3 py-2 text-xs opacity-70 border-b" style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}>
          {threads.length} thread{threads.length === 1 ? '' : 's'}
        </div>
        {threads.length === 0 && <div className="p-4 text-sm opacity-60">No feedback yet.</div>}
        <ul>
          {threads.map((t) => (
            <li key={t.thread_id}>
              <button
                type="button"
                onClick={() => setActiveThreadId(t.thread_id)}
                className={`w-full text-left px-3 py-2 border-b hover:bg-white/5 ${activeThreadId === t.thread_id ? 'bg-white/5' : ''}`}
                style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium truncate">{t.subject}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${t.status === 'open' ? 'bg-green-900/40 text-green-300' : 'bg-gray-700 text-gray-300'}`}>
                    {t.status}
                  </span>
                </div>
                <div className="text-[10px] opacity-60 mt-1 truncate">
                  {t.created_by_user_id} · {t.last_activity_at ? new Date(t.last_activity_at).toLocaleString() : ''}
                </div>
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <section className="border rounded flex flex-col overflow-hidden" style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}>
        {!activeThread ? (
          <div className="flex-1 flex items-center justify-center text-sm opacity-60">Select a thread</div>
        ) : (
          <>
            <header className="flex items-center gap-2 px-4 py-3 border-b" style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}>
              <div className="flex-1">
                <h2 className="text-sm font-medium">{activeThread.subject}</h2>
                <p className="text-[11px] opacity-60">from {activeThread.created_by_user_id}</p>
              </div>
              <button
                type="button"
                onClick={handleStatusToggle}
                className="text-xs px-2 py-1 rounded border flex items-center gap-1 hover:bg-white/5"
                style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}
              >
                {activeThread.status === 'open' ? <CheckCircle2 size={12} /> : <RotateCcw size={12} />}
                {activeThread.status === 'open' ? 'Resolve' : 'Reopen'}
              </button>
            </header>

            {error && <div className="text-red-400 text-xs px-4 py-1">{error}</div>}

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
              {messages.map((m) => (
                <div
                  key={m.message_id}
                  className={`max-w-[80%] rounded px-3 py-2 text-sm ${m.author_role === 'admin' ? 'bg-blue-600/20 ml-auto' : 'bg-white/5 mr-auto'}`}
                >
                  <div className="text-[10px] opacity-60 mb-1">
                    {m.author_role === 'admin' ? 'Support' : 'User'} · {m.created_at ? new Date(m.created_at).toLocaleString() : ''}
                  </div>
                  <div className="whitespace-pre-wrap break-words">{m.body}</div>
                </div>
              ))}
            </div>

            {activeThread.status === 'open' ? (
              <footer className="px-4 py-3 border-t flex gap-2" style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}>
                <input
                  value={replyBody}
                  onChange={(e) => setReplyBody(e.target.value)}
                  maxLength={4000}
                  placeholder="Reply…"
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleReply(); } }}
                  className="flex-1 rounded border px-3 py-2 bg-transparent text-sm"
                  style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}
                />
                <button
                  type="button"
                  onClick={handleReply}
                  disabled={sending || !replyBody.trim()}
                  className="px-3 rounded bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
                >
                  <Send size={16} />
                </button>
              </footer>
            ) : (
              <footer className="px-4 py-3 border-t text-xs opacity-60 text-center" style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}>
                Thread resolved. Reopen to reply.
              </footer>
            )}
          </>
        )}
      </section>
    </div>
  );
}

interface AuditEntry {
  id: string;
  action: string;
  user_id?: string | null;
  resource_type?: string | null;
  resource_id?: string | null;
  created_at?: string | null;
}

function AuditLogView() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/admin/audit-log');
        const payload = res.data as { data?: { entries?: AuditEntry[] } };
        setEntries(payload.data?.entries ?? []);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'Failed to load audit log');
      }
    })();
  }, []);

  if (error) return <div className="text-sm text-red-400">{error}</div>;
  if (entries.length === 0) return <div className="text-sm opacity-60">No audit entries.</div>;

  return (
    <div className="border rounded overflow-hidden" style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}>
      <table className="w-full text-sm">
        <thead className="text-left text-xs opacity-70">
          <tr>
            <th className="px-3 py-2">When</th>
            <th className="px-3 py-2">Action</th>
            <th className="px-3 py-2">User</th>
            <th className="px-3 py-2">Resource</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e) => (
            <tr key={e.id} className="border-t" style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}>
              <td className="px-3 py-2 text-xs opacity-70">{e.created_at ? new Date(e.created_at).toLocaleString() : '—'}</td>
              <td className="px-3 py-2">{e.action}</td>
              <td className="px-3 py-2 text-xs">{e.user_id ?? '—'}</td>
              <td className="px-3 py-2 text-xs">{e.resource_type ? `${e.resource_type}:${e.resource_id ?? '—'}` : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface RegistryEntry {
  id: string;
  purpose: string;
  provider: string;
  model_name: string;
  prompt_version: string;
  status: string;
  validation_status: string;
  created_at?: string | null;
}

function ModelRegistryView() {
  const [entries, setEntries] = useState<RegistryEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/admin/model-registry');
        const payload = res.data as { data?: { entries?: RegistryEntry[] } };
        setEntries(payload.data?.entries ?? []);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'Failed to load registry');
      }
    })();
  }, []);

  const grouped = useMemo(() => {
    const by: Record<string, RegistryEntry[]> = {};
    for (const e of entries) {
      (by[e.purpose] ??= []).push(e);
    }
    return by;
  }, [entries]);

  if (error) return <div className="text-sm text-red-400">{error}</div>;
  if (entries.length === 0) return <div className="text-sm opacity-60">No registry entries.</div>;

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([purpose, items]) => (
        <div key={purpose}>
          <h3 className="text-sm font-medium mb-2">{purpose}</h3>
          <div className="border rounded overflow-hidden" style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}>
            <table className="w-full text-sm">
              <thead className="text-left text-xs opacity-70">
                <tr>
                  <th className="px-3 py-2">Model</th>
                  <th className="px-3 py-2">Prompt</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Validation</th>
                </tr>
              </thead>
              <tbody>
                {items.map((e) => (
                  <tr key={e.id} className="border-t" style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}>
                    <td className="px-3 py-2">{e.provider} / {e.model_name}</td>
                    <td className="px-3 py-2 text-xs">{e.prompt_version}</td>
                    <td className="px-3 py-2 text-xs">{e.status}</td>
                    <td className="px-3 py-2 text-xs">{e.validation_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
