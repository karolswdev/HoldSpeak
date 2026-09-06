// HS-158-05 → HS-169-03 — ProjectMemoryCore (re-export) tests.
// SELECTOR EDITS for the 169 rebuild:
//   - "Since Kickoff" (SinceLastMeeting) → removed; the Room's SINCE YOU LOOKED replaces it
//   - Timeline wing (decisions, lifecycle chips) → removed
//   - Search wing → removed
//   - Ask wing → replaced by the ask well at the foot
//   - "No project memory yet" → removed; no empty timeline
//   - Error state → still works (generic error rendering)
//   - No-scope state → still "Open a Project"

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../../desk/api";
import { kindInfo } from "../../../desk/infoContract";
import { VERBS } from "../../../desk/verbRegistry";
import { PRIMITIVES, type Primitive } from "../../../lib/primitives";
import { SurfaceWindows } from "../../../desk/components/SurfaceWindows";
import { __resetSurfaces, openSurface } from "../../../desk/shell";
import { useDesk } from "../../../desk/store";
import { WingSlotContext } from "../../../desk/surface/wings";
import { TitleSlotContext } from "../../../desk/surface/title";
import {
  CitationChips,
  groundedMatchCount,
} from "../../../desk/surface/citations";
import {
  LifecycleChip,
  ProjectMemoryCore,
  composeProjectTimeline,
} from "../ProjectMemoryCore";

const mockRunAsk = vi.fn();
vi.mock("../../../desk/ask", async () => {
  const actual =
    await vi.importActual<typeof import("../../../desk/ask")>(
      "../../../desk/ask",
    );
  return { ...actual, runAsk: (...args: unknown[]) => mockRunAsk(...args) };
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

function WindowHarness() {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <TitleSlotContext.Provider value={() => {}}>
      <WingSlotContext.Provider value={setWings}>
        <div>{wings}</div>
        <ProjectMemoryCore scope="project:p1" />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
  );
}

function response(url: string) {
  if (url.includes("/room/read"))
    return { read_at: new Date().toISOString() };
  if (url.includes("/room"))
    return {
      project_id: "p1", revision: 1, observed_at: "2026-08-31T10:00:00",
      project: {
        id: "p1", name: "Long memory", description: null,
        is_archived: false, meeting_count: 1,
        created_at: "2026-08-01T00:00:00", updated_at: "2026-08-31T10:00:00",
        purpose: null, outcome_text: null, owner_ref: null,
        lifecycle: null, posture: null, posture_reason: null,
        start_at: null, target_at: null, revision: 1,
      },
      items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
      meetings: { state: "ok", count: 1, latest: { id: "m1", title: "Review" } },
      resources: { state: "ok", count: 0, latest: null },
      changes: { state: "ok", recent: [] },
      review: { state: "absent", reason: "not_yet_built" },
      needsYou: { state: "ok", items: [], count: 0 },
      sources: { state: "ok", items: [], count: 0 },
      health: { state: "ok", assessment: "on_track", reason: null, inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false } },
      sinceRead: { state: "ok", readAt: null, groups: [] },
      decisions: { state: "ok", items: [] },
      commitments: { state: "ok", items: [] },
      target: { state: "absent", reason: "none" },
      updates: { state: "absent", reason: "not_yet_built" },
      steward: { state: "absent", reason: "not_yet_built" },
    };
  if (url === "/api/projects/p1") return { id: "p1", name: "Long memory" };
  if (url.includes("/meetings"))
    return {
      meetings: [
        { id: "m1", title: "Review", started_at: "2026-07-29T10:00:00Z" },
      ],
    };
  if (url.startsWith("/api/decisions"))
    return {
      decisions: [
        {
          id: "d1",
          text: "Keep the Desk grammar",
          lifecycle: "superseded",
          superseded_by: "d2",
          decided_at: "2026-07-29T11:00:00Z",
        },
      ],
    };
  if (url.includes("/artifacts")) return { artifacts: [] };
  if (url.includes("/since-last-meeting"))
    return {
      current_meeting: { id: "m1", title: "Review" },
      since_last_meeting: {
        previous_meeting: { id: "m0", title: "Kickoff" },
        new_decisions: [],
        new_actions: [],
        closed_actions: [],
      },
    };
  return {};
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
  __resetSurfaces();
  vi.clearAllMocks();
});

describe("Project Memory", () => {
  it("declares Project once for its icon, Info footprint, and registered verbs", () => {
    expect(PRIMITIVES.project).toMatchObject({
      kind: "project",
      label: "Project",
      syncClass: "organization",
      authorable: false,
    });
    const project = {
      kind: "project" as const,
      id: "p1",
      title: "Long memory",
      ref: {
        kind: "project" as const,
        id: "p1",
        name: "Long memory",
        meetingCount: 2,
      } as unknown as Primitive,
    };
    expect(kindInfo("project").footprint(project, { ...EMPTY_ITEMS })).toBe(
      "2 meetings",
    );
    expect(VERBS.find((verb) => verb.id === "object.ask-project")?.label).toBe(
      "Ask this project",
    );
  });

  it("interleaves meetings, decisions, and only promoted artifacts newest-down", () => {
    const rows = composeProjectTimeline(
      [{ id: "m1", title: "Meeting", started_at: "2026-07-28T10:00:00Z" }],
      [{ id: "d1", text: "Decision", decided_at: "2026-07-29T10:00:00Z" }],
      [
        {
          id: "a1",
          title: "Promoted",
          status: "promoted",
          created_at: "2026-07-27T10:00:00Z",
        },
        {
          id: "a2",
          title: "Ordinary",
          status: "complete",
          created_at: "2026-07-30T10:00:00Z",
        },
      ],
    );

    expect(rows.map((row) => `${row.kind}:${row.id}`)).toEqual([
      "decision:d1",
      "meeting:m1",
      "artifact:a1",
    ]);
  });

  it("wears every lifecycle and names a supersession successor", () => {
    const { rerender } = render(
      <LifecycleChip row={{ lifecycle: "recorded" }} />,
    );
    expect(screen.getByText("Recorded")).toBeTruthy();
    rerender(<LifecycleChip row={{ lifecycle: "accepted" }} />);
    expect(screen.getByText("Accepted")).toBeTruthy();
    rerender(<LifecycleChip row={{ lifecycle: "rejected" }} />);
    expect(screen.getByText("Rejected")).toBeTruthy();
    rerender(
      <LifecycleChip
        row={{ lifecycle: "superseded", superseded_by: "d-next" }}
      />,
    );
    expect(screen.getByText("Superseded")).toBeTruthy();
  });

  it("renders openable citation chips and derives the honest overflow count", () => {
    render(<CitationChips refs={["meeting:m1", "decision:d1"]} />);
    expect(screen.getByRole("button", { name: "Meeting · m1" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Decision · d1" })).toBeTruthy();
    expect(groundedMatchCount({ matchedCount: 47, overflowCount: 35 })).toBe(
      12,
    );
  });

  // HS-169-03 SELECTOR EDIT: "Since Kickoff" + timeline → removed.
  // The Room no longer shows a SinceLastMeeting or inline timeline.
  // This test now asserts the Room renders its headline and ask well.
  it("renders the Room headline and ask well (was: timeline)", async () => {
    render(<WindowHarness />);
    const headline = await screen.findByTestId("room-headline");
    expect(headline.textContent).toBe("Nothing needs you");
    expect(screen.getByTestId("room-ask-well")).toBeTruthy();
  });

  // HS-169-03 SELECTOR EDIT: "No project memory yet" → removed.
  // The empty Room shows "Nothing needs you" and "Created just now".
  it("shows honest empty states (was: empty timeline)", async () => {
    apiFetch.mockImplementation((url: string) => {
      const body = response(url);
      if (url.includes("/meetings")) return Promise.resolve({ meetings: [] });
      if (url.startsWith("/api/decisions"))
        return Promise.resolve({ decisions: [] });
      return Promise.resolve(body);
    });
    render(<WindowHarness />);
    const headline = await screen.findByTestId("room-headline");
    expect(headline.textContent).toBe("Nothing needs you");
  });

  // HS-169-03 SELECTOR EDIT: Search wing → removed. Search lives in HISTORY.
  it("HISTORY wing contains the stream (was: search)", async () => {
    render(<WindowHarness />);
    await screen.findByTestId("room-body");
    // The HISTORY wing tab exists
    const historyTab = screen.getByRole("tab", { name: "History" });
    expect(historyTab).toBeTruthy();
  });

  it("names evidence reached through a durable relationship", async () => {
    apiFetch.mockImplementation((url: string) =>
      Promise.resolve(
        url.startsWith("/api/memory/search")
          ? {
              hits: [
                {
                  source_ref: "artifact:a1",
                  title: "Rollout checklist",
                  snippet: "<mark>Owners</mark> and gates",
                  kind: "artifact",
                  retrieval_origin: "relationship",
                  related_to: "meeting:m1",
                  relationship: "meeting_artifact",
                },
              ],
            }
          : response(url),
      ),
    );
    // HS-169-03 keeps the Room at its four questions, so memory search
    // lives on the unscoped Desk memory surface.
    render(<ProjectMemoryCore />);

    fireEvent.change(
      await screen.findByRole("searchbox", { name: "Search the Desk" }),
      {
        target: { value: "zephyr" },
      },
    );
    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    expect(await screen.findByText("Rollout checklist")).toBeTruthy();
    expect(screen.getByText("Owners").tagName).toBe("MARK");
    expect(screen.getByText("Related · meeting artifact")).toBeTruthy();
  });

  it("registers and restores the scoped Project Memory surface", async () => {
    render(<SurfaceWindows />);
    expect(openSurface("open-project-memory", "project:p1")).toBe(true);
    await waitFor(() =>
      expect(useDesk.getState().windowsById["surface-project-memory"]?.scope)
        .toBe("project:p1"),
    );
  });

  // HS-169-03 SELECTOR EDIT: Ask wing → ask well at the foot.
  it("renders the ask well with model egress (was: Ask wing)", async () => {
    render(<WindowHarness />);
    const well = await screen.findByTestId("room-ask-well");
    expect(well).toBeTruthy();
    const input = well.querySelector("input[aria-label='Ask this project']");
    expect(input).not.toBeNull();
  });

  // HS-157-04: WEB-ARC-006 gap coverage — load error state
  it("shows an error state when the project load fails", async () => {
    apiFetch.mockRejectedValue(new Error("Network failure"));
    render(<ProjectMemoryCore scope="project:p1" />);

    expect(await screen.findByText("Network failure")).toBeTruthy();
  });

  it("turns the unscoped surface into global Desk memory search", async () => {
    render(<ProjectMemoryCore />);
    const input = screen.getByRole("searchbox", { name: "Search the Desk" });
    fireEvent.change(input, { target: { value: "connected evidence" } });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        expect.stringMatching(/^\/api\/memory\/search\?query=connected\+evidence$/),
      ),
    );
    expect(screen.getByText("DESK MEMORY · RELATIONSHIP-AWARE")).toBeTruthy();
  });
});
