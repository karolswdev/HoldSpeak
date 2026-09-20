// HS-201-11 — a quiet desk for the sitting: the head speaks ONE total.
//
// The rehearsal (audits/rehearsal-07-opus.md, step 1) read `1 need you`
// while the attention list and the SETUP blocker were counted separately.
// The head now speaks one total: the attention list plus what asks beside
// it -- the SETUP row and a FAILED meeting.
//
// Owner's ruling: the calendar row is an OFFER, not a row that asks. A desk
// with no calendar must not say `1 need you` for ever (tenet 3), so
// `Connect calendar` renders beside an all-clear and never moves the count.
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { ChairHome, headlineFor } from "./ChairHome";

vi.mock("../../lib/api", async (original) => ({
  ...await original<typeof import("../../lib/api")>(),
  apiFetch: vi.fn(),
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

describe("HS-201-11 the head speaks one total", () => {
  it("adds what asks outside the attention list", () => {
    // one attention row + one SETUP row = two rows that ask, one total
    expect(headlineFor(1, 1, true, 1)).toBe("2 need you");
    expect(headlineFor(2, 1, true, 2)).toBe("4 need you");
    // the Project clause still speaks for the attention list it counts
    expect(headlineFor(2, 3, true, 1)).toBe("3 need you across 3 projects");
    // pending alone still names itself (HS-201-01 grammar, unchanged)
    expect(headlineFor(0, 1, true, 1)).toBe("1 need you");
    expect(headlineFor(0, 1, true, 0)).toBe("Nothing needs you");
    expect(headlineFor(0, 1, false, 0)).toBe("Coverage incomplete");
  });
});

const NO_ENGINE = {
  id: "meeting.deferred_analysis",
  label: "Deferred meeting analysis",
  group: { id: "meetings", label: "Meetings" },
  has_override: false,
  effective: { status: "no_assignment", inherited_from: null, assignment: null, repair: "Choose default" },
  issues: [],
};
const SPEECH_ASSIGNED = {
  id: "speech.transcribe",
  label: "Speech transcription",
  group: { id: "speech", label: "Speech" },
  has_override: true,
  effective: { status: "assigned", inherited_from: "capability", assignment: null, repair: null },
  issues: [],
};
const ASSIGNED = {
  ...NO_ENGINE,
  has_override: true,
  effective: { status: "assigned", inherited_from: "capability", assignment: null, repair: null },
};

/** `calendarConfigured` is the door's own word; `upcoming: []` leaves the
 *  NEXT line empty, which is exactly when the face draws NO CALENDAR with
 *  its `Connect calendar` Button (ChairHome.tsx, the head token row). */
function wire(overrides: Record<string, unknown>[], calendarConfigured: boolean) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (String(path) === "/api/inference/assignments")
      return {
        schema: "InferenceAssignmentSummary@1",
        rows: [],
        task_overrides: overrides,
        issue_count: 0,
      } as never;
    if (String(path).startsWith("/api/desk/needs-you"))
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
    if (String(path) === "/api/door")
      return { board: {}, upcoming: [], calendar_configured: calendarConfigured } as never;
    return null as never;
  });
}

describe("HS-201-11 the arrival head and its asking rows agree", () => {
  beforeEach(() => vi.mocked(apiFetch).mockReset());

  it("counts the setup row, and the calendar offer beside it never moves it", async () => {
    wire([NO_ENGINE, SPEECH_ASSIGNED], false);
    render(<ChairHome />);
    await screen.findByText("No engine for summaries");
    expect(screen.getByTestId("arrival-blocker-row")).toBeTruthy();
    // the offer IS drawn, with its own library Button
    expect(screen.getByTestId("arrival-connect-calendar")).toBeTruthy();
    expect(screen.getByTestId("arrival-connect-calendar").textContent).toContain(
      "Connect calendar",
    );
    // ...and the head still counts the SETUP row alone
    await waitFor(() =>
      expect(screen.getByTestId("arrival-display").textContent).toBe("1 need you"),
    );
  });

  it("speaks the all-clear beside a calendar offer", async () => {
    wire([ASSIGNED, SPEECH_ASSIGNED], false);
    render(<ChairHome />);
    await waitFor(() =>
      expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"),
    );
    expect(screen.queryByTestId("arrival-blocker")).toBeNull();
    // an offer with no calendar is not an obligation (owner's ruling):
    // the row stands, the head is quiet, and it says the all-clear ONCE.
    expect(screen.getByTestId("arrival-connect-calendar")).toBeTruthy();
    expect(screen.getAllByText("Nothing needs you")).toHaveLength(1);
  });

  it("speaks the all-clear with the calendar connected too", async () => {
    wire([ASSIGNED, SPEECH_ASSIGNED], true);
    render(<ChairHome />);
    await waitFor(() =>
      expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"),
    );
    expect(screen.queryByTestId("arrival-connect-calendar")).toBeNull();
    expect(screen.queryByTestId("arrival-blocker")).toBeNull();
  });
});
