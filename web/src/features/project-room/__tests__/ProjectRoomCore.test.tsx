// HS-158-05 — ProjectRoomCore rendering tests: orientation band,
// focus block, degraded section isolation, empty states.

import { render, screen, waitFor } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../../desk/api";
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
    <WingSlotContext.Provider value={setWings}>
      <div>{wings}</div>
      <ProjectRoomCore scope={scope} />
    </WingSlotContext.Provider>
  );
}

/** Build a well-formed /room response. */
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
    items: overrides.items ?? {
      state: "ok",
      focus: [
        {
          id: "item-1",
          project_id: "p1",
          item_type: "risk",
          title: "Dependency risk",
          severity: "high",
          due_at: "2026-09-01",
          sort_key: 1.0,
          created_at: "2026-08-15T00:00:00",
        },
        {
          id: "item-2",
          project_id: "p1",
          item_type: "milestone",
          title: "Beta release",
          severity: null,
          due_at: "2026-10-01",
          sort_key: 2.0,
          created_at: "2026-08-16T00:00:00",
        },
      ],
      totals_by_type: { risk: 3, milestone: 2 },
      total: 5,
    },
    meetings: overrides.meetings ?? { state: "ok", count: 2, latest: { id: "m1", title: "Review" } },
    resources: overrides.resources ?? { state: "ok", count: 1, latest: null },
    changes: overrides.changes ?? { state: "ok", recent: [] },
    review: { state: "absent", reason: "not_yet_built" },
    sources: { state: "absent", reason: "not_yet_built" },
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
  return {};
}

function response(url: string) {
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

describe("ProjectRoomCore — orientation band (WEB-NOW-001, WEB-IA-001)", () => {
  it("renders the Project name in the orientation band (WEB-IA-001)", async () => {
    render(<WindowHarness scope="project:p1" />);
    const name = await screen.findByTestId("project-room-name");
    expect(name.textContent).toBe("Alpha Project");
  });

  it("renders purpose and outcome when present", async () => {
    render(<WindowHarness scope="project:p1" />);
    expect(await screen.findByTestId("orientation-purpose")).toHaveTextContent("Ship the widget");
    expect(screen.getByTestId("orientation-outcome")).toHaveTextContent("Widget shipped");
  });

  it("renders lifecycle and posture as separate facts (WEB-LC-001/002)", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    const lifecycle = screen.getByTestId("orientation-lifecycle");
    expect(lifecycle.textContent).toBe("Active");

    const posture = screen.getByTestId("orientation-posture");
    expect(posture.textContent).toBe("Green");
    expect(posture.getAttribute("title")).toBe("On track");
  });

  it("renders revision and last activity", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    const revision = screen.getByTestId("orientation-revision");
    expect(revision.textContent).toContain("REV 3");

    const activity = screen.getByTestId("orientation-activity");
    expect(activity.textContent).toBeTruthy();
  });

  it("omits purpose/outcome/posture when absent (Art VI)", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          project: { purpose: null, outcome_text: null, posture: null, posture_reason: null },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    expect(screen.queryByTestId("orientation-purpose")).toBeNull();
    expect(screen.queryByTestId("orientation-outcome")).toBeNull();
    expect(screen.queryByTestId("orientation-posture")).toBeNull();
  });

  it("omits lifecycle chip when lifecycle is null", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({ project: { lifecycle: null } }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");
    expect(screen.queryByTestId("orientation-lifecycle")).toBeNull();
  });
});

describe("ProjectRoomCore — focus block", () => {
  it("renders focus items grouped by kind with totals", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("focus-block");

    // Should show the focus items
    expect(screen.getByText("Dependency risk")).toBeTruthy();
    expect(screen.getByText("Beta release")).toBeTruthy();

    // Should show totals per type
    expect(screen.getByText(/Risks 3/)).toBeTruthy();
    expect(screen.getByText(/Milestones 2/)).toBeTruthy();
  });

  it("shows 'No material yet.' for empty focus (WEB-STA-003)", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    expect(await screen.findByText("No material yet.")).toBeTruthy();
  });

  it("renders degraded items section with error message", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          items: { state: "degraded", error_code: "items_read_failed" },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    expect(await screen.findByText(/Items unavailable/)).toBeTruthy();
  });
});

describe("ProjectRoomCore — degraded section isolation (WEB-STA-002)", () => {
  it("degraded meetings shows inline notice, does not blank orientation", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          meetings: { state: "degraded", error_code: "meetings_read_failed" },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    // Orientation still renders
    expect(await screen.findByTestId("project-room-name")).toHaveTextContent("Alpha Project");
    // Degraded notice shows
    expect(screen.getByTestId("degraded-meetings")).toBeTruthy();
    // Focus still shows
    expect(screen.getByText("Dependency risk")).toBeTruthy();
  });

  it("absent sections render NOTHING (Art VI: no teaser placeholders)", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    // Absent sections: review, sources, updates, steward — should have no DOM presence
    expect(screen.queryByTestId("degraded-review")).toBeNull();
    expect(screen.queryByTestId("degraded-sources")).toBeNull();
    expect(screen.queryByTestId("degraded-updates")).toBeNull();
    expect(screen.queryByTestId("degraded-steward")).toBeNull();
  });
});

describe("ProjectRoomCore — no-scope states", () => {
  it("shows empty state when no project scope is provided", () => {
    render(<ProjectRoomCore />);
    expect(screen.getByText("Open a Project")).toBeTruthy();
  });
});
