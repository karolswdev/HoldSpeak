// HS-158-05 → HS-169-03 — ProjectRoomCore rendering tests.
// Selector edits for the 169 rebuild:
//   - orientation band → room head (headline, chips, Draft update)
//   - focus block → NEEDS YOU section
//   - right rail, MetricStrip, SurfaceColumns → removed (the Room is a single column)
//   - four wings (timeline/decisions/search/ask) → two wings (room/history)
//   - REV chip → removed (D1 cut)
//   - DegradedNotice inline → sections degrade individually via the wire
//   - counters (Meetings 0 · Resources 0 · …) → removed (D1 cut)
//   - identity dedup → the name is said once (title bar); no orientation band

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

function WindowHarness({ scope, onTitle }: { scope?: string; onTitle?: (t: string | null) => void }) {
  const [wings, setWings] = useState<ReactNode>(null);
  const setTitle = onTitle ?? (() => {});
  return (
    <TitleSlotContext.Provider value={setTitle}>
      <WingSlotContext.Provider value={setWings}>
        <div data-testid="wing-slot">{wings}</div>
        <ProjectRoomCore scope={scope} />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
  );
}

/** Build a well-formed /room response with the 169 sections. */
function roomResponse(overrides: Record<string, unknown> = {}) {
  return {
    project_id: "p1",
    revision: 3,
    observed_at: "2026-08-31T10:00:00",
    project: {
      id: "p1",
      name: "Alpha Project",
      description: "Testing the room",
      is_archived: false,
      meeting_count: 2,
      created_at: "2026-08-01T00:00:00",
      updated_at: "2026-08-31T10:00:00",
      purpose: "Ship the widget",
      outcome_text: "Widget shipped",
      owner_ref: "person:owner1",
      lifecycle: "active",
      posture: "green",
      posture_reason: "On track",
      start_at: "2026-08-01",
      target_at: "2026-12-01",
      revision: 3,
      ...(overrides.project as Record<string, unknown> || {}),
    },
    items: overrides.items ?? { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: overrides.meetings ?? { state: "ok", count: 2, latest: { id: "m1", title: "Review" } },
    resources: overrides.resources ?? { state: "ok", count: 1, latest: null },
    changes: overrides.changes ?? { state: "ok", recent: [] },
    review: overrides.review ?? { state: "absent", reason: "not_yet_built" },
    needsYou: overrides.needsYou ?? { state: "ok", items: [], count: 0 },
    sources: overrides.sources ?? { state: "ok", items: [], count: 0 },
    health: overrides.health ?? {
      state: "ok",
      assessment: "on_track",
      reason: null,
      inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false },
    },
    sinceRead: overrides.sinceRead ?? { state: "ok", readAt: null, groups: [] },
    decisions: overrides.decisions ?? { state: "ok", items: [] },
    commitments: overrides.commitments ?? { state: "ok", items: [] },
    target: overrides.target ?? { state: "absent", reason: "none" },
    updates: { state: "absent", reason: "not_yet_built" },
    steward: { state: "absent", reason: "not_yet_built" },
  };
}

function detailResponse(url: string) {
  if (url.includes("/meetings"))
    return { meetings: [{ id: "m1", title: "Review", started_at: "2026-07-29T10:00:00Z" }] };
  if (url.startsWith("/api/decisions"))
    return { decisions: [{ id: "d1", text: "Keep grammar", lifecycle: "recorded" }] };
  if (url.includes("/artifacts")) return { artifacts: [] };
  if (url.includes("/since-last-meeting"))
    return { current_meeting: { id: "m1" }, since_last_meeting: {
      previous_meeting: { id: "m0", title: "Kickoff" },
      new_decisions: [], new_actions: [], closed_actions: [],
    }};
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

// HS-169-03 SELECTOR EDIT: orientation band → room head.
// The old test pinned SurfaceIdentity with lifecycle/posture/REV chips.
// The 169 Room head shows a headline, health chip, and Draft update.
describe("ProjectRoomCore — room head (was: orientation band, WEB-NOW-001)", () => {
  it("renders the headline (was: Project name in orientation band)", async () => {
    render(<WindowHarness scope="project:p1" />);
    // HS-169-03: the headline replaces the SurfaceIdentity name
    const headline = await screen.findByTestId("room-headline");
    expect(headline.textContent).toBe("Nothing needs you");
  });

  it("renders health chip when health data is present", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-head-chips");
    // ON TRACK because the fixture has no risk inputs
    expect(screen.getByText("ON TRACK")).toBeTruthy();
  });

  // HS-169-03 SELECTOR EDIT: REV chip is gone (D1 cut).
  // The old test asserted `orientation-revision` with text "REV 3".
  // 169 removes REV entirely; this test now asserts its absence.
  it("does NOT render REV chip (D1 cut)", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    const body = document.querySelector(".room-body");
    expect(body?.textContent).not.toContain("REV ");
  });

  // HS-169-03 SELECTOR EDIT: lifecycle/posture chips → health chip.
  it("does NOT render lifecycle or posture chips (169: replaced by health)", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect(screen.queryByTestId("orientation-lifecycle")).toBeNull();
    expect(screen.queryByTestId("orientation-posture")).toBeNull();
  });
});

// HS-169-03 SELECTOR EDIT: focus block → NEEDS YOU section.
// The old test pinned focus items grouped by kind.
// The 169 Room replaces them with needs-you rows.
describe("ProjectRoomCore — NEEDS YOU (was: focus block)", () => {
  it("renders needs-you section with count (was: focus items grouped by kind)", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          needsYou: {
            state: "ok",
            items: [
              { source: "github", title: "PR needs review", why: "WAITING", url: null, verb: "open", severity: "warning" },
            ],
            count: 1,
          },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect(screen.getByText("PR needs review")).toBeTruthy();
  });

  it("shows empty state text when nothing needs you (was: 'No material yet.')", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    // The fixture has empty needs-you
    expect(screen.getByTestId("needs-you-empty")).toBeTruthy();
  });
});

// HS-169-03 SELECTOR EDIT: degraded sections → sections handle their own degraded state.
// The old test pinned DegradedNotice inline notices. The 169 Room
// sections render nothing for absent/degraded wire sections.
describe("ProjectRoomCore — section degradation (was: degraded section isolation)", () => {
  it("absent sections render nothing (Art VI)", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    // All absent sections produce no DOM
    expect(screen.queryByTestId("degraded-meetings")).toBeNull();
    expect(screen.queryByTestId("degraded-sources")).toBeNull();
  });
});

// HS-169-03 SELECTOR EDIT: right rail → removed.
// The old tests pinned MetricStrip, SurfaceColumns, rail-meetings, etc.
// 169 removes the two-column layout entirely.
describe("ProjectRoomCore — no right rail (was: R2 desktop composition)", () => {
  it("does NOT render SurfaceColumns or MetricStrip (169 single-column)", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect(document.querySelector(".surface-columns")).toBeNull();
    expect(screen.queryByTestId("project-room-rail")).toBeNull();
  });

  it("does NOT render counters (was: Meetings N · Resources N · Watches N · Changes N)", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect(screen.queryByTestId("rail-meetings")).toBeNull();
    expect(screen.queryByTestId("rail-resources")).toBeNull();
    expect(screen.queryByTestId("rail-changes")).toBeNull();
  });
});

// HS-169-03 SELECTOR EDIT: four wings → two wings.
// The old tests may have asserted the four WINGS array.
// The 169 Room has exactly ROOM · HISTORY.
describe("ProjectRoomCore — two wings (was: four wings)", () => {
  it("renders exactly ROOM and HISTORY tabs", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");

    const wingSlot = screen.getByTestId("wing-slot");
    const tabs = wingSlot.querySelectorAll("[role='tab']");
    expect(tabs.length).toBe(2);
    expect(tabs[0].textContent).toBe("Room");
    expect(tabs[1].textContent).toBe("History");
  });
});

describe("ProjectRoomCore — no-scope states", () => {
  it("shows empty state when no project scope is provided", () => {
    render(<ProjectRoomCore />);
    expect(screen.getByText("Open a Project")).toBeTruthy();
  });
});

describe("ProjectRoomCore — window title slot (HS-158-05, WEB-IA-001)", () => {
  it("pushes the project name into the window title when loaded", async () => {
    const onTitle = vi.fn();
    render(<WindowHarness scope="project:p1" onTitle={onTitle} />);

    await waitFor(() =>
      expect(onTitle).toHaveBeenCalledWith("Alpha Project"),
    );
  });

  it("does not push a title when unscoped (manifest label stays)", () => {
    const onTitle = vi.fn();
    render(<WindowHarness onTitle={onTitle} />);

    const calls = onTitle.mock.calls.map((c: unknown[]) => c[0]);
    expect(calls.every((c: unknown) => c === null)).toBe(true);
  });

  it("clears the title on unmount (no stale titles on rescope/close)", async () => {
    const onTitle = vi.fn();
    const { unmount } = render(
      <WindowHarness scope="project:p1" onTitle={onTitle} />,
    );

    await waitFor(() =>
      expect(onTitle).toHaveBeenCalledWith("Alpha Project"),
    );

    onTitle.mockClear();
    unmount();
    expect(onTitle).toHaveBeenCalledWith(null);
  });
});

// HS-169-03 SELECTOR EDIT: identity dedup → the name is said once by the title bar.
// The old dedup test pinned outcome/purpose suppression on the SurfaceIdentity.
// 169 removes the identity band entirely; the name is said once in the title bar.
describe("ProjectRoomCore — name said once (was: identity dedup)", () => {
  it("does NOT render an orientation-band element (169: head replaces it)", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect(screen.queryByTestId("orientation-band")).toBeNull();
  });

  it("does NOT render REV or PROJECT tokens in the body (D1 cut)", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    const body = document.querySelector(".room-body");
    expect(body?.textContent).not.toContain("REV ");
  });
});
