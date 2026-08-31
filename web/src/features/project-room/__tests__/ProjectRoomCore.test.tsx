// HS-158-05 — ProjectRoomCore rendering tests: orientation band,
// focus block, degraded section isolation, empty states.

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
        <div>{wings}</div>
        <ProjectRoomCore scope={scope} />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
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
  it("renders focus items grouped by kind with totals as count-chips", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("focus-block");

    // Should show the focus items
    expect(screen.getByText("Dependency risk")).toBeTruthy();
    expect(screen.getByText("Beta release")).toBeTruthy();

    // R2: totals render as separate count-chip elements, not appended text
    const labels = screen.getAllByTestId("focus-type-label");
    expect(labels.some(el => el.textContent === "Risks")).toBe(true);
    expect(labels.some(el => el.textContent === "Milestones")).toBe(true);

    const chips = screen.getAllByTestId("focus-count-chip");
    expect(chips.some(el => el.textContent === "3")).toBe(true);
    expect(chips.some(el => el.textContent === "2")).toBe(true);
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

describe("ProjectRoomCore — beauty pass (HS-158-05)", () => {
  it("dependency items render under 'Dependencies' (proper plural, not 'Dependencys') with count-chip", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          items: {
            state: "ok",
            focus: [
              { id: "dep-1", project_id: "p1", item_type: "dependency", title: "External API", severity: null, due_at: null, sort_key: 1, created_at: "2026-08-15T00:00:00" },
            ],
            totals_by_type: { dependency: 1 },
            total: 1,
          },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("focus-block");
    // R2: label and count are separate elements
    const labels = screen.getAllByTestId("focus-type-label");
    expect(labels.some(el => el.textContent === "Dependencies")).toBe(true);
    const chips = screen.getAllByTestId("focus-count-chip");
    expect(chips.some(el => el.textContent === "1")).toBe(true);
  });

  it("posture humanizes underscored tokens ('On track' visible, data-posture='on_track')", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          project: { posture: "on_track", posture_reason: "All milestones green" },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    const posture = screen.getByTestId("orientation-posture");
    expect(posture.textContent).toBe("On track");
    expect(posture.getAttribute("data-posture")).toBe("on_track");
  });

  it("severity renders as a toned chip (high=warn, critical=danger, medium/low=quiet)", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          items: {
            state: "ok",
            focus: [
              { id: "item-c", project_id: "p1", item_type: "risk", title: "Critical risk", severity: "critical", due_at: null, sort_key: 1, created_at: "2026-08-15T00:00:00" },
              { id: "item-h", project_id: "p1", item_type: "risk", title: "High risk", severity: "high", due_at: "2026-09-15", sort_key: 2, created_at: "2026-08-15T00:00:00" },
              { id: "item-m", project_id: "p1", item_type: "risk", title: "Medium risk", severity: "medium", due_at: null, sort_key: 3, created_at: "2026-08-15T00:00:00" },
            ],
            totals_by_type: { risk: 3 },
            total: 3,
          },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("focus-block");

    const chips = screen.getAllByTestId("focus-severity");
    const critical = chips.find(el => el.getAttribute("data-severity") === "critical");
    const high = chips.find(el => el.getAttribute("data-severity") === "high");
    const medium = chips.find(el => el.getAttribute("data-severity") === "medium");

    expect(critical).toBeTruthy();
    expect(critical!.getAttribute("data-tone")).toBe("danger");
    expect(critical!.textContent).toBe("Critical");

    expect(high).toBeTruthy();
    expect(high!.getAttribute("data-tone")).toBe("warn");
    expect(high!.textContent).toBe("High");

    expect(medium).toBeTruthy();
    // medium/low are quiet (no tone)
    expect(medium!.getAttribute("data-tone")).toBeNull();
    expect(medium!.textContent).toBe("Medium");
  });

  it("due date renders as a quiet text token, not an input-like chip", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("focus-block");

    const dueTokens = screen.getAllByTestId("focus-due");
    expect(dueTokens.length).toBeGreaterThan(0);
    // R2: de-inputted — a date-token span, not a desk-chip with border
    expect(dueTokens[0].className).toContain("project-room-date-token");
    expect(dueTokens[0].className).not.toContain("desk-chip");
    // Date value is present (glyph + date text)
    expect(dueTokens[0].textContent).toMatch(/\d{4}-\d{2}-\d{2}/);
  });

  it("outcome has its own OUTCOME eyebrow, purpose has PURPOSE (band label symmetry)", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    // R2: both purpose and outcome carry micro-eyebrows
    const purposeEyebrow = screen.getByTestId("purpose-eyebrow");
    expect(purposeEyebrow.textContent).toBe("PURPOSE");
    expect(purposeEyebrow.className).toContain("project-room-eyebrow");

    const outcomeEyebrow = screen.getByTestId("outcome-eyebrow");
    expect(outcomeEyebrow.textContent).toBe("OUTCOME");
    expect(outcomeEyebrow.className).toContain("project-room-eyebrow");

    // Outcome text is visually separate from purpose
    const outcome = screen.getByTestId("orientation-outcome");
    expect(outcome.textContent).toContain("Widget shipped");
  });

  it("degraded items show plain words, machine code in title attribute", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          items: { state: "degraded", error_code: "items_read_failed" },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    const wrapper = await screen.findByTestId("focus-degraded");
    // Plain words on the glass
    expect(screen.getByText("Items unavailable right now.")).toBeTruthy();
    // Machine code NOT visible as text
    expect(screen.queryByText("items_read_failed")).toBeNull();
    // Machine code accessible via title/data attribute
    expect(wrapper.getAttribute("data-error-code")).toBe("items_read_failed");
    expect(wrapper.getAttribute("title")).toBe("items_read_failed");
  });

  it("lifecycle chip carries data-lifecycle attribute", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    const lifecycle = screen.getByTestId("orientation-lifecycle");
    expect(lifecycle.getAttribute("data-lifecycle")).toBe("active");
  });
});

describe("ProjectRoomCore — R2 desktop composition (HS-158-05)", () => {
  it("renders SurfaceColumns (wide-vs-narrow container branch)", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    // The surface-columns wrapper exists for the two-column layout
    const columns = document.querySelector(".surface-columns");
    expect(columns).not.toBeNull();

    // Main column contains the focus block
    const main = document.querySelector(".surface-columns-main");
    expect(main).not.toBeNull();
    expect(main!.querySelector("[data-testid='focus-block']")).not.toBeNull();

    // Side column contains the right rail
    const side = document.querySelector(".surface-columns-side");
    expect(side).not.toBeNull();
    expect(side!.querySelector("[data-testid='project-room-rail']")).not.toBeNull();
  });

  it("right rail renders meetings count + latest from the projection", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    const meetingsSection = screen.getByTestId("rail-meetings");
    expect(meetingsSection).toBeTruthy();
    expect(screen.getByTestId("rail-meetings-count").textContent).toBe("2");
    expect(screen.getByTestId("rail-meetings-latest").textContent).toBe("Review");
  });

  it("right rail renders resources count from the projection", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    const resourcesSection = screen.getByTestId("rail-resources");
    expect(resourcesSection).toBeTruthy();
    expect(screen.getByTestId("rail-resources-count").textContent).toBe("1");
  });

  it("right rail renders changes section from the projection", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    const changesSection = screen.getByTestId("rail-changes");
    expect(changesSection).toBeTruthy();
    expect(screen.getByTestId("rail-changes-count").textContent).toBe("0");
  });

  it("right rail renders change rows when changes exist", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          changes: {
            state: "ok",
            recent: [
              { id: "c1", change_kind: "project.updated", summary_json: { purpose: "x", posture: "y" }, created_at: "2026-08-30T14:00:00" },
              { id: "c2", change_kind: "project.updated", summary_json: { action: "item.created", item_id: "pitem_x", item_type: "risk" }, created_at: "2026-08-29T10:00:00" },
            ],
          },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    const changeRows = screen.getAllByTestId("rail-change-row");
    expect(changeRows.length).toBe(2);
    expect(changeRows[0].textContent).toContain("Updated · purpose, posture");
  });

  it("right rail omits absent sections (Art VI)", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          meetings: { state: "absent", reason: "not_built" },
          resources: { state: "absent", reason: "not_built" },
          changes: { state: "absent", reason: "not_built" },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    expect(screen.queryByTestId("rail-meetings")).toBeNull();
    expect(screen.queryByTestId("rail-resources")).toBeNull();
    expect(screen.queryByTestId("rail-changes")).toBeNull();
  });
});

describe("ProjectRoomCore — R2 token hierarchy (HS-158-05)", () => {
  it("identity facts (lifecycle, posture) left; meta facts (rev, time) right", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("orientation-band");

    // Identity group contains lifecycle and posture
    const identity = screen.getByTestId("facts-identity");
    expect(identity.querySelector("[data-testid='orientation-lifecycle']")).not.toBeNull();
    expect(identity.querySelector("[data-testid='orientation-posture']")).not.toBeNull();

    // Meta group contains revision and activity
    const meta = screen.getByTestId("facts-meta");
    expect(meta.querySelector("[data-testid='orientation-revision']")).not.toBeNull();
    expect(meta.querySelector("[data-testid='orientation-activity']")).not.toBeNull();

    // Meta group uses quieter styling (margin-left: auto pushes right)
    expect(meta.className).toContain("project-room-facts-meta");
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

    // The only call should be null (cleanup or initial) — never a project name.
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
