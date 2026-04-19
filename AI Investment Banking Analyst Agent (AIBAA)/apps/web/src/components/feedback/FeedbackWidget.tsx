import { useCallback, useEffect, useRef, useState } from 'react';
import { MessageCircle, X, Send, ArrowLeft } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import {
  createFeedbackThread,
  fetchFeedbackMessages,
  fetchFeedbackThreads,
  postFeedbackMessage,
  type FeedbackMessage,
  type FeedbackThread,
} from '../../lib/api';

const POLL_MS = 3000;

type View = 'list' | 'thread' | 'new';

export default function FeedbackWidget() {
  const { isAuthenticated } = useAuth();
  const [open, setOpen] = useState(false);
  const [view, setView] = useState<View>('list');
  const [threads, setThreads] = useState<FeedbackThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<FeedbackMessage[]>([]);
  const [activeThread, setActiveThread] = useState<FeedbackThread | null>(null);
  const [newSubject, setNewSubject] = useState('');
  const [newBody, setNewBody] = useState('');
  const [replyBody, setReplyBody] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadThreads = useCallback(async () => {
    try {
      const list = await fetchFeedbackThreads();
      setThreads(list);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to load threads';
      setError(msg);
    }
  }, []);

  const loadMessages = useCallback(async (threadId: string) => {
    try {
      const data = await fetchFeedbackMessages(threadId);
      setActiveThread(data.thread);
      setMessages(data.messages);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to load thread';
      setError(msg);
    }
  }, []);

  useEffect(() => {
    if (!open || !isAuthenticated) return;
    if (view === 'list') {
      loadThreads();
    } else if (view === 'thread' && activeThreadId) {
      loadMessages(activeThreadId);
    }
  }, [open, isAuthenticated, view, activeThreadId, loadThreads, loadMessages]);

  useEffect(() => {
    if (!open || !isAuthenticated) return;
    if (view !== 'thread' || !activeThreadId) return;
    const interval = window.setInterval(() => loadMessages(activeThreadId), POLL_MS);
    return () => window.clearInterval(interval);
  }, [open, isAuthenticated, view, activeThreadId, loadMessages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  const handleCreate = async () => {
    if (!newSubject.trim() || !newBody.trim()) return;
    setSending(true);
    setError(null);
    try {
      const result = await createFeedbackThread(newSubject.trim(), newBody.trim());
      setActiveThreadId(result.thread.thread_id);
      setActiveThread(result.thread);
      setMessages([result.message]);
      setNewSubject('');
      setNewBody('');
      setView('thread');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to submit';
      setError(msg);
    } finally {
      setSending(false);
    }
  };

  const handleReply = async () => {
    if (!activeThreadId || !replyBody.trim()) return;
    setSending(true);
    setError(null);
    try {
      const msg = await postFeedbackMessage(activeThreadId, replyBody.trim());
      setMessages((prev) => [...prev, msg]);
      setReplyBody('');
    } catch (e: unknown) {
      const errMsg = e instanceof Error ? e.message : 'Failed to send';
      setError(errMsg);
    } finally {
      setSending(false);
    }
  };

  if (!isAuthenticated) return null;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="fixed bottom-6 right-6 z-50 flex items-center justify-center w-14 h-14 rounded-full shadow-lg bg-blue-600 hover:bg-blue-700 text-white"
        aria-label={open ? 'Close feedback' : 'Open feedback'}
      >
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </button>

      {open && (
        <div
          className="fixed bottom-24 right-6 z-50 w-[380px] max-w-[calc(100vw-3rem)] h-[560px] max-h-[calc(100vh-8rem)] rounded-lg shadow-2xl flex flex-col overflow-hidden"
          style={{ background: 'var(--bg-primary, #0f1115)', border: '1px solid var(--border-subtle, #2a2f3a)' }}
        >
          <header className="flex items-center gap-2 px-4 py-3 border-b" style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}>
            {view !== 'list' && (
              <button
                type="button"
                onClick={() => { setView('list'); setActiveThreadId(null); setActiveThread(null); }}
                className="opacity-70 hover:opacity-100"
                aria-label="Back"
              >
                <ArrowLeft size={16} />
              </button>
            )}
            <h3 className="text-sm font-medium flex-1">
              {view === 'list' && 'Feedback'}
              {view === 'thread' && (activeThread?.subject ?? 'Thread')}
              {view === 'new' && 'New feedback'}
            </h3>
            {view === 'list' && (
              <button
                type="button"
                onClick={() => setView('new')}
                className="text-xs px-2 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white"
              >
                + New
              </button>
            )}
          </header>

          <div className="flex-1 overflow-y-auto px-4 py-3 text-sm">
            {error && <div className="text-red-400 text-xs mb-2">{error}</div>}

            {view === 'list' && (
              <FeedbackThreadList
                threads={threads}
                onSelect={(id) => { setActiveThreadId(id); setView('thread'); }}
              />
            )}

            {view === 'thread' && (
              <MessageList messages={messages} />
            )}

            {view === 'new' && (
              <div className="space-y-2">
                <input
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  maxLength={200}
                  placeholder="Subject"
                  className="w-full rounded border px-3 py-2 bg-transparent text-sm"
                  style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}
                />
                <textarea
                  value={newBody}
                  onChange={(e) => setNewBody(e.target.value)}
                  maxLength={4000}
                  placeholder="What's on your mind?"
                  rows={8}
                  className="w-full rounded border px-3 py-2 bg-transparent text-sm resize-none"
                  style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}
                />
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {(view === 'thread' || view === 'new') && (
            <footer className="px-4 py-3 border-t" style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}>
              {view === 'new' ? (
                <button
                  type="button"
                  onClick={handleCreate}
                  disabled={sending || !newSubject.trim() || !newBody.trim()}
                  className="w-full rounded py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
                >
                  {sending ? 'Submitting…' : 'Submit feedback'}
                </button>
              ) : activeThread?.status === 'resolved' ? (
                <p className="text-xs opacity-60 text-center">This thread is resolved.</p>
              ) : (
                <div className="flex gap-2">
                  <input
                    value={replyBody}
                    onChange={(e) => setReplyBody(e.target.value)}
                    maxLength={4000}
                    placeholder="Type a reply…"
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleReply(); } }}
                    className="flex-1 rounded border px-3 py-2 bg-transparent text-sm"
                    style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}
                  />
                  <button
                    type="button"
                    onClick={handleReply}
                    disabled={sending || !replyBody.trim()}
                    className="px-3 rounded bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
                    aria-label="Send"
                  >
                    <Send size={16} />
                  </button>
                </div>
              )}
            </footer>
          )}
        </div>
      )}
    </>
  );
}

function FeedbackThreadList({ threads, onSelect }: { threads: FeedbackThread[]; onSelect: (id: string) => void }) {
  if (threads.length === 0) {
    return <p className="opacity-60 text-xs">No feedback yet. Start a new thread.</p>;
  }
  return (
    <ul className="space-y-2">
      {threads.map((t) => (
        <li key={t.thread_id}>
          <button
            type="button"
            onClick={() => onSelect(t.thread_id)}
            className="w-full text-left rounded border px-3 py-2 hover:bg-white/5"
            style={{ borderColor: 'var(--border-subtle, #2a2f3a)' }}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium truncate text-sm">{t.subject}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${t.status === 'open' ? 'bg-green-900/40 text-green-300' : 'bg-gray-700 text-gray-300'}`}>
                {t.status}
              </span>
            </div>
            {t.last_activity_at && (
              <div className="text-[10px] opacity-50 mt-1">{new Date(t.last_activity_at).toLocaleString()}</div>
            )}
          </button>
        </li>
      ))}
    </ul>
  );
}

function MessageList({ messages }: { messages: FeedbackMessage[] }) {
  if (messages.length === 0) return <p className="opacity-60 text-xs">No messages yet.</p>;
  return (
    <div className="space-y-3">
      {messages.map((m) => (
        <div
          key={m.message_id}
          className={`max-w-[85%] rounded px-3 py-2 text-sm ${m.author_role === 'admin' ? 'bg-blue-600/20 ml-auto' : 'bg-white/5 mr-auto'}`}
        >
          <div className="text-[10px] opacity-60 mb-1">
            {m.author_role === 'admin' ? 'Support' : 'You'} · {m.created_at ? new Date(m.created_at).toLocaleTimeString() : ''}
          </div>
          <div className="whitespace-pre-wrap break-words">{m.body}</div>
        </div>
      ))}
    </div>
  );
}
