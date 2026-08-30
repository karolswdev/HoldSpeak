import type { RuntimeFrame } from "../../../runtime/RuntimeBus";

export const WORKBENCH_RUN_FRAME_TYPES = [
  "workbench.run_start",
  "workbench.item_claimed",
  "workbench.item_done",
  "workbench.item_failed",
  "workbench.run_complete",
] as const;

export type WorkbenchRunFrameType = (typeof WORKBENCH_RUN_FRAME_TYPES)[number];

export type WorkbenchRunPhase =
  | "idle"
  | "starting"
  | "running"
  | "reconciling"
  | "complete"
  | "refused"
  | "failed";

export interface WorkbenchRunProgress {
  index: number;
  total: number;
}

type TerminalPhase = Extract<WorkbenchRunPhase, "complete" | "failed">;

export interface WorkbenchRunState {
  phase: WorkbenchRunPhase;
  runId: string | null;
  progress: WorkbenchRunProgress | null;
  terminalPhase: TerminalPhase | null;
  reason: string | null;
}

export const initialWorkbenchRunState: WorkbenchRunState = {
  phase: "idle",
  runId: null,
  progress: null,
  terminalPhase: null,
  reason: null,
};

export type WorkbenchRunAction =
  | { type: "start_requested"; total: number }
  | { type: "run_started"; runId: string | null; total: number }
  | {
      type: "item_advanced";
      runId: string | null;
      progress: WorkbenchRunProgress;
    }
  | {
      type: "run_ended";
      runId: string | null;
      terminalPhase: TerminalPhase;
      reason: string | null;
    }
  | { type: "request_succeeded" }
  | { type: "reconciled" }
  | { type: "request_refused"; reason: string }
  | { type: "request_failed"; reason: string }
  | { type: "request_timed_out" }
  | { type: "detail_observed"; hasClaimedItem: boolean };

export function workbenchRunReducer(
  state: WorkbenchRunState,
  action: WorkbenchRunAction,
): WorkbenchRunState {
  switch (action.type) {
    case "start_requested":
      return {
        phase: "starting",
        runId: null,
        progress: { index: 0, total: action.total },
        terminalPhase: null,
        reason: null,
      };
    case "run_started":
      return {
        phase: "running",
        runId: action.runId,
        progress: { index: 0, total: action.total },
        terminalPhase: null,
        reason: null,
      };
    case "item_advanced":
      return {
        phase: "running",
        runId: action.runId ?? state.runId,
        progress: action.progress,
        terminalPhase: null,
        reason: null,
      };
    case "run_ended":
      return {
        phase: "reconciling",
        runId: action.runId ?? state.runId,
        progress: null,
        terminalPhase: action.terminalPhase,
        reason: action.reason,
      };
    case "request_succeeded":
      if (state.phase !== "starting" && state.phase !== "running") return state;
      return {
        ...state,
        phase: "reconciling",
        progress: null,
        terminalPhase: "complete",
        reason: null,
      };
    case "reconciled":
      if (state.phase !== "reconciling" || !state.terminalPhase) return state;
      return {
        ...state,
        phase: state.terminalPhase,
        terminalPhase: null,
      };
    case "request_refused":
      if (state.phase === "reconciling" || state.phase === "complete") return state;
      return {
        phase: "refused",
        runId: null,
        progress: null,
        terminalPhase: null,
        reason: action.reason,
      };
    case "request_failed":
      if (state.phase === "reconciling" || state.phase === "complete") return state;
      return {
        phase: "failed",
        runId: null,
        progress: null,
        terminalPhase: null,
        reason: action.reason,
      };
    case "request_timed_out":
      return {
        phase: "failed",
        runId: state.runId,
        progress: null,
        terminalPhase: null,
        reason: "RUN TIMEOUT",
      };
    case "detail_observed":
      if (action.hasClaimedItem && state.phase === "idle") {
        return {
          phase: "running",
          runId: null,
          progress: null,
          terminalPhase: null,
          reason: null,
        };
      }
      if (
        !action.hasClaimedItem &&
        state.phase === "running" &&
        state.progress === null
      ) {
        return initialWorkbenchRunState;
      }
      return state;
  }
}

export function isWorkbenchRunActive(state: WorkbenchRunState): boolean {
  return (
    state.phase === "starting" ||
    state.phase === "running" ||
    state.phase === "reconciling"
  );
}

export interface WorkbenchRunRefreshPlan {
  detail: boolean;
  runs: boolean;
  memory: boolean;
}

export interface WorkbenchRunFramePlan {
  action: WorkbenchRunAction;
  refresh: WorkbenchRunRefreshPlan;
  clearRequestTimeout: boolean;
}

const NO_REFRESH: WorkbenchRunRefreshPlan = {
  detail: false,
  runs: false,
  memory: false,
};

const DETAIL_REFRESH: WorkbenchRunRefreshPlan = {
  detail: true,
  runs: false,
  memory: false,
};

const TERMINAL_REFRESH: WorkbenchRunRefreshPlan = {
  detail: true,
  runs: true,
  memory: true,
};

/**
 * Validate one bus frame and turn it into a lifecycle transition plus the
 * data that must be reconciled. This is deliberately pure: the window owns
 * subscriptions and I/O, while this controller owns protocol meaning.
 */
export function planWorkbenchRunFrame(
  workbenchId: string,
  frame: RuntimeFrame,
): WorkbenchRunFramePlan | null {
  if (!isWorkbenchRunFrameType(frame.type)) return null;
  const event = record(frame.data);
  if (!event || string(event.workbench_id) !== workbenchId) return null;

  const runId = nullableString(event.run_id);
  if (frame.type === "workbench.run_start") {
    return {
      action: {
        type: "run_started",
        runId,
        total: nonNegativeInteger(event.item_count),
      },
      refresh: NO_REFRESH,
      clearRequestTimeout: false,
    };
  }

  if (frame.type === "workbench.run_complete") {
    const disposition = string(event.disposition) || "failed";
    return {
      action: {
        type: "run_ended",
        runId,
        terminalPhase: disposition === "succeeded" ? "complete" : "failed",
        reason: disposition === "succeeded" ? null : disposition.toUpperCase(),
      },
      refresh: TERMINAL_REFRESH,
      clearRequestTimeout: true,
    };
  }

  return {
    action: {
      type: "item_advanced",
      runId,
      progress: {
        index: nonNegativeInteger(event.index),
        total: nonNegativeInteger(event.total),
      },
    },
    refresh: DETAIL_REFRESH,
    clearRequestTimeout: false,
  };
}

export function workbenchRunRequestFailure(reason: string): WorkbenchRunAction {
  const normalized = reason.trim().toUpperCase() || "WRITE REFUSED";
  const refused =
    normalized === "WRITE REFUSED" ||
    /^HTTP 4\d\d$/.test(normalized);
  return {
    type: refused ? "request_refused" : "request_failed",
    reason: normalized,
  };
}

function isWorkbenchRunFrameType(type: string): type is WorkbenchRunFrameType {
  return (WORKBENCH_RUN_FRAME_TYPES as readonly string[]).includes(type);
}

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function string(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function nullableString(value: unknown): string | null {
  const valueString = string(value);
  return valueString || null;
}

function nonNegativeInteger(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value)
    ? Math.max(0, Math.trunc(value))
    : 0;
}
