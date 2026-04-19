/**
 * Feedback threads and messages — Convex module.
 *
 * Authorization is enforced by the edge handler in `api/feedback.js` which
 * validates the Clerk JWT and passes a trusted userId + isAdmin flag. Callers
 * here are expected to have already performed that check.
 */
import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

const MAX_SUBJECT = 200;
const MAX_BODY = 4000;

function clamp(str: string, max: number): string {
  return str.length > max ? str.slice(0, max) : str;
}

export const listThreads = query({
  args: {
    userId: v.string(),
    isAdmin: v.boolean(),
    status: v.optional(v.union(v.literal("open"), v.literal("resolved"))),
  },
  handler: async (ctx, { userId, isAdmin, status }) => {
    let threads;
    if (isAdmin) {
      threads = await ctx.db
        .query("feedbackThreads")
        .withIndex("by_activity")
        .order("desc")
        .take(200);
    } else {
      threads = await ctx.db
        .query("feedbackThreads")
        .withIndex("by_user_activity", (q) => q.eq("createdByUserId", userId))
        .order("desc")
        .take(200);
    }
    if (status) threads = threads.filter((t) => t.status === status);
    return threads.map((t) => ({
      thread_id: t._id,
      subject: t.subject,
      status: t.status,
      created_by_user_id: t.createdByUserId,
      created_at: new Date(t.createdAt).toISOString(),
      last_activity_at: new Date(t.lastActivityAt).toISOString(),
    }));
  },
});

export const listMessages = query({
  args: {
    threadId: v.id("feedbackThreads"),
    userId: v.string(),
    isAdmin: v.boolean(),
  },
  handler: async (ctx, { threadId, userId, isAdmin }) => {
    const thread = await ctx.db.get(threadId);
    if (!thread) throw new Error("Thread not found");
    if (!isAdmin && thread.createdByUserId !== userId) {
      throw new Error("Not allowed");
    }
    const messages = await ctx.db
      .query("feedbackMessages")
      .withIndex("by_thread", (q) => q.eq("threadId", threadId))
      .order("asc")
      .collect();
    return {
      thread: {
        thread_id: thread._id,
        subject: thread.subject,
        status: thread.status,
        created_by_user_id: thread.createdByUserId,
        created_at: new Date(thread.createdAt).toISOString(),
        last_activity_at: new Date(thread.lastActivityAt).toISOString(),
      },
      messages: messages.map((m) => ({
        message_id: m._id,
        thread_id: m.threadId,
        author_user_id: m.authorUserId,
        author_role: m.authorRole,
        body: m.body,
        created_at: new Date(m.createdAt).toISOString(),
      })),
    };
  },
});

export const createThread = mutation({
  args: {
    userId: v.string(),
    isAdmin: v.boolean(),
    subject: v.string(),
    body: v.string(),
  },
  handler: async (ctx, { userId, isAdmin, subject, body }) => {
    const subjectClean = clamp(subject.trim(), MAX_SUBJECT);
    const bodyClean = clamp(body.trim(), MAX_BODY);
    if (!subjectClean || !bodyClean) throw new Error("Subject and body required");

    const now = Date.now();
    const threadId = await ctx.db.insert("feedbackThreads", {
      createdByUserId: userId,
      subject: subjectClean,
      status: "open",
      createdAt: now,
      lastActivityAt: now,
    });
    const messageId = await ctx.db.insert("feedbackMessages", {
      threadId,
      authorUserId: userId,
      authorRole: isAdmin ? "admin" : "user",
      body: bodyClean,
      createdAt: now,
    });
    return { threadId, messageId };
  },
});

export const appendMessage = mutation({
  args: {
    threadId: v.id("feedbackThreads"),
    userId: v.string(),
    isAdmin: v.boolean(),
    body: v.string(),
  },
  handler: async (ctx, { threadId, userId, isAdmin, body }) => {
    const thread = await ctx.db.get(threadId);
    if (!thread) throw new Error("Thread not found");
    if (!isAdmin && thread.createdByUserId !== userId) {
      throw new Error("Not allowed");
    }
    if (thread.status !== "open") throw new Error("Thread is resolved");

    const bodyClean = clamp(body.trim(), MAX_BODY);
    if (!bodyClean) throw new Error("Body required");

    const now = Date.now();
    const messageId = await ctx.db.insert("feedbackMessages", {
      threadId,
      authorUserId: userId,
      authorRole: isAdmin ? "admin" : "user",
      body: bodyClean,
      createdAt: now,
    });
    await ctx.db.patch(threadId, { lastActivityAt: now });
    return { messageId };
  },
});

export const setStatus = mutation({
  args: {
    threadId: v.id("feedbackThreads"),
    isAdmin: v.boolean(),
    status: v.union(v.literal("open"), v.literal("resolved")),
  },
  handler: async (ctx, { threadId, isAdmin, status }) => {
    if (!isAdmin) throw new Error("Admin only");
    const thread = await ctx.db.get(threadId);
    if (!thread) throw new Error("Thread not found");
    await ctx.db.patch(threadId, {
      status,
      lastActivityAt: Date.now(),
    });
    return { status };
  },
});
