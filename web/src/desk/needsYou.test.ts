import { act, renderHook, waitFor } from "@testing-library/react";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fromWireMeeting } from "./api";
import { apiFetch } from "../lib/api";
import {
  computeNeedsYou,
  useNeedsYou,
  type NeedsYouDoorProjection,
  type NeedsYouInputs,
  type NeedsYouRoomItem,
} from "./needsYou";

vi.mock("../lib/api", async (original) => ({
  ...await original<typeof import("../lib/api")>(),
  apiFetch: vi.fn(),
}));

const NOW = new Date("2026-10-01T12:00:00Z");

function room(
  id: string,
  extra: Partial<NeedsYouRoomItem> = {},
): NeedsYouRoomItem {
  return {
    id,
    ref: id,
    projectId: "p1",
    title: id,
    why: "WAITING",
    severity: "info",
    source: "commitment",
    ...extra,
  };
}

function doorCard(id: string, extra: Record<string, unknown> = {}) {
  return {
    id,
    source: "action_item",
    title: id,
    ...extra,
  };
}

const noEngines = {
  schema: "InferenceAssignmentSummary@1" as const,
  rows: [],
  task_overrides: [
    {
      id: "speech.transcribe",
      label: "Speech",
      group: { id: "meetings", label: "Meetings" },
      has_override: false,
      effective: { status: "no_assignment" as const, inherited_from: null, assignment: null, repair: "Choose an engine" },
      issues: [],
    },
    {
      id: "meeting.deferred_analysis",
      label: "Summary",
      group: { id: "meetings", label: "Meetings" },
      has_override: false,
      effective: { status: "no_assignment" as const, inherited_from: null, assignment: null, repair: "Choose an engine" },
      issues: [],
    },
  ],
  issue_count: 0,
};

function meeting(wire: Record<string, unknown>) {
  const result = fromWireMeeting(wire);
  if (!result) throw new Error("test meeting did not adapt");
  return result;
}

describe("the one needs-you membership", () => {
  it("counts a settled R1-R3 example once and preserves each ref", () => {
    const door: NeedsYouDoorProjection = {
      board: {
        overdue: [doorCard("A1", { due: "2026-09-30" })],
        now: [doorCard("A2", { due: "2026-10-01" })],
        waiting: [doorCard("A3", { owner: "Priya" })],
        unassigned: [doorCard("A4")],
        active: [doorCard("active")],
      },
    };
    const result = computeNeedsYou({
      door,
      roomItems: [
        room("A2-room", {
          ref: "A2",
          title: "A2",
          actionItemId: "A2",
          dueAt: "2026-10-01",
        }),
        room("M1", { projectId: "muted-project", title: "M1" }),
      ],
      mutedProjectIds: ["muted-project"],
      assignments: noEngines,
      assignmentRead: "ok",
      meetings: [
        meeting({ id: "F1", title: "Failed", intel_status: "saved", intel_job: { status: "failed", attempts: 1, last_error: "worker failed" } }),
        meeting({ id: "S1", title: "Saved", intel_status: "ready", intel_job: { status: "complete", attempts: 1, last_error: null } }),
      ],
      now: NOW,
    });

    expect(result.count).toBe(6);
    expect(result.members.map(({ ref }) => ref).sort()).toEqual([
      "A1",
      "A2",
      "A3",
      "A4",
      "F1",
      "blocker:engines",
    ]);
    expect(result.unmutedItems.map((item) => item.ref)).toEqual(["A1", "A2", "A4", "A3"]);
    expect(result.mutedItems.map((item) => item.ref)).toEqual(["M1"]);
  });

  it("keeps a retried job as RETRYING after its due time", () => {
    const retrying = meeting({
      id: "R1",
      title: "Retry",
      intel_status: "ready",
      intel_job: {
        status: "queued",
        attempts: 1,
        last_error: "first attempt failed",
        next_retry_at: "2026-09-30T09:00:00Z",
      },
    });
    const result = computeNeedsYou({ meetings: [retrying], now: NOW });
    expect(result.failedMeetings.map((item) => item.id)).toEqual(["R1"]);
    expect(result.members).toEqual([
      expect.objectContaining({ ref: "R1", kind: "meeting" }),
    ]);
  });

  it("does not infer a missing engine from an absent roster row", () => {
    const result = computeNeedsYou({
      assignments: { ...noEngines, task_overrides: [] },
      assignmentRead: "ok",
    });
    expect(result.blockers).toEqual([]);
    expect(result.count).toBe(0);
  });

  it("makes a failed assignment read unknown instead of clear", () => {
    const result = computeNeedsYou({
      assignments: noEngines,
      assignmentRead: "failed",
    });
    expect(result.blockers.map((blocker) => blocker.key)).toEqual(["unknown"]);
    expect(result.members).toEqual([
      expect.objectContaining({ ref: "blocker:unknown", kind: "blocker" }),
    ]);
  });
});

const HEALTHY_COVERAGE = {
  source_id: "project:alpha",
  kind: "project",
  state: "available" as const,
  observed_at: "2026-10-01T12:00:00Z",
  label: "Alpha",
  project_id: "alpha",
  reason: null,
  repair: null,
};

const FAILED_COVERAGE = {
  source_id: "project:beta",
  kind: "project",
  state: "failed" as const,
  observed_at: null,
  label: "Beta",
  project_id: "beta",
  reason: "read failed",
  repair: { token: "READ FAILED", verb: "Retry", href: "/projects/beta" },
};

function meetingWire(id: string, intelJob?: Record<string, unknown>) {
  return {
    id,
    title: id,
    started_at: "2026-10-01T10:00:00Z",
    intel_status: "ready",
    intel_job: intelJob ?? { status: "complete", attempts: 1, last_error: null },
  };
}

function emptyRoom(overrides: Record<string, unknown> = {}) {
  return {
    items: [],
    projects: [],
    coverage: [],
    complete: true,
    computedAt: "2026-10-01T12:00:00Z",
    stale: false,
    ...overrides,
  };
}

function installWire(options: {
  room?: unknown;
  assignmentError?: boolean;
  roomError?: boolean;
  meetings?: unknown[];
  meetingTotal?: number;
} = {}) {
  const paths: string[] = [];
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    paths.push(String(path));
    if (path === "/api/door") return { board: {} } as never;
    if (path.startsWith("/api/desk/needs-you")) {
      if (options.roomError) throw new Error("Room unavailable");
      return (options.room ?? emptyRoom()) as never;
    }
    if (path === "/api/inference/assignments") {
      if (options.assignmentError) throw new Error("Roster unavailable");
      return { ...noEngines, task_overrides: [] } as never;
    }
    if (path.startsWith("/api/meetings?")) {
      return {
        meetings: options.meetings ?? [],
        total: options.meetingTotal ?? (options.meetings ?? []).length,
      } as never;
    }
    if (path === "/api/settings/heartbeat") return { muted_projects: [] } as never;
    throw new Error(`unexpected needs-you read: ${path}`);
  });
  return paths;
}

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
});

describe("the shared needs-you read", () => {
  it("keeps one poll when an event-only Dock subscribes beside a polling face", async () => {
    installWire();
    const interval = vi.spyOn(globalThis, "setInterval");
    const clear = vi.spyOn(globalThis, "clearInterval");
    const face = renderHook(() => useNeedsYou());
    const dock = renderHook(() => useNeedsYou({ poll: false }));
    try {
      await waitFor(() => expect(face.result.current.loading).toBe(false));
      const polls = interval.mock.calls.filter((call) => call[1] === 60_000);
      expect(polls).toHaveLength(1);
      const timer = interval.mock.results[
        interval.mock.calls.findIndex((call) => call[1] === 60_000)
      ].value;
      dock.unmount();
      expect(clear).not.toHaveBeenCalledWith(timer);
      face.unmount();
      expect(clear.mock.calls.filter((call) => call[0] === timer)).toHaveLength(1);
    } finally {
      dock.unmount();
      face.unmount();
      interval.mockRestore();
      clear.mockRestore();
    }
  });

  it("uses the producer-backed summary filter and never reads an unfiltered meeting page", async () => {
    const home = mkdtempSync(join(tmpdir(), "philo13-a2-c1-hook-"));
    try {
      const seeded = runFixture(home, "seed");
      const wire = seeded.before as Record<string, any>;
      const allMeetings = wire.meetingsWire.meetings as Array<Record<string, unknown>>;
      const attentionMeetings = allMeetings.filter(
        (row) => row.id === "philo13-a2-failed-meeting",
      );
      const paths: string[] = [];
      vi.mocked(apiFetch).mockImplementation(async (path: string) => {
        paths.push(String(path));
        if (path === "/api/door") return wire.door as never;
        if (path.startsWith("/api/desk/needs-you")) return wire.needsYou as never;
        if (path === "/api/inference/assignments") return wire.assignments as never;
        if (path === "/api/settings/heartbeat") return wire.heartbeat as never;
        if (path.startsWith("/api/meetings?summary_attention=true")) {
          return { meetings: attentionMeetings, total: attentionMeetings.length } as never;
        }
        if (path.startsWith("/api/meetings?")) {
          return wire.meetingsWire as never;
        }
        throw new Error(`unexpected needs-you read: ${path}`);
      });

      const hook = renderHook(() => useNeedsYou());
      await waitFor(() => expect(hook.result.current.loading).toBe(false));
      expect(hook.result.current.complete).toBe(true);
      expect(hook.result.current.failedMeetings.map((meeting) => meeting.id)).toEqual([
        "philo13-a2-failed-meeting",
      ]);
      expect(paths.filter((path) => path.startsWith("/api/meetings?"))).toEqual([
        "/api/meetings?summary_attention=true&limit=500&offset=0",
      ]);
      hook.unmount();
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  });

  it("uses the cached Room read on mount and poll, and fresh only for explicit refresh", async () => {
    vi.useFakeTimers();
    try {
      const paths = installWire();
      const hook = renderHook(() => useNeedsYou());
      await vi.waitFor(() => expect(hook.result.current.loading).toBe(false));
      expect(paths.filter((path) => path.startsWith("/api/desk/needs-you"))).toEqual([
        "/api/desk/needs-you",
      ]);

      paths.length = 0;
      await act(async () => {
        vi.advanceTimersByTime(60_000);
        await Promise.resolve();
      });
      await vi.waitFor(() => expect(hook.result.current.loading).toBe(false));
      expect(paths.filter((path) => path.startsWith("/api/desk/needs-you"))).toEqual([
        "/api/desk/needs-you",
      ]);

      paths.length = 0;
      await act(async () => { await hook.result.current.refresh(); });
      expect(paths.filter((path) => path.startsWith("/api/desk/needs-you"))).toEqual([
        "/api/desk/needs-you?fresh=1",
      ]);
      hook.unmount();
    } finally {
      vi.useRealTimers();
    }
  });

  it("paginates meetings by offset when the HTTP route omits next_cursor", async () => {
    const firstPage = Array.from({ length: 500 }, (_, index) => meetingWire(`M${index}`));
    const paths: string[] = [];
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      paths.push(String(path));
      if (path === "/api/door") return { board: {} } as never;
      if (path.startsWith("/api/desk/needs-you")) return emptyRoom() as never;
      if (path === "/api/inference/assignments") return { ...noEngines, task_overrides: [] } as never;
      if (path === "/api/settings/heartbeat") return { muted_projects: [] } as never;
      if (path === "/api/meetings?summary_attention=true&limit=500&offset=0")
        return { meetings: firstPage, total: 501 } as never;
      if (path === "/api/meetings?summary_attention=true&limit=500&offset=500")
        return { meetings: [meetingWire("F501", { status: "failed", attempts: 1, last_error: "worker failed" })], total: 501 } as never;
      throw new Error(`unexpected needs-you read: ${path}`);
    });

    const hook = renderHook(() => useNeedsYou());
    await waitFor(() => expect(hook.result.current.loading).toBe(false));
    expect(paths).toContain("/api/meetings?summary_attention=true&limit=500&offset=500");
    expect(hook.result.current.failedMeetings.map((meeting) => meeting.id)).toEqual(["F501"]);
    hook.unmount();
  });

  it("uses shared coverage semantics when complete is true over a failed row", async () => {
    installWire({ room: emptyRoom({ coverage: [HEALTHY_COVERAGE, FAILED_COVERAGE], complete: true }) });
    const hook = renderHook(() => useNeedsYou());
    await waitFor(() => expect(hook.result.current.loading).toBe(false));
    expect(hook.result.current.complete).toBe(false);
    expect(hook.result.current.room?.coverage).toHaveLength(2);
    hook.unmount();
  });

  it("keeps the meeting-path blocker unknown when the roster read fails", async () => {
    const paths = installWire({ assignmentError: true });
    const hook = renderHook(() => useNeedsYou());
    await waitFor(() => expect(hook.result.current.loading).toBe(false));
    expect(hook.result.current.errors.assignments).toContain("Roster unavailable");
    expect(hook.result.current.blockers.map((blocker) => blocker.key)).toEqual(["unknown"]);
    expect(hook.result.current.complete).toBe(false);
    expect(paths).toContain("/api/inference/assignments");
    hook.unmount();
  });

  it("retains the last Room rows after a later Room read fails", async () => {
    let roomError = false;
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (path === "/api/door") return { board: {} } as never;
      if (path.startsWith("/api/desk/needs-you")) {
        if (roomError) throw new Error("Room unavailable");
        return emptyRoom({ items: [room("kept-room-row")] }) as never;
      }
      if (path === "/api/inference/assignments") return { ...noEngines, task_overrides: [] } as never;
      if (path.startsWith("/api/meetings?")) return { meetings: [], total: 0 } as never;
      if (path === "/api/settings/heartbeat") return { muted_projects: [] } as never;
      throw new Error(`unexpected needs-you read: ${path}`);
    });
    const hook = renderHook(() => useNeedsYou());
    await waitFor(() => expect(hook.result.current.loading).toBe(false));
    expect(hook.result.current.unmutedItems.map((item) => item.ref)).toContain("kept-room-row");

    roomError = true;
    await act(async () => { await hook.result.current.refresh(); });
    expect(hook.result.current.unmutedItems.map((item) => item.ref)).toContain("kept-room-row");
    expect(hook.result.current.errors.room).toContain("Room unavailable");
    expect(hook.result.current.complete).toBe(false);
    hook.unmount();
  });

  it("shares one in-flight read between two mounted consumers", async () => {
    let releaseRoom!: (value: unknown) => void;
    const roomPending = new Promise((resolve) => { releaseRoom = resolve; });
    const paths: string[] = [];
    let freshRoomReads = 0;
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      paths.push(String(path));
      if (path === "/api/door") return { board: {} } as never;
      if (path === "/api/desk/needs-you") return roomPending as never;
      if (path === "/api/desk/needs-you?fresh=1") {
        freshRoomReads += 1;
        return emptyRoom() as never;
      }
      if (path === "/api/inference/assignments") return { ...noEngines, task_overrides: [] } as never;
      if (path.startsWith("/api/meetings?")) return { meetings: [], total: 0 } as never;
      if (path === "/api/settings/heartbeat") return { muted_projects: [] } as never;
      throw new Error(`unexpected needs-you read: ${path}`);
    });
    const first = renderHook(() => useNeedsYou());
    const second = renderHook(() => useNeedsYou());
    expect(paths.filter((path) => path.startsWith("/api/desk/needs-you"))).toHaveLength(1);
    expect(paths.filter((path) => path === "/api/inference/assignments")).toHaveLength(1);

    const refreshes = [first.result.current.refresh(), second.result.current.refresh()];
    await act(async () => {
      releaseRoom(emptyRoom());
      await Promise.all(refreshes);
    });
    expect(freshRoomReads).toBe(1);
    expect(first.result.current.complete).toBe(true);
    expect(second.result.current.complete).toBe(true);
    first.unmount();
    second.unmount();
  });
});

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const FIXTURE_PYTHON = resolve(REPO_ROOT, ".venv/bin/python");
const FIXTURE_SCRIPT = resolve(REPO_ROOT, "scripts/philo13_needs_you_fixture.py");
const ORACLE_REFS = [
  "philo13-a2-A1",
  "A2 confirm the room commitment",
  "philo13-a2-A3",
  "philo13-a2-A4",
  "blocker:engines",
  "philo13-a2-failed-meeting",
];

function runFixture(home: string, mode: "seed" | "export" | "dedup-probe"): Record<string, any> {
  const db = join(home, ".local", "share", "holdspeak", "holdspeak.db");
  const text = execFileSync(
    FIXTURE_PYTHON,
    [FIXTURE_SCRIPT, mode, "--db", db, "--home", home],
    {
      cwd: REPO_ROOT,
      env: { ...process.env, HOME: home },
      encoding: "utf8",
      maxBuffer: 32 * 1024 * 1024,
    },
  );
  return JSON.parse(text) as Record<string, any>;
}

function oracleInputs(payload: Record<string, any>, phase: "before" | "after"): NeedsYouInputs {
  const wire = payload[phase] as Record<string, any>;
  const meetings = (wire.meetingsWire?.meetings ?? wire.meetings ?? [])
    .map((row: unknown) => fromWireMeeting(row))
    .filter((meeting: ReturnType<typeof fromWireMeeting>): meeting is NonNullable<ReturnType<typeof fromWireMeeting>> => meeting !== null);
  return {
    door: wire.door,
    roomItems: wire.roomItems,
    mutedProjectIds: wire.mutedProjects,
    assignments: wire.assignments,
    assignmentRead: wire.assignmentRead,
    meetings,
    now: new Date(wire.now),
  };
}

function assertOracleResult(
  result: ReturnType<typeof computeNeedsYou>,
  expectedRefs: string[],
  expectedCount: number,
) {
  expect(result.count).toBe(expectedCount);
  expect(result.members.map(({ ref }) => ref).sort()).toEqual([...expectedRefs].sort());
  return result;
}

function oracleAssert(input: NeedsYouInputs, expectedRefs: string[], expectedCount: number) {
  return assertOracleResult(computeNeedsYou(input), expectedRefs, expectedCount);
}

describe("the real producer membership oracle", () => {
  it("matches before/after real wire and rejects controlled wrong projections", () => {
    const home = mkdtempSync(join(tmpdir(), "philo13-a2-oracle-"));
    try {
      const seeded = runFixture(home, "seed");
      expect(seeded.mode).toBe("seed");
      const exported = runFixture(home, "export");
      expect(exported.mode).toBe("export");

      const before = oracleInputs(exported, "before");
      const after = oracleInputs(exported, "after");
      const beforeResult = oracleAssert(before, ORACLE_REFS, 6);
      const afterResult = oracleAssert(
        after,
        ORACLE_REFS.filter((ref) => ref !== "philo13-a2-A1"),
        5,
      );
      expect(exported.actualMutation.status).toBe(200);
      expect(exported.actualMutation.method).toBe("PATCH");
      expect(exported.actualMutation.path).toBe("/api/all-action-items/philo13-a2-A1");
      expect(beforeResult.mutedItems.map((item) => item.ref)).toContain("M1 muted project attention");
      expect(beforeResult.members.map(({ ref }) => ref)).not.toContain("M1 muted project attention");
      expect(beforeResult.members.map(({ ref }) => ref)).not.toContain("philo13-a2-D1");
      expect(afterResult.members.map(({ ref }) => ref)).not.toContain("M1 muted project attention");
      expect(afterResult.members.map(({ ref }) => ref)).not.toContain("philo13-a2-D1");

      const roomA2 = before.roomItems?.find((item) => item.ref === "A2 confirm the room commitment");
      expect(roomA2?.actionItemId).toBe((exported.ids as Record<string, string>).A2);
      expect(beforeResult.members.filter(({ ref }) => ref === "A2 confirm the room commitment")).toHaveLength(1);

      const actualA2Id = (exported.ids as Record<string, string>).A2;
      const board = ((before.door as Record<string, any>).board ?? {}) as Record<string, any[]>;
      const a2DoorCard = Object.values(board)
        .flat()
        .find((card) => String(card.id) === actualA2Id);
      expect(a2DoorCard).toBeDefined();

      const mutants: Array<{
        name: string;
        input: NeedsYouInputs;
        project?: (result: ReturnType<typeof computeNeedsYou>) => ReturnType<typeof computeNeedsYou>;
      }> = [
        {
          name: "count M1",
          input: {
            ...before,
            roomItems: before.roomItems?.map((item) =>
              item.ref === "M1 muted project attention" ? { ...item, muted: false } : item,
            ),
            mutedProjectIds: [],
          },
        },
        {
          name: "retain A2 Door duplicate",
          input: before,
          project: (result) => {
            const members = [
              ...result.members,
              { ref: String(a2DoorCard.id), kind: "attention" as const },
            ];
            return { ...result, members, count: members.length };
          },
        },
        {
          name: "drop R3 failed meeting",
          input: {
            ...before,
            meetings: before.meetings?.filter((meeting) => meeting.id !== "philo13-a2-failed-meeting"),
          },
        },
      ];
      for (const mutant of mutants) {
        let rejection: unknown;
        const projected = mutant.project
          ? mutant.project(computeNeedsYou(mutant.input))
          : computeNeedsYou(mutant.input);
        try {
          assertOracleResult(projected, ORACLE_REFS, 6);
        } catch (error) {
          rejection = error;
        }
        console.log(JSON.stringify({
          mutant: mutant.name,
          rejection: rejection instanceof Error ? rejection.message : "NONE",
          expectedCount: 6,
          actualCount: projected.count,
          expectedRefs: ORACLE_REFS,
          actualRefs: projected.members.map(({ ref }) => ref).sort(),
        }));
        expect(rejection).toBeInstanceOf(Error);
      }
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  });

  it("rejects a code mutant that skips dedupAttention on the real producer oracle", async () => {
    const home = mkdtempSync(join(tmpdir(), "philo13-a2-c4-dedup-"));
    try {
      // The pre-fix canonical week had no duplicate producer pair, so this
      // mutant returned six and escaped the C4 fence.
      const probe = runFixture(home, "dedup-probe");
      const before = oracleInputs(probe, "before");
      const expectedRefs = probe.expectedRefs as string[];
      const expectedCount = Number(probe.expectedCount);
      const expectedMutantCount = Number(probe.expectedMutantCount);
      expect(expectedRefs).toEqual(ORACLE_REFS);
      expect(expectedCount).toBe(6);
      expect(expectedMutantCount).toBe(expectedCount + 1);

      const evidence = probe.producerEvidence as Record<string, any>;
      const doorEvidence = evidence.doorRoute as Record<string, any>;
      const roomEvidence = evidence.roomRoute as Record<string, any>;
      expect(doorEvidence.path).toBe("/api/door");
      expect(doorEvidence.id).toBe(evidence.duplicateDoorRef);
      expect(doorEvidence.title).toBe(evidence.duplicateTitle);
      expect(roomEvidence.path).toBe("/api/desk/needs-you?fresh=1");
      expect(roomEvidence.ref).toBe(evidence.duplicateTitle);
      expect(roomEvidence.title).toBe(evidence.duplicateTitle);
      expect(roomEvidence.source).toBe("commitment");
      expect(roomEvidence.projectId).toBe(evidence.duplicateProjectId);
      expect(roomEvidence.actionItemId).not.toBe(evidence.duplicateDoorRef);
      const linkedMeeting = evidence.linkedMeeting as Record<string, any>;
      expect(linkedMeeting.projectId).toBe(evidence.duplicateProjectId);
      expect(linkedMeeting.actionItemId).toBe(evidence.duplicateDoorRef);
      expect(linkedMeeting.title).toBe(evidence.duplicateTitle);
      expect(linkedMeeting.success).toBe(true);

      const door = ((before.door as Record<string, any>).board ?? {}) as Record<string, any[]>;
      const duplicateDoorCard = Object.values(door)
        .flat()
        .find((card) => String(card.id) === doorEvidence.id);
      expect(duplicateDoorCard).toBeDefined();
      expect(duplicateDoorCard?.text).toBe(evidence.duplicateTitle);
      const roomDuplicate = before.roomItems?.find(
        (item) => item.ref === evidence.duplicateTitle && item.source === "commitment",
      );
      expect(roomDuplicate).toMatchObject({
        title: evidence.duplicateTitle,
        projectId: evidence.duplicateProjectId,
        source: "commitment",
      });

      const normal = oracleAssert(before, expectedRefs, expectedCount);
      const mergedA2 = normal.unmutedItems.find(
        (item) => item.ref === evidence.duplicateTitle,
      );
      expect(mergedA2?.sources).toHaveLength(2);
      expect(normal.members.map(({ ref }) => ref)).not.toContain(evidence.duplicateDoorRef);

      const mutant = {
        dedupAttention: (items: readonly NeedsYouRoomItem[]) => [...items],
      };
      const projected = computeNeedsYou(before, mutant);
      let rejection: unknown;
      try {
        expect(projected.count).toBe(expectedCount);
        expect(projected.members.map(({ ref }) => ref).sort()).toEqual([...expectedRefs].sort());
      } catch (error) {
        rejection = error;
      }
      console.log(JSON.stringify({
        mutant: "skip dedupAttention",
        rejection: rejection instanceof Error ? rejection.message : "NONE",
        expectedCount,
        actualCount: projected.count,
        expectedRefs: [...expectedRefs].sort(),
        actualRefs: projected.members.map(({ ref }) => ref).sort(),
        extraRef: evidence.duplicateDoorRef,
      }));
      expect(rejection).toBeInstanceOf(Error);
      expect(projected.count).toBe(expectedMutantCount);
      expect(projected.members.map(({ ref }) => ref)).toContain(evidence.duplicateDoorRef);
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  });
});
