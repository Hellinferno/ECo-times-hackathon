/**
 * Feedback API client — thin typed wrapper around the edge /api/feedback
 * handler. Attaches the Clerk bearer token on every request.
 */
import { getClerkToken } from './clerk';

export interface FeedbackThread {
  thread_id: string;
  subject: string;
  status: 'open' | 'resolved';
  created_by_user_id: string;
  created_at: string;
  last_activity_at: string;
}

export interface FeedbackMessage {
  message_id: string;
  thread_id: string;
  author_user_id: string;
  author_role: 'user' | 'admin';
  body: string;
  created_at: string;
}

export interface FeedbackThreadDetail {
  thread: FeedbackThread;
  messages: FeedbackMessage[];
}

async function request<T>(
  path: string,
  init?: RequestInit & { json?: unknown },
): Promise<T> {
  const token = await getClerkToken();
  if (!token) throw new Error('Not signed in');

  const headers = new Headers(init?.headers);
  headers.set('Authorization', `Bearer ${token}`);
  if (init?.json !== undefined) headers.set('Content-Type', 'application/json');

  const res = await fetch(path, {
    ...init,
    headers,
    body: init?.json !== undefined ? JSON.stringify(init.json) : init?.body,
  });
  if (!res.ok) {
    const payload = (await res.json().catch(() => null)) as { error?: string } | null;
    throw new Error(payload?.error || `Request failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

export function listFeedbackThreads(options?: { status?: 'open' | 'resolved' }) {
  const qs = options?.status ? `?status=${options.status}` : '';
  return request<{ threads: FeedbackThread[]; total: number }>(`/api/feedback${qs}`);
}

export function createFeedbackThread(subject: string, body: string) {
  return request<{ threadId: string; messageId: string }>('/api/feedback', {
    method: 'POST',
    json: { subject, body },
  });
}

export function getFeedbackThread(threadId: string) {
  return request<FeedbackThreadDetail>(`/api/feedback?thread=${encodeURIComponent(threadId)}`);
}

export function postFeedbackMessage(threadId: string, body: string) {
  return request<{ messageId: string }>(
    `/api/feedback?thread=${encodeURIComponent(threadId)}`,
    { method: 'POST', json: { body } },
  );
}

export function setFeedbackThreadStatus(threadId: string, status: 'open' | 'resolved') {
  return request<{ status: 'open' | 'resolved' }>(
    `/api/feedback?thread=${encodeURIComponent(threadId)}`,
    { method: 'PATCH', json: { status } },
  );
}
