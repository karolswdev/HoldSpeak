// HS-201-01 — the desk names the one thing it needs.
//
// Two fences:
//   1. the headline never reads `Nothing needs you` while something is
//      pending (the meeting-path blocker, or a FAILED meeting);
//   2. the Chair draws the blocker as ONE row with ONE library Button
//      that opens Models, and the row is gone once an engine is assigned.
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

describe("HS-201-01 headline", () => {
  it("never says the all-clear while something is pending", () => {
    expect(headlineFor(0, 1, true, 0)).toBe("Nothing needs you");
    expect(headlineFor(0, 1, true, 1)).toBe("1 need you");
    expect(headlineFor(0, 1, true, 2)).toBe("2 need you");
    // an incomplete read still names the coverage, not the all-clear
    expect(headlineFor(0, 1, false, 0)).toBe("Coverage incomplete");
    // the existing grammar is untouched
    expect(headlineFor(17, 3)).toBe("17 need you across 3 projects");
    expect(headlineFor(3, 1)).toBe("3 need you");
  });
});

// ── The blocker row ────────────────────────────────────────────────

function summary(overrides: Record<string, unknown>[]) {
  return {
    schema: "InferenceAssignmentSummary@1",
    rows: [],
    task_overrides: overrides,
    issue_count: 0,
  };
}

const NO_ENGINE = {
  id: "meeting.deferred_analysis",
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
// A `global` head does NOT clear the meeting path: the queue's service
// route policy permits only the `capability` source
// (inference_service_route_policy.py:43, :93).
const GLOBAL_ONLY = {
  ...NO_ENGINE,
  has_override: false,
  effective: { status: "assigned", inherited_from: "global", assignment: null, repair: null },
};

function wire(overrides: Record<string, unknown>[]) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (String(path) === "/api/inference/assignments") return summary(overrides) as never;
    if (String(path).startsWith("/api/desk/needs-you"))
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
    if (String(path) === "/api/door") return { board: {}, upcoming: [] } as never;
    return null as never;
  });
}

describe("HS-201-01 the Chair names the one thing", () => {
  beforeEach(() => vi.mocked(apiFetch).mockReset());

  it("draws ONE row with ONE Button when no engine makes summaries", async () => {
    wire([NO_ENGINE]);
    render(<ChairHome />);
    const row = await screen.findByTestId("arrival-blocker-row");
    expect(row.textContent).toContain("No engine for summaries");
    const section = screen.getByTestId("arrival-blocker");
    expect(section.querySelectorAll("[data-testid='arrival-blocker-row']").length).toBe(1);
    const verbs = section.querySelectorAll("button");
    expect(verbs.length).toBe(1);
    expect(verbs[0].textContent).toBe("Choose an engine");
    // no prose: the row says a state and a verb, nothing else
    expect(section.textContent).not.toMatch(/[.!?]/);
    // and the headline does not lie over it
    expect(screen.getByTestId("arrival-display").textContent).toBe("1 need you");
  });

  it("is gone once the summary capability is assigned", async () => {
    wire([ASSIGNED]);
    render(<ChairHome />);
    await waitFor(() =>
      expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"),
    );
    expect(screen.queryByTestId("arrival-blocker")).toBeNull();
  });

  it("stays while only a global head exists (the queue cannot use it)", async () => {
    wire([GLOBAL_ONLY]);
    render(<ChairHome />);
    expect(await screen.findByTestId("arrival-blocker-row")).toBeTruthy();
  });

  it("is withheld when the roster could not be read", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path) === "/api/inference/assignments") throw new Error("offline");
      if (String(path).startsWith("/api/desk/needs-you"))
        return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      return null as never;
    });
    render(<ChairHome />);
    await waitFor(() =>
      expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"),
    );
    expect(screen.queryByTestId("arrival-blocker")).toBeNull();
  });
});

// The row is NOT driven by `/api/setup/status.primary_action`: that field
// may name a microphone or a first-dictation step, which Models cannot
// repair (story Scope; setup_status.py:59-82).
describe("HS-201-01 a microphone action never opens Models", () => {
  beforeEach(() => vi.mocked(apiFetch).mockReset());

  it("draws no blocker row for a microphone primary_action", async () => {
    const asked: string[] = [];
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      asked.push(String(path));
      if (String(path) === "/api/inference/assignments") return summary([ASSIGNED]) as never;
      if (String(path) === "/api/setup/status")
        return {
          overall: "needs_attention",
          primary_action: { id: "microphone-access", label: "Allow the microphone", route: "/setup#microphone-access" },
        } as never;
      if (String(path).startsWith("/api/desk/needs-you"))
        return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      return null as never;
    });
    render(<ChairHome />);
    await waitFor(() =>
      expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"),
    );
    expect(screen.queryByTestId("arrival-blocker")).toBeNull();
    expect(screen.queryByTestId("arrival-blocker-verb")).toBeNull();
  });
});
