// PHILO-13-06 (B1) — the Room's activity rows open their object; the Room's
// load failure is a plain failure name with Try again (the A3 ledger).
// Red on b3805b73: History rows were text only, and a failed /room read
// printed the hub's own message. Harness copied from room169.test.tsx.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../../desk/api";
import { TitleSlotContext } from "../../../desk/surface/title";
import { WingSlotContext } from "../../../desk/surface/wings";
import { useDesk } from "../../../desk/store";
import { openSurfaceOr } from "../../../desk/shell";
import { ProjectRoomCore } from "../ProjectRoomCore";

vi.mock("../../../desk/ask", async () => {
  const actual =
    await vi.importActual<typeof import("../../../desk/ask")>(
      "../../../desk/ask",
    );
  return { ...actual, runAsk: vi.fn() };
});

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual =
    await vi.importActual<typeof import("../../../lib/api")>(
      "../../../lib/api",
    );
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

vi.mock("../../../desk/shell", async () => {
  const actual = await vi.importActual<typeof import("../../../desk/shell")>(
    "../../../desk/shell",
  );
  return { ...actual, openPrimitive: vi.fn(), openSurfaceOr: vi.fn() };
});

function WindowHarness({ scope }: { scope?: string }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <TitleSlotContext.Provider value={() => {}}>
      <WingSlotContext.Provider value={setWings}>
        <div data-testid="wing-slot">{wings}</div>
        <ProjectRoomCore scope={scope} />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
  );
}

/* ── fixture builders ── */

function roomResponse(overrides: Record<string, unknown> = {}) {
  return {
    project_id: "p1",
    revision: 3,
    observed_at: "2026-09-04T10:00:00",
    project: {
      id: "p1",
      name: "Ship the Q4 platform on schedule with zero incidents",
      description: null,
      is_archived: false,
      meeting_count: 2,
      created_at: "2026-08-01T00:00:00",
      updated_at: "2026-09-04T10:00:00",
      purpose: null,
      outcome_text: "Ship the Q4 platform on schedule with zero incidents",
      owner_ref: "person:owner1",
      lifecycle: "active",
      posture: null,
      posture_reason: null,
      start_at: "2026-08-01",
      target_at: "2026-10-15",
      revision: 3,
      ...(overrides.project as Record<string, unknown> || {}),
    },
    items: overrides.items ?? { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: overrides.meetings ?? { state: "ok", count: 2, latest: null },
    resources: overrides.resources ?? { state: "ok", count: 0, latest: null },
    changes: overrides.changes ?? { state: "ok", recent: [] },
    review: overrides.review ?? { state: "absent", reason: "not_yet_built" },
    needsYou: overrides.needsYou ?? {
      state: "ok",
      items: [
        { source: "github", title: "#612 Rig settles animations before every shot", why: "WAITING ON YOUR REVIEW · 3 DAYS", url: "https://github.com/karolswdev/HoldSpeak/pull/612", verb: "open", severity: "danger" },
        { source: "github", title: "CI failing on main", why: "40 MIN AGO", url: null, verb: "open", severity: "danger" },
        { source: "jira", title: "KAN-7 Payments cut-over runbook", why: "OVERDUE · 2 DAYS", url: "https://karolsaneapple.atlassian.net/browse/KAN-7", verb: "open", severity: "warning" },
      ],
      count: 3,
    },
    sources: overrides.sources ?? {
      state: "ok",
      items: [
        { watchId: "w1", provider: "github", scope: "karolswdev/HoldSpeak", tokens: ["12 OPEN PRS", "2 WAITING ON YOU", "CI RED"], checkedAt: "2026-09-04T09:57:00", host: "GITHUB.COM", state: "live", plainReason: null, suggested: false, nextCheckAt: null },
        { watchId: "w2", provider: "jira", scope: "KAN", tokens: ["3 OVERDUE", "5 DUE THIS WEEK"], checkedAt: "2026-09-04T09:57:00", host: "KAROLSANEAPPLE.ATLASSIAN.NET", state: "live", plainReason: null, suggested: false, nextCheckAt: null },
        { watchId: "w3", provider: "meeting", scope: "Meeting activity", tokens: [], checkedAt: null, host: "", state: "cant_check", plainReason: "No local adapter for meeting activity yet", suggested: false, nextCheckAt: null },
      ],
      count: 3,
      nextCheckAt: null,
    },
    health: overrides.health ?? {
      state: "ok",
      assessment: "at_risk",
      reason: "3 OVERDUE",
      inputs: { overdue: 3, ciFailing: true, reviewWaitingDays: 3, targetPassed: false },
    },
    sinceRead: overrides.sinceRead ?? {
      state: "ok",
      readAt: "2026-09-03T09:21:00",
      groups: [
        { source: "GitHub", summary: "2 opened · 1 merged", entries: [
          { phrase: "#618 Footer never truncates a host · opened by mira", at: "2026-09-04T08:00:00", url: null },
          { phrase: "#611 Per-provider proposal cap · merged", at: "2026-09-03T16:00:00", url: null },
        ]},
        { source: "Jira", summary: "1 moved", entries: [
          { phrase: "KAN-2 moved to In Progress", at: "2026-09-03T14:00:00", url: null },
        ]},
        { source: "Room", summary: "", entries: [
          { phrase: "Update drafted", at: "2026-09-02T10:00:00", url: null },
        ]},
      ],
    },
    decisions: overrides.decisions ?? {
      state: "ok",
      items: [
        { id: "dec1", text: "use acli for Jira, never REST", at: "2026-09-02T10:00:00", url: null },
      ],
    },
    commitments: overrides.commitments ?? {
      state: "ok",
      items: [
        { id: "com1", text: "a review of #612", dueAt: "2026-09-06T00:00:00", owner: null },
      ],
    },
    target: overrides.target ?? {
      state: "ok",
      targetAt: "2026-10-15",
      daysLeft: 41,
      passed: false,
    },
    updates: { state: "absent", reason: "not_yet_built" },
    steward: { state: "absent", reason: "not_yet_built" },
  };
}

function quietRoomResponse() {
  return roomResponse({
    needsYou: { state: "ok", items: [], count: 0 },
    health: {
      state: "ok",
      assessment: "on_track",
      reason: null,
      inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false },
    },
    sources: {
      state: "ok",
      items: [
        { watchId: "w1", provider: "github", scope: "karolswdev/HoldSpeak", tokens: ["12 OPEN PRS", "CI GREEN"], checkedAt: "2026-09-04T09:57:00", host: "GITHUB.COM", state: "live", plainReason: null, suggested: false, nextCheckAt: null },
        { watchId: "w2", provider: "jira", scope: "KAN", tokens: ["5 DUE THIS WEEK"], checkedAt: "2026-09-04T09:57:00", host: "KAROLSANEAPPLE.ATLASSIAN.NET", state: "live", plainReason: null, suggested: false, nextCheckAt: null },
      ],
      count: 2,
      nextCheckAt: null,
    },
    sinceRead: {
      state: "ok",
      readAt: null,
      groups: [],
    },
    decisions: { state: "ok", items: [] },
    commitments: { state: "ok", items: [] },
    target: { state: "absent", reason: "none" },
  });
}

function detailResponse(url: string) {
  if (url.includes("/meetings"))
    return { meetings: [{ id: "m1", title: "Review", started_at: "2026-07-29T10:00:00Z" }] };
  if (url.startsWith("/api/decisions"))
    return { decisions: [] };
  if (url.includes("/artifacts")) return { artifacts: [] };
  if (url.includes("/since-last-meeting"))
    return { current_meeting: null, since_last_meeting: null };
  if (url.includes("/room/read"))
    return { read_at: new Date().toISOString() };
  return {};
}

function response(url: string) {
  if (url.includes("/room/read")) return { read_at: new Date().toISOString() };
  if (url.includes("/room")) return roomResponse();
  return detailResponse(url);
}

beforeEach(() => {
  apiFetch.mockImplementation((url: string) => Promise.resolve(response(url)));
  useDesk.setState({
    windowsById: {},
    items: { ...EMPTY_ITEMS },
    projects: [],
    inferenceTargets: [],
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

const CHANGES = {
  state: "ok",
  recent: [
    { id: "c-meeting", change_kind: "project.updated", target_ref: "meeting:p13-cutover-sync", summary_json: "{}", created_at: new Date().toISOString() },
    { id: "c-created", change_kind: "project.created", target_ref: "project:p1", summary_json: "{}", created_at: new Date().toISOString() },
  ],
};

describe("PHILO-13-06: a Room activity row opens its object", () => {
  it("History: the meeting row opens the meeting; the Room's own row draws no Open", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) return Promise.resolve(roomResponse({ changes: CHANGES }));
      return Promise.resolve(detailResponse(url));
    });
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    fireEvent.click(within(screen.getByTestId("wing-slot")).getByRole("tab", { name: "History" }));
    const entries = await screen.findAllByTestId("history-entry");
    expect(entries).toHaveLength(2);
    const opens = screen.getAllByTestId("history-entry-open");
    expect(opens).toHaveLength(1);
    fireEvent.click(opens[0]);
    expect(openSurfaceOr).toHaveBeenCalledWith("review-meetings", "/history", "meeting:p13-cutover-sync");
  });
});

describe("PHILO-13-06: the Room's load failure in plain words", () => {
  it("names the failure, offers Try again, never the hub's text", async () => {
    let fail = true;
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) {
        return fail
          ? Promise.reject(Object.assign(new Error("sqlite3.OperationalError: no such table: rooms"), { status: 500 }))
          : Promise.resolve(roomResponse());
      }
      return Promise.resolve(detailResponse(url));
    });
    render(<WindowHarness scope="project:p1" />);
    const face = await screen.findByTestId("room-load-failed");
    expect(face.textContent).toContain("ROOM DID NOT LOAD · HUB FAILED");
    expect(document.body.textContent).not.toContain("sqlite3");
    fail = false;
    fireEvent.click(within(face).getByRole("button", { name: "Try again" }));
    await screen.findByTestId("room-body");
    await waitFor(() => expect(screen.queryByTestId("room-load-failed")).toBeNull());
  });
});

// Phase 16 (Astra r1 M3): the Room window's History and Steward verbs
// (`openProjectRoomAt`) REVEAL their place, whatever the Room shows: every
// other posture steps aside first, as a proposal request does.
describe("Phase 16: a Room request reveals its place", () => {
  it("Steward opens the Steward posture; History asked for under it shows the History wing", async () => {
    const { openProjectRoomAt } = await import("../../../desk/openObject");
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/steward/runs")) return Promise.resolve({ runs: [] });
      if (url.includes("/room")) return Promise.resolve(roomResponse({ changes: CHANGES }));
      return Promise.resolve(detailResponse(url));
    });
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    openProjectRoomAt("p1", "steward");
    await screen.findByTestId("steward-posture");
    expect(screen.queryByTestId("room-body")).toBeNull();
    openProjectRoomAt("p1", "history");
    await screen.findByTestId("room-history");
    expect(screen.queryByTestId("steward-posture")).toBeNull();
    expect(await screen.findAllByTestId("history-entry")).toHaveLength(2);
  });

  it("Steward asked for from the History wing leaves History for the Steward posture", async () => {
    const { openProjectRoomAt } = await import("../../../desk/openObject");
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/steward/runs")) return Promise.resolve({ runs: [] });
      if (url.includes("/room")) return Promise.resolve(roomResponse({ changes: CHANGES }));
      return Promise.resolve(detailResponse(url));
    });
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    openProjectRoomAt("p1", "history");
    await screen.findByTestId("room-history");
    openProjectRoomAt("p1", "steward");
    await screen.findByTestId("steward-posture");
    expect(screen.queryByTestId("room-history")).toBeNull();
  });
});
