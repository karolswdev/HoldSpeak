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
import { computeVerticalScrollHint, isModelTouchingKind } from "../model";

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
    nextCheckAt: null,
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
    needsYou: { state: "ok", items: [], count: 0 },
    sources: { state: "ok", items: [], count: 0, nextCheckAt: null },
    health: { state: "ok", assessment: "on_track", reason: null, inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false } },
    sinceRead: { state: "ok", readAt: null, groups: [] },
    decisions: { state: "ok", items: [] },
    commitments: { state: "ok", items: [] },
    target: { state: "absent", reason: "none" },
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
    unattended_enabled: false,
    created_at: "2026-09-01T08:00:00",
    updated_at: "2026-09-01T08:00:00",
    ...overrides,
  };
}

/** Watch fixture (wire shape from list_watches). */
function watchFixture(overrides: Record<string, unknown> = {}) {
  return {
    id: "cw_watch_001",
    name: "GitHub PRs",
    connector_id: "github",
    state: "tested",
    evaluation_cadence_minutes: 30,
    circuit_state: "closed",
    circuit_failure_streak: 0,
    circuit_opened_at: null,
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
  watches?: Record<string, unknown>[];
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
  const watchesVal = opts.watches ?? [watchFixture()];

  apiFetch.mockImplementation((url: string, init?: Record<string, unknown>) => {
    // HS-169-03: room read marker
    if (url.includes("/room/read")) {
      return Promise.resolve({ read_at: new Date().toISOString() });
    }
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
          unattended_enabled: body?.unattended_enabled ?? false,
        }),
      });
    }
    // Project watches
    if (url.match(/\/api\/projects\/[^/]+\/watches$/)) {
      return Promise.resolve({ watches: watchesVal });
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

    // HS-167-05: ProgressPlan renders six canonical phases, not per-step rows
    const planSteps = screen.getByTestId("steward-run-plan")
      .querySelectorAll(".surface-plan-step");
    expect(planSteps.length).toBe(6);
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

    // HS-167-05 R4: ProgressPlan rate = counts only; effect labels in the chip row
    const planSteps = screen.getByTestId("steward-run-plan")
      .querySelectorAll(".surface-plan-step");
    expect(planSteps.length).toBe(6);

    // Observe phase: counts only (no effect-kind name)
    expect(planSteps[0].textContent).toContain("1 source");

    // Effect-kind labels are in the receipt-ref chip row
    const refChipArea = screen.getByTestId("steward-receipt-refs");
    expect(refChipArea.textContent).toContain("Refreshed sources");
    expect(refChipArea.textContent).toContain("Created proposals");
    expect(refChipArea.textContent).toContain("Drafted update");
    expect(refChipArea.textContent).toContain("Door item created");
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

    // HS-167-05: ProgressPlan phases replace individual step rows
    const detail = screen.getByTestId("steward-detail");
    const planSteps = screen.getByTestId("steward-run-plan")
      .querySelectorAll(".surface-plan-step");
    for (const item of planSteps) {
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

    // Secondary line carries substance, not the state (state lives in the primary token)
    const summaries = screen.getAllByTestId("steward-list-summary");
    // First row: completed with 2 effects -- secondary shows substance only
    expect(summaries[0].textContent).toContain("2 effects");
    expect(summaries[0].textContent).not.toContain("Completed");

    // Second row: interrupted with reason -- secondary shows reason only
    expect(summaries[1].textContent).toContain("Stopped by you");
    expect(summaries[1].textContent).not.toContain("Interrupted");
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

    // HS-167-05: StepperGadgets wrap the input; query the input inside the testid span
    const maxRetries = screen.getByTestId("steward-policy-max-retries").querySelector("input") as HTMLInputElement;
    expect(maxRetries.value).toBe("5");

    const maxActions = screen.getByTestId("steward-policy-max-actions").querySelector("input") as HTMLInputElement;
    expect(maxActions.value).toBe("20");

    const cooldown = screen.getByTestId("steward-policy-cooldown").querySelector("input") as HTMLInputElement;
    expect(cooldown.value).toBe("60");

    // Effect kind toggles are present
    const effectsSection = screen.getByTestId("steward-policy-effects");
    expect(effectsSection).toBeTruthy();

    // There are checkboxes for 5 effect kinds
    const checkboxes = effectsSection.querySelectorAll('input[type="checkbox"]');
    expect(checkboxes.length).toBe(6);

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

    // HS-167-05: StepperGadgets wrap the input; query the input inside
    const maxRetries = screen.getByTestId("steward-policy-max-retries").querySelector("input") as HTMLInputElement;
    expect(maxRetries.value).toBe("3");

    const maxActions = screen.getByTestId("steward-policy-max-actions").querySelector("input") as HTMLInputElement;
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

    // EgressChip should be present on model-touching kinds.
    // Only draft_update touches the model today (create_proposals is
    // an identity no-op, DEL-007 step 11).
    const egressChips = screen.getByTestId("steward-policy-effects")
      .querySelectorAll(".gadget-chip-egress");
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

// ── FINDING 1: Policy toggles render visible labels ──

describe("Policy: visible labels on toggles", () => {
  it("enabled toggle has visible 'Steward enabled' label", async () => {
    setupStewardPosture({ policy: policyFixture() });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click(screen.getByTestId("steward-verb-policy"));
    await waitFor(() => screen.getByTestId("steward-policy"));

    const enabledRow = screen.getByTestId("steward-policy-enabled-row");
    expect(enabledRow.textContent).toContain("Steward enabled");
  });

  it("each effect kind toggle has its human label visible", async () => {
    setupStewardPosture({ policy: policyFixture() });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click(screen.getByTestId("steward-verb-policy"));
    await waitFor(() => screen.getByTestId("steward-policy"));

    const effectsSection = screen.getByTestId("steward-policy-effects");

    // All five human labels render as visible text
    expect(effectsSection.textContent).toContain("Refreshed sources");
    expect(effectsSection.textContent).toContain("Created proposals");
    expect(effectsSection.textContent).toContain("Applied proposal effects");
    expect(effectsSection.textContent).toContain("Drafted update");
    expect(effectsSection.textContent).toContain("Door item created");

    // Each has a dedicated label element
    expect(screen.getByTestId("steward-policy-kind-label-refresh_sources").textContent).toBe("Refreshed sources");
    expect(screen.getByTestId("steward-policy-kind-label-create_proposals").textContent).toBe("Created proposals");
    expect(screen.getByTestId("steward-policy-kind-label-apply_proposal_effects").textContent).toBe("Applied proposal effects");
    expect(screen.getByTestId("steward-policy-kind-label-draft_update").textContent).toBe("Drafted update");
    expect(screen.getByTestId("steward-policy-kind-label-create_door_item").textContent).toBe("Door item created");
  });
});

// ── FINDING 2: Secondary line substance, not state duplication ──

describe("History list: secondary line substance", () => {
  it("secondary line shows effect count without repeating the state", async () => {
    setupStewardPosture({
      listRuns: [completedRunFixture()],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const summary = screen.getByTestId("steward-list-summary");
    expect(summary.textContent).toBe("2 effects");
  });

  it("secondary line shows reason for interrupted runs", async () => {
    setupStewardPosture({
      listRuns: [interruptedRunFixture()],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const summary = screen.getByTestId("steward-list-summary");
    expect(summary.textContent).toBe("Stopped by you");
  });

  it("no secondary line when run has nothing to say", async () => {
    setupStewardPosture({
      listRuns: [runningRunFixture()],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    // Running run with empty summary has no substance -> no secondary line
    expect(screen.queryByTestId("steward-list-summary")).toBeNull();
  });
});

// ── FINDING 3: Degraded coverage renders a visible marker ──

describe("Degraded coverage: visible warning", () => {
  it("shows PARTIAL COVERAGE chip when a source is not ok", async () => {
    const degradedRun = completedRunFixture({
      summary: {
        outcome: "completed",
        phases_completed: ["observe"],
        effects_applied: 1,
        phase_results: {
          observe: {
            coverage: {
              "GitHub Issues": { state: "ok" },
              "Jira Board": { state: "error" },
              "Confluence": { state: "ok" },
            },
          },
        },
      },
    });

    setupStewardPosture({
      listRuns: [degradedRun],
      runDetail: {
        run: degradedRun,
        steps: [
          completedStepFixture({
            effect_kind: "refresh_sources",
            observed: { partial: true, sources_ok: 2, sources_total: 3 },
          }),
        ],
      },
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const items = screen.getAllByTestId("steward-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("steward-detail"));

    // The PARTIAL COVERAGE marker is visible in the detail band
    const degradedChip = screen.getByTestId("steward-coverage-degraded");
    expect(degradedChip).toBeTruthy();
    expect(degradedChip.textContent).toContain("PARTIAL COVERAGE");
    expect(degradedChip.textContent).toContain("2 of 3 sources answered");
    expect(degradedChip.getAttribute("data-tone")).toBe("warn");
  });

  it("step row shows PARTIAL chip when observed.partial is true", async () => {
    const degradedRun = completedRunFixture();
    setupStewardPosture({
      listRuns: [degradedRun],
      runDetail: {
        run: degradedRun,
        steps: [
          completedStepFixture({
            effect_kind: "refresh_sources",
            observed: { partial: true },
          }),
        ],
      },
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click((await screen.findAllByTestId("steward-list-item"))[0]);
    await waitFor(() => screen.getByTestId("steward-detail"));

    const partialChip = screen.getByTestId("steward-step-partial");
    expect(partialChip.textContent).toBe("PARTIAL");
    expect(partialChip.getAttribute("data-tone")).toBe("warn");
  });

  it("no degraded marker when all sources are ok", async () => {
    const healthyRun = completedRunFixture({
      summary: {
        outcome: "completed",
        phases_completed: ["observe"],
        effects_applied: 2,
        phase_results: {
          observe: {
            coverage: {
              "GitHub Issues": { state: "ok" },
              "Jira Board": { state: "ok" },
            },
          },
        },
      },
    });

    setupStewardPosture({
      listRuns: [healthyRun],
      runDetail: {
        run: healthyRun,
        steps: stepsForCompletedRun(),
      },
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click((await screen.findAllByTestId("steward-list-item"))[0]);
    await waitFor(() => screen.getByTestId("steward-detail"));

    expect(screen.queryByTestId("steward-coverage-degraded")).toBeNull();
  });
});

// ── FINDING 4: Footer pluralization ──

// HS-167-05 R4: footer reads RUN N · STATE · N PHASES (not N STEPS)
describe("Footer: honest pluralization", () => {
  it("detail footer reads RUN N · COMPLETED · N PHASES", async () => {
    const run = completedRunFixture();
    setupStewardPosture({
      listRuns: [run],
      runDetail: {
        run,
        steps: [completedStepFixture()],
      },
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click((await screen.findAllByTestId("steward-list-item"))[0]);
    await waitFor(() => screen.getByTestId("steward-detail"));

    const footer = screen.getByTestId("steward-footer-receipt");
    expect(footer.textContent).toContain("COMPLETED");
    expect(footer.textContent).toContain("PHASE");
  });

  it("completed run with all 6 phases shows '6 PHASES'", async () => {
    setupStewardPosture({
      listRuns: [completedRunFixture()],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click((await screen.findAllByTestId("steward-list-item"))[0]);
    await waitFor(() => screen.getByTestId("steward-detail"));

    const footer = screen.getByTestId("steward-footer-receipt");
    expect(footer.textContent).toContain("6 PHASES");
  });
});

// ── HS-164-05: PROVENANCE -- unattended vs manual ──

describe("Provenance: run history distinguishes unattended from manual", () => {
  it("manual run shows 'Manual' provenance in list", async () => {
    setupStewardPosture({
      listRuns: [
        completedRunFixture({ requested_by: "principal:owner-session" }),
      ],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const provenanceChips = screen.getAllByTestId("steward-run-provenance");
    expect(provenanceChips[0].textContent).toBe("Manual");
  });

  it("conductor run shows 'Scheduled' provenance in list", async () => {
    setupStewardPosture({
      listRuns: [
        completedRunFixture({ requested_by: "principal:local-steward-conductor" }),
      ],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const provenanceChips = screen.getAllByTestId("steward-run-provenance");
    expect(provenanceChips[0].textContent).toBe("Scheduled");
  });

  it("mixed history shows both provenance labels", async () => {
    setupStewardPosture({
      listRuns: [
        completedRunFixture({
          id: "pstrun_manual_12345678",
          requested_by: "principal:owner-session",
        }),
        completedRunFixture({
          id: "pstrun_sched_123456789",
          requested_by: "principal:local-steward-conductor",
        }),
      ],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const chips = screen.getAllByTestId("steward-run-provenance");
    expect(chips.length).toBe(2);
    expect(chips[0].textContent).toBe("Manual");
    expect(chips[1].textContent).toBe("Scheduled");
  });

  it("detail view shows provenance in the band", async () => {
    setupStewardPosture({
      listRuns: [
        completedRunFixture({ requested_by: "principal:local-steward-conductor" }),
      ],
      runDetail: {
        run: completedRunFixture({ requested_by: "principal:local-steward-conductor" }),
        steps: stepsForCompletedRun(),
      },
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click((await screen.findAllByTestId("steward-list-item"))[0]);
    await waitFor(() => screen.getByTestId("steward-detail"));

    const provenance = screen.getAllByTestId("steward-run-provenance");
    // Detail view has its own provenance chip
    expect(provenance.some((el) => el.textContent === "Scheduled")).toBe(true);
  });
});

// ── HS-164-05: UNATTENDED TOGGLE + GRANT TEXT ──

describe("Unattended toggle and grant text assembly", () => {
  it("policy view shows unattended toggle defaulting to off", async () => {
    setupStewardPosture({
      policy: policyFixture({ unattended_enabled: false }),
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click(screen.getByTestId("steward-verb-policy"));
    await waitFor(() => screen.getByTestId("steward-policy"));

    const section = screen.getByTestId("steward-unattended-section");
    expect(section).toBeTruthy();

    // HS-167-05 R4: grant tokens — "UNATTENDED OFF" when disabled
    const grantText = screen.getByTestId("steward-grant-text");
    expect(grantText.textContent).toContain("UNATTENDED OFF");
  });

  it("enabling unattended shows grant tokens with real values", async () => {
    setupStewardPosture({
      policy: policyFixture({
        unattended_enabled: true,
        eligible_effect_kinds: ["refresh_sources", "draft_update"],
        max_actions_per_run: 20,
      }),
      watches: [
        watchFixture({ evaluation_cadence_minutes: 30 }),
      ],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click(screen.getByTestId("steward-verb-policy"));
    await waitFor(() => screen.getByTestId("steward-policy"));

    // HS-167-05 R4: separate uppercase tokens
    const grantText = screen.getByTestId("steward-grant-text");
    expect(grantText.textContent).toContain("EVERY");
    expect(grantText.textContent).toContain("MIN");
    expect(grantText.textContent).toContain("REFRESH SOURCES");
    expect(grantText.textContent).toContain("DRAFT UPDATE");
    expect(grantText.textContent).toContain("MAX 20 / RUN");
  });

  it("toggle round-trips through PUT with unattended_enabled", async () => {
    setupStewardPosture({
      policy: policyFixture({ unattended_enabled: false }),
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click(screen.getByTestId("steward-verb-policy"));
    await waitFor(() => screen.getByTestId("steward-policy"));

    // Find the unattended row's toggle and click it
    const unattendedRow = screen.getByTestId("steward-unattended-row");
    const checkbox = unattendedRow.querySelector("input[type='checkbox']");
    expect(checkbox).toBeTruthy();
    fireEvent.click(checkbox!);

    // Save
    fireEvent.click(screen.getByTestId("steward-verb-save-policy"));

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        expect.stringContaining("/steward/policy"),
        expect.objectContaining({
          method: "PUT",
          json: expect.objectContaining({
            unattended_enabled: true,
          }),
        }),
      );
    });
  });

  it("grant text shows 'no effects are eligible' when empty effect list", async () => {
    setupStewardPosture({
      policy: policyFixture({
        unattended_enabled: true,
        eligible_effect_kinds: [],
        max_actions_per_run: 10,
      }),
      watches: [watchFixture({ evaluation_cadence_minutes: 60 })],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click(screen.getByTestId("steward-verb-policy"));
    await waitFor(() => screen.getByTestId("steward-policy"));

    // HS-167-05 R4: "NO EFFECTS" token when empty
    const grantText = screen.getByTestId("steward-grant-text");
    expect(grantText.textContent).toContain("NO EFFECTS");
  });
});

// ── HS-164-05: CIRCUIT STATE ──

describe("Circuit state: watches with non-closed circuits", () => {
  it("shows no circuit section when all watches are closed", async () => {
    setupStewardPosture({
      policy: policyFixture(),
      watches: [watchFixture({ circuit_state: "closed" })],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click(screen.getByTestId("steward-verb-policy"));
    await waitFor(() => screen.getByTestId("steward-policy"));

    expect(screen.queryByTestId("steward-circuit-row")).toBeNull();
  });

  it("shows circuit rows for open watches", async () => {
    setupStewardPosture({
      policy: policyFixture(),
      watches: [
        watchFixture({
          id: "cw_open_001",
          name: "GitHub PRs",
          circuit_state: "open",
          circuit_failure_streak: 3,
          circuit_opened_at: "2026-09-01T10:00:00",
        }),
      ],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click(screen.getByTestId("steward-verb-policy"));
    await waitFor(() => screen.getByTestId("steward-policy"));

    const circuitRows = screen.getAllByTestId("steward-circuit-row");
    expect(circuitRows.length).toBe(1);

    const stateToken = screen.getByTestId("steward-circuit-state");
    expect(stateToken.textContent).toBe("Circuit open");

    const streak = screen.getByTestId("steward-circuit-streak");
    expect(streak.textContent).toBe("3 failures");

    // The opened-at time rides the house ledger time slot now
    // (52px column), not a separate since-span.
  });

  it("half-open circuit shows 'Probing' state", async () => {
    setupStewardPosture({
      policy: policyFixture(),
      watches: [
        watchFixture({
          circuit_state: "half_open",
          circuit_failure_streak: 2,
        }),
      ],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click(screen.getByTestId("steward-verb-policy"));
    await waitFor(() => screen.getByTestId("steward-policy"));

    const stateToken = screen.getByTestId("steward-circuit-state");
    expect(stateToken.textContent).toBe("Probing");
  });
});

// ── SCROLL HINT: vertical scroll-hint pure function (DoorBoardLane species, Y axis) ──

describe("computeVerticalScrollHint (pure function)", () => {
  it("returns none when nothing clips", () => {
    expect(computeVerticalScrollHint(0, 800, 800)).toBe("none");
    expect(computeVerticalScrollHint(0, 700, 800)).toBe("none");
  });
  it("returns bottom at the top edge", () => {
    expect(computeVerticalScrollHint(0, 1200, 400)).toBe("bottom");
  });
  it("returns top at the bottom edge", () => {
    expect(computeVerticalScrollHint(800, 1200, 400)).toBe("top");
  });
  it("returns both at a mid-scroll position", () => {
    expect(computeVerticalScrollHint(200, 1200, 400)).toBe("both");
  });
  it("absorbs the 20px tolerance", () => {
    // At scrollTop 790, clientHeight 400, scrollHeight 1200:
    // scrollTop + clientHeight = 1190, scrollHeight - 20 = 1180 -> atBottom = true
    expect(computeVerticalScrollHint(790, 1200, 400)).toBe("top");
  });
});

describe("Scroll hint: data-scroll-hint is set on the posture root", () => {
  it("sets data-scroll-hint on the steward posture element", async () => {
    setupStewardPosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    const posture = screen.getByTestId("steward-posture");
    expect(posture.hasAttribute("data-scroll-hint")).toBe(true);
  });
});

// ── MODEL CHIP HONESTY ──

describe("Model chip honesty: only draft_update wears the MODEL egress badge", () => {
  it("create_proposals is NOT model-touching (identity no-op)", () => {
    expect(isModelTouchingKind("create_proposals")).toBe(false);
  });

  it("draft_update IS model-touching", () => {
    expect(isModelTouchingKind("draft_update")).toBe(true);
  });

  it("refresh_sources is NOT model-touching", () => {
    expect(isModelTouchingKind("refresh_sources")).toBe(false);
  });

  it("egress chip title names the wiring (Settings > Models)", async () => {
    setupStewardPosture({
      policy: policyFixture(),
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("steward-verb"));
    await waitFor(() => screen.getByTestId("steward-posture"));

    fireEvent.click(screen.getByTestId("steward-verb-policy"));
    await waitFor(() => screen.getByTestId("steward-policy"));

    const egressChips = screen.getByTestId("steward-policy-effects")
      .querySelectorAll(".gadget-chip-egress");
    expect(egressChips.length).toBe(2);
    // The title names the wiring: Settings > Models path + fallback.
    const title = egressChips[0].getAttribute("title") ?? "";
    expect(title).toContain("Settings");
    expect(title).toContain("Models");
    expect(title).toContain("deterministic");
  });
});
