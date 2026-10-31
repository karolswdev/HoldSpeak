import { apiFetch, apiRequest } from "../../lib/api";
import type {
  TerminalDescriptor,
  TerminalContext,
  TerminalKey,
  TerminalPaneGeometry,
  TerminalReceipt,
  TerminalTarget,
  TerminalDimensions,
} from "./types";

export interface TerminalSessionsResponse {
  status: "ok" | "tmux_absent" | "error" | string;
  detail?: string;
  sessions: TerminalDescriptor[];
}

function asText(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : value == null ? fallback : String(value);
}

function target(value: unknown): TerminalTarget {
  const row = value && typeof value === "object" ? value as Record<string, unknown> : {};
  return {
    node_id: asText(row.node_id, "local"),
    target_id: asText(row.target_id),
    target_generation: asText(row.target_generation),
  };
}

function object(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? value as Record<string, unknown> : {};
}

function project(value: unknown) {
  const row = object(value);
  return row.id ? { id: asText(row.id), name: asText(row.name, asText(row.id)) } : null;
}

function source(value: unknown) {
  const row = object(value);
  return row.id ? { id: asText(row.id), name: asText(row.name, asText(row.id)) } : null;
}

function worktree(value: unknown) {
  const row = object(value);
  return row.id ? { id: asText(row.id), branch: asText(row.branch) } : null;
}

function launch(value: unknown) {
  const row = object(value);
  return row.id ? {
    id: asText(row.id),
    profile_id: asText(row.profile_id),
    state: asText(row.state),
    role: asText(row.role),
    origin_ref: typeof row.origin_ref === "string"
      ? row.origin_ref
      : row.origin_ref && typeof row.origin_ref === "object"
        ? row.origin_ref as { kind?: string; id?: string; [key: string]: unknown }
        : null,
    attempt_id: asText(row.attempt_id),
  } : null;
}

function program(value: unknown) {
  const row = object(value);
  return row.id ? {
    id: asText(row.id),
    title: asText(row.title, asText(row.id)),
    step_id: asText(row.step_id),
    step_ordinal: typeof row.step_ordinal === "number" ? row.step_ordinal : null,
  } : null;
}

function mcp(value: unknown) {
  const row = object(value);
  const status = row.status === "configured" ? "configured" : "unknown";
  if (!Object.keys(row).length) return null;
  return {
    status,
    server: asText(row.server),
    palette: asText(row.palette),
    pre_approved: row.pre_approved === true,
    read_only: row.read_only === true,
  } as const;
}

function context(value: unknown): TerminalContext {
  const row = object(value);
  const status = ["bound", "worktree", "unbound", "unavailable"].includes(asText(row.status))
    ? asText(row.status) as TerminalContext["status"]
    : "unbound";
  return {
    status,
    project: project(row.project),
    source: source(row.source),
    worktree: worktree(row.worktree),
    launch: launch(row.launch),
    program: program(row.program),
    mcp: mcp(row.mcp),
  };
}

function descriptor(value: unknown): TerminalDescriptor {
  const row = value && typeof value === "object" ? value as Record<string, unknown> : {};
  return {
    id: asText(row.id),
    label: asText(row.label, asText(row.session, "Terminal")),
    session: asText(row.session),
    key: asText(row.key, asText(row.pane_id)),
    agent: asText(row.agent, "pane"),
    command: asText(row.command),
    current_path: asText(row.current_path),
    state: asText(row.state, "live"),
    target: target(row.target),
    pane_id: asText(row.pane_id),
    context: context(row.context),
  };
}

/** Read the server's terminal inventory.  Discovery is never inferred from
 * browser state, and an absent inventory remains an explicit response. */
export async function readTerminalSessions(): Promise<TerminalSessionsResponse> {
  try {
    const body = await apiFetch<Record<string, unknown>>(
      "/api/delivery/terminal/sessions",
      { headers: { Accept: "application/json" } },
    );
    const status = asText(body.status, "ok");
    return {
      status,
      detail: typeof body.detail === "string" ? body.detail : undefined,
      sessions: Array.isArray(body.sessions) ? body.sessions.map(descriptor) : [],
    };
  } catch (error) {
    return {
      status: "error",
      detail: error instanceof Error ? error.message : "terminal inventory unavailable",
      sessions: [],
    };
  }
}

export interface TerminalSubscriptionResponse {
  status?: string;
  detail?: string;
  content?: string;
  raw?: string;
  lines?: string[];
  sequence?: number;
  hash?: string;
  pane?: {
    width?: number;
    height?: number;
    cursor_x?: number;
    cursor_y?: number;
  } | TerminalPaneGeometry;
  deltas?: Array<{
    data?: string;
    content?: string;
    raw?: string;
    sequence?: number;
    kind?: string;
    mode?: string;
    type?: string;
    replace?: boolean;
  }>;
}

export async function readTerminalSubscription(
  targetValue: TerminalTarget,
  resumeSequence: number,
  lastHash: string | null,
): Promise<{ response: Response; body: TerminalSubscriptionResponse }> {
  const response = await apiRequest("/api/delivery/terminal/subscriptions", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      target_id: targetValue.target_id,
      target_generation: targetValue.target_generation,
      resume_sequence: resumeSequence || undefined,
      last_hash: lastHash || undefined,
    }),
  });
  const body = await response.json().catch(() => ({}));
  return { response, body: body as TerminalSubscriptionResponse };
}

/** Open the native terminal's byte stream. The response is NDJSON and must be
 * consumed incrementally by the session controller; callers never turn this
 * into a snapshot poll. The target is copied once and is not replaceable by a
 * later inventory row. */
export async function readTerminalLive(
  targetValue: TerminalTarget,
  streamId: string | null,
  resumeSequence: number,
  signal: AbortSignal,
): Promise<Response> {
  return apiRequest("/api/delivery/terminal/live", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/x-ndjson",
    },
    body: JSON.stringify({
      target_id: targetValue.target_id,
      target_generation: targetValue.target_generation,
      stream_id: streamId || undefined,
      resume_sequence: resumeSequence > 0 ? resumeSequence : undefined,
    }),
    signal,
  });
}

function commandId(): string {
  try {
    return crypto.randomUUID();
  } catch {
    const hex = () => Math.floor(Math.random() * 0x100000000).toString(16).padStart(8, "0");
    return `${hex()}-${hex().slice(0, 4)}-4${hex().slice(0, 3)}-a${hex().slice(0, 3)}-${hex()}${hex().slice(0, 4)}`;
  }
}

export async function sendTerminalCommand(
  descriptorValue: TerminalDescriptor,
  verb: "terminal.text" | "terminal.keys",
  payload: Record<string, unknown>,
): Promise<
  | { ok: true; receipt: TerminalReceipt | null }
  | { ok: false; error: string; receipt?: TerminalReceipt | null; revoke?: boolean }
> {
  const body = {
    command_schema: 1,
    command_id: commandId(),
    target: descriptorValue.target,
    operation: { family: "coder_steering", verb },
    payload: {
      session_key: descriptorValue.key,
      agent: descriptorValue.agent,
      ...payload,
    },
  };
  try {
    const response = await apiRequest("/api/delivery/terminal/commands", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({})) as Record<string, unknown>;
    const receipt = data.receipt && typeof data.receipt === "object"
      ? data.receipt as TerminalReceipt
      : null;
    const state = asText(data.state);
    const receiptState = asText(receipt?.state).toLowerCase();
    const receiptOutcome = asText(receipt?.outcome).toLowerCase();
    const failedReceipt = ["refused", "failed", "error", "unknown", "indeterminate"].includes(receiptState)
      || ["refused", "failed", "error", "unknown", "indeterminate"].includes(receiptOutcome);
    const deliveredReceipt = receiptState === "succeeded" && receiptOutcome === "delivered";
    if (response.ok && ["complete", "sent"].includes(state) && deliveredReceipt && !failedReceipt) {
      return { ok: true, receipt };
    }
    const refusal = asText(
      data.detail,
      asText(data.error, asText(receipt?.detail, asText(receipt?.error, asText(receipt?.outcome, receipt ? "terminal delivery was not acknowledged" : "terminal delivery receipt unavailable")))),
    );
    return {
      ok: false,
      error: refusal,
      receipt,
      revoke: ["unarmed", "expired", "pane_mismatch", "pane_gone", "generation_mismatch"].includes(
        asText(data.status) || asText(receipt?.outcome),
      ),
    };
  } catch {
    // Unknown transport outcome is visible and never retried automatically.
    return { ok: false, error: "hub unreachable" };
  }
}

function dimensions(value: unknown): TerminalDimensions | null {
  if (!value || typeof value !== "object") return null;
  const row = value as Record<string, unknown>;
  const cols = Number(row.cols ?? row.columns ?? row.width);
  const rows = Number(row.rows ?? row.height);
  return Number.isInteger(cols) && Number.isInteger(rows) && cols > 0 && rows > 0
    ? { cols, rows }
    : null;
}

/** Resize the actual host process. A receipt without matching dimensions is
 * deliberately not success: the window must never say it saved a size that
 * the backend did not acknowledge. */
export async function resizeTerminal(
  descriptorValue: TerminalDescriptor,
  size: TerminalDimensions,
): Promise<
  | { ok: true; receipt: TerminalReceipt | null; dimensions: TerminalDimensions }
  | { ok: false; error: string; receipt?: TerminalReceipt | null; revoke?: boolean }
> {
  const body = {
    command_schema: 1,
    command_id: commandId(),
    target: descriptorValue.target,
    operation: { family: "coder_steering", verb: "process.resize@1" },
    payload: {
      session_key: descriptorValue.key,
      agent: descriptorValue.agent,
      cols: size.cols,
      rows: size.rows,
    },
  };
  try {
    const response = await apiRequest("/api/delivery/terminal/commands", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({})) as Record<string, unknown>;
    const receipt = data.receipt && typeof data.receipt === "object"
      ? data.receipt as TerminalReceipt
      : null;
    const ack = dimensions(data.actual_dimensions)
      || dimensions(data.dimensions)
      || dimensions(data.size)
      || dimensions(receipt?.dimensions);
    const state = asText(data.state);
    const receiptState = asText(receipt?.state).toLowerCase();
    const receiptOutcome = asText(receipt?.outcome).toLowerCase();
    const delivered = response.ok
      && ["complete", "sent"].includes(state)
      && receiptState === "succeeded"
      && receiptOutcome === "delivered"
      && ack?.cols === size.cols
      && ack.rows === size.rows;
    if (delivered) return { ok: true, receipt, dimensions: ack };
    const refusal = asText(
      data.detail,
      asText(data.error, asText(receipt?.detail, asText(receipt?.error, "Terminal resize was not acknowledged"))),
    );
    return {
      ok: false,
      error: refusal,
      receipt,
      revoke: ["unarmed", "expired", "pane_mismatch", "pane_gone", "generation_mismatch"].includes(
        asText(data.status) || asText(receipt?.outcome),
      ),
    };
  } catch {
    return { ok: false, error: "hub unreachable" };
  }
}

function steeringUrl(key: string, nodeId: string, verb: "arm" | "disarm"): { url: string; body: object } {
  if (nodeId && nodeId !== "local") {
    return {
      url: `/api/coders/relay/${encodeURIComponent(nodeId)}/${verb}`,
      body: { key },
    };
  }
  return {
    url: `/api/coders/${encodeURIComponent(key)}/${verb}`,
    body: {},
  };
}

export async function armTerminal(descriptorValue: TerminalDescriptor): Promise<
  { ok: true; expiresInSeconds?: number } | { ok: false; error: string }
> {
  const targetValue = steeringUrl(descriptorValue.key, descriptorValue.target.node_id, "arm");
  try {
    const response = await apiRequest(targetValue.url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(targetValue.body),
    });
    const body = await response.json().catch(() => ({})) as Record<string, unknown>;
    return response.ok && asText(body.status) === "armed"
      ? { ok: true, expiresInSeconds: Number(body.expires_in_seconds) || undefined }
      : { ok: false, error: asText(body.detail, asText(body.status, `HTTP ${response.status}`)) };
  } catch {
    return { ok: false, error: "hub unreachable" };
  }
}

export async function disarmTerminal(descriptorValue: TerminalDescriptor): Promise<
  | { ok: true; status: "disarmed"; receipt?: TerminalReceipt | null }
  | { ok: false; error: string; status?: string; receipt?: TerminalReceipt | null }
> {
  const targetValue = steeringUrl(descriptorValue.key, descriptorValue.target.node_id, "disarm");
  try {
    const response = await apiRequest(targetValue.url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(targetValue.body),
    });
    const data = await response.json().catch(() => ({})) as Record<string, unknown>;
    const status = asText(data.status);
    const receipt = data.receipt && typeof data.receipt === "object"
      ? data.receipt as TerminalReceipt
      : null;
    if (response.ok && status === "disarmed") return { ok: true, status, receipt };
    return {
      ok: false,
      error: asText(data.detail, asText(data.error, status || `HTTP ${response.status}`)),
      status: status || undefined,
      receipt,
    };
  } catch {
    return { ok: false, error: "hub unreachable" };
  }
}

export function keyPayload(keys: TerminalKey[]): { keys: TerminalKey[] } {
  return { keys };
}
