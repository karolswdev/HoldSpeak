// HS-163-05 -- StewardPosture mounted-path tests: posture swap, run states,
// stop, receipts, policy round-trip.
// Proves the mount: from the real Room, open the Steward posture by real clicks.
// Pattern: UpdatePosture.test.tsx (the 162 exemplar).

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TitleSlotContext } from "../../../../desk/surface/title";
import { WingSlotContext } from "../../../../desk/surface/wings";
import { useDesk } from "../../../../desk/store";
import { EMPTY_ITEMS } from "../../../../desk/api";
import { ProjectRoomCore } from "../../ProjectRoomCore";

// ── Mocks ──

vi.mock("../../../../desk/ask", async () => {
  const actual =
    await vi.importActual<typeof import("../../../../desk/ask")>(
      "../../../../desk/ask",
    );
  return { ...actual, runAsk: vi.fn() };
});

vi.mock("../../../../desk/components/DeskEditor", () => ({
  DeskEditor: ({
    value,
    onChange,
    ariaLabel,
    placeholder,
  }: {
    value: string;
    onChange: (value: string) => void;
    ariaLabel?: string;
    placeholder?: string;
  }) => (
    <textarea
      aria-label={ariaLabel || "Body"}
      data-testid="mock-desk-editor"
      placeholder={placeholder}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  ),
}));

const apiFetch = vi.fn();
vi.mock("../../../../lib/api", async () => {
  const actual =
    await vi.importActual<typeof import("../../../../lib/api")>(
      "../../../../lib/api",
    );
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

const mockOpenPrimitive = vi.fn();
const mockOpenSurfaceOr = vi.fn();
vi.mock("../../../../desk/shell", async () => {
  const actual = await vi.importActual<typeof import("../../../../desk/shell")>(
    "../../../../desk/shell",
  );
  return {
    ...actual,
    openPrimitive: (...args: unknown[]) => mockOpenPrimitive(...args),
    openSurfaceOr: (...args: unknown[]) => mockOpenSurfaceOr(...args),
  };
});

// ── Harness ──

function WindowHarness({ scope }: { scope?: string }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <TitleSlotContext.Provider value={() => {}}>
      <WingSlotContext.Provider value={setWings}>
        <div>{wings}</div>
        <ProjectRoomCore scope={scope} />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
  );
}

// ── Fixture factories (mined from tests/integration/test_steward_routes.py) ──

function roomResponse(overrides: Record<string, unknown> = {}) {
  return {
    project_id: "p1",
    revision: 5,
    observed_at: "2026-09-01T10:00:00",
    project: {
      id: "p1",
      name: "Steward Project",
      description: "Testing steward",
      is_archived: false,
      meeting_count: 2,
      created_at: "2026-08-01T00:00:00",
      updated_at: "2026-09-01T10:00:00",
      purpose: "Ship the widget",
      outcome_text: "Widget shipped",
      owner_ref: "person:owner1",
      lifecycle: "active",
      posture: "green",
      posture_reason: "On track",
      start_at: "2026-08-01",
      target_at: "2026-12-01",
      revision: 5,
    },
    items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: { state: "ok", count: 2, latest: { id: "m1", title: "Review" } },
    resources: { state: "ok", count: 1, latest: null },
    changes: { state: "ok", recent: [] },
    review: { state: "absent", reason: "not_yet_built" },
    sources: { state: "absent", reason: "not_yet_built" },
    updates: { state: "absent", reason: "not_yet_built" },
    steward: overrides.steward ?? { state: "ok" },
    ...overrides,
  };
}

function detailResponse(url: string) {
  if (url.includes("/meetings")) return { meetings: [] };
  if (url.startsWith("/api/decisions")) return { decisions: [] };
  if (url.includes("/artifacts")) return { artifacts: [] };
  if (url.includes("/since-last-meeting"))
    return { current_meeting: null, since_last_meeting: null };
  return {};
}

/** A completed run fixture (wire shape from _serialize_run). */
function completedRunFixture(overrides: Record<string, unknown> = {}) {
  return {
    id: "pstrun_abcdef1234567890",
    project_id: "p1",
    policy_id: null,
    state: "completed",
    phase: "record",
    requested_by: "steward-test",
    watermark: "",
    summary: {
      outcome: "completed",
      phases_completed: ["observe", "compare", "propose", "act", "verify", "record"],
      effects_applied: 2,
    },
    created_at: "2026-09-01T09:14:00",
    updated_at: "2026-09-01T09:15:00",
    started_at: "2026-09-01T09:14:01",
    completed_at: "2026-09-01T09:15:00",
    stop_requested_at: null,
    ...overrides,
  };
}

/** A running run fixture (for polling). */
function runningRunFixture(overrides: Record<string, unknown> = {}) {
  return completedRunFixture({
    id: "pstrun_running123456789",
    state: "running",
    phase: "observe",
    summary: {},
    completed_at: null,
    ...overrides,
  });
}

/** An interrupted run fixture. */
function interruptedRunFixture(overrides: Record<string, unknown> = {}) {
  return completedRunFixture({
    id: "pstrun_interrupted12345",
    state: "interrupted",
    summary: {
      outcome: "interrupted",
      reason: "stop_requested",
      interrupted_phase: "observe",
    },
    ...overrides,
  });
}

/** Step fixtures (wire shape from _serialize_step). */
function completedStepFixture(overrides: Record<string, unknown> = {}) {
  return {
    id: "pststep_step1234567890",
    phase: "observe",
    seq: 0,
    state: "completed",
    effect_kind: "refresh_sources",
    idempotency_key: "pstrun_abcdef1234567890:observe",
    expected: {},
    observed: { ok: true },
    receipt: { action: "observe", result: "ok", ref: "item:itm-001" },
    error: null,
    ...overrides,
  };
}

function stepsForCompletedRun() {
  return [
    completedStepFixture({
      id: "pststep_step001",
      phase: "observe",
      seq: 0,
      effect_kind: "refresh_sources",
      receipt: { action: "observe", result: "ok", ref: "item:itm-001" },
    }),
    completedStepFixture({
      id: "pststep_step002",
      phase: "propose",
      seq: 1,
      effect_kind: "create_proposals",
      receipt: { action: "propose", result: "ok", ref: "decision:dec-001" },
    }),
    completedStepFixture({
      id: "pststep_step003",
      phase: "act",
      seq: 2,
      effect_kind: "draft_update",
      receipt: { action: "act", result: "ok", ref: "update:upd-001" },
    }),
    completedStepFixture({
      id: "pststep_step004",
      phase: "act",
      seq: 3,
      effect_kind: "create_door_item",
      receipt: { action: "act", result: "ok", ref: "observation:obs-001" },
    }),
  ];
}

/** Policy fixture (wire shape from _serialize_policy). */
function policyFixture(overrides: Record<string, unknown> = {}) {
  return {
    id: "pstpol_policy12345678",
    project_id: "p1",
    eligible_effect_kinds: ["refresh_sources", "draft_update"],
    yolo_flags: {},
    max_retries: 5,
    max_actions_per_run: 20,
    cooldown_seconds: 60,
    bounds: { max_proposals: 10 },
    enabled: true,
    created_at: "2026-09-01T08:00:00",
    updated_at: "2026-09-01T08:00:00",
    ...overrides,
  };
}

// ── Lifecycle ──

beforeEach(() => {
  useDesk.setState({
    windowsById: {},
    items: { ...EMPTY_ITEMS },
    projects: [],
    inferenceTargets: [],
  });
  mockOpenPrimitive.mockClear();
  mockOpenSurfaceOr.mockClear();
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

afterEach(() => {
  vi.clearAllMocks();
  vi.useRealTimers();
});

// ── Helpers ──

/** Set up apiFetch to serve the room + details + steward endpoints. */
function setupStewardPosture(opts: {
  listRuns?: Record<string, unknown>[];
  runDetail?: {
    run: Record<string, unknown>;
    steps: Record<string, unknown>[];
  };
  startRunResult?: Record<string, unknown>;
  policy?: Record<string, unknown> | null;
} = {}) {
  const listRuns = opts.listRuns ?? [completedRunFixture()];
  const runDetail = opts.runDetail ?? {
    run: completedRunFixture(),
    steps: stepsForCompletedRun(),
  };
  const startResult = opts.startRunResult ?? {
    success: true,
    run_id: "pstrun_new_run_12345678",
  };
  const policyVal = opts.policy !== undefined ? opts.policy : null;

  apiFetch.mockImplementation((url: string, init?: Record<string, unknown>) => {
    // Room
    if (url.includes("/room")) {
      return Promise.resolve(roomResponse());
    }
    // Steward runs list
    if (url.match(/\/api\/projects\/[^/]+\/steward\/runs$/) && (!init || init.method !== "POST")) {
      return Promise.resolve({ runs: listRuns });
    }
    // Start run
    if (url.match(/\/api\/projects\/[^/]+\/steward\/runs$/) && init?.method === "POST") {
      return Promise.resolve(startResult);
    }
    // Get run (poll)
    if (url.match(/\/api\/steward\/runs\/[^/]+$/) && (!init || init.method !== "POST")) {
      return Promise.resolve(runDetail);
    }
    // Stop run
    if (url.includes("/stop") && init?.method === "POST") {
      return Promise.resolve({ success: true, run_id: runDetail.run.id });
    }
    // Get policy
    if (url.match(/\/api\/projects\/[^/]+\/steward\/policy$/) && (!init || init.method !== "PUT")) {
      return Promise.resolve({ policy: policyVal });
    }
    // Put policy
    if (url.match(/\/api\/projects\/[^/]+\/steward\/policy$/) && init?.method === "PUT") {
      const body = init?.json as Record<string, unknown> | undefined;
      return Promise.resolve({
        success: true,
        policy: policyFixture({
          eligible_effect_kinds: body?.eligible_effect_kinds ?? [],
          max_retries: body?.max_retries ?? 3,
          max_actions_per_run: body?.max_actions_per_run ?? 10,
          cooldown_seconds: body?.cooldown_seconds ?? 0,
          enabled: body?.enabled ?? true,
        }),
      });
    }
    // Detail responses
    return Promise.resolve(detailResponse(url));
  });
}

// ── MOUNT PROOF: The posture opens from the Room by real clicks ──

describe("Mount proof: Steward verb in Room chrome", () => {
  it("shows 'Steward' button in the Room", async () => {
    setupStewardPosture();
    render(<WindowHarness scope="project:p1" />);

    const btn = await screen.findByTestId("steward-verb");
    expect(btn.textContent).toBe("Steward");
  });

  it("clicking 'Steward' enters the steward list posture", async () => {
    setupStewardPosture();
    render(<WindowHarness scope="project:p1" />);

    const btn = await screen.findByTestId("steward-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("steward-posture")).toBeTruthy();
    });

    expect(screen.getByTestId("steward-posture").getAttribute("data-phase")).toBe("list");
  });
});

// ── MOUNTED-PATH: Run once -> phases/steps -> detail ──

describe("Mounted-path: run once and view detail", () => {
  it("run once fires POST, enters detail, shows steps from poll", async () => {
    const runningDetail = {
      run: runningRunFixture({ id: "pstrun_new_run_12345678" }),
      steps: [],
    };
    const completedDetail = {
      run: completedRunFixture({ id: "pstrun_new_run_12345678" }),
      steps: stepsForCompletedRun(),
    };

    let pollCount = 0;
    setupStewardPosture({
      listRuns: [],
      startRunResult: { success: true, run_id: "pstrun_new_run_12345678" },
    });
    // Override the poll to transition from running -> completed
    const originalImpl = apiFetch.getMockImplementation()!;
    apiFetch.mockImplementation((url: string, init?: Record<string, unknown>) => {
      if (url.match(/\/api\/steward\/runs\/[^/]+$/) && (!init || init.method !== "POST")) {
        pollCount++;
        if (pollCount <= 1) return Promise.resolve(runningDetail);
        return Promise.resolve(completedDetail);
      }
      return originalImpl(url, init);
    });

    render(<WindowHarness scope="project:p1" />);

    // Enter steward posture
    const btn = await screen.findByTestId("steward-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("steward-posture")).toBeTruthy();
    });

    // Click "Run once"
    const runBtn = screen.getByTestId("steward-verb-run");
    fireEvent.click(runBtn);

    // POST was fired
    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        expect.stringContaining("/steward/runs"),
        expect.objectContaining({ method: "POST" }),
      );
    });

    // Detail view opens
    await waitFor(() => {
      expect(screen.getByTestId("steward-detail")).toBeTruthy();
    });

    // Initially shows Running state
    await waitFor(() => {
      expect(screen.getByTestId("steward-run-state")).toBeTruthy();
    });

    // Advance the poll timer to get the completed state
    await vi.advanceTimersByTimeAsync(2500);

    // After poll, should show completed + steps
    await waitFor(() => {
      const stateEl = screen.getByTestId("steward-run-state");
      expect(stateEl.textContent).toBe("Completed");
    });

    // Steps should be visible
    const stepItems = screen.getAllByTestId("steward-step-item");
    expect(stepItems.length).toBe(4);
  });
});

// ── STEP ROWS: effect kind in human words + receipt refs ──

describe("Step rows: human labels and receipt refs", () => {
  it("renders effect kind as human label, not machine token", async () => {
    setupStewardPosture({
      listRuns: [completedRunFixture()],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    // Open the completed run
    const items = await screen.findAllByTestId("steward-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("steward-detail"));

    // Check that step rows use human labels
    const stepRows = screen.getAllByTestId("steward-step-row");
    expect(stepRows.length).toBe(4);

    // First step: refresh_sources -> "Refreshed sources"
    expect(stepRows[0].textContent).toContain("Refreshed sources");
    // Second step: create_proposals -> "Created proposals"
    expect(stepRows[1].textContent).toContain("Created proposals");
    // Third step: draft_update -> "Drafted update"
    expect(stepRows[2].textContent).toContain("Drafted update");
    // Fourth step: create_door_item -> "Door item created"
    expect(stepRows[3].textContent).toContain("Door item created");
  });

  it("receipt refs render as openable chips with human labels", async () => {
    setupStewardPosture({
      listRuns: [completedRunFixture()],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const items = await screen.findAllByTestId("steward-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("steward-detail"));

    const refChips = screen.getAllByTestId("steward-receipt-ref");
    expect(refChips.length).toBe(4);

    // Item ref
    const itemRef = refChips.find((el) => el.getAttribute("data-ref") === "item:itm-001");
    expect(itemRef).toBeTruthy();
    expect(itemRef!.textContent).toBe("Open item");

    // Decision ref
    const decRef = refChips.find((el) => el.getAttribute("data-ref") === "decision:dec-001");
    expect(decRef).toBeTruthy();
    expect(decRef!.textContent).toBe("Open decision");

    // Update ref
    const updRef = refChips.find((el) => el.getAttribute("data-ref") === "update:upd-001");
    expect(updRef).toBeTruthy();
    expect(updRef!.textContent).toBe("Open update");

    // Observation ref
    const obsRef = refChips.find((el) => el.getAttribute("data-ref") === "observation:obs-001");
    expect(obsRef).toBeTruthy();
    expect(obsRef!.textContent).toBe("Open observation");
  });

  it("clicking a receipt ref opens via the house citation opener", async () => {
    setupStewardPosture({
      listRuns: [completedRunFixture()],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const items = await screen.findAllByTestId("steward-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("steward-detail"));

    const refChips = screen.getAllByTestId("steward-receipt-ref");

    // Click the item ref -> openPrimitive
    const itemRef = refChips.find((el) => el.getAttribute("data-ref") === "item:itm-001");
    fireEvent.click(itemRef!);
    expect(mockOpenPrimitive).toHaveBeenCalledWith("item:itm-001");

    // Click the decision ref -> openPrimitive
    const decRef = refChips.find((el) => el.getAttribute("data-ref") === "decision:dec-001");
    fireEvent.click(decRef!);
    expect(mockOpenPrimitive).toHaveBeenCalledWith("decision:dec-001");
  });
});

// ── NO RAW IDS ON GLASS ──

describe("No raw IDs on glass", () => {
  it("no rendered text matches the raw ID pattern (pstrun_/pststep_)", async () => {
    setupStewardPosture({
      listRuns: [completedRunFixture()],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    // In the list view
    const posture = screen.getByTestId("steward-posture");
    const rawIdPattern = /p[a-z]+_[0-9a-f]{16,}/;

    // Check all visible text in the list (exclude title/aria attributes)
    const listItems = screen.getAllByTestId("steward-list-item");
    for (const item of listItems) {
      expect(item.textContent).not.toMatch(rawIdPattern);
    }

    // Open the detail
    fireEvent.click(listItems[0]);
    await waitFor(() => screen.getByTestId("steward-detail"));

    // Check all visible text in the detail
    const detail = screen.getByTestId("steward-detail");
    const stepItems = screen.getAllByTestId("steward-step-item");
    for (const item of stepItems) {
      expect(item.textContent).not.toMatch(rawIdPattern);
    }

    // The run ID lives in title attributes, not visible text
    const listRow = posture.querySelector("[title]");
    // title may carry the raw ID (that's OK -- it's title/aria, not glass)
  });
});

// ── STOP: consequential styling, stopping -> interrupted states ──

describe("Stop: consequential styling and honest states", () => {
  it("Stop button renders with consequential styling during a running run", async () => {
    setupStewardPosture({
      listRuns: [runningRunFixture()],
      runDetail: {
        run: runningRunFixture(),
        steps: [],
      },
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    // Open the running run
    const items = await screen.findAllByTestId("steward-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("steward-detail"));

    // Stop button is present with consequential styling
    const stopBtn = screen.getByTestId("steward-verb-stop");
    expect(stopBtn).toBeTruthy();
    expect(stopBtn.textContent).toBe("Stop");
    expect(stopBtn.classList.contains("is-consequential")).toBe(true);
  });

  it("Stop fires POST and the poll shows stopping then interrupted", async () => {
    const stoppingRun = {
      ...runningRunFixture(),
      state: "stopping",
    };
    const interrupted = interruptedRunFixture({ id: stoppingRun.id });

    let pollCount = 0;
    setupStewardPosture({
      listRuns: [runningRunFixture()],
      runDetail: {
        run: runningRunFixture(),
        steps: [],
      },
    });

    const originalImpl = apiFetch.getMockImplementation()!;
    apiFetch.mockImplementation((url: string, init?: Record<string, unknown>) => {
      // After stop is clicked, the poll should show stopping then interrupted
      if (url.match(/\/api\/steward\/runs\/[^/]+$/) && (!init || init.method !== "POST")) {
        pollCount++;
        if (pollCount <= 2) {
          return Promise.resolve({ run: runningRunFixture(), steps: [] });
        }
        if (pollCount === 3) {
          return Promise.resolve({ run: stoppingRun, steps: [] });
        }
        return Promise.resolve({ run: interrupted, steps: [] });
      }
      return originalImpl(url, init);
    });

    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const items = await screen.findAllByTestId("steward-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("steward-detail"));

    // Click Stop
    const stopBtn = screen.getByTestId("steward-verb-stop");
    fireEvent.click(stopBtn);

    // POST /stop was fired
    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        expect.stringContaining("/stop"),
        expect.objectContaining({ method: "POST" }),
      );
    });

    // Advance timers to see the state transitions
    await vi.advanceTimersByTimeAsync(5000);

    // The state renders Stopping
    await waitFor(() => {
      const stateEl = screen.getByTestId("steward-run-state");
      expect(stateEl.textContent).toBe("Stopping");
    });

    await vi.advanceTimersByTimeAsync(3000);

    // Then Interrupted
    await waitFor(() => {
      const stateEl = screen.getByTestId("steward-run-state");
      expect(stateEl.textContent).toBe("Interrupted");
    });

    // The summary reason is rendered
    await waitFor(() => {
      const reasonEl = screen.getByTestId("steward-run-reason");
      expect(reasonEl.textContent).toBe("Stopped by you");
    });
  });
});

// ── STW-002: busy/disabled with honest reason ──

describe("STW-002: run disabled with honest reason", () => {
  it("Run button is disabled when an active run exists and shows the reason", async () => {
    setupStewardPosture({
      listRuns: [runningRunFixture()],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const runBtn = screen.getByTestId("steward-verb-run");
    expect(runBtn).toBeTruthy();
    expect((runBtn as HTMLButtonElement).disabled).toBe(true);

    // The honest reason is shown
    const reason = screen.getByTestId("steward-run-disabled-reason");
    expect(reason.textContent).toBe("A run is in progress");
  });
});

// ── HISTORY LIST: designed rows ──

describe("History list: designed rows", () => {
  it("renders run rows with state, time, summary, chevron", async () => {
    setupStewardPosture({
      listRuns: [
        completedRunFixture(),
        interruptedRunFixture({ id: "pstrun_interrupted12345" }),
      ],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const items = screen.getAllByTestId("steward-list-item");
    expect(items.length).toBe(2);

    // Chevron present
    const chevrons = screen.getAllByTestId("steward-list-chevron");
    expect(chevrons.length).toBe(2);
    expect(chevrons[0].textContent).toBe(">");

    // First row: completed
    const row1 = items[0].querySelector(".steward-list-row");
    expect(row1).toBeTruthy();
    expect(row1!.getAttribute("data-state")).toBe("completed");

    // Summary is human words
    const summaries = screen.getAllByTestId("steward-list-summary");
    expect(summaries[0].textContent).toContain("Completed");
    expect(summaries[0].textContent).toContain("2 effects");

    // Second row: interrupted with reason
    expect(summaries[1].textContent).toContain("Interrupted");
    expect(summaries[1].textContent).toContain("Stopped by you");
  });

  it("row is keyboard-accessible (button tag, no aria-expanded)", async () => {
    setupStewardPosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const item = screen.getByTestId("steward-list-item");
    expect(item.tagName).toBe("BUTTON");
    expect(item.hasAttribute("aria-expanded")).toBe(false);
  });

  it("two-line row structure: primary + secondary as separate children", async () => {
    setupStewardPosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const items = screen.getAllByTestId("steward-list-item");
    const row = items[0].querySelector(".steward-list-row");
    expect(row).toBeTruthy();

    const primary = row!.querySelector(".steward-list-primary");
    const secondary = row!.querySelector(".steward-list-secondary");
    expect(primary).toBeTruthy();
    expect(secondary).toBeTruthy();

    // Primary has state token + time
    expect(primary!.querySelector(".surface-token")).toBeTruthy();
    expect(primary!.querySelector(".steward-list-time")).toBeTruthy();

    // The row sits inside .surface-ledger-primary
    const ledgerPrimary = row!.closest(".surface-ledger-primary");
    expect(ledgerPrimary).toBeTruthy();
  });
});

// ── POLICY ROUND-TRIP ──

describe("Policy: round-trip", () => {
  it("enters policy view, shows fields, saves with PUT", async () => {
    setupStewardPosture({
      policy: policyFixture(),
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    // Click "Policy"
    const policyBtn = screen.getByTestId("steward-verb-policy");
    fireEvent.click(policyBtn);

    await waitFor(() => {
      expect(screen.getByTestId("steward-policy")).toBeTruthy();
    });

    expect(screen.getByTestId("steward-posture").getAttribute("data-phase")).toBe("policy");

    // Numeric fields are present
    const maxRetries = screen.getByTestId("steward-policy-max-retries") as HTMLInputElement;
    expect(maxRetries.value).toBe("5");

    const maxActions = screen.getByTestId("steward-policy-max-actions") as HTMLInputElement;
    expect(maxActions.value).toBe("20");

    const cooldown = screen.getByTestId("steward-policy-cooldown") as HTMLInputElement;
    expect(cooldown.value).toBe("60");

    // Effect kind toggles are present
    const effectsSection = screen.getByTestId("steward-policy-effects");
    expect(effectsSection).toBeTruthy();

    // There are checkboxes for 5 effect kinds
    const checkboxes = effectsSection.querySelectorAll('input[type="checkbox"]');
    expect(checkboxes.length).toBe(5);

    // Save
    const saveBtn = screen.getByTestId("steward-verb-save-policy");
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        expect.stringContaining("/steward/policy"),
        expect.objectContaining({ method: "PUT" }),
      );
    });
  });

  it("no policy returns null and shows defaults", async () => {
    setupStewardPosture({
      policy: null,
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const policyBtn = screen.getByTestId("steward-verb-policy");
    fireEvent.click(policyBtn);

    await waitFor(() => {
      expect(screen.getByTestId("steward-policy")).toBeTruthy();
    });

    // Default values
    const maxRetries = screen.getByTestId("steward-policy-max-retries") as HTMLInputElement;
    expect(maxRetries.value).toBe("3");

    const maxActions = screen.getByTestId("steward-policy-max-actions") as HTMLInputElement;
    expect(maxActions.value).toBe("10");
  });

  it("egress badge on model-touching effect kinds", async () => {
    setupStewardPosture({
      policy: policyFixture(),
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const policyBtn = screen.getByTestId("steward-verb-policy");
    fireEvent.click(policyBtn);

    await waitFor(() => screen.getByTestId("steward-policy"));

    // EgressChip should be present on model-touching kinds
    const egressChips = screen.getByTestId("steward-policy-effects")
      .querySelectorAll(".gadget-chip-egress");
    // create_proposals and draft_update are model-touching = 2 egress chips
    expect(egressChips.length).toBe(2);
  });
});

// ── VOCABULARY: no em/en dashes ──

describe("Vocabulary: no em/en dashes in rendered text", () => {
  it("no em or en dashes in any visible text or aria-labels", async () => {
    setupStewardPosture({
      listRuns: [completedRunFixture(), interruptedRunFixture()],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const posture = screen.getByTestId("steward-posture");

    // Check visible text
    expect(posture.textContent).not.toContain("—"); // em dash
    expect(posture.textContent).not.toContain("–"); // en dash

    // Check aria-labels
    const withAria = posture.querySelectorAll("[aria-label]");
    for (const el of withAria) {
      const label = el.getAttribute("aria-label") ?? "";
      expect(label).not.toContain("—");
      expect(label).not.toContain("–");
    }
  });
});

// ── EMPTY STATE ──

describe("Empty state", () => {
  it("shows empty state when no runs exist", async () => {
    setupStewardPosture({ listRuns: [] });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    // The empty state is visible
    const emptyLabel = screen.getByText("No steward runs yet. Run once to start.");
    expect(emptyLabel).toBeTruthy();
  });
});
