/** The immutable-target terminal on the Desk (HS-94-08 / §5, §7, §8).
 *
 * The Phase-93 session pull-out watched a pane by a client-resolved
 * `pane:%N`. Phase 94 replaces that with a node-issued opaque target: a
 * command names {node_id, target_id, target_generation} together, and the
 * node re-verifies the generation before every input (§5). The load-bearing
 * rule this store enforces:
 *
 *   An OPEN target can never be reinterpreted. `open(target)` stores the whole
 *   server-issued handle; there is no setter that mutates an open target's id
 *   or generation. Selecting a different node/worktree/pane is `open()` with a
 *   DIFFERENT target — a different subscription, never the same one pointed
 *   somewhere new. Commands always read the currently-open target; the client
 *   supplies no authority, policy, actor, or target of its own (§8: a
 *   client-supplied `authority` block refuses by name hub-side).
 *
 * Watching is free (subscriptions carry no grant). The poll runs ONLY while a
 * target is open, single-flight, resume-by-sequence with a hash gate.
 */

import { create } from "zustand";
import { apiRequest } from "../lib/api";

/** A server-issued terminal handle — every field comes from the node, never
 *  the client. `targetId` + `targetGeneration` are the immutable identity. */
export interface OpenTarget {
  targetId: string;
  targetGeneration: string;
  nodeId: string;
  label: string;
  sessionLabel: string;
  worktreeId: string | null;
  agent: string;
}

/** The identity two handles are compared by — a change in node OR target OR
 *  generation is a DIFFERENT target (never a reinterpretation). */
export function targetKey(t: {
  nodeId: string;
  targetId: string;
  targetGeneration: string;
}): string {
  return `${t.nodeId}|${t.targetId}|${t.targetGeneration}`;
}

export function sameTarget(
  a: OpenTarget | null,
  b: OpenTarget | null,
): boolean {
  if (!a || !b) return false;
  return targetKey(a) === targetKey(b);
}

export type TerminalStatus =
  | "idle"
  | "live"
  | "resyncing"
  | "stream_unavailable"
  | "target_gone"
  | "generation_mismatch"
  | "unauthorized"
  | "unreachable";

const ABSENCE_STATUSES: TerminalStatus[] = [
  "stream_unavailable",
  "target_gone",
  "generation_mismatch",
  "unauthorized",
];

export const TERMINAL_POLL_MS = 1_500;

/** The exact destination + consequence shown at the send boundary (§8: the
 *  client shows where the effect lands and what it does before it sends). */
export interface SendPreview {
  destination: string;
  consequence: string;
}

export function sendPreview(
  target: OpenTarget | null,
  verb: "terminal.text" | "terminal.keys",
  submit: boolean,
): SendPreview | null {
  if (!target) return null;
  const destination = `${target.label} · ${target.nodeId}`;
  const consequence =
    verb === "terminal.keys"
      ? "sends keys to the pane"
      : submit
        ? "types text and submits"
        : "types text without submit";
  return { destination, consequence };
}

interface TerminalState {
  openTarget: OpenTarget | null;
  status: TerminalStatus;
  detail: string;
  lines: string[];
  sequence: number;
  hash: string | null;
  inflight: boolean;
  sendState: "idle" | "sending" | "sent" | "refused";
  sendDetail: string;
  lastReceiptId: string | null;
  /** Open a server-issued target. Replaces any open target wholesale — the
   *  ONLY way the open target changes. */
  open(target: OpenTarget): void;
  close(): void;
  poll(): Promise<void>;
  sendText(text: string, submit: boolean): Promise<boolean>;
  sendKeys(seq: string[], label: string): Promise<boolean>;
}

let timer: ReturnType<typeof setInterval> | null = null;

const CLEARED = {
  status: "idle" as TerminalStatus,
  detail: "",
  lines: [] as string[],
  sequence: 0,
  hash: null as string | null,
  sendState: "idle" as const,
  sendDetail: "",
  lastReceiptId: null as string | null,
};

// The subscription content is ANSI-preserving (§7); the Desk has no terminal
// emulator, so strip escape sequences to plain readable lines (parity with the
// steering peek, which the node already strips server-side). Spaces and layout
// are preserved — only ESC-prefixed sequences and carriage returns go.
// eslint-disable-next-line no-control-regex
const ANSI = /\u001b\[[0-9;?]*[ -/]*[@-~]|\u001b\][\s\S]*?(?:\u0007|\u001b\\)|\u001b[@-Z\\-_]/g;

function toLines(content: string): string[] {
  return content.replace(ANSI, "").replace(/\r/g, "").split("\n");
}

function commandId(): string {
  try {
    return crypto.randomUUID();
  } catch {
    return `cmd-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }
}

async function submitCommand(
  target: OpenTarget,
  verb: "terminal.text" | "terminal.keys",
  payload: Record<string, unknown>,
): Promise<
  | { ok: true; receiptId: string | null; destination: string }
  | { ok: false; error: string }
> {
  // The client builds target + operation + payload ONLY. No authority,
  // actor, policy, or grant — the hub derives every one of those, and a
  // smuggled authority block refuses by name.
  const body = {
    command_schema: 1,
    command_id: commandId(),
    target: {
      node_id: target.nodeId,
      target_id: target.targetId,
      target_generation: target.targetGeneration,
    },
    operation: { family: "coder_steering", verb },
    payload,
  };
  try {
    const res = await apiRequest("/api/delivery/terminal/commands", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok && (data.state === "complete" || data.state === "sent")) {
      const receipt = data.receipt || null;
      if (receipt && receipt.state === "refused") {
        return {
          ok: false,
          error: `${receipt.outcome || "refused"}${
            receipt.error ? ` · ${receipt.error}` : ""
          }`,
        };
      }
      return {
        ok: true,
        receiptId: receipt ? String(receipt.receipt_id || "") || null : null,
        destination: receipt
          ? String(receipt.target_id || target.targetId)
          : target.targetId,
      };
    }
    return {
      ok: false,
      error: String(data.detail || data.error || `HTTP ${res.status}`),
    };
  } catch {
    return { ok: false, error: "hub unreachable" };
  }
}

export const useDeliveryTerminal = create<TerminalState>((set, get) => ({
  openTarget: null,
  inflight: false,
  ...CLEARED,

  open(target) {
    // Replace wholesale — a different node/target/generation is a different
    // subscription. There is deliberately no path to mutate an open target.
    if (timer !== null) clearInterval(timer);
    set({ openTarget: target, ...CLEARED });
    void get().poll();
    timer = setInterval(() => void get().poll(), TERMINAL_POLL_MS);
  },

  close() {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
    set({ openTarget: null, ...CLEARED });
  },

  async poll() {
    const target = get().openTarget;
    if (!target || get().inflight) return;
    set({ inflight: true });
    try {
      const res = await apiRequest("/api/delivery/terminal/subscriptions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_id: target.targetId,
          target_generation: target.targetGeneration,
          resume_sequence: get().sequence || undefined,
          last_hash: get().hash || undefined,
        }),
      });
      const body = await res.json().catch(() => ({}));
      // A close/open mid-flight must not let a stale poll paint the wrong
      // pane: the open target is compared by its immutable identity.
      const now = get().openTarget;
      if (!now || !sameTarget(now, target)) return;
      const status = String(body.status || "");
      if (res.status === 401) {
        set({ status: "unauthorized", detail: String(body.detail || "") });
        return;
      }
      if ((ABSENCE_STATUSES as string[]).includes(status)) {
        set({
          status: status as TerminalStatus,
          detail: String(body.detail || body.current_generation || ""),
          lines: [],
        });
        return;
      }
      if (status === "snapshot" || status === "resync_required") {
        set({
          status: status === "resync_required" ? "resyncing" : "live",
          lines: toLines(String(body.content || "")),
          sequence: Number(body.sequence || 0),
          hash: body.hash ? String(body.hash) : null,
          detail: "",
        });
        return;
      }
      if (status === "deltas") {
        const chunks = (body.deltas || [])
          .map((d: any) => String(d.data || ""))
          .join("");
        set({
          status: "live",
          lines: [...get().lines, ...toLines(chunks)],
          sequence: Number(body.sequence || get().sequence),
        });
        return;
      }
      // not_modified: the gate held; keep the view.
      set({ status: "live" });
    } catch {
      if (sameTarget(get().openTarget, target))
        set({ status: "unreachable", detail: "" });
    } finally {
      set({ inflight: false });
    }
  },

  async sendText(text, submit) {
    const target = get().openTarget;
    if (!target || !text.trim()) return false;
    set({ sendState: "sending", sendDetail: "" });
    const out = await submitCommand(target, "terminal.text", {
      text,
      submit,
    });
    if (!sameTarget(get().openTarget, target)) return out.ok;
    if (out.ok) {
      set({
        sendState: "sent",
        sendDetail: out.receiptId
          ? `Receipt ${out.receiptId} · ${out.destination}`
          : `delivered · ${out.destination}`,
        lastReceiptId: out.receiptId,
      });
      return true;
    }
    set({ sendState: "refused", sendDetail: out.error });
    return false;
  },

  async sendKeys(seq, label) {
    const target = get().openTarget;
    if (!target || seq.length === 0) return false;
    set({ sendState: "sending", sendDetail: label });
    const out = await submitCommand(target, "terminal.keys", { keys: seq });
    if (!sameTarget(get().openTarget, target)) return out.ok;
    if (out.ok) {
      set({
        sendState: "sent",
        sendDetail: out.receiptId
          ? `Receipt ${out.receiptId} · ${out.destination}`
          : `${label} delivered`,
        lastReceiptId: out.receiptId,
      });
      return true;
    }
    set({ sendState: "refused", sendDetail: out.error });
    return false;
  },
}));
