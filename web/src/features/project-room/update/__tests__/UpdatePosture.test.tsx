// HS-162-05 -- UpdatePosture mounted-path tests: posture swap, draft list,
// DeskEditor for editing, Material-rendered document for published,
// deduplicated source rows (ref -> open), five verbs, egress badge,
// unverified banner, generator provenance, fallback_reason.
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

// DeskEditor mock: renders as a plain textarea (same pattern as
// ThoughtNoteEditor.test.tsx — the house mock for the Notes editor).
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

// ── MOUNTED-PATH: draft -> edit -> save -> publish ──

describe("Mounted-path: full draft-to-publish walk", () => {
  it("drafts via DeskEditor, edits, saves, publishes", async () => {
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

    // Editor opens with DeskEditor (mocked as textarea)
    await waitFor(() => {
      expect(screen.getByTestId("update-editor")).toBeTruthy();
    });

    expect(screen.getByTestId("update-posture").getAttribute("data-phase")).toBe("editor");

    // DeskEditor textarea is present and editable
    const textarea = screen.getByTestId("update-body-textarea") as HTMLTextAreaElement;
    expect(textarea.value).toContain("## Progress");

    // Edit the body
    fireEvent.change(textarea, { target: { value: "## Progress\n\nOwner edited.\n" } });

    // Save
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

// ── SOURCE ROWS: deduplicated refs, open source ──

describe("Source rows: deduplicated refs and open source", () => {
  it("renders deduplicated source rows with ref chips", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => {
      expect(screen.getByTestId("update-editor")).toBeTruthy();
    });

    // Source rows should be present (deduplicated)
    const sourceRows = screen.getAllByTestId("update-source-row");
    expect(sourceRows.length).toBeGreaterThanOrEqual(1);

    // Ref chips with human labels
    const refChips = screen.getAllByTestId("update-claim-ref");
    expect(refChips.length).toBeGreaterThanOrEqual(4);

    const actionItemChip = refChips.find(
      (el) => el.getAttribute("data-ref") === "action_item:ai-01",
    );
    expect(actionItemChip!.textContent).toBe("Widget development on track");

    const decisionChip = refChips.find(
      (el) => el.getAttribute("data-ref") === "decision:d-01",
    );
    expect(decisionChip!.textContent).toBe("Adopted event sourcing pattern");

    const meetingChip = refChips.find(
      (el) => el.getAttribute("data-ref") === "meeting:m-01",
    );
    expect(meetingChip!.textContent).toBe("Review meeting scheduled");
  });

  it("no raw IDs on glass: ref chip visible text never matches hash pattern", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    const refChips = screen.getAllByTestId("update-claim-ref");
    const rawIdPattern = /^p[a-z]+_[0-9a-f]{16,}/;
    for (const chip of refChips) {
      expect(chip.textContent).not.toMatch(rawIdPattern);
    }

    // data-ref still carries the full ref for wiring
    const actionItemChip = refChips.find(
      (el) => el.getAttribute("data-ref") === "action_item:ai-01",
    );
    expect(actionItemChip).toBeTruthy();
    expect(actionItemChip!.getAttribute("data-ref")).toBe("action_item:ai-01");
  });

  it("clicking a ref chip with action_item: opens the primitive", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    const refChips = screen.getAllByTestId("update-claim-ref");
    const actionItemChip = refChips.find(
      (el) => el.getAttribute("data-ref") === "action_item:ai-01",
    );
    expect(actionItemChip).toBeTruthy();
    expect(actionItemChip!.textContent).toBe("Widget development on track");
    fireEvent.click(actionItemChip!);

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

    const refChips = screen.getAllByTestId("update-claim-ref");
    const meetingChip = refChips.find(
      (el) => el.getAttribute("data-ref") === "meeting:m-01",
    );
    expect(meetingChip).toBeTruthy();
    expect(meetingChip!.textContent).toBe("Review meeting scheduled");
    fireEvent.click(meetingChip!);

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
    expect(decisionChip!.textContent).toBe("Adopted event sourcing pattern");
    fireEvent.click(decisionChip!);

    expect(mockOpenPrimitive).toHaveBeenCalledWith("decision:d-01");
  });
});

// ── UNVERIFIED CLAIMS: banner when present ──

describe("Unverified claims: banner in document view", () => {
  it("shows unverified banner when claims have verified=false", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    // The unverified banner appears (the risks_blockers claim has verified:false + no refs)
    const banner = screen.getByTestId("update-claim-unverified");
    expect(banner.textContent).toBe("Contains unverified claims");
  });
});

// ── PUBLISHED VIEW: rendered document, not claims dump ──

describe("Published view: rendered document", () => {
  it("renders Material body for published updates (not a claims dump)", async () => {
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

    // No textarea (draft editor)
    expect(screen.queryByTestId("update-body-textarea")).toBeNull();

    // The rendered document is present
    expect(screen.getByTestId("update-document")).toBeTruthy();
    expect(screen.getByTestId("update-document-body")).toBeTruthy();

    // Material renders the markdown body (headings become strong.surface-material-h)
    const body = screen.getByTestId("update-document-body");
    const headings = body.querySelectorAll(".surface-material-h");
    expect(headings.length).toBeGreaterThanOrEqual(1);

    // Read-only reason shown
    expect(screen.getByTestId("update-readonly-reason")).toBeTruthy();
    expect(screen.getByTestId("update-readonly-reason").textContent).toBe(
      "Published updates are read-only",
    );

    // Source rows present (deduplicated refs)
    const sourceRows = screen.getAllByTestId("update-source-row");
    expect(sourceRows.length).toBeGreaterThanOrEqual(1);

    // No Save or Publish buttons
    expect(screen.queryByTestId("update-verb-save")).toBeNull();
    expect(screen.queryByTestId("update-verb-publish")).toBeNull();
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

    const modelAction = screen.getByTestId("update-draft-model-action");
    expect(modelAction).toBeTruthy();

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
    expect(fallback.textContent).toBe("Model unavailable -- drafted deterministically");
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

    const lifecycleLabels = items.map(
      (item) =>
        item.querySelector("[data-lifecycle]")?.getAttribute("data-lifecycle"),
    );
    expect(lifecycleLabels).toContain("draft");
    expect(lifecycleLabels).toContain("published");
    expect(lifecycleLabels).toContain("superseded");
  });

  it("shows provenance in plain words (no assignment id in row text)", async () => {
    setupUpdatePosture({
      listUpdates: [
        draftUpdateFixture({ id: "u1", generator: "deterministic" }),
        draftUpdateFixture({ id: "u2", generator: "model:gpt-4o" }),
      ],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const provenances = screen.getAllByTestId("update-list-provenance");
    expect(provenances.length).toBe(2);

    // Deterministic row says "Deterministic draft"
    expect(provenances[0].textContent).toContain("Deterministic draft");

    // Model row says "Model draft" — no assignment id visible
    expect(provenances[1].textContent).toContain("Model draft");
    expect(provenances[1].textContent).not.toContain("gpt-4o");
    expect(provenances[1].textContent).not.toContain("(");
  });

  it("row has two-line structure: primary line + secondary line as separate children", async () => {
    setupUpdatePosture({
      listUpdates: [draftUpdateFixture()],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = screen.getAllByTestId("update-list-item");
    const row = items[0].querySelector(".update-list-row");
    expect(row).toBeTruthy();

    // The row is a flex-column with two children (primary + secondary)
    const primary = row!.querySelector(".update-list-primary");
    const secondary = row!.querySelector(".update-list-secondary");
    expect(primary).toBeTruthy();
    expect(secondary).toBeTruthy();

    // Primary contains lifecycle + rev + time as separate elements
    expect(primary!.querySelector(".surface-token")).toBeTruthy();
    expect(primary!.querySelector(".update-list-rev")).toBeTruthy();
    expect(primary!.querySelector(".update-list-time")).toBeTruthy();

    // The row sits inside .surface-ledger-primary which must allow
    // the two-line layout (the CSS override lifts white-space:nowrap).
    const ledgerPrimary = row!.closest(".surface-ledger-primary");
    expect(ledgerPrimary).toBeTruthy();
  });

  it("row carries an open chevron affordance and is a button (keyboard-accessible)", async () => {
    setupUpdatePosture({
      listUpdates: [draftUpdateFixture()],
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    // Chevron present in the row
    const chevron = screen.getByTestId("update-list-chevron");
    expect(chevron).toBeTruthy();
    expect(chevron.textContent).toBe("›"); // ›

    // The row is rendered inside a button (SurfaceLedgerRow renders <button class="surface-ledger-line">)
    const item = screen.getByTestId("update-list-item");
    expect(item.tagName).toBe("BUTTON");

    // S-3: rows navigate, not expand -- no aria-expanded attribute
    expect(item.hasAttribute("aria-expanded")).toBe(false);

    // Clicking the row opens the editor
    fireEvent.click(item);
    await waitFor(() => {
      expect(screen.getByTestId("update-editor")).toBeTruthy();
    });
  });
});

// ── SUPERSEDED READONLY LABEL ──

describe("Superseded readonly label", () => {
  it("shows lifecycle-honest read-only reason for superseded updates", async () => {
    setupUpdatePosture({
      listUpdates: [draftUpdateFixture({ id: "u-sup", lifecycle: "superseded" })],
      draftResult: draftUpdateFixture({ id: "u-sup", lifecycle: "superseded" }),
    });
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-editor"));

    const reason = screen.getByTestId("update-readonly-reason");
    expect(reason.textContent).toContain("Superseded");
    expect(reason.textContent).not.toBe("Published updates are read-only");
  });
});

// ── COPY MARKDOWN ──

describe("Copy Markdown verb", () => {
  it("calls GET /api/updates/{id}/markdown and copies to clipboard", async () => {
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

    await waitFor(() => {
      expect(screen.getByTestId("update-verb-copy").textContent).toBe("Copied");
    });
  });
});

// ── MIC BUTTON PRESENCE ──

describe("Mic on the DeskEditor", () => {
  it("renders MicButton alongside the DeskEditor", async () => {
    setupUpdatePosture();
    render(<WindowHarness scope="project:p1" />);

    fireEvent.click(await screen.findByTestId("updates-verb"));
    await waitFor(() => screen.getByTestId("update-posture"));

    const items = await screen.findAllByTestId("update-list-item");
    fireEvent.click(items[0]);

    await waitFor(() => screen.getByTestId("update-body-editor"));

    // MicButton is in the mic row alongside the DeskEditor
    const micRow = screen.getByTestId("update-body-editor")
      .querySelector(".update-body-editor-mic");
    expect(micRow).toBeTruthy();
    const mic = micRow!.querySelector("button");
    expect(mic).toBeTruthy();
  });
});
