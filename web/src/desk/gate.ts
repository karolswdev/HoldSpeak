// HS-104-02 — the tool-call gate's desk side. Held proposals are
// "what needs you" items: session, tool, the REDACTED argument
// preview (sha256 + first 120 chars is all the hub ever has), age,
// and exactly two verbs. Deny carries an optional one line reason
// that rides back to the agent verbatim.
import { create } from "zustand";
import { apiFetch } from "../lib/api";

export interface GateProposal {
  id: string;
  session_key: string;
  agent: string;
  tool: string;
  args_sha256: string;
  args_head: string;
  cwd: string;
  created_at: number;
  expires_at: number;
  state: "held" | "approved" | "denied" | "expired" | "invalidated";
  decided_by: string | null;
  decided_at: number | null;
  reason: string | null;
}

interface GateStore {
  held: GateProposal[];
  loaded: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  decide: (
    id: string,
    decision: "approved" | "denied",
    reason?: string,
  ) => Promise<void>;
}

export const useGate = create<GateStore>((set, get) => ({
  held: [],
  loaded: false,
  error: null,

  refresh: async () => {
    try {
      const data = await apiFetch<{ proposals: GateProposal[] }>(
        "/api/gate/proposals?state=held",
      );
      set({ held: data.proposals ?? [], loaded: true, error: null });
    } catch (err) {
      set({ loaded: true, error: err instanceof Error ? err.message : String(err) });
    }
  },

  decide: async (id, decision, reason) => {
    try {
      await apiFetch(`/api/gate/proposals/${encodeURIComponent(id)}/decide`, {
        method: "POST",
        json: { decision, reason: reason?.trim() || undefined, actor: "owner" },
      });
    } catch {
      // A 409 means the race was lost (already decided or expired);
      // the refresh below shows the standing truth either way.
    }
    await get().refresh();
  },
}));

export function gateAge(proposal: GateProposal, nowSeconds = Date.now() / 1000): string {
  const seconds = Math.max(0, Math.round(nowSeconds - proposal.created_at));
  if (seconds < 60) return `${seconds}s`;
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
}
