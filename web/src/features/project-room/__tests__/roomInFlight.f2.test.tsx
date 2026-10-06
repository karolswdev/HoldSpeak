// Conductor F2 (ratified boards K4b, K6): the Room's OPEN HERE rows wear the
// agent working on them, and a merged PR that closed a commitment names it on
// the Room receipt line. Harness copied from roomOpen.philo1306.test.tsx.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useAgentFlights } from "../../../desk/agentFlights";
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

const NOW = Date.now();
const MERGED_AT = new Date(NOW - 5 * 60 * 1000).toISOString();

function flight(over: Record<string, unknown>) {
  return {
    origin_ref: "action:ai-runbook", kind: "action", id: "ai-runbook", title: "Write the rollback runbook",
    project_id: "p1", project_name: "Payments ledger cutover", agent: "claude", state: "waiting",
    session_key: "claude:s1", pr: null, close: null, merged_at: null, launch_id: "l1", ...over,
  };
}

const OPEN_HERE = {
  state: "ok",
  count: 3,
  items: [
    { source: "meeting", kind: "action_item", title: "Write the rollback runbook", why: "OWNER · UNKNOWN", url: null, verb: "open", severity: "warning", action_item_id: "ai-runbook" },
    { source: "meeting", kind: "action_item", title: "Shard the reconciliation job", why: "OWNER · UNKNOWN", url: null, verb: "open", severity: "warning", action_item_id: "ai-recon" },
    { source: "meeting", kind: "action_item", title: "Add the ledger freeze flag", why: "OWNER · UNKNOWN", url: null, verb: "open", severity: "warning", action_item_id: "ai-flag" },
  ],
};

function wire(flights: unknown[], needsYou: unknown = OPEN_HERE) {
  apiFetch.mockImplementation((url: string) => {
    if (url.startsWith("/api/coders/sessions")) return Promise.resolve({ sessions: [], flights });
    if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
    if (url.includes("/room")) return Promise.resolve(roomResponse({ needsYou }));
    return Promise.resolve(detailResponse(url));
  });
}

describe("Conductor F2 K4b: OPEN HERE rows wear their agent", () => {
  beforeEach(() => useAgentFlights.setState({ sessions: [], flights: [], loaded: false }));

  it("waiting, working and PR open, each with its verb", async () => {
    wire([
      flight({}),
      flight({ origin_ref: "action:ai-recon", id: "ai-recon", title: "Shard the reconciliation job", agent: "codex", state: "working", session_key: "codex:x1" }),
      flight({ origin_ref: "action:ai-flag", id: "ai-flag", title: "Add the ledger freeze flag", state: "pr_open", session_key: null,
        pr: { number: 412, url: "https://github.com/acme/ledger/pull/412", state: "open" } }),
    ]);
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() => expect(screen.getAllByTestId("flight-chip")).toHaveLength(3));
    const rows = screen.getAllByTestId("needs-you-row");
    expect(within(rows[0]).getByTestId("flight-chip").textContent).toContain("CLAUDE CODE · WAITING");
    expect(within(rows[1]).getByTestId("flight-chip").textContent).toContain("CODEX · WORKING");
    expect(within(rows[2]).getByTestId("flight-chip").textContent).toContain("PR #412 · OPEN");
    expect(within(rows[0]).getByRole("button", { name: "Open session: Write the rollback runbook" })).toBeTruthy();
    // Egress where egress happens: the host chip beside Open PR.
    expect(within(rows[2]).getByText("GITHUB.COM")).toBeTruthy();
    const open = vi.spyOn(window, "open").mockImplementation(() => null);
    fireEvent.click(within(rows[2]).getByRole("button", { name: "Open PR #412: Add the ledger freeze flag" }));
    expect(open).toHaveBeenCalledWith("https://github.com/acme/ledger/pull/412", "_blank", "noopener");
    // Each row keeps its own Open.
    expect(within(rows[0]).getByTestId("needs-you-open-action")).toBeTruthy();
  });

  it("a row with no flight wears no chip", async () => {
    wire([]);
    render(<WindowHarness scope="project:p1" />);
    await screen.findAllByTestId("needs-you-row");
    expect(screen.queryByTestId("flight-chip")).toBeNull();
  });
});

describe("Conductor F2 K6: the merge receipt", () => {
  beforeEach(() => useAgentFlights.setState({ sessions: [], flights: [], loaded: false }));

  it("names the closed commitment, its PR and the time on the Room receipt line", async () => {
    wire([flight({ state: "merged", close: "closed", merged_at: MERGED_AT,
      pr: { number: 413, url: "https://github.com/acme/ledger/pull/413", state: "merged" } })],
      { state: "ok", count: 2, items: OPEN_HERE.items.slice(1) });
    render(<WindowHarness scope="project:p1" />);
    const receipt = await screen.findByTestId("room-merge-receipt");
    const d = new Date(MERGED_AT);
    const hhmm = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
    expect(receipt.textContent).toBe(`DONE · Write the rollback runbook · PR #413 MERGED · ${hhmm}`);
    expect(screen.queryByText("Write the rollback runbook", { selector: ".surface-primary" })).toBeNull();
  });

  it("another Project's merge, or a merge not closed, writes no receipt", async () => {
    wire([
      flight({ state: "merged", close: "closed", merged_at: MERGED_AT, project_id: "p2", pr: { number: 9, url: "u", state: "merged" } }),
      flight({ origin_ref: "action:ai-flag", state: "merged", close: "awaiting_confirm", merged_at: MERGED_AT, pr: { number: 10, url: "u", state: "merged" } }),
    ]);
    render(<WindowHarness scope="project:p1" />);
    await screen.findAllByTestId("needs-you-row");
    expect(screen.queryByTestId("room-merge-receipt")).toBeNull();
    expect(screen.getByTestId("room-footer-receipt")).toBeTruthy();
  });
});
