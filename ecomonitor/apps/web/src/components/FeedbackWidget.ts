/**
 * Feedback widget — floating button + drawer for posting feedback.
 *
 * Mount once at app startup via mountFeedbackWidget(). The drawer hides when
 * unauthenticated and hydrates once the Clerk user resolves.
 *
 * All DOM is built with document.createElement + textContent (no innerHTML)
 * so user-supplied subject/body strings cannot inject markup.
 */
import '@/styles/feedback-widget.css';
import { subscribeAuthState, getAuthState } from '@/services/auth-state';
import {
  listFeedbackThreads,
  createFeedbackThread,
  getFeedbackThread,
  postFeedbackMessage,
  type FeedbackMessage,
  type FeedbackThread,
} from '@/services/feedback-api';

type View = 'list' | 'thread' | 'new';

const WIDGET_ID = 'feedback-widget-root';
const POLL_MS = 3000;

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
  type?: string;
  placeholder?: string;
  maxLength?: number;
  ariaLabel?: string;
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
  if (attrs.ariaLabel) node.setAttribute('aria-label', attrs.ariaLabel);
  if (attrs.type && 'type' in node) (node as HTMLInputElement).type = attrs.type;
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
    for (const [k, v] of Object.entries(attrs.dataset)) {
      node.dataset[k] = v;
    }
  }
  if (attrs.onClick) node.addEventListener('click', attrs.onClick);
  for (const child of children) {
    if (child == null) continue;
    if (typeof child === 'string') node.appendChild(document.createTextNode(child));
    else node.appendChild(child);
  }
  return node;
}

interface State {
  open: boolean;
  view: View;
  threads: FeedbackThread[];
  activeThreadId: string | null;
  messages: FeedbackMessage[];
  error: string | null;
  sending: boolean;
}

export function mountFeedbackWidget(): void {
  if (document.getElementById(WIDGET_ID)) return;

  const host = document.createElement('div');
  host.id = WIDGET_ID;
  document.body.appendChild(host);

  const state: State = {
    open: false,
    view: 'list',
    threads: [],
    activeThreadId: null,
    messages: [],
    error: null,
    sending: false,
  };
  let pollTimer: number | null = null;

  const clear = () => {
    while (host.firstChild) host.removeChild(host.firstChild);
  };

  const toggle = async () => {
    state.open = !state.open;
    if (state.open) {
      state.view = 'list';
      state.activeThreadId = null;
      await refreshThreads();
    } else {
      stopPoll();
    }
    render();
  };

  const refreshThreads = async () => {
    try {
      const res = await listFeedbackThreads();
      state.threads = res.threads;
      state.error = null;
    } catch (e) {
      state.error = (e as Error).message;
    }
  };

  const refreshMessages = async () => {
    if (!state.activeThreadId) return;
    try {
      const res = await getFeedbackThread(state.activeThreadId);
      state.messages = res.messages;
      state.threads = state.threads.map((t) =>
        t.thread_id === res.thread.thread_id ? res.thread : t,
      );
    } catch (e) {
      state.error = (e as Error).message;
    }
  };

  const startPoll = () => {
    stopPoll();
    if (!state.open || state.view !== 'thread') return;
    pollTimer = window.setInterval(async () => {
      await refreshMessages();
      render();
    }, POLL_MS);
  };
  const stopPoll = () => {
    if (pollTimer !== null) {
      window.clearInterval(pollTimer);
      pollTimer = null;
    }
  };

  const submitNew = async () => {
    const subject = (host.querySelector<HTMLInputElement>('[data-fw-input="subject"]')?.value ?? '').trim();
    const body = (host.querySelector<HTMLTextAreaElement>('[data-fw-input="body"]')?.value ?? '').trim();
    if (!subject || !body) return;
    state.sending = true;
    state.error = null;
    render();
    try {
      const res = await createFeedbackThread(subject, body);
      state.activeThreadId = res.threadId;
      state.view = 'thread';
      await refreshThreads();
      await refreshMessages();
      startPoll();
    } catch (e) {
      state.error = (e as Error).message;
    } finally {
      state.sending = false;
      render();
    }
  };

  const submitReply = async () => {
    const body = (host.querySelector<HTMLTextAreaElement>('[data-fw-input="reply"]')?.value ?? '').trim();
    if (!body || !state.activeThreadId) return;
    state.sending = true;
    state.error = null;
    render();
    try {
      await postFeedbackMessage(state.activeThreadId, body);
      await refreshMessages();
    } catch (e) {
      state.error = (e as Error).message;
    } finally {
      state.sending = false;
      render();
    }
  };

  const selectThread = async (threadId: string) => {
    state.activeThreadId = threadId;
    state.view = 'thread';
    state.messages = [];
    render();
    await refreshMessages();
    render();
    startPoll();
  };

  const back = async () => {
    state.view = 'list';
    state.activeThreadId = null;
    state.messages = [];
    stopPoll();
    await refreshThreads();
    render();
  };

  const render = () => {
    clear();
    const authed = Boolean(getAuthState().user);
    if (!authed) return;

    const button = el(
      'button',
      {
        className: 'fw-button',
        ariaLabel: 'Open feedback',
        textContent: state.open ? '✕' : '💬',
        onClick: () => void toggle(),
      },
    );
    host.appendChild(button);

    if (!state.open) return;

    const drawer = el('div', { className: 'fw-drawer' });

    const headerBar = el('header', { className: 'fw-header' }, [
      el('div', {}, [
        state.view !== 'list'
          ? el('button', {
              className: 'fw-icon',
              ariaLabel: 'Back',
              textContent: '←',
              onClick: () => void back(),
            })
          : null,
        el('span', { className: 'fw-title', textContent: 'Feedback' }),
      ]),
      el('button', {
        className: 'fw-icon',
        ariaLabel: 'Close',
        textContent: '✕',
        onClick: () => void toggle(),
      }),
    ]);
    drawer.appendChild(headerBar);

    if (state.error) {
      drawer.appendChild(el('div', { className: 'fw-error', textContent: state.error }));
    }

    if (state.view === 'list') {
      const list = el('div', { className: 'fw-scroll' });
      if (state.threads.length === 0) {
        list.appendChild(el('p', { className: 'fw-empty', textContent: 'No threads yet. Start one below.' }));
      } else {
        for (const t of state.threads) {
          const threadBtn = el(
            'button',
            {
              className: 'fw-thread',
              onClick: () => void selectThread(t.thread_id),
            },
            [
              el('div', { className: 'fw-thread-row' }, [
                el('span', { className: 'fw-thread-subject', textContent: t.subject }),
                el('span', {
                  className: `fw-thread-status fw-status-${t.status}`,
                  textContent: t.status,
                }),
              ]),
              el('span', { className: 'fw-thread-meta', textContent: formatTime(t.last_activity_at) }),
            ],
          );
          list.appendChild(threadBtn);
        }
      }
      drawer.appendChild(list);
      drawer.appendChild(
        el('footer', { className: 'fw-footer' }, [
          el('button', {
            className: 'fw-cta',
            textContent: 'Start new thread',
            onClick: () => {
              state.view = 'new';
              render();
            },
          }),
        ]),
      );
    } else if (state.view === 'new') {
      const form = el('div', { className: 'fw-form' }, [
        el('input', {
          className: 'fw-input',
          placeholder: 'Subject',
          maxLength: 200,
          dataset: { fwInput: 'subject' },
        }),
        el('textarea', {
          className: 'fw-textarea',
          placeholder: 'How can we help?',
          maxLength: 4000,
          dataset: { fwInput: 'body' },
        }),
        el('button', {
          className: 'fw-cta',
          textContent: state.sending ? 'Sending…' : 'Send',
          disabled: state.sending,
          onClick: () => void submitNew(),
        }),
      ]);
      drawer.appendChild(form);
    } else {
      const thread = state.threads.find((t) => t.thread_id === state.activeThreadId) ?? null;
      const scroll = el('div', { className: 'fw-scroll fw-thread-scroll' });
      if (state.messages.length === 0) {
        scroll.appendChild(el('p', { className: 'fw-empty', textContent: 'No messages.' }));
      } else {
        for (const m of state.messages) {
          scroll.appendChild(
            el('div', { className: `fw-msg fw-msg-${m.author_role}` }, [
              el('div', { className: 'fw-msg-body', textContent: m.body }),
              el('div', {
                className: 'fw-msg-meta',
                textContent: `${m.author_role} · ${formatTime(m.created_at)}`,
              }),
            ]),
          );
        }
      }
      drawer.appendChild(scroll);

      const footer = el('footer', { className: 'fw-footer' });
      if (thread?.status === 'open') {
        const composer = el('div', { className: 'fw-composer' }, [
          el('textarea', {
            className: 'fw-textarea',
            placeholder: 'Write a reply…',
            maxLength: 4000,
            dataset: { fwInput: 'reply' },
          }),
          el('button', {
            className: 'fw-cta',
            textContent: state.sending ? 'Sending…' : 'Reply',
            disabled: state.sending,
            onClick: () => void submitReply(),
          }),
        ]);
        footer.appendChild(composer);
      } else {
        footer.appendChild(
          el('div', { className: 'fw-muted', textContent: 'Thread is resolved.' }),
        );
      }
      drawer.appendChild(footer);
    }

    host.appendChild(drawer);
  };

  subscribeAuthState(() => render());
  render();
}
