import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  registrations: defineTable({
    email: v.string(),
    normalizedEmail: v.string(),
    registeredAt: v.number(),
    source: v.optional(v.string()),
    appVersion: v.optional(v.string()),
    referralCode: v.optional(v.string()),
    referredBy: v.optional(v.string()),
    referralCount: v.optional(v.number()),
  })
    .index("by_normalized_email", ["normalizedEmail"])
    .index("by_referral_code", ["referralCode"]),
  contactMessages: defineTable({
    name: v.string(),
    email: v.string(),
    organization: v.optional(v.string()),
    phone: v.optional(v.string()),
    message: v.optional(v.string()),
    source: v.string(),
    receivedAt: v.number(),
  }),
  counters: defineTable({
    name: v.string(),
    value: v.number(),
  }).index("by_name", ["name"]),
  feedbackThreads: defineTable({
    createdByUserId: v.string(),
    subject: v.string(),
    status: v.union(v.literal("open"), v.literal("resolved")),
    createdAt: v.number(),
    lastActivityAt: v.number(),
  })
    .index("by_user_activity", ["createdByUserId", "lastActivityAt"])
    .index("by_status_activity", ["status", "lastActivityAt"])
    .index("by_activity", ["lastActivityAt"]),
  feedbackMessages: defineTable({
    threadId: v.id("feedbackThreads"),
    authorUserId: v.string(),
    authorRole: v.union(v.literal("user"), v.literal("admin")),
    body: v.string(),
    createdAt: v.number(),
  }).index("by_thread", ["threadId", "createdAt"]),
});
