import { describe, expect, it } from "vitest";
import {
  initialWorkbenchRunState,
  isWorkbenchRunActive,
  planWorkbenchRunFrame,
  workbenchRunReducer,
  workbenchRunRequestFailure,
} from "./runLifecycle";

describe("Workbench run lifecycle", () => {
  it("moves a requested run through start, progress, reconcile, and complete", () => {
    const starting = workbenchRunReducer(initialWorkbenchRunState, {
      type: "start_requested",
      total: 2,
    });
    expect(starting).toMatchObject({
      phase: "starting",
      progress: { index: 0, total: 2 },
    });

    const start = planWorkbenchRunFrame("wb1", {
      type: "workbench.run_start",
      data: { workbench_id: "wb1", run_id: "run1", item_count: 2 },
    });
    expect(start).not.toBeNull();
    const running = workbenchRunReducer(starting, start!.action);
    expect(running).toMatchObject({
      phase: "running",
      runId: "run1",
      progress: { index: 0, total: 2 },
    });

    const item = planWorkbenchRunFrame("wb1", {
      type: "workbench.item_done",
      data: {
        workbench_id: "wb1",
        run_id: "run1",
        item_id: "item1",
        index: 1,
        total: 2,
      },
    });
    expect(item?.refresh).toEqual({ detail: true, runs: false, memory: false });
    const progressed = workbenchRunReducer(running, item!.action);
    expect(progressed.progress).toEqual({ index: 1, total: 2 });

    const end = planWorkbenchRunFrame("wb1", {
      type: "workbench.run_complete",
      data: { workbench_id: "wb1", run_id: "run1", disposition: "succeeded" },
    });
    expect(end).toMatchObject({
      clearRequestTimeout: true,
      refresh: { detail: true, runs: true, memory: true },
    });
    const reconciling = workbenchRunReducer(progressed, end!.action);
    expect(reconciling.phase).toBe("reconciling");
    expect(isWorkbenchRunActive(reconciling)).toBe(true);

    const complete = workbenchRunReducer(reconciling, { type: "reconciled" });
    expect(complete.phase).toBe("complete");
    expect(isWorkbenchRunActive(complete)).toBe(false);
  });

  it("retains a failed terminal disposition through reconciliation", () => {
    const end = planWorkbenchRunFrame("wb1", {
      type: "workbench.run_complete",
      data: { workbench_id: "wb1", run_id: "run1", disposition: "expired" },
    });
    const reconciling = workbenchRunReducer(initialWorkbenchRunState, end!.action);
    const failed = workbenchRunReducer(reconciling, { type: "reconciled" });
    expect(failed).toMatchObject({ phase: "failed", reason: "EXPIRED" });
  });

  it("reconciles from the completed request when the runtime bus was silent", () => {
    const starting = workbenchRunReducer(initialWorkbenchRunState, {
      type: "start_requested",
      total: 1,
    });
    const reconciling = workbenchRunReducer(starting, {
      type: "request_succeeded",
    });
    expect(reconciling).toMatchObject({
      phase: "reconciling",
      terminalPhase: "complete",
      progress: null,
    });
  });

  it("distinguishes a hub refusal from a transport failure", () => {
    const refused = workbenchRunReducer(
      initialWorkbenchRunState,
      workbenchRunRequestFailure("HTTP 409"),
    );
    const failed = workbenchRunReducer(
      initialWorkbenchRunState,
      workbenchRunRequestFailure("HUB UNREACHABLE"),
    );
    expect(refused.phase).toBe("refused");
    expect(failed.phase).toBe("failed");
  });

  it("recovers a running phase from claimed detail after reconnect", () => {
    const recovered = workbenchRunReducer(initialWorkbenchRunState, {
      type: "detail_observed",
      hasClaimedItem: true,
    });
    expect(recovered).toMatchObject({ phase: "running", progress: null });

    const idle = workbenchRunReducer(recovered, {
      type: "detail_observed",
      hasClaimedItem: false,
    });
    expect(idle).toEqual(initialWorkbenchRunState);
  });

  it("ignores malformed, unrelated, and cross-workbench frames", () => {
    expect(
      planWorkbenchRunFrame("wb1", {
        type: "workbench.run_start",
        data: { workbench_id: "wb2", item_count: 9 },
      }),
    ).toBeNull();
    expect(
      planWorkbenchRunFrame("wb1", {
        type: "workbench.run_start",
        data: "not-an-event",
      }),
    ).toBeNull();
    expect(
      planWorkbenchRunFrame("wb1", {
        type: "other.event",
        data: { workbench_id: "wb1" },
      }),
    ).toBeNull();
  });
});
