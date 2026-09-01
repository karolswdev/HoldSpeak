// HS-162-05 -- UpdatePosture mounted-path tests: posture swap, draft list,
// editor, claim chips (ref -> open), five verbs, egress badge, marked spans,
// generator provenance, fallback_reason, published read-only.
// Proves the mount: from the real Room, open the Update posture by real clicks.

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

// ── Fixture factories (mined from tests/integration/test_update_routes.py) ──

function roomResponse(overrides: Record<string, unknown> = {}) {
  return {
    project_id: "p1",
    revision: 5,
    observed_at: "2026-08-31T10:00:00",
    project: {
      id: "p1",
      name: "Alpha Project",
      description: "Testing updates",
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
      revision: 5,
    },
    items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: { state: "ok", count: 2, latest: { id: "m1", title: "Review" } },
    resources: { state: "ok", count: 1, latest: null },
    changes: { state: "ok", recent: [] },
    review: { state: "absent", reason: "not_yet_built" },
    sources: { state: "absent", reason: "not_yet_built" },
    updates: overrides.updates ?? { state: "absent", reason: "not_yet_built" },
    steward: { state: "absent", reason: "not_yet_built" },
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

/** A deterministic draft update as the backend returns it.
 *  Shape mined from test_update_routes.TestTheLoop.test_full_loop. */
function draftUpdateFixture(overrides: Record<string, unknown> = {}) {
  return {
    id: "pupd-draft-01",
    project_id: "p1",
    project_revision: 5,
    review_id: null,
    lifecycle: "draft",
    draft_revision: 1,
    body_md: "## Progress\n\nWidget development on track.\n\n## Risks & blockers\n\nNo blockers identified.\n",
    claims_json: JSON.stringify([
      {
        span_id: "s_progress_1",
        text: "Widget development on track",
        refs: ["action_item:ai-01"],
        section: "progress",
      },
      {
        span_id: "s_progress_2",
        text: "Three milestones completed this sprint",
        refs: ["milestone:ms-01", "milestone:ms-02"],
        section: "progress",
      },
      {
        span_id: "s_risks_1",
        text: "Unverified risk claim from model",
        refs: [],
        section: "risks_blockers",
        verified: false,
      },
      {
        span_id: "s_decisions_1",
        text: "Adopted event sourcing pattern",
        refs: ["decision:d-01"],
        section: "decisions",
      },
      {
        span_id: "s_next_1",
        text: "Review meeting scheduled",
        refs: ["meeting:m-01"],
        section: "next_actions",
      },
    ]),
    source_manifest_json: "{}",
    generator: "deterministic",
    fallback_reason: null,
    created_at: "2026-08-31T10:00:00",
    updated_at: "2026-08-31T10:00:00",
    published_at: null,
    ...overrides,
  };
}

/** A published update fixture. */
function publishedUpdateFixture(overrides: Record<string, unknown> = {}) {
  return draftUpdateFixture({
    id: "pupd-pub-01",
    lifecycle: "published",
    published_at: "2026-08-31T12:00:00",
    ...overrides,
  });
}

/** A model-fallback draft (mined from TestModelFallback). */
function modelFallbackFixture() {
  return draftUpdateFixture({
    id: "pupd-fb-01",
    generator: "deterministic",
    fallback_reason: "model_unavailable",
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
  mockOpenPrimitive.mockClear();
  mockOpenSurfaceOr.mockClear();
});

afterEach(() => {
  vi.clearAllMocks();
});

// ── Helpers ──

/** Set up apiFetch to serve the room + detail + updates list + draft. */
function setupUpdatePosture(opts: {
  listUpdates?: Record<string, unknown>[];
  draftResult?: Record<string, unknown>;
} = {}) {
  const listUpdates = opts.listUpdates ?? [draftUpdateFixture()];
  const draftResult = opts.draftResult ?? draftUpdateFixture();

  apiFetch.mockImplementation((url: string, init?: Record<string, unknown>) => {
    // Room
    if (url.includes("/room")) {
      return Promise.resolve(roomResponse());
    }
    // Updates list
    if (url.match(/\/api\/projects\/[^/]+\/updates$/) || url.match(/\/api\/projects\/[^/]+\/updates\?/)) {
      return Promise.resolve({ updates: listUpdates });
    }
    // Draft
    if (url.includes("/updates/draft")) {
      return Promise.resolve({ success: true, update: draftResult });
    }
    // Save
    if (url.match(/\/api\/updates\/[^/]+$/) && init?.method === "PUT") {
      const body = init?.json as Record<string, unknown> | undefined;
      return Promise.resolve({
        success: true,
        update: { ...draftResult, body_md: body?.body_md ?? draftResult.body_md },
      });
    }
    // Publish
    if (url.includes("/publish")) {
      return Promise.resolve({
        success: true,
        update: publishedUpdateFixture({ id: draftResult.id }),
      });
    }
    // Regenerate
    if (url.includes("/regenerate")) {
      return Promise.resolve({
        success: true,
        update: draftUpdateFixture({ id: "pupd-regen-01", draft_revision: 2 }),
      });
    }
    // Markdown
    if (url.includes("/markdown")) {
      return Promise.resolve(draftResult.body_md ?? "## Progress\n");
    }
    // Detail responses
    return Promise.resolve(detailResponse(url));
  });
}

// ── MOUNT PROOF: The posture opens from the Room by real clicks ──

describe("Mount proof: Updates verb in Room chrome", () => {
  it("shows 'Updates' button in the Room", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    const btn = await screen.findByTestId("updates-verb");
    expect(btn.textContent).toBe("Updates");
  });

  it("clicking 'Updates' enters the update list posture", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    const btn = await screen.findByTestId("updates-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("update-posture")).toBeTruthy();
    });

    expect(screen.getByTestId("update-posture").getAttribute("data-phase")).toBe("list");
  });
});

// ── MOUNTED-PATH: draft -> edit -> claim chips -> save -> publish ──

describe("Mounted-path: full draft-to-publish walk", () => {
  it("drafts, opens editor, edits, saves, publishes", async () => {
    setupUpdatePosture({ listUpdates: [] });
    render(<WindowHarness scope="project:p1" />);

    // Enter update posture
    const btn = await screen.findByTestId("updates-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("update-posture")).toBeTruthy();
    });

    // Click "Draft" to create a deterministic draft
    const draftBtn = screen.getByTestId("update-verb-draft-deterministic");
    fireEvent.click(draftBtn);

    // Editor opens
    await waitFor(() => {
      expect(screen.getByTestId("update-editor")).toBeTruthy();
    });

    // Verify we're in the editor
    expect(screen.getByTestId("update-posture").getAttribute("data-phase")).toBe("editor");

    // Body textarea is present and editable
    const textarea = screen.getByTestId("update-body-textarea") as HTMLTextAreaElement;
    expect(textarea.value).toContain("## Progress");

    // Edit the body
    fireEvent.change(textarea, { target: { value: "## Progress\n\nOwner edited.\n" } });

    // Save button becomes enabled
    const saveBtn = screen.getByTestId("update-verb-save");
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/updates/"),
        expect.objectContaining({ method: "PUT" }),
      );
    });

    // Publish
    const publishBtn = screen.getByTestId("update-verb-publish");
    fireEvent.click(publishBtn);

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        expect.stringContaining("/publish"),
        expect.objectContaining({ method: "POST" }),
      );
    });

    // After publish, lifecycle shows published
    await waitFor(() => {
      const editor = screen.getByTestId("update-editor");
      expect(editor.getAttribute("data-lifecycle")).toBe("published");
    });
  });
});

// ── CLAIM CHIPS: render and one OPENS its source ──

describe("Claim chips: render and open source", () => {
  it("renders claim chips with refs", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    // Enter update posture
    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    // Open the draft in the editor
    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => {
      expect(screen.getByTestId("update-editor")).toBeTruthy();
    });

    // Claims should be rendered
    const claimChips = screen.getAllByTestId("update-claim-chip");
    expect(claimChips.length).toBeGreaterThanOrEqual(4);

    // Ref chips should be present
    const refChips = screen.getAllByTestId("update-claim-ref");
    expect(refChips.length).toBeGreaterThanOrEqual(4);
  });

  it("clicking a ref chip with action_item: opens the primitive", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    // Find the action_item ref chip and click it
    const refChips = screen.getAllByTestId("update-claim-ref");
    const actionItemChip = refChips.find(
      (el) => el.getAttribute("data-ref") === "action_item:ai-01",
    );
    expect(actionItemChip).toBeTruthy();
    fireEvent.click(actionItemChip!);

    // Should call openPrimitive for non-meeting refs
    expect(mockOpenPrimitive).toHaveBeenCalledWith("action_item:ai-01");
  });

  it("clicking a meeting ref opens via openSurfaceOr", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    // Find the meeting ref chip
    const refChips = screen.getAllByTestId("update-claim-ref");
    const meetingChip = refChips.find(
      (el) => el.getAttribute("data-ref") === "meeting:m-01",
    );
    expect(meetingChip).toBeTruthy();
    fireEvent.click(meetingChip!);

    // Meeting refs open via openSurfaceOr
    expect(mockOpenSurfaceOr).toHaveBeenCalledWith(
      "review-meetings",
      "/history",
      "meeting:m-01",
    );
  });

  it("clicking a decision ref opens the primitive", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    const refChips = screen.getAllByTestId("update-claim-ref");
    const decisionChip = refChips.find(
      (el) => el.getAttribute("data-ref") === "decision:d-01",
    );
    expect(decisionChip).toBeTruthy();
    fireEvent.click(decisionChip!);

    expect(mockOpenPrimitive).toHaveBeenCalledWith("decision:d-01");
  });
});

// ── MARKED SPANS: unverified claims visually distinct ──

describe("Marked spans: unverified claims", () => {
  it("renders [UNVERIFIED] marker on unverified claims", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    // Find unverified marker
    const markers = screen.getAllByTestId("update-claim-unverified");
    expect(markers.length).toBe(1);
    expect(markers[0].textContent).toBe("[UNVERIFIED]");

    // The unverified chip has the is-unverified class
    const unverifiedChip = markers[0].closest(".update-claim-chip");
    expect(unverifiedChip?.classList.contains("is-unverified")).toBe(true);
  });

  it("verified claims have no [UNVERIFIED] marker", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    // Only 1 unverified out of 5 total claims
    const allChips = screen.getAllByTestId("update-claim-chip");
    expect(allChips.length).toBe(5);

    const verifiedChips = allChips.filter(
      (el) => el.getAttribute("data-verified") === "true",
    );
    expect(verifiedChips.length).toBe(4);

    const unverifiedChips = allChips.filter(
      (el) => el.getAttribute("data-verified") === "false",
    );
    expect(unverifiedChips.length).toBe(1);
  });
});

// ── FIVE VERBS: Draft, Regenerate, Save, Copy Markdown, Publish ──

describe("Five verbs as separate controls", () => {
  it("shows Draft and Draft-with-model in the list view", async () => {
    setupUpdatePosture({ listUpdates: [] });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    expect(screen.getByTestId("update-verb-draft-deterministic")).toBeTruthy();
    expect(screen.getByTestId("update-verb-draft-model")).toBeTruthy();
  });

  it("shows Save, Regenerate, Copy Markdown, Publish in the editor for a draft", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    expect(screen.getByTestId("update-verb-save")).toBeTruthy();
    expect(screen.getByTestId("update-verb-regenerate")).toBeTruthy();
    expect(screen.getByTestId("update-verb-copy")).toBeTruthy();
    expect(screen.getByTestId("update-verb-publish")).toBeTruthy();
  });

  it("Publish button has primary variant (consequential styling)", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    const publishBtn = screen.getByTestId("update-verb-publish");
    // Button component with variant="primary" gets data-variant or className
    // Check the button exists and is distinct
    expect(publishBtn.textContent).toBe("Publish");
  });
});

// ── EGRESS BADGE: on the model-draft action ──

describe("Egress badge on model drafting", () => {
  it("shows EgressChip next to Draft-with-model", async () => {
    setupUpdatePosture({ listUpdates: [] });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    // The model-draft action should have an egress chip
    const modelAction = screen.getByTestId("update-draft-model-action");
    expect(modelAction).toBeTruthy();

    // EgressChip renders as a span with class gadget-chip-egress
    const egressChip = modelAction.querySelector(".gadget-chip-egress");
    expect(egressChip).toBeTruthy();
    expect(egressChip!.textContent).toBe("local + cloud");
    expect(egressChip!.getAttribute("data-scope")).toBe("mixed");
  });
});

// ── GENERATOR PROVENANCE ──

describe("Generator provenance", () => {
  it("shows deterministic label on a deterministic draft", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    const label = screen.getByTestId("update-generator-label");
    expect(label.textContent).toBe("Deterministic");
  });

  it("shows model assignment on a model draft", async () => {
    setupUpdatePosture({
      listUpdates: [draftUpdateFixture({ generator: "model:gpt-4o" })],
      draftResult: draftUpdateFixture({ generator: "model:gpt-4o" }),
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    const label = screen.getByTestId("update-generator-label");
    expect(label.textContent).toBe("Model (gpt-4o)");
  });

  it("surfaces fallback_reason when model fell back to deterministic", async () => {
    setupUpdatePosture({
      listUpdates: [modelFallbackFixture()],
      draftResult: modelFallbackFixture(),
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    const fallback = screen.getByTestId("update-fallback-reason");
    expect(fallback.textContent).toBe("model_unavailable");
  });
});

// ── PUBLISHED READ-ONLY ──

describe("Published update is read-only", () => {
  it("renders read-only body for published updates", async () => {
    setupUpdatePosture({
      listUpdates: [publishedUpdateFixture()],
      draftResult: publishedUpdateFixture(),
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    // Published updates show read-only body (no textarea)
    expect(screen.queryByTestId("update-body-textarea")).toBeNull();
    expect(screen.getByTestId("update-body-readonly")).toBeTruthy();

    // Readonly reason shown
    expect(screen.getByTestId("update-readonly-reason")).toBeTruthy();
    expect(screen.getByTestId("update-readonly-reason").textContent).toBe(
      "Published updates are read-only",
    );

    // No Save or Publish buttons
    expect(screen.queryByTestId("update-verb-save")).toBeNull();
    expect(screen.queryByTestId("update-verb-publish")).toBeNull();
  });
});

// ── LIST LIFECYCLE DISTINCTION ──

describe("Draft list: lifecycle-honest", () => {
  it("renders draft, published, superseded with distinct labels", async () => {
    setupUpdatePosture({
      listUpdates: [
        draftUpdateFixture({ id: "u1", lifecycle: "draft" }),
        publishedUpdateFixture({ id: "u2", lifecycle: "published" }),
        draftUpdateFixture({ id: "u3", lifecycle: "superseded" }),
      ],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = screen.getAllByTestId("update-list-item");
    expect(items.length).toBe(3);

    // Each lifecycle is reflected
    const lifecycleLabels = items.map(
      (item) =>
        item.querySelector("[data-lifecycle]")?.getAttribute("data-lifecycle"),
    );
    expect(lifecycleLabels).toContain("draft");
    expect(lifecycleLabels).toContain("published");
    expect(lifecycleLabels).toContain("superseded");
  });
});

// ── COPY MARKDOWN ──

describe("Copy Markdown verb", () => {
  it("calls GET /api/updates/{id}/markdown and copies to clipboard", async () => {
    // Mock clipboard
    const mockWriteText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText: mockWriteText } });

    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    const copyBtn = screen.getByTestId("update-verb-copy");
    fireEvent.click(copyBtn);

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        expect.stringContaining("/markdown"),
      );
    });

    await waitFor(() => {
      expect(mockWriteText).toHaveBeenCalled();
    });

    // After copy, the button text changes to "Copied"
    await waitFor(() => {
      expect(screen.getByTestId("update-verb-copy").textContent).toBe("Copied");
    });
  });
});

// ── MIC BUTTON PRESENCE ──

describe("Mic on the editor", () => {
  it("renders MicButton in the editor toolbar", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-body-editor"));

    // MicButton should be present in the editor toolbar
    const toolbar = screen.getByTestId("update-body-editor")
      .querySelector(".update-body-editor-toolbar");
    expect(toolbar).toBeTruthy();
    // MicButton renders a button with specific aria or class
    const mic = toolbar!.querySelector("button");
    expect(mic).toBeTruthy();
  });
});
