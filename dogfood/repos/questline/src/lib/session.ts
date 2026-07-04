// Session helper — resolves the current user from the request cookie.
// (Auth shipped in Stage 1; this is the read side used by server comps.)

import { cookies } from "next/headers";
import { prisma } from "./db";

export interface SessionUser {
  id: string;
  plan: "FREE" | "PRO";
  timezone: string;
}

export async function getSessionUser(): Promise<SessionUser | null> {
  const token = cookies().get("ql_session")?.value;
  if (!token) return null;

  const session = await prisma.session?.findUnique?.({
    where: { token },
    include: { user: true },
  });
  if (!session?.user) return null;

  const { id, plan, timezone } = session.user;
  return { id, plan, timezone };
}
