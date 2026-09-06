// HS-173-04 -- StewardPosture 173 face tests: the sixth row (Reviewer nudge),
// its EgressChip GITHUB.COM, PER-NUDGE APPROVAL token, and the nudge_template
// StringGadget row that appears only when github_comment is checked.

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TitleSlotContext } from "../../../../desk/surface/title";
import { WingSlotContext } from "../../../../desk/surface/wings";
import { useDesk } from "../../../../desk/store";
import { EMPTY_ITEMS } from "../../../../desk/api";
import { ProjectRoomCore } from "../../ProjectRoomCore";
import { effectKindLabel, isModelTouchingKind, effectKindEgressHost } from "../model";

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

vi.mock("../../../../desk/shell", async () => {
  const actual = await vi.importActual<typeof import("../../../../desk/shell")>(
    "../../../../desk/shell",
  );
  return {
    ...actual,
    openPrimitive: vi.fn(),
    openSurfaceOr: vi.fn(),
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

// ── Fixture factories ──

function roomResponse() {
  return {
    project_id: "p1",
    revision: 5,
    observed_at: "2026-09-05T10:00:00",
    nextCheckAt: null,
    project: {
      id: "p1",
      name: "Steward Project",
      description: "Testing steward",
      is_archived: false,
      meeting_count: 0,
      created_at: "2026-08-01T00:00:00",
      updated_at: "2026-09-05T10:00:00",
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
    meetings: { state: "ok", count: 0, latest: null },
    resources: { state: "ok", count: 0, latest: null },
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
    steward: { state: "ok" },
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

function policyFixture(overrides: Record<string, unknown> = {}) {
  return {
    id: "pstpol_policy12345678",
    project_id: "p1",
    eligible_effect_kinds: [],
    yolo_flags: {},
    max_retries: 3,
    max_actions_per_run: 10,
    cooldown_seconds: 0,
    bounds: {},
    enabled: true,
    unattended_enabled: false,
    nudge_template: null,
    created_at: "2026-09-05T08:00:00",
    updated_at: "2026-09-05T08:00:00",
    ...overrides,
  };
}

function watchFixture() {
  return {
    id: "cw_watch_001",
    name: "GitHub PRs",
    connector_id: "github",
    state: "tested",
    evaluation_cadence_minutes: 30,
    circuit_state: "closed",
    circuit_failure_streak: 0,
    circuit_opened_at: null,
  };
}

function setupStewardPolicy(opts: {
  policy?: Record<string, unknown> | null;
} = {}) {
  const policyVal = opts.policy !== undefined ? opts.policy : policyFixture();

  apiFetch.mockImplementation((url: string, init?: Record<string, unknown>) => {
    if (url.includes("/room/read")) {
      return Promise.resolve({ read_at: new Date().toISOString() });
    }
    if (url.includes("/room")) {
      return Promise.resolve(roomResponse());
    }
    if (url.match(/\/api\/projects\/[^/]+\/steward\/runs$/)) {
      return Promise.resolve({ runs: [] });
    }
    if (url.match(/\/api\/projects\/[^/]+\/steward\/policy$/) && (!init || init.method !== "PUT")) {
      return Promise.resolve({ policy: policyVal });
    }
    if (url.match(/\/api\/projects\/[^/]+\/steward\/policy$/) && init?.method === "PUT") {
      const body = init?.json as Record<string, unknown> | undefined;
      return Promise.resolve({
        success: true,
        policy: policyFixture({
          eligible_effect_kinds: body?.eligible_effect_kinds ?? [],
          nudge_template: body?.nudge_template ?? null,
        }),
      });
    }
    if (url.match(/\/api\/projects\/[^/]+\/watches$/)) {
      return Promise.resolve({ watches: [watchFixture()] });
    }
    return Promise.resolve(detailResponse(url));
  });
}

// ── Lifecycle ──

beforeEach(() => {
  useDesk.setState({
    windowsById: {},
    items: { ...EMPTY_ITEMS },
    projects: [],
    inferenceTargets: [],
  });
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

afterEach(() => {
  vi.clearAllMocks();
  vi.useRealTimers();
});

// ── Helper: navigate to policy ──

async function openPolicy() {
  const btn = await screen.findByTestId("steward-verb");
  fireEvent.click(btn);
  await waitFor(() => screen.getByTestId("steward-posture"));
  fireEvent.click(screen.getByTestId("steward-verb-policy"));
  await waitFor(() => screen.getByTestId("steward-policy"));
}

// ── HS-173-04: model.ts labels ──

describe("HS-173-04: github_comment model labels", () => {
  it("effectKindLabel returns 'Reviewer nudge'", () => {
    expect(effectKindLabel("github_comment")).toBe("Reviewer nudge");
  });

  it("isModelTouchingKind returns false", () => {
    expect(isModelTouchingKind("github_comment")).toBe(false);
  });

  it("effectKindEgressHost returns 'GITHUB.COM'", () => {
    expect(effectKindEgressHost("github_comment")).toBe("GITHUB.COM");
  });
});

// ── HS-173-04: the sixth row ──

describe("HS-173-04: sixth row (Reviewer nudge) in policy", () => {
  it("renders the sixth CheckGadget row with label 'Reviewer nudge'", async () => {
    setupStewardPolicy();
    render(<WindowHarness scope="project:p1" />);
    await openPolicy();

    const label = screen.getByTestId("steward-policy-kind-label-github_comment");
    expect(label.textContent).toBe("Reviewer nudge");
  });

  it("sixth row carries EgressChip GITHUB.COM", async () => {
    setupStewardPolicy();
    render(<WindowHarness scope="project:p1" />);
    await openPolicy();

    const effectsSection = screen.getByTestId("steward-policy-effects");
    const egressChips = effectsSection.querySelectorAll(".gadget-chip-egress");
    const githubChip = Array.from(egressChips).find(
      (el) => el.textContent === "GITHUB.COM",
    );
    expect(githubChip).toBeTruthy();
    expect(githubChip!.getAttribute("data-scope")).toBe("cloud");
  });

  it("sixth row is unchecked by default", async () => {
    setupStewardPolicy({ policy: policyFixture({ eligible_effect_kinds: [] }) });
    render(<WindowHarness scope="project:p1" />);
    await openPolicy();

    const effectsSection = screen.getByTestId("steward-policy-effects");
    const checkboxes = effectsSection.querySelectorAll('input[type="checkbox"]');
    // github_comment is the last checkbox (index 5)
    const githubCheckbox = checkboxes[5] as HTMLInputElement;
    expect(githubCheckbox.checked).toBe(false);
  });

  it("PER-NUDGE APPROVAL token is visible", async () => {
    setupStewardPolicy();
    render(<WindowHarness scope="project:p1" />);
    await openPolicy();

    const approvalToken = screen.getByTestId("steward-policy-nudge-approval");
    expect(approvalToken.textContent).toContain("PER-NUDGE APPROVAL");
  });
});

// ── HS-173-04: nudge template appears when checked ──

describe("HS-173-04: nudge template row conditional visibility", () => {
  it("no nudge template row when github_comment is unchecked", async () => {
    setupStewardPolicy({ policy: policyFixture({ eligible_effect_kinds: [] }) });
    render(<WindowHarness scope="project:p1" />);
    await openPolicy();

    expect(screen.queryByTestId("steward-policy-nudge-template")).toBeNull();
  });

  it("nudge template row appears when github_comment is checked", async () => {
    setupStewardPolicy({
      policy: policyFixture({
        eligible_effect_kinds: ["github_comment"],
        nudge_template: "PR waiting {days} days.",
      }),
    });
    render(<WindowHarness scope="project:p1" />);
    await openPolicy();

    const templateRow = screen.getByTestId("steward-policy-nudge-template");
    expect(templateRow).toBeTruthy();

    const input = templateRow.querySelector("input") as HTMLInputElement;
    expect(input.value).toBe("PR waiting {days} days.");
  });

  it("checking github_comment reveals the template row", async () => {
    setupStewardPolicy({ policy: policyFixture({ eligible_effect_kinds: [] }) });
    render(<WindowHarness scope="project:p1" />);
    await openPolicy();

    // Initially no template
    expect(screen.queryByTestId("steward-policy-nudge-template")).toBeNull();

    // Check the sixth checkbox (github_comment)
    const effectsSection = screen.getByTestId("steward-policy-effects");
    const checkboxes = effectsSection.querySelectorAll('input[type="checkbox"]');
    const githubCheckbox = checkboxes[5] as HTMLInputElement;
    fireEvent.click(githubCheckbox);

    // Template row now visible
    await waitFor(() => {
      expect(screen.getByTestId("steward-policy-nudge-template")).toBeTruthy();
    });
  });

  it("Save round-trips with nudge_template", async () => {
    setupStewardPolicy({
      policy: policyFixture({
        eligible_effect_kinds: ["github_comment"],
        nudge_template: "Custom template {days}.",
      }),
    });
    render(<WindowHarness scope="project:p1" />);
    await openPolicy();

    // Edit the template
    const templateRow = screen.getByTestId("steward-policy-nudge-template");
    const input = templateRow.querySelector("input") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Updated {days} template." } });

    // Save
    fireEvent.click(screen.getByTestId("steward-verb-save-policy"));

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        expect.stringContaining("/steward/policy"),
        expect.objectContaining({
          method: "PUT",
          json: expect.objectContaining({
            nudge_template: "Updated {days} template.",
          }),
        }),
      );
    });
  });
});
