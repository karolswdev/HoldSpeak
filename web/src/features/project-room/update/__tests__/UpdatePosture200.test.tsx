// HS-200-06 -- the three claim axes on the glass: kind as the lead
// emblem, support and acceptance as their own tokens. A citation shows
// LINKED, never SUPPORTED; a migrated record says so; an edited
// sentence says its support was invalidated.

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TitleSlotContext } from "../../../../desk/surface/title";
import { WingSlotContext } from "../../../../desk/surface/wings";
import { useDesk } from "../../../../desk/store";
import { EMPTY_ITEMS } from "../../../../desk/api";
import { ProjectRoomCore } from "../../ProjectRoomCore";

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
  return { ...actual, openPrimitive: vi.fn(), openSurfaceOr: vi.fn() };
});

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

function roomResponse() {
  return {
    project_id: "p1",
    revision: 5,
    observed_at: "2026-09-06T10:00:00",
    nextCheckAt: null,
    project: {
      id: "p1",
      name: "Alpha Project",
      description: "Testing claim axes",
      is_archived: false,
      meeting_count: 0,
      created_at: "2026-08-01T00:00:00",
      updated_at: "2026-09-06T10:00:00",
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
    health: {
      state: "ok",
      assessment: "on_track",
      reason: null,
      inputs: {
        overdue: 0,
        ciFailing: false,
        reviewWaitingDays: null,
        targetPassed: false,
      },
    },
    sinceRead: { state: "ok", readAt: null, groups: [] },
    decisions: { state: "ok", items: [] },
    commitments: { state: "ok", items: [] },
    target: { state: "absent", reason: "none" },
    updates: { state: "absent", reason: "not_yet_built" },
    steward: { state: "absent", reason: "not_yet_built" },
  };
}

/** One draft carrying every support state the service can serve. */
function mixedAxesDraft() {
  return {
    id: "pupd-axes-01",
    project_id: "p1",
    project_revision: 5,
    review_id: null,
    lifecycle: "draft",
    draft_revision: 2,
    body_md:
      "## Progress\n\n- Milestone [high]: Launch v2.0 -- planned\n" +
      "- API schema migration merged\n\n## Decisions\n\n" +
      "- API Gateway degraded (risk_attention) -- accepted\n",
    claims_json: JSON.stringify([
      {
        span_id: "s1",
        text: "Milestone [high]: Launch v2.0 -- planned",
        refs: ["item:pr-612"],
        section: "progress",
        kind: "observation",
        support: "supported",
        acceptance: "unreviewed",
        support_record: {
          method: "field_mapping",
          source_version: "project:p1@r5",
          source_refs: ["item:pr-612"],
          fields: ["item_type", "severity", "title", "lifecycle"],
        },
      },
      {
        span_id: "s2",
        text: "API Gateway degraded (risk_attention) -- accepted",
        refs: ["decision:kan-7"],
        section: "decisions",
        kind: "decision",
        support: "supported",
        acceptance: "accepted",
        support_record: {
          method: "field_mapping",
          source_version: "project:p1@r5",
          source_refs: ["decision:kan-7"],
          fields: ["title", "proposal_kind", "lifecycle"],
          reviewer_ref: "principal:owner",
        },
      },
      {
        span_id: "s3",
        text: "Priya expects the cut-over at 95% by 2026-12-31",
        refs: ["meeting:2026-09-05"],
        section: "progress",
        kind: "inference",
        support: "source_linked",
        acceptance: "unreviewed",
        unknowns: [
          { type: "deadline", value: "2026-12-31" },
          { type: "name", value: "Priya" },
          { type: "number", value: "95%" },
        ],
      },
      {
        span_id: "s4",
        text: "Sprint velocity improved over the trailing average",
        refs: [],
        section: "progress",
        kind: "inference",
        support: "unknown",
        acceptance: "unreviewed",
        verified: false,
      },
      {
        span_id: "s5",
        text: "Dependency: API Gateway -- at_risk",
        refs: ["item:kan-7"],
        section: "dependencies",
        kind: "observation",
        support: "source_linked",
        acceptance: "unreviewed",
        support_mapping_version: "c2.1",
      },
      {
        span_id: "s6",
        text: "Something the owner rewrote",
        refs: ["item:pr-612"],
        section: "progress",
        kind: "observation",
        support: "source_linked",
        acceptance: "unreviewed",
        support_record: {
          method: "field_mapping",
          source_version: "project:p1@r5",
          source_refs: ["item:pr-612"],
          invalidated_at: "2026-09-06T11:00:00+00:00",
          invalidation_reason: "text_edited",
        },
      },
    ]),
    source_manifest_json: "{}",
    generator: "model:qwen3-32b",
    generatorHost: "192.168.1.43",
    generatorModel: "QWEN3 32B Q6",
    fallback_reason: null,
    created_at: "2026-09-06T10:00:00",
    updated_at: "2026-09-06T10:00:00",
    published_at: null,
  };
}

function setupUpdatePosture(draft: Record<string, unknown>) {
  apiFetch.mockImplementation((url: string) => {
    if (url.includes("/room/read")) {
      return Promise.resolve({ read_at: new Date().toISOString() });
    }
    if (url.includes("/room")) return Promise.resolve(roomResponse());
    if (
      url.match(/\/api\/projects\/[^/]+\/updates$/) ||
      url.match(/\/api\/projects\/[^/]+\/updates\?/)
    ) {
      return Promise.resolve({ updates: [draft] });
    }
    if (url.includes("/updates/draft")) {
      return Promise.resolve({ success: true, update: draft });
    }
    if (url.includes("/markdown")) return Promise.resolve("## Progress\n");
    if (url.includes("/meetings")) return Promise.resolve({ meetings: [] });
    if (url.startsWith("/api/decisions")) {
      return Promise.resolve({ decisions: [] });
    }
    if (url.includes("/artifacts")) return Promise.resolve({ artifacts: [] });
    if (url.includes("/since-last-meeting")) {
      return Promise.resolve({
        current_meeting: null,
        since_last_meeting: null,
      });
    }
    return Promise.resolve({});
  });
}

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

/** The chip's accessible label -- its glyph is decorative. */
function chipLabels(testId: string): (string | null)[] {
  return screen
    .getAllByTestId(testId)
    .map((el) =>
      el.querySelector(".surface-state-chip")?.getAttribute("aria-label") ??
      null,
    );
}

async function openEditor() {
  const btn = await screen.findByTestId("updates-verb");
  fireEvent.click(btn);
  await waitFor(() => screen.getByTestId("update-posture"));
  const items = await screen.findAllByTestId("update-list-item");
  fireEvent.click(items[0]);
  await waitFor(() => screen.getByTestId("update-editor"));
}

describe("HS-200-06: the three claim axes on the glass", () => {
  it("every claim leads with its kind and carries support + acceptance", async () => {
    setupUpdatePosture(mixedAxesDraft());
    render(<WindowHarness scope="project:p1" />);
    await openEditor();

    const axes = screen.getAllByTestId("update-claim-axes");
    expect(axes.length).toBe(6);

    const kinds = screen
      .getAllByTestId("update-claim-kind")
      .map((el) => el.textContent);
    expect(kinds).toEqual([
      "OBSERVATION",
      "DECISION",
      "INFERENCE",
      "INFERENCE",
      "OBSERVATION",
      "OBSERVATION",
    ]);

    expect(chipLabels("update-claim-support")).toEqual([
      "SUPPORTED",
      "SUPPORTED",
      "LINKED",
      "UNSUPPORTED",
      "LINKED · MIGRATED",
      "LINKED · EDITED",
    ]);

    expect(chipLabels("update-claim-acceptance")).toEqual([
      "UNREVIEWED",
      "ACCEPTED",
      "UNREVIEWED",
      "UNREVIEWED",
      "UNREVIEWED",
      "UNREVIEWED",
    ]);
  });

  it("a real record id shows its kind word, never the raw hash", async () => {
    const draft = mixedAxesDraft();
    const claims = JSON.parse(draft.claims_json as string) as Record<
      string,
      unknown
    >[];
    claims[0].refs = ["item:pitem_830A2CB095AB442CA61E64EEC728B448"];
    draft.claims_json = JSON.stringify(claims);
    setupUpdatePosture(draft);
    render(<WindowHarness scope="project:p1" />);
    await openEditor();

    const labels = screen
      .getAllByTestId("update-claim-ref")
      .map((el) => el.textContent);
    expect(labels).toContain("ITEM");
    expect(labels.join(" ")).not.toContain("830A2CB0");
  });

  it("a cited model sentence reads LINKED, never SUPPORTED", async () => {
    setupUpdatePosture(mixedAxesDraft());
    render(<WindowHarness scope="project:p1" />);
    await openEditor();

    const rows = screen.getAllByTestId("update-inline-claim");
    const inferred = rows[2];
    expect(inferred.textContent).toContain("LINKED");
    expect(inferred.textContent).not.toContain("SUPPORTED");
  });

  it("names the typed unknowns the cited source cannot carry", async () => {
    setupUpdatePosture(mixedAxesDraft());
    render(<WindowHarness scope="project:p1" />);
    await openEditor();

    expect(chipLabels("update-claim-unknown")).toEqual([
      "DEADLINE · 2026-12-31",
      "NAME · Priya",
      "NUMBER · 95%",
    ]);
  });

  it("says nothing where there is nothing to say: no unknown chips on a clean claim", async () => {
    setupUpdatePosture(mixedAxesDraft());
    render(<WindowHarness scope="project:p1" />);
    await openEditor();

    const rows = screen.getAllByTestId("update-inline-claim");
    expect(
      rows[0].querySelectorAll('[data-testid="update-claim-unknown"]').length,
    ).toBe(0);
  });

  it("a claim carrying the axes states its support once (no legacy UNVERIFIED chip)", async () => {
    setupUpdatePosture(mixedAxesDraft());
    render(<WindowHarness scope="project:p1" />);
    await openEditor();

    expect(screen.queryByTestId("update-claim-unverified")).toBeNull();
    const unsupported = chipLabels("update-claim-support").filter(
      (label) => label === "UNSUPPORTED",
    );
    expect(unsupported.length).toBe(1);
  });
});
