/** HS-201-01 (counsel fix round, 2026-09-19) — the row clears without a
 *  navigation.
 *
 *  Astra finding 1: the Chair read the assignment roster once, on mount.
 *  The owner repaired the meeting path in Models, came back to the same
 *  open Desk, and the row still asked for an engine until something made
 *  the Chair mount again. So the Chair re-reads the roster on the hub's
 *  `desk_changed` frame and when the window takes focus again.
 */
import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { ChairHome } from "./ChairHome";

vi.mock("../../lib/api", async (original) => ({
  ...await original<typeof import("../../lib/api")>(),
  apiFetch: vi.fn(),
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));

const frameListeners = new Map<string, Set<(frame: { data: unknown }) => void>>();
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, listener: (frame: { data: unknown }) => void) => {
      const set = frameListeners.get(type) ?? new Set();
      set.add(listener);
      frameListeners.set(type, set);
      return () => set.delete(listener);
    },
  }),
  useRuntimeFrame: () => null,
}));

const CAPABILITY = "meeting.deferred_analysis";
const NO_ENGINE = {
  id: CAPABILITY,
  label: "Deferred meeting analysis",
  group: { id: "meetings", label: "Meetings" },
  has_override: false,
  effective: { status: "no_assignment", inherited_from: null, assignment: null, repair: "Choose default" },
  issues: [],
};
const ASSIGNED = {
  ...NO_ENGINE,
  has_override: true,
  effective: { status: "assigned", inherited_from: "capability", assignment: null, repair: null },
};

/** The roster the hub would answer right now; the repair flips it. */
let roster = [NO_ENGINE as Record<string, unknown>];

function wire() {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (String(path) === "/api/inference/assignments")
      return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: roster, issue_count: 0 } as never;
    if (String(path).startsWith("/api/desk/needs-you"))
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
    return null as never;
  });
}

function emitDeskChanged() {
  for (const listener of frameListeners.get("desk_changed") ?? []) {
    listener({ data: { kind: "note", id: "n1", op: "update", origin: "agent" } });
  }
}

describe("HS-201-01 the row clears on the OPEN desk", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    frameListeners.clear();
    roster = [NO_ENGINE as Record<string, unknown>];
    wire();
  });

  it("re-reads the roster when the window takes focus again", async () => {
    render(<ChairHome />);
    await screen.findByText("No engine for summaries");

    // The owner assigns the engine elsewhere (Models, the CLI, an agent),
    // then comes back to this same, never-navigated Desk.
    roster = [ASSIGNED as Record<string, unknown>];
    act(() => { window.dispatchEvent(new Event("focus")); });

    await waitFor(() => expect(screen.queryByTestId("arrival-blocker")).toBeNull());
    expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you");
  });

  // Counsel round 2 (condition 1): the product's own return signal, the
  // one Models fires after it applies a set
  // (`features/concierge/useConciergeController.ts:507` ->
  // `desk/returnToTask.ts:113`, event `holdspeak:settings-updated`).
  it("re-reads the roster on the product's settings-updated signal", async () => {
    render(<ChairHome />);
    await screen.findByText("No engine for summaries");

    roster = [ASSIGNED as Record<string, unknown>];
    act(() => { window.dispatchEvent(new Event("holdspeak:settings-updated")); });

    await waitFor(() => expect(screen.queryByTestId("arrival-blocker")).toBeNull());
    expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you");
  });

  it("re-reads the roster on the hub's desk_changed frame", async () => {
    render(<ChairHome />);
    await screen.findByText("No engine for summaries");
    expect(frameListeners.get("desk_changed")?.size).toBeGreaterThan(0);

    roster = [ASSIGNED as Record<string, unknown>];
    act(() => { emitDeskChanged(); });

    await waitFor(() => expect(screen.queryByTestId("arrival-blocker")).toBeNull(), {
      timeout: 5000,
    });
  });
});
