/* Calls (CALLS-DESIGN-2026-10-28 §6): the faces' reads and writes.
 *
 * One hook holds the window's copy: the `calls` settings section, the
 * status, the past calls and the call on the line. A `call_state` frame
 * replaces the call it names (one frame per change). A hub without the
 * Calls slice has no `calls` settings section: the faces then draw the
 * install checklist with every step open and read nothing more (no 404 on
 * the console). A status read that 404s draws the same checklist. */
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { useOptionalRuntimeBus } from "../../runtime/RuntimeBus";
import type { Call, CallStateFrame, CallStep, CallSummary, CallsSettings, CallsStatus, LineCode, LineNode, LineStatus, LineTestResult } from "./types";

/** The checklist in its order, every step open: what the faces draw when
 *  the hub has no Calls slice or its status read fails. */
export const OPEN_STEPS: CallStep[] = [
  { id: "install", done: false, words: "Not installed" },
  { id: "daemon", done: false, words: "Not running" },
  { id: "line", done: false, words: "No line" },
  { id: "engine", done: false, words: "Not set" },
  { id: "passphrase", done: false, words: "Not set" },
  { id: "enable", done: false, words: "Off" },
];

export const ABSENT_STATUS: CallsStatus = {
  enabled: false,
  aiphone: { state: "not_found", words: "Not installed" },
  lines: [],
  engine: { profile_id: null, model: null, state: "none", words: "Not set" },
  passphrase_set: false,
  listening: false,
  active: null,
  steps: OPEN_STEPS,
};

function notFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

export async function readCallsSettings(): Promise<CallsSettings | null> {
  const body = await apiFetch<{ calls?: CallsSettings }>("/api/settings");
  const calls = body?.calls;
  return calls && typeof calls === "object" ? calls : null;
}

export async function writeCallsSetting(key: keyof CallsSettings | "passphrase", value: unknown): Promise<CallsSettings | null> {
  const body = await apiFetch<{ settings?: { calls?: CallsSettings } }>("/api/settings", {
    method: "PUT",
    json: { calls: { [key]: value } },
  });
  return body?.settings?.calls ?? null;
}

/** The status; a hub without the route answers the open checklist. */
export async function readCallsStatus(): Promise<CallsStatus> {
  try {
    const status = await apiFetch<CallsStatus>("/api/calls/status");
    return status && Array.isArray(status.steps) ? status : ABSENT_STATUS;
  } catch (error) {
    if (notFound(error)) return ABSENT_STATUS;
    throw error;
  }
}

/** The Line's status; a hub without the route answers the Line off. */
export const LINE_OFF: LineStatus = { node: "", state: "off", words: "Off", address: "", secrets: {} };

export async function readLineStatus(): Promise<LineStatus> {
  try {
    const status = await apiFetch<LineStatus>("/api/calls/line/status");
    return status && typeof status.state === "string" ? status : LINE_OFF;
  } catch (error) {
    if (notFound(error)) return LINE_OFF;
    throw error;
  }
}

/** Test call: the Line calls him and hangs up. A refusal (409) answers its
 *  reason as the result (`no_number`, `no_line`, `busy`). */
export async function testLine(): Promise<LineTestResult> {
  try {
    return await apiFetch<LineTestResult>("/api/calls/line/test", { method: "POST", json: {} });
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      const reason = String((error.payload as { reason?: unknown } | null)?.reason ?? "");
      if (reason) return { result: reason, to: "" };
    }
    throw error;
  }
}

/** The enrolled Line nodes; a hub without the route has none. */
export async function readLineNodes(): Promise<LineNode[]> {
  try {
    const body = await apiFetch<{ nodes?: LineNode[] }>("/api/calls/line/nodes");
    return Array.isArray(body?.nodes) ? body.nodes : [];
  } catch (error) {
    if (notFound(error)) return [];
    throw error;
  }
}

/** Install the Line on a machine: the hub mints its one-time code and the
 *  command, with this desk's own address as the hub to call. */
export function mintLineCode(node: string): Promise<LineCode> {
  return apiFetch<LineCode>("/api/calls/line/codes", { method: "POST", json: { node, hub: window.location.origin } });
}

/** Revoke a Line node's credential. */
export function revokeLineNode(node: string): Promise<unknown> {
  return apiFetch(`/api/calls/line/nodes/${encodeURIComponent(node)}`, { method: "DELETE" });
}

/** The Line is the phone on this hub (its block is not `off`). */
export function lineInUse(status: CallsStatus | null | undefined): boolean {
  return Boolean(status?.line && status.line.state !== "off");
}

export async function readCalls(): Promise<CallSummary[]> {
  try {
    const body = await apiFetch<{ calls?: CallSummary[] }>("/api/calls");
    return Array.isArray(body?.calls) ? body.calls : [];
  } catch (error) {
    if (notFound(error)) return [];
    throw error;
  }
}

export function readCall(id: string): Promise<Call> {
  return apiFetch<Call>(`/api/calls/${encodeURIComponent(id)}`);
}

export function placeCall(): Promise<CallSummary> {
  return apiFetch<CallSummary>("/api/calls/place", { method: "POST", json: {} });
}

export function hangUp(id: string): Promise<CallSummary> {
  return apiFetch<CallSummary>(`/api/calls/${encodeURIComponent(id)}/hangup`, { method: "POST", json: {} });
}

export function decide(id: string, decision: "approve" | "deny"): Promise<CallSummary> {
  return apiFetch<CallSummary>(`/api/calls/${encodeURIComponent(id)}/decide`, { method: "POST", json: { decision } });
}

/** The words of a refused Call me (409 `reason`). */
export const PLACE_REFUSALS: Record<string, string> = {
  busy: "A call is on the line",
  not_running: "ai-phone not running",
  no_line: "No line",
  daily_limit: "Daily call limit",
  no_answer: "No answer",
  rejected: "Call refused",
};

export function refusalWords(error: unknown, line = false): string {
  if (error instanceof ApiError) {
    const reason = String((error.payload as { reason?: unknown } | null)?.reason ?? "");
    if (line && reason === "not_running") return "Line not running";
    if (PLACE_REFUSALS[reason]) return PLACE_REFUSALS[reason];
  }
  return readableError(error);
}

/** Keep the transcript a summary does not carry. */
export function withTranscript(summary: CallSummary, call: Call | null): Call {
  return { ...summary, transcript: call && call.id === summary.id ? call.transcript : [] };
}

export interface CallsState {
  loading: boolean;
  error: string;
  settings: CallsSettings | null;
  status: CallsStatus;
  calls: CallSummary[];
  /** The call on the line (not ended), with its transcript. */
  active: Call | null;
  /** The call that just ended in this window: the "after" document. */
  ended: Call | null;
}

export function useCalls() {
  const [state, setState] = useState<CallsState>({
    loading: true, error: "", settings: null, status: ABSENT_STATUS, calls: [], active: null, ended: null,
  });
  const alive = useRef(true);
  useEffect(() => () => { alive.current = false; }, []);

  const load = useCallback(async () => {
    try {
      const settings = await readCallsSettings();
      if (!settings) {
        if (alive.current) setState((now) => ({ ...now, loading: false, error: "", settings: null, status: ABSENT_STATUS, calls: [] }));
        return;
      }
      const [status, calls] = await Promise.all([readCallsStatus(), readCalls()]);
      const open = status.active && status.active.state !== "ended" ? await readCall(status.active.id).catch(() => withTranscript(status.active!, null)) : null;
      if (!alive.current) return;
      setState((now) => ({ ...now, loading: false, error: "", settings, status, calls, active: open }));
    } catch (error) {
      if (alive.current) setState((now) => ({ ...now, loading: false, error: readableError(error) }));
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  /** One call changed (a frame, or the answer of a press). */
  const apply = useCallback((call: Call) => {
    setState((now) => {
      const calls = [call, ...now.calls.filter((row) => row.id !== call.id)];
      if (call.state === "ended") {
        const wasHere = now.active?.id === call.id || now.ended?.id === call.id;
        return { ...now, calls, active: now.active?.id === call.id ? null : now.active, ended: wasHere ? call : now.ended };
      }
      return { ...now, calls, active: call, ended: null };
    });
  }, []);

  const subscribe = useOptionalRuntimeBus()?.subscribe;
  useEffect(() => {
    if (!subscribe) return;
    return subscribe("call_state", (frame) => {
      const data = frame.data as CallStateFrame | null;
      if (data?.reason === "status") { void load(); return; }
      if (!data?.call?.id) return;
      apply(data.call);
    });
  }, [subscribe, apply, load]);

  return { ...state, reload: load, apply, clearEnded: () => setState((now) => ({ ...now, ended: null })) };
}
