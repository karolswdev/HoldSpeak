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
import { asHub } from "../../test/hubNeedsYou";
import { meetingPathBlockers } from "./meetingPathBlocker";
import { openChairWindows } from "./__tests__/fixtures/openChairWindows";

// PHILO-14 A1: the Chair is the screen; these specs read its windows, so they open them first.
beforeEach(() => openChairWindows());

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


// PHILO-14 A5: the Needs-you window body is the smart drawer; the SETUP rows
// are its rows (the object, one lamp, one verb) and the head is its display.
const setupRows = () => [...document.querySelectorAll<HTMLElement>(
  '[data-testid="needs-drawer"] .needs-row[data-object-id^="blocker:"]',
)];
const setupRow = () => setupRows()[0] ?? null;

describe("HS-201-01 headline", () => {
  it("never says the all-clear while something is pending", () => {
    expect(headlineFor(0, 1, true, 0)).toBe("Nothing needs you");
    expect(headlineFor(0, 1, true, 1)).toBe("1 needs you");
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
// The other half of the meeting path: audio becomes text before anything
// summarises it (`speech.transcribe`). An OWNER-started recording resolves
// it through the ordinary inheritance chain, so ANY effective assignment
// clears this row. The summary row asks the meeting-intel queue's route
// policy instead (`queue`, PHILO-15 01).
const NO_SPEECH = {
  id: "speech.transcribe",
  label: "Speech transcription",
  group: { id: "speech", label: "Speech" },
  has_override: false,
  effective: { status: "no_assignment", inherited_from: null, assignment: null, repair: "Choose default" },
  issues: [],
};
const SPEECH_ASSIGNED = {
  ...NO_SPEECH,
  has_override: true,
  effective: { status: "assigned", inherited_from: "capability", assignment: null, repair: null },
};
// PHILO-15 01: a `global` head clears the meeting path. The queue's route
// policy (meeting-intel-queue@2) reads it, and the roster says so in
// `queue`; the row asks `queue`, not `has_override`.
const GLOBAL_ONLY = {
  ...NO_ENGINE,
  has_override: false,
  effective: { status: "assigned", inherited_from: "global", assignment: null, repair: null },
  queue: { policy_id: "meeting-intel-queue@2", status: "assigned", inherited_from: "global" },
};
// The queue's answer outranks the owner chain: were the policy to read no
// global head, the row stays although the owner chain resolves one.
const QUEUE_REFUSES = {
  ...GLOBAL_ONLY,
  queue: { policy_id: "meeting-intel-queue@1", status: "no_assignment", inherited_from: null },
};

function wire(overrides: Record<string, unknown>[]) {
  vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
    if (String(path) === "/api/inference/assignments") return summary(overrides) as never;
    if (String(path).startsWith("/api/desk/needs-you"))
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
    if (String(path) === "/api/door") return { board: {}, upcoming: [] } as never;
    return null as never;
  }));
}

describe("HS-201-01 the Chair names the one thing", () => {
  beforeEach(() => vi.mocked(apiFetch).mockReset());

  it("draws ONE row with ONE Button when no engine makes summaries", async () => {
    wire([NO_ENGINE, SPEECH_ASSIGNED]);
    render(<ChairHome />);
    await screen.findByText("No engine for summaries");
    const row = setupRow()!;
    expect(row.textContent).toContain("No engine for summaries");
    const section = setupRow()!;
    expect(setupRows().length).toBe(1);
    const verbs = section.querySelectorAll("button");
    expect(verbs.length).toBe(1);
    expect(verbs[0].textContent).toBe("Choose an engine");
    // no prose: the row says a state and a verb, nothing else
    expect(section.textContent).not.toMatch(/[.!?]/);
    // and the headline does not lie over it
    expect(screen.getByTestId("arrival-display").textContent).toBe("1 needs you");
  });

  it("is gone once the summary capability is assigned", async () => {
    wire([ASSIGNED]);
    render(<ChairHome />);
    await waitFor(() =>
      expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"),
    );
    expect(setupRow()).toBeNull();
  });

  it("clears when only the default (global) head exists: the queue runs on it", async () => {
    wire([GLOBAL_ONLY, SPEECH_ASSIGNED]);
    render(<ChairHome />);
    await waitFor(() =>
      expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"),
    );
    expect(setupRow()).toBeNull();
    expect(screen.queryByText("No engine for summaries")).toBeNull();
    expect(meetingPathBlockers(summary([GLOBAL_ONLY, SPEECH_ASSIGNED]) as never)).toEqual([]);
  });

  it("draws no row when the owner turned summaries OFF over a default", async () => {
    const OFF = {
      ...GLOBAL_ONLY,
      queue: { policy_id: "meeting-intel-queue@2", status: "off", inherited_from: null },
    };
    expect(meetingPathBlockers(summary([OFF, SPEECH_ASSIGNED]) as never)).toEqual([]);
    // OFF is not a missing engine: with no speech either, only speech asks.
    expect(meetingPathBlockers(summary([OFF, NO_SPEECH]) as never)).toEqual([
      { key: "speech", label: "No engine for speech", verb: "Choose an engine" },
    ]);
    wire([OFF, SPEECH_ASSIGNED]);
    render(<ChairHome />);
    await waitFor(() =>
      expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"),
    );
    expect(setupRow()).toBeNull();
    expect(screen.queryByText("No engine for summaries")).toBeNull();
  });

  it("asks the queue's answer, not the owner chain", () => {
    expect(meetingPathBlockers(summary([QUEUE_REFUSES, SPEECH_ASSIGNED]) as never)).toEqual([
      { key: "summary", label: "No engine for summaries", verb: "Choose an engine" },
    ]);
    // Nothing assigned anywhere: one row for both halves.
    expect(meetingPathBlockers(summary([NO_ENGINE, NO_SPEECH]) as never)).toEqual([
      { key: "engines", label: "No engine yet", verb: "Choose an engine" },
    ]);
  });

  // Counsel fix round, second pass (ruling 1): a read still in flight
  // draws NO setup row -- no noise on every arrival (tenet 3) -- and the
  // headline still withholds the all-clear over the unknown.
  it("draws no setup row while the roster read is still in flight", async () => {
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
      if (String(path) === "/api/inference/assignments")
        return new Promise(() => {}) as never; // never settles
      if (String(path).startsWith("/api/desk/needs-you"))
        return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      return null as never;
    }));
    render(<ChairHome />);
    await waitFor(() => {
      expect(setupRow()).toBeNull();
      expect(screen.getByTestId("arrival-display").textContent).not.toBe("Nothing needs you");
    });
  });

  // Counsel fix round (Astra finding 3): a FAILED read is an UNKNOWN,
  // and an unknown is never drawn as a clear desk. The Chair names the
  // unknown as its own row instead (UX-CANON A10 - honest states).
  it("names the unknown as its own row when the roster could not be read", async () => {
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
      if (String(path) === "/api/inference/assignments") throw new Error("offline");
      if (String(path).startsWith("/api/desk/needs-you"))
        return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      return null as never;
    }));
    render(<ChairHome />);
    const row = await screen.findByText("Could not read setup");
    expect(row).toBeTruthy();
    expect(screen.getByTestId("arrival-display").textContent).not.toBe("Nothing needs you");
    // one verb, and it is the library Button
    const section = setupRow()!;
    const verbs = section.querySelectorAll("button");
    expect(verbs.length).toBe(1);
    expect(verbs[0].className).toContain("btn");
  });

  // Counsel fix round (Muad'Dib response 3): the speech engine is the
  // other half of the meeting path. A recording with no transcription
  // engine produces nothing to summarise.
  it("draws a row when no engine transcribes speech", async () => {
    wire([ASSIGNED, NO_SPEECH]);
    render(<ChairHome />);
    const row = await screen.findByText("No engine for speech");
    expect(row).toBeTruthy();
    const section = setupRow()!;
    const verbs = section.querySelectorAll("button");
    expect(verbs.length).toBe(1);
    expect(verbs[0].textContent).toBe("Choose an engine");
    expect(screen.getByTestId("arrival-display").textContent).toBe("1 needs you");
  });

  // Counsel fix round, second pass (ruling 2): ONE filled primary on the
  // face. Neither engine assigned is ONE state -- "no engine yet" -- and
  // it is drawn as one row with one Button.
  it("draws ONE row when neither engine is assigned", async () => {
    wire([NO_ENGINE, NO_SPEECH]);
    render(<ChairHome />);
    await screen.findByText("No engine yet");
    const section = setupRow()!;
    expect(setupRows().length).toBe(1);
    const verbs = section.querySelectorAll("button");
    expect(verbs.length).toBe(1);
    expect(verbs[0].textContent).toBe("Choose an engine");
    // ...and it is not a second FILLED primary: the ratified law gives
    // the filled primary to the attention band, and a quiet face has none
    // (full-suite fallout, test_hs200_attention_glass.py:463, :694).
    expect(section.querySelectorAll(".btn--primary").length).toBe(0);
    expect(verbs[0].className).toContain("btn");
    expect(screen.queryByText("No engine for speech")).toBeNull();
    expect(screen.queryByText("No engine for summaries")).toBeNull();
    expect(screen.getByTestId("arrival-display").textContent).toBe("1 needs you");
  });

  it("clears the speech row when the speech capability is assigned", async () => {
    wire([ASSIGNED, SPEECH_ASSIGNED]);
    render(<ChairHome />);
    await waitFor(() =>
      expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"),
    );
    expect(setupRow()).toBeNull();
  });
});

// The row is NOT driven by `/api/setup/status.primary_action`: that field
// may name a microphone or a first-dictation step, which Models cannot
// repair (story Scope; setup_status.py:59-82).
describe("HS-201-01 a microphone action never opens Models", () => {
  beforeEach(() => vi.mocked(apiFetch).mockReset());

  it("draws no blocker row for a microphone primary_action", async () => {
    const asked: string[] = [];
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
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
    }));
    render(<ChairHome />);
    await waitFor(() =>
      expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"),
    );
    expect(setupRow()).toBeNull();
    expect(document.querySelector("[data-verb='setup']")).toBeNull();
  });
});
