// HS-168-03 — typed client for GET /api/connections and POST /api/connections/{provider}/recheck.
// Reads the D6 wire shape; tolerates missing fields (the 02 wire may not exist yet).

import { apiFetch } from "../../../lib/api";

/* ── Wire types (D6) ── */

export type ConnectionState =
  | "connected"
  | "owner_action_required"
  | "unavailable"
  | "degraded"
  | "not_configured"
  /** PHILO-9-02 B1: a remote row no probe has checked yet. */
  | "never_checked"
  /** PHILO-15 B31: no probe yet, but gh's sign-in file names an active login. */
  | "signed_in";

export interface ConnectionAccount {
  login?: string;
  site?: string;
  email?: string;
  sources?: number;
  assigned?: number;
  total?: number;
  /** PHILO-15 B33: where meeting summaries run (the queue's route), or null. */
  summary_host?: string | null;
}

export interface ConnectionNextAction {
  kind: string;
  label: string;
}

export interface ConnectionTool {
  provider_id: string;
  state: ConnectionState;
  account?: ConnectionAccount;
  next_action?: ConnectionNextAction;
  recovery_hint?: string;
  error_detail?: string;
  /** The stored time of the last real probe (null: never checked). */
  last_checked_at?: string;
  /** Seconds since that probe, computed by the hub at read time. */
  checked_age_seconds?: number;
  /** PHILO-15 B31: "gh_config" when the state is read from gh's config (no check, no time). */
  checked_by?: string;
  egress_host?: string;
  /** Jira: per-(site,email) connection rows. */
  connections?: JiraSubConnection[];
}

export interface JiraSubConnection {
  connection_ref: string;
  state: ConnectionState;
  account: { site: string; email: string };
  recovery_hint?: string;
  error_detail?: string;
  egress_host?: string;
  /** This row's own stored check time (PHILO-9-02 B1). */
  last_checked_at?: string;
  checked_age_seconds?: number;
}

export interface ConnectionsResponse {
  tools: ConnectionTool[];
}

/* ── Decoder (tolerates missing / partial payloads) ── */

const VALID_STATES = new Set<ConnectionState>([
  "connected",
  "owner_action_required",
  "unavailable",
  "degraded",
  "not_configured",
  "never_checked",
  "signed_in",
]);

export function decodeState(raw: unknown): ConnectionState {
  if (typeof raw === "string" && VALID_STATES.has(raw as ConnectionState)) {
    return raw as ConnectionState;
  }
  return "not_configured";
}

function decodeAccount(raw: unknown): ConnectionAccount | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const obj = raw as Record<string, unknown>;
  return {
    login: typeof obj.login === "string" ? obj.login : undefined,
    site: typeof obj.site === "string" ? obj.site : undefined,
    email: typeof obj.email === "string" ? obj.email : undefined,
    sources: typeof obj.sources === "number" ? obj.sources : undefined,
    assigned: typeof obj.assigned === "number" ? obj.assigned : undefined,
    total: typeof obj.total === "number" ? obj.total : undefined,
    summary_host: typeof obj.summary_host === "string" ? obj.summary_host : null,
  };
}

function decodeNextAction(raw: unknown): ConnectionNextAction | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const obj = raw as Record<string, unknown>;
  if (typeof obj.kind !== "string" || typeof obj.label !== "string") return undefined;
  return { kind: obj.kind, label: obj.label };
}

function decodeSubConnection(raw: unknown): JiraSubConnection | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const obj = raw as Record<string, unknown>;
  const acct = obj.account as Record<string, unknown> | undefined;
  if (!acct || typeof acct.site !== "string" || typeof acct.email !== "string") return undefined;
  return {
    connection_ref: typeof obj.connection_ref === "string" ? obj.connection_ref : "",
    state: decodeState(obj.state),
    account: { site: acct.site, email: acct.email },
    recovery_hint: typeof obj.recovery_hint === "string" ? obj.recovery_hint : undefined,
    error_detail: typeof obj.error_detail === "string" ? obj.error_detail : undefined,
    egress_host: typeof obj.egress_host === "string" ? obj.egress_host : undefined,
    last_checked_at: typeof obj.last_checked_at === "string" ? obj.last_checked_at : undefined,
    checked_age_seconds: typeof obj.checked_age_seconds === "number" ? obj.checked_age_seconds : undefined,
  };
}

function decodeTool(raw: unknown): ConnectionTool | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const obj = raw as Record<string, unknown>;
  if (typeof obj.provider_id !== "string") return undefined;
  return {
    provider_id: obj.provider_id,
    state: decodeState(obj.state),
    account: decodeAccount(obj.account),
    next_action: decodeNextAction(obj.next_action),
    recovery_hint: typeof obj.recovery_hint === "string" ? obj.recovery_hint : undefined,
    error_detail: typeof obj.error_detail === "string" ? obj.error_detail : undefined,
    last_checked_at: typeof obj.last_checked_at === "string" ? obj.last_checked_at : undefined,
    checked_age_seconds: typeof obj.checked_age_seconds === "number" ? obj.checked_age_seconds : undefined,
    checked_by: typeof obj.checked_by === "string" ? obj.checked_by : undefined,
    egress_host: typeof obj.egress_host === "string" ? obj.egress_host : undefined,
    connections: Array.isArray(obj.connections)
      ? (obj.connections.map(decodeSubConnection).filter(Boolean) as JiraSubConnection[])
      : undefined,
  };
}

export function decodeConnectionsResponse(raw: unknown): ConnectionsResponse {
  if (!raw || typeof raw !== "object") return { tools: [] };
  const obj = raw as Record<string, unknown>;
  if (!Array.isArray(obj.tools)) return { tools: [] };
  return {
    tools: obj.tools.map(decodeTool).filter(Boolean) as ConnectionTool[],
  };
}

/* ── API calls ── */

export async function fetchConnections(): Promise<ConnectionsResponse> {
  try {
    const raw = await apiFetch("/api/connections");
    return decodeConnectionsResponse(raw);
  } catch {
    return { tools: [] };
  }
}

/** PHILO-17 U29: add a Jira or Confluence account (site, email); the caller
 *  checks it at once, so it never stays NEVER CHECKED. */
export async function addAtlassianAccount(providerId: "jira" | "confluence", site: string, email: string): Promise<void> {
  await apiFetch(`/api/providers/${providerId}/connections`, { method: "POST", json: { site, email } });
}

export async function recheckProvider(providerId: string): Promise<ConnectionTool | null> {
  try {
    const raw = await apiFetch(`/api/connections/${providerId}/recheck`, {
      method: "POST",
    });
    return decodeTool(raw) ?? null;
  } catch {
    return null;
  }
}
