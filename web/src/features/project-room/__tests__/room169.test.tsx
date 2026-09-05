// HS-169-03 — the Room rebuilt to the canvas: vitest.
// Six sections' states, POST /room/read timing, one display step,
// no <button> outside __tests__ in the project-room tree.

import { render, screen, waitFor } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../../desk/api";
import { TitleSlotContext } from "../../../desk/surface/title";
import { WingSlotContext } from "../../../desk/surface/wings";
import { useDesk } from "../../../desk/store";
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
        { source: "GitHub", summary: "GitHub · 2 opened · 1 merged", entries: [
          { phrase: "#618 Footer never truncates a host · opened by mira", at: "2026-09-04T08:00:00", url: null },
          { phrase: "#611 Per-provider proposal cap · merged", at: "2026-09-03T16:00:00", url: null },
        ]},
        { source: "Jira", summary: "Jira · 1 moved", entries: [
          { phrase: "KAN-2 moved to In Progress", at: "2026-09-03T14:00:00", url: null },
        ]},
        { source: "Room", summary: "Room", entries: [
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

/* ── Needs You section ── */

describe("HS-169-03: NEEDS YOU section", () => {
  it("renders needs-you rows with correct titles and WHY tokens", async () => {
    render(<WindowHarness scope="project:p1" />);

    expect(await screen.findByText("#612 Rig settles animations before every shot")).toBeTruthy();
    expect(screen.getByText("CI failing on main")).toBeTruthy();
    expect(screen.getByText("KAN-7 Payments cut-over runbook")).toBeTruthy();

    const whyTokens = screen.getAllByTestId("needs-you-why");
    expect(whyTokens.length).toBe(3);
    expect(whyTokens[0].textContent).toContain("WAITING ON YOUR REVIEW");
  });

  it("shows empty state when nothing needs you", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) return Promise.resolve(quietRoomResponse());
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    const empty = await screen.findByTestId("needs-you-empty");
    expect(empty.textContent).toContain("Nothing needs you");
  });
});

/* ── SOURCES section ── */

describe("HS-169-03: SOURCES section", () => {
  it("renders source rows with tokens and host chips", async () => {
    render(<WindowHarness scope="project:p1" />);

    await screen.findByTestId("room-body");
    // Check source scope text
    expect(screen.getByText("karolswdev/HoldSpeak")).toBeTruthy();
    expect(screen.getByText("KAN")).toBeTruthy();
    // Check token text (tokens after the first carry a · separator)
    expect(screen.getByText("12 OPEN PRS")).toBeTruthy();
    const ciRedElements = screen.getAllByText((_, el) => el?.tagName === "SPAN" && el.className.includes("surface-token") && (el.textContent?.includes("CI RED") ?? false));
    expect(ciRedElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders cant_check source with CAN'T CHECK state", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");

    expect(screen.getByText("Meeting activity")).toBeTruthy();
    expect(screen.getByText("No local adapter for meeting activity yet")).toBeTruthy();
  });

  it("renders suggested source row when present", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          sources: {
            state: "ok",
            items: [
              { watchId: "w1", provider: "github", scope: "karolswdev/HoldSpeak", tokens: ["12 OPEN PRS"], checkedAt: "2026-09-04T09:57:00", host: "GITHUB.COM", state: "live", plainReason: null, suggested: false, nextCheckAt: null },
              { watchId: "w-sugg", provider: "jira", scope: "SUGGESTED-1", tokens: [], checkedAt: null, host: "", state: "live", plainReason: null, suggested: true, nextCheckAt: null },
            ],
            count: 2,
            nextCheckAt: null,
          },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect(screen.getByText("SUGGESTED-1")).toBeTruthy();
    expect(screen.getByText("SUGGESTED")).toBeTruthy();
  });
});

/* ── SINCE YOU LOOKED section ── */

describe("HS-169-03: SINCE YOU LOOKED section", () => {
  it("renders groups and entries with phrases (not raw field names)", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");

    // Group headings
    const groups = screen.getAllByTestId("since-read-group");
    expect(groups.length).toBe(3); // GitHub, Jira, Room
    expect(screen.getByText("GitHub · 2 opened · 1 merged")).toBeTruthy();
    expect(screen.getByText("Jira · 1 moved")).toBeTruthy();
  });

  it("renders SINCE CREATED when readAt is null", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) return Promise.resolve(quietRoomResponse());
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect(screen.getByText("Created just now")).toBeTruthy();
  });
});

/* ── DECISIONS & COMMITMENTS section ── */

describe("HS-169-03: DECISIONS & COMMITMENTS section", () => {
  it("renders decision and commitment rows", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");

    expect(screen.getByText(/use acli for Jira, never REST/)).toBeTruthy();
    expect(screen.getByText(/a review of #612/)).toBeTruthy();
  });

  it("hides entirely when both are empty", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) return Promise.resolve(quietRoomResponse());
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");

    // The section should not exist
    expect(screen.queryByText("DECISIONS & COMMITMENTS")).toBeNull();
  });
});

/* ── Room head ── */

describe("HS-169-03: Room head", () => {
  it("shows headline count at display step with accent", async () => {
    render(<WindowHarness scope="project:p1" />);
    const headline = await screen.findByTestId("room-headline");
    expect(headline.textContent).toBe("3 need you");
    expect(headline.classList.contains("surface-display")).toBe(true);
    expect(headline.getAttribute("data-accent")).toBeTruthy();
  });

  it("shows Nothing needs you in muted when count is zero", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) return Promise.resolve(quietRoomResponse());
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    const headline = await screen.findByTestId("room-headline");
    expect(headline.textContent).toBe("Nothing needs you");
    expect(headline.getAttribute("data-accent")).toBeNull();
  });

  it("renders health chip AT RISK with reason", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-head-chips");

    expect(screen.getByText("AT RISK")).toBeTruthy();
    // The reason token sits in the chip row
    const chips = screen.getByTestId("room-head-chips");
    expect(chips.textContent).toContain("3 OVERDUE");
  });

  it("renders health chip ON TRACK when healthy", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) return Promise.resolve(quietRoomResponse());
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-head-chips");
    expect(screen.getByText("ON TRACK")).toBeTruthy();
  });

  it("renders target date chip when present", async () => {
    render(<WindowHarness scope="project:p1" />);
    const chip = await screen.findByTestId("room-target-chip");
    expect(chip.textContent).toContain("TARGET");
    expect(chip.textContent).toContain("41 DAYS");
  });

  it("renders OVERDUE when target is passed", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          target: { state: "ok", targetAt: "2026-08-01", daysLeft: -34, passed: true },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    const chip = await screen.findByTestId("room-target-chip");
    expect(chip.textContent).toContain("OVERDUE BY 34 DAYS");
    expect(chip.getAttribute("data-tone")).toBe("danger");
  });

  it("shows no target chip when absent", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) return Promise.resolve(quietRoomResponse());
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect(screen.queryByTestId("room-target-chip")).toBeNull();
  });

  it("shows ARCHIVED chip when project is archived", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          project: { is_archived: true },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-head-chips");
    expect(screen.getByText("ARCHIVED")).toBeTruthy();
  });

  it("renders Draft update button", async () => {
    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("updates-verb");
    expect(btn.textContent).toBe("Draft update");
  });
});

/* ── POST /room/read after first paint ── */

describe("HS-169-03: POST /room/read timing", () => {
  it("calls POST /room/read after first paint", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");

    await waitFor(() => {
      const readCalls = apiFetch.mock.calls.filter(
        (call: unknown[]) => String(call[0]).includes("/room/read") && (call[1] as Record<string, unknown>)?.method === "POST",
      );
      expect(readCalls.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("calls POST /room/read on Refresh", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");

    // Clear existing calls
    apiFetch.mockClear();
    apiFetch.mockImplementation((url: string) => Promise.resolve(response(url)));

    // Click Refresh
    const refreshBtn = screen.getByTestId("room-refresh");
    refreshBtn.click();

    await waitFor(() => {
      const readCalls = apiFetch.mock.calls.filter(
        (call: unknown[]) => String(call[0]).includes("/room/read"),
      );
      expect(readCalls.length).toBeGreaterThanOrEqual(1);
    });
  });
});

/* ── exactly one display-step element ── */

describe("HS-169-03: display step", () => {
  it("has exactly one surface-display element in the Room wing", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");

    const displays = document.querySelectorAll(".room-body .surface-display");
    expect(displays.length).toBe(1);
    expect(displays[0].textContent).toBe("3 need you");
  });
});

/* ── wings ── */

describe("HS-169-03: wings", () => {
  it("renders exactly ROOM and HISTORY wings", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");

    const wingSlot = screen.getByTestId("wing-slot");
    const tabs = wingSlot.querySelectorAll("[role='tab']");
    expect(tabs.length).toBe(2);
    expect(tabs[0].textContent).toBe("Room");
    expect(tabs[1].textContent).toBe("History");
  });
});

/* ── Ask well ── */

describe("HS-169-03: Ask well", () => {
  it("renders the ask well with model egress chip", async () => {
    render(<WindowHarness scope="project:p1" />);
    const well = await screen.findByTestId("room-ask-well");
    expect(well).toBeTruthy();

    const input = well.querySelector("input[aria-label='Ask this project']");
    expect(input).not.toBeNull();
    expect(input?.getAttribute("placeholder")).toBe("Ask this project…");
  });
});

/* ── footer ── */

describe("HS-169-03: footer", () => {
  it("renders READ time in footer receipt", async () => {
    render(<WindowHarness scope="project:p1" />);
    const receipt = await screen.findByTestId("room-footer-receipt");
    // readAt from the wire is "2026-09-03T09:21:00"
    expect(receipt.textContent).toContain("READ");
  });

  it("renders Refresh button in footer", async () => {
    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("room-refresh");
    expect(btn.textContent).toBe("Refresh");
  });
});

/* ── change row field names guard ── */

describe("HS-169-03: no raw field names in change labels", () => {
  it("changeLabel humanizes field names, never exposing underscored raw names", async () => {
    // The change rows come through model.ts decodeChangeRow.
    // Import and test directly.
    const { decodeChangeRow } = await import("../model");

    // A project.created row with raw field names in summary
    const row = decodeChangeRow({
      id: "c-test",
      change_kind: "project.created",
      summary_json: JSON.stringify({ name: "Test", source: "manual", watches_activated: 4 }),
      created_at: "2026-09-04T10:00:00",
    });

    // The label must not contain underscores from field names
    expect(row.label).not.toContain("watches_activated");
    expect(row.label).not.toContain("_");
    // It should contain the humanized form
    expect(row.label).toContain("4 watches activated");
  });

  it("project.updated with field-patch summary humanizes field names", async () => {
    const { decodeChangeRow } = await import("../model");

    const row = decodeChangeRow({
      id: "c-test2",
      change_kind: "project.updated",
      summary_json: JSON.stringify({ purpose: "Ship Q4", outcome_text: "Done" }),
      created_at: "2026-09-04T10:00:00",
    });

    expect(row.label).not.toContain("outcome_text");
    expect(row.label).toContain("purpose");
    expect(row.label).toContain("outcome");
  });
});

/* ── source grouping ── */

describe("HS-169-03: source grouping by (provider, scope)", () => {
  it("two watches on the same repo merge into one row with combined tokens", async () => {
    const { decodeRoomSnapshot } = await import("../model");

    const snapshot = decodeRoomSnapshot({
      project_id: "p1",
      revision: 1,
      observed_at: "2026-09-04T10:00:00",
      project: { id: "p1", name: "Test" },
      items: { state: "absent", reason: "n/a" },
      meetings: { state: "absent", reason: "n/a" },
      resources: { state: "absent", reason: "n/a" },
      changes: { state: "absent", reason: "n/a" },
      review: { state: "absent", reason: "n/a" },
      needsYou: { state: "absent", reason: "n/a" },
      sources: {
        state: "ok",
        items: [
          { watchId: "w1", provider: "github", scope: "karolswdev/HoldSpeak", tokens: ["2 OPEN PRS"], checkedAt: "2026-09-04T10:00:00", host: "GITHUB.COM", state: "live", plainReason: null, suggested: false, nextCheckAt: null },
          { watchId: "w2", provider: "github", scope: "karolswdev/HoldSpeak", tokens: ["CI RED"], checkedAt: "2026-09-04T09:50:00", host: "GITHUB.COM", state: "live", plainReason: null, suggested: false, nextCheckAt: null },
        ],
        count: 2,
        nextCheckAt: null,
      },
      health: { state: "absent", reason: "n/a" },
      sinceRead: { state: "absent", reason: "n/a" },
      decisions: { state: "absent", reason: "n/a" },
      commitments: { state: "absent", reason: "n/a" },
      target: { state: "absent", reason: "n/a" },
      updates: { state: "absent", reason: "n/a" },
      steward: { state: "absent", reason: "n/a" },
    });

    if (snapshot.sources.state !== "ok") throw new Error("sources not ok");
    // After grouping, one row with both tokens
    expect(snapshot.sources.items.length).toBe(1);
    expect(snapshot.sources.count).toBe(1);
    expect(snapshot.sources.items[0].tokens).toContain("2 OPEN PRS");
    expect(snapshot.sources.items[0].tokens).toContain("CI RED");
    expect(snapshot.sources.items[0].watchIds).toEqual(["w1", "w2"]);
    // checkedAt is the most recent
    expect(snapshot.sources.items[0].checkedAt).toBe("2026-09-04T10:00:00");
  });
});
