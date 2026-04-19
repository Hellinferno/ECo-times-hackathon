export const config = { runtime: 'edge' };

import { ConvexHttpClient } from 'convex/browser';
import { getCorsHeaders, isDisallowedOrigin } from './_cors.js';
import { getClientIp } from './_turnstile.js';
import { jsonResponse } from './_json-response.js';
import { createIpRateLimiter } from './_ip-rate-limit.js';
import { validateBearerToken } from '../apps/web/server/auth-session.ts';

const MAX_SUBJECT = 200;
const MAX_BODY = 4000;

// Users may post 20 messages per minute per IP.
const rateLimiter = createIpRateLimiter({ limit: 20, windowMs: 60_000 });

function str(value, max) {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  return trimmed.length > max ? trimmed.slice(0, max) : trimmed;
}

async function readJson(req) {
  try {
    return await req.json();
  } catch {
    return null;
  }
}

function getThreadIdFromUrl(url) {
  const id = url.searchParams.get('thread');
  return id && id.length > 0 ? id : null;
}

export default async function handler(req) {
  if (isDisallowedOrigin(req)) {
    return jsonResponse({ error: 'Origin not allowed' }, 403);
  }

  const cors = getCorsHeaders(req, 'GET, POST, PATCH, OPTIONS');

  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: cors });
  }

  const authHeader = req.headers.get('authorization') || '';
  if (!authHeader.toLowerCase().startsWith('bearer ')) {
    return jsonResponse({ error: 'Missing bearer token' }, 401, cors);
  }
  const session = await validateBearerToken(authHeader.slice(7));
  if (!session.valid || !session.userId) {
    return jsonResponse({ error: 'Invalid session' }, 401, cors);
  }

  const ip = getClientIp(req);
  if (rateLimiter.isRateLimited(ip)) {
    return jsonResponse({ error: 'Too many requests' }, 429, cors);
  }

  const convexUrl = process.env.CONVEX_URL;
  if (!convexUrl) {
    return jsonResponse({ error: 'Service unavailable' }, 503, cors);
  }
  const convex = new ConvexHttpClient(convexUrl);
  const url = new URL(req.url);
  const threadId = getThreadIdFromUrl(url);
  const { userId, isAdmin = false } = session;

  try {
    if (req.method === 'GET' && !threadId) {
      const filter = url.searchParams.get('status');
      const status = filter === 'open' || filter === 'resolved' ? filter : undefined;
      const threads = await convex.query('feedback:listThreads', {
        userId,
        isAdmin,
        status,
      });
      return jsonResponse({ threads, total: threads.length }, 200, cors);
    }

    if (req.method === 'GET' && threadId) {
      const detail = await convex.query('feedback:listMessages', {
        threadId,
        userId,
        isAdmin,
      });
      return jsonResponse(detail, 200, cors);
    }

    if (req.method === 'POST' && !threadId) {
      const body = await readJson(req);
      if (!body) return jsonResponse({ error: 'Invalid JSON' }, 400, cors);
      const subject = str(body.subject, MAX_SUBJECT);
      const message = str(body.body, MAX_BODY);
      if (!subject || !message) {
        return jsonResponse({ error: 'subject and body are required' }, 400, cors);
      }
      const result = await convex.mutation('feedback:createThread', {
        userId,
        isAdmin,
        subject,
        body: message,
      });
      return jsonResponse(result, 201, cors);
    }

    if (req.method === 'POST' && threadId) {
      const body = await readJson(req);
      if (!body) return jsonResponse({ error: 'Invalid JSON' }, 400, cors);
      const message = str(body.body, MAX_BODY);
      if (!message) return jsonResponse({ error: 'body is required' }, 400, cors);
      const result = await convex.mutation('feedback:appendMessage', {
        threadId,
        userId,
        isAdmin,
        body: message,
      });
      return jsonResponse(result, 201, cors);
    }

    if (req.method === 'PATCH' && threadId) {
      if (!isAdmin) return jsonResponse({ error: 'Admin only' }, 403, cors);
      const body = await readJson(req);
      const status = body?.status === 'resolved' ? 'resolved' : body?.status === 'open' ? 'open' : null;
      if (!status) return jsonResponse({ error: 'status must be open|resolved' }, 400, cors);
      const result = await convex.mutation('feedback:setStatus', {
        threadId,
        isAdmin,
        status,
      });
      return jsonResponse(result, 200, cors);
    }

    return jsonResponse({ error: 'Method not allowed' }, 405, cors);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error('[feedback] error:', msg);
    const status = msg.includes('Not allowed') ? 403 : msg.includes('not found') ? 404 : 400;
    return jsonResponse({ error: msg }, status, cors);
  }
}
