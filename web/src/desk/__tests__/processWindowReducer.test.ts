import { describe, expect, it } from "vitest";
import {
  PROCESS_HEAD_LIMIT,
  foldProcessWindow,
  mergeProcessEvents,
  type KernelProcessEvent,
  type KernelProcessObject,
} from "../processWindowReducer";

const event = (
  operationId: string,
  cursor: number,
  eventType: string,
  extra: Partial<KernelProcessEvent> = {},
): KernelProcessEvent => ({
  cursor,
  operation_id: operationId,
  correlation_id: operationId,
  event_type: eventType,
  timestamp: `2026-07-29T00:00:${String(cursor).padStart(2, "0")}Z`,
  refs: [`target:${operationId}`],
  ...extra,
});

const object = (
  operationId: string,
  state: string,
  genericState: string,
  extra: Record<string, unknown> = {},
): KernelProcessObject => ({
  ref: `operation:${operationId}`,
  operation: {
    operation_id: operationId,
    state,
    principal_identity: "owner",
    name: "process.spawn",
    target_ref: `target:${operationId}`,
    placement: "this-device",
    correlation_id: operationId,
    created_at: "2026-07-29T00:00:00Z",
    ...extra,
  },
  process: {
    generic_state: genericState,
    domain_state: genericState,
    principal: "owner",
    kind: "process.spawn",
    target_ref: `target:${operationId}`,
  },
});

const rows = (sections: ReturnType<typeof foldProcessWindow>, id: string) =>
  sections.find((section) => section.id === id)?.rows ?? [];

function flatten(sectionRows: ReturnType<typeof rows>): string[] {
  const ids: string[] = [];
  const visit = (row: (typeof sectionRows)[number]) => {
    ids.push(row.operationId);
    row.children.forEach(visit);
  };
  sectionRows.forEach(visit);
  return ids;
}

describe("process window journal fold", () => {
  it("folds projected lifecycle into the five fixed sections", () => {
    const events = [
      event("op_needs", 1, "operation.awaiting_decision"),
      event("op_running", 2, "operation.claimed"),
      event("op_waiting", 3, "operation.approved"),
      event("op_unknown", 4, "operation.admitted"),
      event("op_ended", 5, "operation.receipt", { head: "succeeded" }),
      event("op_failed", 6, "operation.receipt", { head: "executor_failed" }),
      event("op_cancelled", 7, "operation.receipt", { head: "cancelled" }),
    ];
    const objects = [
      object("op_needs", "awaiting_decision", "waiting"),
      object("op_running", "claimed", "running"),
      object("op_waiting", "awaiting_execution", "waiting"),
      object("op_unknown", "claimed", "unknown"),
      object("op_ended", "succeeded", "ended"),
      object("op_failed", "failed", "failed"),
      object("op_cancelled", "cancelled", "cancelled"),
    ];
    const sections = foldProcessWindow(events, objects);

    expect(sections.map((section) => section.label)).toEqual([
      "Needs you",
      "Running",
      "Waiting",
      "Unknown",
      "Recently ended",
    ]);
    expect(flatten(rows(sections, "needs-you"))).toEqual(["op_needs"]);
    expect(flatten(rows(sections, "running"))).toEqual(["op_running"]);
    expect(flatten(rows(sections, "waiting"))).toEqual(["op_waiting"]);
    expect(flatten(rows(sections, "unknown"))).toEqual(["op_unknown"]);
    expect(new Set(flatten(rows(sections, "recently-ended")))).toEqual(
      new Set(["op_ended", "op_failed", "op_cancelled"]),
    );
  });

  it("groups explicit children under their run and lifts a needs-you child", () => {
    const events = [
      event("op_parent", 1, "operation.claimed", { correlation_id: "op_parent" }),
      event("op_child", 2, "operation.awaiting_decision", {
        correlation_id: "op_parent",
        causation_id: "op_parent",
      }),
    ];
    const objects = [
      object("op_parent", "claimed", "running"),
      object("op_child", "awaiting_decision", "waiting", {
        parent_operation_id: "op_parent",
        correlation_id: "op_parent",
      }),
    ];
    const needs = rows(foldProcessWindow(events, objects), "needs-you");
    expect(needs).toHaveLength(1);
    expect(needs[0].operationId).toBe("op_parent");
    expect(needs[0].children.map((child) => child.operationId)).toEqual(["op_child"]);
  });

  it("uses a correlation root when no explicit parent is present", () => {
    const events = [
      event("op_root", 1, "operation.claimed", { correlation_id: "op_root" }),
      event("op_peer", 2, "operation.claimed", { correlation_id: "op_root" }),
    ];
    const objects = [
      object("op_root", "claimed", "running"),
      object("op_peer", "claimed", "running", { correlation_id: "op_root" }),
    ];
    const running = rows(foldProcessWindow(events, objects), "running");
    expect(running).toHaveLength(1);
    expect(running[0].children[0].operationId).toBe("op_peer");
  });

  it("bounds the recently-ended tail by newest operation", () => {
    const events = Array.from({ length: 8 }, (_, index) =>
      event(`op_${index}`, index + 1, "operation.receipt"),
    );
    const objects = events.map((item) => object(item.operation_id, "succeeded", "ended"));
    const ended = rows(foldProcessWindow(events, objects, 3), "recently-ended");
    expect(ended.map((row) => row.operationId)).toEqual(["op_7", "op_6", "op_5"]);
  });

  it("keeps a pending-forever operation Waiting regardless of timestamp", () => {
    const ancient = event("op_old", 1, "operation.approved", {
      timestamp: "2001-01-01T00:00:00Z",
    });
    const sections = foldProcessWindow(
      [ancient],
      [object("op_old", "awaiting_execution", "waiting")],
    );
    expect(rows(sections, "waiting")[0].state).toBe("waiting");
    expect(rows(sections, "recently-ended")).toEqual([]);
  });

  it("compacts lifecycle records while retaining bounded heads, refs, and first age", () => {
    const merged = mergeProcessEvents(
      [event("op_1", 1, "operation.admitted", { head: "x".repeat(300) })],
      [event("op_1", 2, "operation.claimed", { head: "", refs: ["target:a", "result:b"] })],
    );
    expect(merged).toHaveLength(1);
    expect(merged[0]).toMatchObject({
      cursor: 2,
      event_type: "operation.claimed",
      first_timestamp: "2026-07-29T00:00:01Z",
      refs: ["target:a", "result:b"],
    });
    expect(merged[0].head).toHaveLength(PROCESS_HEAD_LIMIT);
  });

  it("keeps a refusal's named reason when its generic receipt follows", () => {
    const merged = mergeProcessEvents(
      [event("op_refused", 1, "operation.refused", { head: "warrant_expired" })],
      [event("op_refused", 2, "operation.receipt", { head: "refused" })],
    );
    const ended = rows(
      foldProcessWindow(merged, [object("op_refused", "refused", "ended")]),
      "recently-ended",
    );
    expect(ended[0].head).toBe("warrant_expired");
    expect(ended[0].latestEventType).toBe("operation.receipt");
  });
});
