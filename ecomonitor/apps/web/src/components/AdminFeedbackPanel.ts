/**
 * AdminFeedbackPanel — admin inbox for feedback threads.
 *
 * mountAdminFeedbackPanel(host) renders a two-column inbox/detail view into
 * the given container. Access is gated by auth-state.isAdmin; if the current
 * user is not an admin the panel renders a 403 placeholder.
 */
import { getAuthState, subscribeAuthState } from '@/services/auth-state';
import {
  listFeedbackThreads,
  getFeedbackThread,
  postFeedbackMessage,
  setFeedbackThreadStatus,
  type FeedbackMessage,
  type FeedbackThread,
} from '@/services/feedback-api';

const INBOX_POLL_MS = 10_000;
const THREAD_POLL_MS = 3_000;

function formatTime(iso: string | undefined | null): string {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return '';
  }
}

type ElAttrs = {
  className?: string;
  textContent?: string;
  placeholder?: string;
  maxLength?: number;
  disabled?: boolean;
  dataset?: Record<string, string>;
  onClick?: (e: Event) => void;
};

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: ElAttrs = {},
  children: Array<HTMLElement | string | null | undefined> = [],
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (attrs.className) node.className = attrs.className;
  if (attrs.textContent !== undefined) node.textContent = attrs.textContent;
  if (attrs.placeholder && 'placeholder' in node) {
    (node as HTMLInputElement).placeholder = attrs.placeholder;
  }
  if (attrs.maxLength !== undefined && 'maxLength' in node) {
    (node as HTMLInputElement).maxLength = attrs.maxLength;
  }
  if (attrs.disabled && 'disabled' in node) {
    (node as HTMLButtonElement).disabled = attrs.disabled;
  }
  if (attrs.dataset) {
    for (const [k, v] of Object.entries(attrs.dataset)) node.dataset[k] = v;
  }
  if (attrs.onClick) node.addEventListener('click', attrs.onClick);
  for (const child of children) {
    if (child == null) continue;
    if (typeof child === 'string') node.appendChild(document.createTextNode(child));
    else node.appendChild(child);
  }
  return node;
}

export function mountAdminFeedbackPanel(container: HTMLElement): () => void {
  let threads: FeedbackThread[] = [];
  let messages: FeedbackMessage[] = [];
  let activeThreadId: string | null = null;
  let filter: 'all' | 'open' | 'resolved' = 'open';
  let error: string | null = null;
  let sending = false;
  let loading = true;

  let inboxTimer: number | null = null;
  let threadTimer: number | null = null;

  const clear = () => {
    while (container.firstChild) container.removeChild(container.firstChild);
  };

  const refreshThreads = async () => {
    try {
      const res = await listFeedbackThreads();
      threads = res.threads;
      error = null;
    } catch (e) {
      error = (e as Error).message;
    }
    loading = false;
  };

  const refreshMessages = async () => {
    if (!activeThreadId) return;
    try {
      const res = await getFeedbackThread(activeThreadId);
      messages = res.messages;
      threads = threads.map((t) => (t.thread_id === res.thread.thread_id ? res.thread : t));
    } catch (e) {
      error = (e as Error).message;
    }
  };

  const selectThread = async (threadId: string) => {
    activeThreadId = threadId;
    messages = [];
    render();
    await refreshMessages();
    render();
    if (threadTimer !== null) window.clearInterval(threadTimer);
    threadTimer = window.setInterval(async () => {
      await refreshMessages();
      render();
    }, THREAD_POLL_MS);
  };

  const toggleStatus = async () => {
    const thread = threads.find((t) => t.thread_id === activeThreadId);
    if (!thread) return;
    try {
      const next = thread.status === 'open' ? 'resolved' : 'open';
      await setFeedbackThreadStatus(thread.thread_id, next);
      await refreshThreads();
      render();
    } catch (e) {
      error = (e as Error).message;
      render();
    }
  };

  const submitReply = async () => {
    if (!activeThreadId) return;
    const body = (container.querySelector<HTMLTextAreaElement>('[data-admin-input="reply"]')?.value ?? '').trim();
    if (!body) return;
    sending = true;
    render();
    try {
      await postFeedbackMessage(activeThreadId, body);
      await refreshMessages();
    } catch (e) {
      error = (e as Error).message;
    } finally {
      sending = false;
      render();
    }
  };

  const render = () => {
    clear();
    const auth = getAuthState();
    if (!auth.user) {
      container.appendChild(el('div', { className: 'admin-empty', textContent: 'Sign in required.' }));
      return;
    }
    if (!auth.user.isAdmin) {
      container.appendChild(el('div', { className: 'admin-empty', textContent: 'Admins only.' }));
      return;
    }
    if (loading) {
      container.appendChild(el('div', { className: 'admin-empty', textContent: 'Loading inbox…' }));
      return;
    }

    const filtered =
      filter === 'all' ? threads : threads.filter((t) => t.status === filter);

    const header = el('div', { className: 'admin-header' }, [
      el('h2', { textContent: 'Feedback inbox' }),
      el(
        'div',
        { className: 'admin-filter' },
        (['open', 'resolved', 'all'] as const).map((f) =>
          el('button', {
            className: `admin-chip${filter === f ? ' active' : ''}`,
            textContent: f,
            onClick: () => {
              filter = f;
              render();
            },
          }),
        ),
      ),
    ]);
    container.appendChild(header);

    if (error) {
      container.appendChild(el('div', { className: 'admin-error', textContent: error }));
    }

    const grid = el('div', { className: 'admin-grid' });

    const inbox = el('div', { className: 'admin-inbox' });
    inbox.appendChild(el('h3', { textContent: `${filtered.length} threads` }));
    if (filtered.length === 0) {
      inbox.appendChild(el('p', { className: 'admin-empty', textContent: 'No threads.' }));
    } else {
      const list = el('ul', { className: 'admin-list' });
      for (const t of filtered) {
        list.appendChild(
          el(
            'li',
            {},
            [
              el(
                'button',
                {
                  className: `admin-thread${activeThreadId === t.thread_id ? ' active' : ''}`,
                  onClick: () => void selectThread(t.thread_id),
                },
                [
                  el('div', { className: 'admin-thread-row' }, [
                    el('span', { className: 'admin-thread-subject', textContent: t.subject }),
                    el('span', {
                      className: `admin-thread-status admin-status-${t.status}`,
                      textContent: t.status,
                    }),
                  ]),
                  el('span', {
                    className: 'admin-thread-meta',
                    textContent: formatTime(t.last_activity_at),
                  }),
                ],
              ),
            ],
          ),
        );
      }
      inbox.appendChild(list);
    }
    grid.appendChild(inbox);

    const detail = el('div', { className: 'admin-detail' });
    const activeThread = threads.find((t) => t.thread_id === activeThreadId) ?? null;
    if (!activeThread) {
      detail.appendChild(el('p', { className: 'admin-empty', textContent: 'Pick a thread to reply.' }));
    } else {
      detail.appendChild(
        el('div', { className: 'admin-detail-header' }, [
          el('div', {}, [
            el('h3', { textContent: activeThread.subject }),
            el('span', {
              className: 'admin-thread-meta',
              textContent: `Status: ${activeThread.status}`,
            }),
          ]),
          el('button', {
            className: 'admin-cta',
            textContent: activeThread.status === 'open' ? 'Mark resolved' : 'Reopen',
            onClick: () => void toggleStatus(),
          }),
        ]),
      );
      const stream = el('div', { className: 'admin-stream' });
      if (messages.length === 0) {
        stream.appendChild(el('p', { className: 'admin-empty', textContent: 'No messages.' }));
      } else {
        for (const m of messages) {
          stream.appendChild(
            el('div', { className: `admin-msg admin-msg-${m.author_role}` }, [
              el('div', { className: 'admin-msg-body', textContent: m.body }),
              el('div', {
                className: 'admin-msg-meta',
                textContent: `${m.author_role} · ${formatTime(m.created_at)}`,
              }),
            ]),
          );
        }
      }
      detail.appendChild(stream);

      if (activeThread.status === 'open') {
        detail.appendChild(
          el('div', { className: 'admin-composer' }, [
            el('textarea', {
              className: 'admin-textarea',
              placeholder: 'Write a reply…',
              maxLength: 4000,
              dataset: { adminInput: 'reply' },
            }),
            el('button', {
              className: 'admin-cta',
              textContent: sending ? 'Sending…' : 'Send reply',
              disabled: sending,
              onClick: () => void submitReply(),
            }),
          ]),
        );
      }
    }
    grid.appendChild(detail);

    container.appendChild(grid);
  };

  void refreshThreads().then(render);
  inboxTimer = window.setInterval(async () => {
    await refreshThreads();
    render();
  }, INBOX_POLL_MS);

  const authUnsub = subscribeAuthState(() => render());

  return () => {
    if (inboxTimer !== null) window.clearInterval(inboxTimer);
    if (threadTimer !== null) window.clearInterval(threadTimer);
    authUnsub();
  };
}
