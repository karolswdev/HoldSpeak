/* First run — the Agents step (the Conductor canvas K1a/K1b/K1c, ratified
 * 2026-10-06). The onboarding routes (Conductor K1):
 *
 *   GET  /api/onboarding/agents        claude / codex / pi / tmux readiness
 *                                      (PATH and files only; no process)
 *   POST /api/onboarding/agents/use    {agent}: the admitted kernel operation
 *                                      `agent_hooks.install`; answers with its
 *                                      operation_id and terminal receipt
 *
 * HOOKS IN is the hub's fact: after the press the face reads the list again.
 * The step is optional: no agent installed never blocks Ready. */
import { useCallback, useEffect, useState } from "react";
import { ApiError, apiFetch } from "../../lib/api";

export const AGENTS_PATH = "/api/onboarding/agents";
export const AGENTS_USE_PATH = "/api/onboarding/agents/use";

export type AgentId = "claude" | "codex" | "pi";
export type HooksState = "installed" | "partial" | "missing" | "unreadable" | "broken";

export interface AgentRow {
  id: AgentId;
  label: string;
  installed: boolean;
  path: string | null;
  version?: string | null;
  hooks: HooksState;
  signed_in: "yes" | "unknown";
  ready: boolean;
  verb: string | null;
}

export interface AgentsDetect {
  agents: AgentRow[];
  tmux: { installed: boolean; path: string | null; version?: string | null; install_hint: string | null };
}

/** The install line each agent's own docs give (Copy install). */
export const AGENT_INSTALL: Record<AgentId, string> = {
  claude: "npm install -g @anthropic-ai/claude-code",
  codex: "npm install -g @openai/codex",
  pi: "npm install -g @earendil-works/pi-coding-agent",
};
export const AGENT_GLYPH: Record<AgentId, string> = { claude: "CC", codex: "CX", pi: "PI" };
/** The host each agent's model runs on (the egress of a hand-off). pi runs
 *  on the hub's engine for coding work (the LAN box); the Hand line names
 *  that engine's own host from the preview (`engineEgress`). */
export const AGENT_HOST: Record<AgentId, string> = { claude: "API.ANTHROPIC.COM", codex: "API.OPENAI.COM", pi: "LAN" };
export const AGENT_NAME: Record<AgentId, string> = { claude: "Claude Code", codex: "Codex", pi: "pi" };

/** An agent whose hooks the press would install: on PATH, hooks not in. */
export function needsHooks(row: AgentRow): boolean {
  return row.installed && row.hooks !== "installed";
}

export interface InstallReceipt {
  agent: AgentId;
  operationId: string | null;
  code: string | null;
}

export function useAgentsStep() {
  const [detect, setDetect] = useState<AgentsDetect | null>(null);
  const [unread, setUnread] = useState("");
  const [busy, setBusy] = useState(false);
  const [checking, setChecking] = useState(false);
  const [refused, setRefused] = useState<InstallReceipt[]>([]);

  const read = useCallback(async () => {
    setChecking(true);
    try {
      setDetect(await apiFetch<AgentsDetect>(AGENTS_PATH));
      setUnread("");
    } catch (error) {
      // A token, never the request's sentence: the status when the hub
      // answered, HUB OFFLINE when it did not.
      setUnread(error instanceof ApiError ? `HTTP ${error.status}` : "HUB OFFLINE");
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    void read();
  }, [read]);

  const rows = detect?.agents ?? [];
  const pending = rows.filter(needsHooks);

  /** One press: the hooks of every installed agent that lacks them. */
  const install = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    const failed: InstallReceipt[] = [];
    for (const row of pending) {
      try {
        await apiFetch(AGENTS_USE_PATH, { method: "POST", json: { agent: row.id } });
      } catch (error) {
        const payload = error instanceof ApiError ? (error.payload as Record<string, unknown> | null) : null;
        failed.push({
          agent: row.id,
          operationId: payload && typeof payload.operation_id === "string" ? payload.operation_id : null,
          code: payload && typeof payload.code === "string" ? payload.code : "failed",
        });
      }
    }
    setRefused(failed);
    await read();
    setBusy(false);
  }, [busy, pending, read]);

  const installed = rows.filter((row) => row.installed);
  return {
    loaded: detect !== null || unread !== "",
    unread,
    rows,
    tmux: detect?.tmux ?? null,
    installed,
    pending,
    refused,
    busy,
    checking,
    // Done: at least one agent, every installed agent has its hooks in, and
    // tmux is here (every launch runs in tmux; without it none can start).
    done: detect !== null && installed.length > 0 && pending.length === 0 && Boolean(detect?.tmux.installed),
    read,
    install,
  };
}

export type AgentsStep = ReturnType<typeof useAgentsStep>;
