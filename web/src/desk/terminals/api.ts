import { apiFetch, apiRequest } from "../../lib/api";
import type {
  TerminalDescriptor,
  TerminalKey,
  TerminalPaneGeometry,
  TerminalReceipt,
  TerminalTarget,
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

export async function disarmTerminal(descriptorValue: TerminalDescriptor): Promise<void> {
  const targetValue = steeringUrl(descriptorValue.key, descriptorValue.target.node_id, "disarm");
  try {
    await apiRequest(targetValue.url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(targetValue.body),
    });
  } catch {
    // The next read will report the authoritative posture.  Close is local and
    // must not turn a disarm transport failure into a retry loop.
  }
}

export function keyPayload(keys: TerminalKey[]): { keys: TerminalKey[] } {
  return { keys };
}
