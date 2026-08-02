import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../../desk/api";
import { kindInfo } from "../../../desk/infoContract";
import { VERBS } from "../../../desk/verbRegistry";
import { PRIMITIVES } from "../../../lib/primitives";
import {
  SurfaceWindows,
  useSurfaceWindows,
} from "../../../desk/components/SurfaceWindows";
import { __resetSurfaces, openSurface } from "../../../desk/shell";
import { useDesk } from "../../../desk/store";
import { WingSlotContext } from "../../../desk/surface/wings";
import {
  CitationChips,
  groundedMatchCount,
} from "../../../desk/surface/citations";
import {
  LifecycleChip,
  ProjectMemoryCore,
  composeProjectTimeline,
} from "../ProjectMemoryCore";

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
    <WingSlotContext.Provider value={setWings}>
      <div>{wings}</div>
      <ProjectMemoryCore scope="project:p1" />
    </WingSlotContext.Provider>
  );
}

function response(url: string) {
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
  useSurfaceWindows.setState({ open: {} });
  useDesk.setState({
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
      },
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
    expect(screen.getByText("Superseded → d-next")).toBeTruthy();
  });

  it("renders openable citation chips and derives the honest overflow count", () => {
    render(<CitationChips refs={["meeting:m1", "decision:d1"]} />);
    expect(screen.getByRole("button", { name: "Meeting · m1" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Decision · d1" })).toBeTruthy();
    expect(groundedMatchCount({ matchedCount: 47, overflowCount: 35 })).toBe(
      12,
    );
  });

  it("renders the named comparison and lifecycle in the timeline", async () => {
    render(<ProjectMemoryCore scope="project:p1" scopeLabel="Long memory" />);

    expect(await screen.findByText("Since Kickoff")).toBeTruthy();
    expect(screen.getByText("Keep the Desk grammar")).toBeTruthy();
    expect(screen.getByText("Superseded → d2")).toBeTruthy();
  });

  it("shows an honest empty timeline", async () => {
    apiFetch.mockImplementation((url: string) => {
      const body = response(url);
      if (url.includes("/meetings")) return Promise.resolve({ meetings: [] });
      if (url.startsWith("/api/decisions"))
        return Promise.resolve({ decisions: [] });
      return Promise.resolve(body);
    });
    render(<ProjectMemoryCore scope="project:p1" />);

    expect(await screen.findByText("No project memory yet")).toBeTruthy();
  });

  it("shows an honest zero state after a project-scoped search", async () => {
    apiFetch.mockImplementation((url: string) =>
      Promise.resolve(
        url.startsWith("/api/memory/search") ? { hits: [] } : response(url),
      ),
    );
    render(<WindowHarness />);

    fireEvent.click(await screen.findByRole("tab", { name: "Search" }));
    fireEvent.change(screen.getByRole("searchbox", { name: "Search this project" }), {
      target: { value: "unfindable quasar" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    expect(await screen.findByText("No matches in this project")).toBeTruthy();
  });

  it("registers and restores the scoped Project Memory surface", async () => {
    render(<SurfaceWindows />);
    expect(openSurface("open-project-memory", "project:p1")).toBe(true);
    await waitFor(() =>
      expect(useSurfaceWindows.getState().open["open-project-memory"]).toBe(
        "project:p1",
      ),
    );
  });
});
