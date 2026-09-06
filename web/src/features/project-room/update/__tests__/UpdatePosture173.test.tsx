// HS-173-02 -- UpdatePosture 173 face tests: per-claim UNVERIFIED chips,
// footer model+host for model drafts, no footer egress for deterministic.

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
      data-testid="update-body-textarea"
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
      name: "Alpha Project",
      description: "Testing updates",
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
    steward: { state: "absent", reason: "not_yet_built" },
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

function draftWithModel() {
  return {
    id: "pupd-model-01",
    project_id: "p1",
    project_revision: 5,
    review_id: null,
    lifecycle: "draft",
    draft_revision: 3,
    body_md: "## Progress\n\nThe API schema migration merged.\n",
    claims_json: JSON.stringify([
      {
        span_id: "s1",
        text: "The API schema migration merged",
        refs: ["item:pr-612"],
        section: "progress",
        verified: true,
      },
      {
        span_id: "s2",
        text: "Payments cut-over runbook overdue by 2 days",
        refs: ["item:kan-7"],
        section: "progress",
        verified: true,
      },
      {
        span_id: "s3",
        text: "Team agreed to target Oct 12 for the cut-over",
        refs: ["meeting:2026-09-05"],
        section: "progress",
        verified: true,
      },
      {
        span_id: "s4",
        text: "Sprint velocity improved 15% over the trailing average",
        refs: [],
        section: "progress",
        verified: false,
      },
    ]),
    source_manifest_json: "{}",
    generator: "model:qwen3-32b",
    generatorHost: "192.168.1.43",
    generatorModel: "QWEN3 32B Q6",
    fallback_reason: null,
    created_at: "2026-09-05T10:00:00",
    updated_at: "2026-09-05T10:00:00",
    published_at: null,
  };
}

function deterministicDraft() {
  return {
    id: "pupd-det-01",
    project_id: "p1",
    project_revision: 5,
    review_id: null,
    lifecycle: "draft",
    draft_revision: 2,
    body_md: "## Progress\n\nAPI schema migration merged.\n",
    claims_json: JSON.stringify([
      {
        span_id: "s1",
        text: "API schema migration merged",
        refs: ["item:pr-612"],
        section: "progress",
        verified: true,
      },
    ]),
    source_manifest_json: "{}",
    generator: "deterministic",
    generatorHost: null,
    generatorModel: null,
    fallback_reason: null,
    created_at: "2026-09-05T10:00:00",
    updated_at: "2026-09-05T10:00:00",
    published_at: null,
  };
}

function setupUpdatePosture(opts: {
  listUpdates?: Record<string, unknown>[];
  draftResult?: Record<string, unknown>;
} = {}) {
  const listUpdates = opts.listUpdates ?? [draftWithModel()];
  const draftResult = opts.draftResult ?? draftWithModel();

  apiFetch.mockImplementation((url: string, init?: Record<string, unknown>) => {
    if (url.includes("/room/read")) {
      return Promise.resolve({ read_at: new Date().toISOString() });
    }
    if (url.includes("/room")) {
      return Promise.resolve(roomResponse());
    }
    if (url.match(/\/api\/projects\/[^/]+\/updates$/) || url.match(/\/api\/projects\/[^/]+\/updates\?/)) {
      return Promise.resolve({ updates: listUpdates });
    }
    if (url.includes("/updates/draft")) {
      return Promise.resolve({ success: true, update: draftResult });
    }
    if (url.match(/\/api\/updates\/[^/]+$/) && init?.method === "PUT") {
      return Promise.resolve({ success: true, update: draftResult });
    }
    if (url.includes("/publish")) {
      return Promise.resolve({ success: true, update: { ...draftResult, lifecycle: "published" } });
    }
    if (url.includes("/markdown")) {
      return Promise.resolve("## Progress\n");
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
});

afterEach(() => {
  vi.clearAllMocks();
});

// ── Helper: navigate to editor ──

async function openEditor() {
  const btn = await screen.findByTestId("updates-verb");
  fireEvent.click(btn);
  await waitFor(() => screen.getByTestId("update-posture"));
  const items = await screen.findAllByTestId("update-list-item");
  fireEvent.click(items[0]);
  await waitFor(() => screen.getByTestId("update-editor"));
}

// ── HS-173-02: inline claims view ──

describe("HS-173-02: inline claims with chips per sentence", () => {
  it("renders each claim as a sentence with inline ref identity chips", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);
    await openEditor();

    // Inline claims container present
    const container = screen.getByTestId("update-inline-claims");
    expect(container).toBeTruthy();

    // Each claim gets its own row (4 claims now)
    const claimRows = screen.getAllByTestId("update-inline-claim");
    expect(claimRows.length).toBe(4);

    // Three claims have ref chips (s1, s2, s3 have refs; s4 has none)
    const refChips = screen.getAllByTestId("update-claim-ref");
    expect(refChips.length).toBe(3);

    // Chip labels are ref identities, not claim text
    const chipLabels = refChips.map((c) => c.textContent);
    expect(chipLabels).toContain("PR #612");
    expect(chipLabels).toContain("KAN-7");
    expect(chipLabels).toContain("MTG 09-05");

    // Claim text is rendered inline as plain text
    expect(claimRows[0].textContent).toContain("The API schema migration merged");
  });

  it("UNVERIFIED badge only for verified=false claims, inline beside the sentence", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);
    await openEditor();

    const badges = screen.getAllByTestId("update-claim-unverified");
    expect(badges.length).toBe(1);
    expect(badges[0].textContent).toContain("UNVERIFIED");

    // The badge is inside the fourth claim row (the unverified one, s4)
    const claimRows = screen.getAllByTestId("update-inline-claim");
    expect(claimRows[3].querySelector('[data-testid="update-claim-unverified"]')).toBeTruthy();
  });

  it("no UNVERIFIED badge when all claims are verified", async () => {
    const allVerified = draftWithModel();
    allVerified.claims_json = JSON.stringify([
      { span_id: "s1", text: "API migration merged", refs: ["item:pr-612"], section: "progress", verified: true },
    ]);
    setupUpdatePosture({ listUpdates: [allVerified], draftResult: allVerified });
    render(<WindowHarness scope="project:p1" />);
    await openEditor();

    expect(screen.queryByTestId("update-claim-unverified")).toBeNull();
  });
});

// ── HS-173-02: footer model + host for model drafts ──

describe("HS-173-02: footer model name + host chip for model drafts", () => {
  it("shows model name token and EgressChip with host for model drafts", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);
    await openEditor();

    // Model name token in footer
    const modelToken = screen.getByTestId("update-footer-model");
    expect(modelToken.textContent).toBe("QWEN3 32B Q6");

    // EgressChip with LAN label
    const footer = screen.getByTestId("update-posture");
    const egressChips = footer.querySelectorAll(".gadget-chip-egress");
    const hostChip = Array.from(egressChips).find(
      (el) => el.textContent?.includes("192.168.1.43"),
    );
    expect(hostChip).toBeTruthy();
    expect(hostChip!.textContent).toContain("LAN");
  });

  it("no model token or host chip for deterministic drafts", async () => {
    setupUpdatePosture({
      listUpdates: [deterministicDraft()],
      draftResult: deterministicDraft(),
    });
    render(<WindowHarness scope="project:p1" />);
    await openEditor();

    expect(screen.queryByTestId("update-footer-model")).toBeNull();
  });
});
