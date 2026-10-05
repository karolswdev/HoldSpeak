/* First run, option A "One screen" (owner ratified 2026-10-05) — the
 * Connections step. The onboarding routes (PR #868):
 *
 *   GET  /api/onboarding/connections        gh / acli sign-ins, read as files
 *   POST /api/onboarding/connections/use    {id}: adds the connector and runs
 *                                           its status probe (reaches the host)
 *
 * CONNECTED is the hub's fact: after every press the face reads the list
 * again, and a row says CONNECTED only when the hub says `connected`. */
import { useCallback, useEffect, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";

export const CONNECTIONS_PATH = "/api/onboarding/connections";
export const CONNECTIONS_USE_PATH = "/api/onboarding/connections/use";

export type Provider = "github" | "jira" | "confluence";

export interface ConnectionCandidate {
  id: string;
  provider: Provider;
  label: string;
  account: string;
  site: string;
  active: boolean;
  connected: boolean;
  lamp: string;
  egress_host: string;
  verb: string | null;
}

export interface ConnectionsDetect {
  candidates: ConnectionCandidate[];
  tools: { gh?: { installed: boolean }; acli?: { installed: boolean } };
}

interface UseAnswer {
  candidate: string;
  provider: Provider;
  entry?: { state?: string; error_detail?: string | null; recovery_hint?: string | null };
}

export const PROVIDER_NAME: Record<Provider, string> = { github: "GitHub", jira: "Jira", confluence: "Confluence" };
export const PROVIDER_GLYPH: Record<Provider, string> = { github: "⑂", jira: "◇", confluence: "▤" };
export const PROVIDER_TOOL: Record<Provider, "gh" | "acli"> = { github: "gh", jira: "acli", confluence: "acli" };

type RowState = { kind: "busy" } | { kind: "refused"; reason: string };

export function useConnectionsStep() {
  const [detect, setDetect] = useState<ConnectionsDetect | null>(null);
  const [unread, setUnread] = useState("");
  const [states, setStates] = useState<Record<string, RowState>>({});

  const read = useCallback(async () => {
    try {
      setDetect(await apiFetch<ConnectionsDetect>(CONNECTIONS_PATH));
      setUnread("");
    } catch (error) {
      setUnread(readableError(error));
    }
  }, []);

  useEffect(() => {
    void read();
  }, [read]);

  const use = useCallback(
    async (candidate: ConnectionCandidate) => {
      setStates((prev) => ({ ...prev, [candidate.id]: { kind: "busy" } }));
      let next: RowState | null = null;
      try {
        const answer = await apiFetch<UseAnswer>(CONNECTIONS_USE_PATH, { method: "POST", json: { id: candidate.id } });
        const entry = answer?.entry;
        if (entry && entry.state && entry.state !== "connected") {
          next = { kind: "refused", reason: String(entry.error_detail || entry.recovery_hint || entry.state) };
        }
      } catch (error) {
        next = { kind: "refused", reason: readableError(error) };
      }
      setStates((prev) => {
        const copy = { ...prev };
        if (next) copy[candidate.id] = next;
        else delete copy[candidate.id];
        return copy;
      });
      await read();
    },
    [read],
  );

  const rows = detect?.candidates ?? [];
  const connected = rows.filter((row) => row.connected);
  // Done: no row is left that his press can connect (a row with no verb —
  // not the active gh login, or the tool not installed — cannot be used).
  const open = rows.filter((row) => row.verb && !row.connected);
  const providers = [...new Set(connected.map((row) => row.provider))];
  return {
    loaded: detect !== null || unread !== "",
    unread,
    rows,
    tools: detect?.tools ?? {},
    states,
    connected,
    providers,
    done: detect !== null && open.length === 0,
    read,
    use,
  };
}

export type ConnectionsStep = ReturnType<typeof useConnectionsStep>;
