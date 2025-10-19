import { TRPCError } from "@trpc/server";
import { z } from "zod";

import type { ChatEvent, ChatMessage, ChatSession } from "@/lib/types/chat";
import type { TrpcContext } from "../context";
import { createTRPCRouter, publicProcedure } from "../trpc";

const BACKEND_API_BASE =
  process.env.BACKEND_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000/api";

async function backendFetch<TReturn>(
  ctx: TrpcContext,
  path: string,
  init?: RequestInit,
): Promise<TReturn> {
  const url = `${BACKEND_API_BASE}${path}`;
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type") && init?.body) {
    headers.set("Content-Type", "application/json");
  }
  if (ctx.headers) {
    const forwardHeaders = new Headers(ctx.headers);
    const auth = forwardHeaders.get("authorization");
    if (auth && !headers.has("authorization")) {
      headers.set("authorization", auth);
    }
  }

  const response = await fetch(url, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new TRPCError({
      code: "BAD_REQUEST",
      message: message || `Backend request failed with status ${response.status}`,
    });
  }

  if (response.status === 204) {
    return null as TReturn;
  }

  return (await response.json()) as TReturn;
}

export const chatRouter = createTRPCRouter({
  createSession: publicProcedure
    .input(
      z.object({
        projectId: z.number().int().positive().optional(),
        title: z.string().max(200).optional(),
      }),
    )
    .mutation(async ({ ctx, input }) => {
      return backendFetch<ChatSession>(ctx, "/chat/sessions", {
        method: "POST",
        body: JSON.stringify({
          project_id: input.projectId,
          title: input.title,
        }),
      });
    }),

  listSessions: publicProcedure
    .input(
      z
        .object({
          projectId: z.number().int().positive().optional(),
          status: z.enum(["active", "closed", "archived"]).optional(),
          limit: z.number().int().min(1).max(100).optional(),
          offset: z.number().int().min(0).optional(),
        })
        .optional(),
    )
    .query(async ({ ctx, input }) => {
      const params = new URLSearchParams();
      if (input?.projectId) params.set("project_id", String(input.projectId));
      if (input?.status) params.set("status", input.status);
      if (input?.limit) params.set("limit", String(input.limit));
      if (input?.offset) params.set("offset", String(input.offset));
      const qs = params.toString();
      const path = `/chat/sessions${qs ? `?${qs}` : ""}`;
      return backendFetch<{ items: ChatSession[] }>(ctx, path);
    }),

  getSession: publicProcedure
    .input(
      z.object({
        sessionId: z.number().int().positive(),
      }),
    )
    .query(async ({ ctx, input }) => {
      return backendFetch<ChatSession>(ctx, `/chat/sessions/${input.sessionId}`);
    }),

  listMessages: publicProcedure
    .input(
      z.object({
        sessionId: z.number().int().positive(),
        limit: z.number().int().min(1).max(200).optional(),
        offset: z.number().int().min(0).optional(),
      }),
    )
    .query(async ({ ctx, input }) => {
      const params = new URLSearchParams();
      if (input.limit) params.set("limit", String(input.limit));
      if (input.offset) params.set("offset", String(input.offset));
      const qs = params.toString();
      const path = `/chat/sessions/${input.sessionId}/messages${qs ? `?${qs}` : ""}`;
      return backendFetch<{ items: ChatMessage[] }>(ctx, path);
    }),

  sendMessage: publicProcedure
    .input(
      z.object({
        sessionId: z.number().int().positive(),
        content: z.string().min(1).max(4000),
      }),
    )
    .mutation(async ({ ctx, input }) => {
      return backendFetch<{
        user_message: ChatMessage;
        assistant_message: ChatMessage;
        events: ChatEvent[];
      }>(ctx, `/chat/sessions/${input.sessionId}/messages`, {
        method: "POST",
        body: JSON.stringify({ content: input.content }),
      });
    }),

  listEvents: publicProcedure
    .input(
      z.object({
        sessionId: z.number().int().positive(),
        after: z.number().int().min(0).optional(),
        limit: z.number().int().min(1).max(200).optional(),
      }),
    )
    .query(async ({ ctx, input }) => {
      const params = new URLSearchParams();
      if (input.after !== undefined) params.set("after", String(input.after));
      if (input.limit) params.set("limit", String(input.limit));
      const qs = params.toString();
      const path = `/chat/sessions/${input.sessionId}/events${qs ? `?${qs}` : ""}`;
      return backendFetch<{ items: ChatEvent[] }>(ctx, path);
    }),
});
