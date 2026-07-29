import { afterEach, describe, expect, it, vi } from "vitest";
import {
  PROCESS_CHECKPOINT_KEY,
  PROCESS_EVENT_BATCH,
  createProcessWindowStore,
  loadProcessCheckpoint,
} from "../processWindow";
import type { KernelProcessEvent, KernelProcessObject } from "../processWindowReducer";

class MemoryStorage {
  values = new Map<string, string>();
  getItem(key: string) {
    return this.values.get(key) ?? null;
  }
  setItem(key: string, value: string) {
    this.values.set(key, value);
  }
}

const events: KernelProcessEvent[] = [
  {
    cursor: 1,
    operation_id: "op_parent",
    correlation_id: "op_parent",
    event_type: "operation.claimed",
    refs: ["launch:parent"],
    head: "spawn agent",
    timestamp: "2026-07-29T01:00:00Z",
  },
  {
    cursor: 2,
    operation_id: "op_child",
    correlation_id: "op_parent",
    causation_id: "op_parent",
    event_type: "operation.awaiting_decision",
    refs: ["command:child"],
    timestamp: "2026-07-29T01:00:01Z",
  },
];

const objects: KernelProcessObject[] = [
  {
    ref: "operation:op_parent",
    operation: {
      operation_id: "op_parent",
      state: "claimed",
      principal_identity: "owner",
      name: "process.spawn",
      target_ref: "agent:build",
      placement: "node:studio",
      parent_operation_id: "",
      correlation_id: "op_parent",
      created_at: "2026-07-29T01:00:00Z",
    },
    process: {
      generic_state: "running",
      domain_state: "launched",
      principal: "owner",
      kind: "process.spawn",
      target_ref: "agent:build",
    },
  },
  {
    ref: "operation:op_child",
    operation: {
      operation_id: "op_child",
      state: "awaiting_decision",
      principal_identity: "agent:builder",
      name: "process.input",
      target_ref: "pane:7",
      placement: "node:studio",
      parent_operation_id: "op_parent",
      correlation_id: "op_parent",
      created_at: "2026-07-29T01:00:01Z",
    },
    process: {
      generic_state: "waiting",
      domain_state: "sent",
      principal: "agent:builder",
      kind: "process.input",
      target_ref: "pane:7",
    },
  },
];

function response(body: unknown, ok = true) {
  return {
    ok,
    status: ok ? 200 : 500,
    json: async () => body,
  };
}

function seededJournal(fetcher: ReturnType<typeof vi.fn>) {
  fetcher.mockImplementation(async (input: string) => {
    const url = new URL(String(input), "http://desk.test");
    if (url.pathname === "/api/kernel/events") {
      const cursor = Number(url.searchParams.get("after_cursor") || 0);
      return cursor < 2
        ? response({ cursor: 2, events })
        : response({ cursor, events: [] });
    }
    if (url.pathname === "/api/kernel/read") return response({ objects });
    return response({ error: "unexpected endpoint" }, false);
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("process window replay store", () => {
  it("cold-replays, persists its cursor, and restarts to a byte-equal fold", async () => {
    const storage = new MemoryStorage();
    const firstFetch = vi.fn();
    seededJournal(firstFetch);
    vi.stubGlobal("fetch", firstFetch);

    const first = createProcessWindowStore(storage);
    await first.getState().poll();
    const firstBytes = JSON.stringify(first.getState().sections);
    expect(first.getState().cursor).toBe(2);
    expect(
      first.getState().sections.find((section) => section.id === "needs-you")?.rows[0]
        .children[0].operationId,
    ).toBe("op_child");
    expect(loadProcessCheckpoint(storage).cursor).toBe(2);

    const restartedFetch = vi.fn();
    seededJournal(restartedFetch);
    vi.stubGlobal("fetch", restartedFetch);
    const restarted = createProcessWindowStore(storage);
    await restarted.getState().poll();

    expect(JSON.stringify(restarted.getState().sections)).toBe(firstBytes);
    const firstRestartUrl = new URL(
      String(restartedFetch.mock.calls[0][0]),
      "http://desk.test",
    );
    expect(firstRestartUrl.searchParams.get("after_cursor")).toBe("2");
  });

  it("touches only events and process-read endpoints", async () => {
    const storage = new MemoryStorage();
    const fetcher = vi.fn();
    seededJournal(fetcher);
    vi.stubGlobal("fetch", fetcher);

    await createProcessWindowStore(storage).getState().poll();

    const urls = fetcher.mock.calls.map(([input]) =>
      new URL(String(input), "http://desk.test"),
    );
    expect(new Set(urls.map((url) => url.pathname))).toEqual(
      new Set(["/api/kernel/events", "/api/kernel/read"]),
    );
    for (const url of urls) {
      if (url.pathname === "/api/kernel/events") {
        expect(Number(url.searchParams.get("limit"))).toBeLessThanOrEqual(500);
        expect(url.searchParams.get("stream")).toBe("operations");
      } else {
        expect(url.searchParams.get("view")).toBe("process");
      }
    }
    expect(PROCESS_EVENT_BATCH).toBe(500);
  });

  it("persists every replay page before hydration", async () => {
    const storage = new MemoryStorage();
    const writes = vi.spyOn(storage, "setItem");
    const fetcher = vi.fn(async (input: string) => {
      const url = new URL(String(input), "http://desk.test");
      if (url.pathname === "/api/kernel/events") {
        const cursor = Number(url.searchParams.get("after_cursor") || 0);
        if (cursor === 0) return response({ cursor: 1, events: [events[0]] });
        if (cursor === 1) return response({ cursor: 2, events: [events[1]] });
        return response({ cursor, events: [] });
      }
      return response({ objects });
    });
    vi.stubGlobal("fetch", fetcher);

    await createProcessWindowStore(storage).getState().poll();

    const checkpoints = writes.mock.calls
      .filter(([key]) => key === PROCESS_CHECKPOINT_KEY)
      .map(([, value]) => JSON.parse(value));
    expect(checkpoints.some((checkpoint) => checkpoint.cursor === 1)).toBe(true);
    expect(checkpoints.some((checkpoint) => checkpoint.cursor === 2)).toBe(true);
    expect(checkpoints.at(-1).events).toHaveLength(2);
  });
});
