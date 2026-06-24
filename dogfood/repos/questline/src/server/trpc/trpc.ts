// Minimal tRPC setup: context, base router, and a protected procedure
// that requires an authenticated user.

import { initTRPC, TRPCError } from "@trpc/server";
import superjson from "superjson";

export interface SessionUser {
  id: string;
  plan: "FREE" | "PRO";
  timezone: string;
}

export interface Context {
  user: SessionUser | null;
}

const t = initTRPC.context<Context>().create({ transformer: superjson });

export const router = t.router;
export const publicProcedure = t.procedure;

export const protectedProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.user) {
    throw new TRPCError({ code: "UNAUTHORIZED" });
  }
  return next({ ctx: { ...ctx, user: ctx.user } });
});
