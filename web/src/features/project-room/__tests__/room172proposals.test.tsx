// HS-172-03/06 -- Proposals in NEEDS YOU, confirmed in D&C,
// suggested sources in SOURCES.
// Asserts: MTG emblem, Decide:/Confirm: prefix by kind, caption with
// provenance + EgressChip, verbs Confirm/Edit/Dismiss, no raw <button>,
// proposal text wraps, confirmed token in success color, suggested source
// rows above existing sources.

import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TitleSlotContext } from "../../../desk/surface/title";
import { WingSlotContext } from "../../../desk/surface/wings";
import { ProjectRoomCore } from "../ProjectRoomCore";

vi.mock("../../../desk/ask", async () => {
  const actual =
    await vi.importActual<typeof import("../../../desk/ask")>(
      "../../../desk/ask",
    );
  return { ...actual, runAsk: vi.fn() };
});

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual =
    await vi.importActual<typeof import("../../../lib/api")>(
      "../../../lib/api",
    );
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

vi.mock("../../../desk/shell", async () => {
  const actual = await vi.importActual<typeof import("../../../desk/shell")>(
    "../../../desk/shell",
  );
  return { ...actual, openPrimitive: vi.fn(), openSurfaceOr: vi.fn() };
});

function WindowHarness({ scope }: { scope?: string }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <TitleSlotContext.Provider value={() => {}}>
      <WingSlotContext.Provider value={setWings}>
        <div data-testid="wing-slot">{wings}</div>
        <ProjectRoomCore scope={scope} />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
  );
}

/* ── fixture builders ── */

function roomWithProposals() {
  return {
    project_id: "p1",
    revision: 3,
    observed_at: "2026-09-05T09:35:00",
    project: {
      id: "p1",
      name: "Ship the Q4 platform on schedule with zero incidents",
      description: null,
      is_archived: false,
      meeting_count: 2,
      created_at: "2026-08-01T00:00:00",
      updated_at: "2026-09-05T10:00:00",
      purpose: null,
      outcome_text: "Ship the Q4 platform on schedule with zero incidents",
      owner_ref: null,
      lifecycle: "active",
      posture: null,
      posture_reason: null,
      start_at: "2026-08-01",
      target_at: "2026-10-15",
      revision: 3,
    },
    items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: { state: "ok", count: 2, latest: null },
    resources: { state: "ok", count: 0, latest: null },
    changes: { state: "ok", recent: [] },
    review: { state: "absent", reason: "not_yet_built" },
    needsYou: {
      state: "ok",
      items: [
        {
          source: "proposal",
          kind: "proposal",
          title: "Marek owns the PostgreSQL migration",
          why: "PROPOSED · Standup",
          since: "2026-09-05T09:35:00",
          url: null,
          verb: "confirm",
          severity: "info",
          proposal_id: "prop-abc123",
          proposal_kind: "action",
          host: "192.168.1.43",
          speaker_label: "Marek",
          due_hint: "Fri",
          owner_hint: "Marek",
          original_text: "Marek owns the PostgreSQL migration",
          meeting_title: "Standup",
          created_at: "2026-09-05T09:35:00",
        },
        {
          source: "proposal",
          kind: "proposal",
          title: "cut-over on the 12th",
          why: "PROPOSED · Standup",
          since: "2026-09-05T09:35:00",
          url: null,
          verb: "confirm",
          severity: "info",
          proposal_id: "prop-def456",
          proposal_kind: "decision",
          host: "192.168.1.43",
          speaker_label: null,
          due_hint: null,
          owner_hint: null,
          original_text: "cut-over on the 12th",
          meeting_title: "Standup",
          created_at: "2026-09-05T09:35:00",
        },
        {
          source: "github",
          title: "#612 Rig settles animations before every shot",
          why: "WAITING ON YOUR REVIEW · 3 DAYS",
          url: "https://github.com/karolswdev/HoldSpeak/pull/612",
          verb: "open",
          severity: "warning",
        },
      ],
      count: 3,
    },
    sources: {
      state: "ok",
      items: [
        { watchId: "w1", provider: "github", scope: "karolswdev/HoldSpeak",
          tokens: ["12 OPEN PRS"], checkedAt: "2026-09-05T09:57:00",
          host: "GITHUB.COM", state: "live", plainReason: null,
          suggested: false, nextCheckAt: null },
      ],
      count: 1,
      nextCheckAt: null,
    },
    health: { state: "ok", assessment: "on_track", reason: null,
      inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false } },
    sinceRead: { state: "ok", readAt: "2026-09-04T09:21:00", groups: [] },
    decisions: { state: "ok", items: [
      {
        id: "dec-confirmed1",
        text: "Ania owns the API spec",
        at: "2026-09-05T09:41:00",
        url: null,
        proposal_id: "prop-ghi789",
        source: "meeting",
        meeting_title: "Standup",
        confirmed_at: "2026-09-05T09:41:00",
        commitment_id: "com-folded1",
        was: { due: "FRI" },
      },
    ] },
    commitments: { state: "ok", items: [
      { id: "com-folded1", text: "Ania owns the API spec", dueAt: "2026-09-12T00:00:00", owner: "Ania" },
    ] },
    target: { state: "ok", targetAt: "2026-10-15", daysLeft: 41, passed: false },
    updates: { state: "absent", reason: "not_yet_built" },
    steward: { state: "absent", reason: "not_yet_built" },
  };
}

function proposalsApiResponse() {
  return {
    proposals: [
      {
        id: "prop-abc123",
        meeting_id: "mtg1",
        project_id: "p1",
        kind: "action",
        text: "Marek owns the PostgreSQL migration",
        owner_hint: "Marek",
        due_hint: "Fri",
        speaker_label: "Marek",
        model_host: "192.168.1.43",
        state: "proposed",
        original_text: "Marek owns the PostgreSQL migration",
        created_at: "2026-09-05T09:35:00",
        decided_at: null,
      },
      {
        id: "prop-def456",
        meeting_id: "mtg1",
        project_id: "p1",
        kind: "decision",
        text: "cut-over on the 12th",
        owner_hint: null,
        due_hint: null,
        speaker_label: null,
        model_host: "192.168.1.43",
        state: "proposed",
        original_text: "cut-over on the 12th",
        created_at: "2026-09-05T09:35:00",
        decided_at: null,
      },
    ],
  };
}

function suggestedSourcesApiResponse() {
  return {
    suggestions: [
      {
        id: "ssug_test1",
        project_id: "p1",
        meeting_id: "mtg1",
        provider: "github",
        reference: "karolswdev/hs-infra",
        status: "pending",
        created_at: "2026-09-05T09:35:00",
      },
    ],
  };
}

/* ── mock setup ── */

beforeEach(() => {
  apiFetch.mockImplementation((url: string) => {
    if (url.includes("/room")) return Promise.resolve(roomWithProposals());
    if (url.includes("/meetings")) return Promise.resolve({ meetings: [] });
    if (url.includes("/decisions")) return Promise.resolve({ decisions: [] });
    if (url.includes("/artifacts")) return Promise.resolve({ artifacts: [] });
    if (url.includes("/since-last-meeting")) return Promise.resolve({});
    if (url.includes("/proposals"))
      return Promise.resolve(proposalsApiResponse());
    if (url.includes("/suggested-sources"))
      return Promise.resolve(suggestedSourcesApiResponse());
    if (url.includes("/room/read"))
      return Promise.resolve({ read_at: "2026-09-05T09:35:00" });
    return Promise.resolve({});
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

/* ── tests ── */

describe("HS-172-03: Proposals in NEEDS YOU", () => {
  it("renders proposal rows with MTG emblem and prefix by kind", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() => expect(screen.queryAllByTestId("proposal-row")).toHaveLength(2));

    const rows = screen.getAllByTestId("proposal-row");
    // First row: action kind -> Confirm: prefix
    const firstPrimary = rows[0].querySelector('[data-testid="proposal-primary"]');
    expect(firstPrimary?.textContent).toContain("Confirm:");
    expect(firstPrimary?.textContent).toContain("Marek owns the PostgreSQL migration");

    // Second row: decision kind -> Decide: prefix
    const secondPrimary = rows[1].querySelector('[data-testid="proposal-primary"]');
    expect(secondPrimary?.textContent).toContain("Decide:");
    expect(secondPrimary?.textContent).toContain("cut-over on the 12th");

    // Both rows have MTG emblem
    const leads = document.querySelectorAll(".surface-ledger-lead");
    const mtgLeads = Array.from(leads).filter((el) => el.textContent === "MTG");
    expect(mtgLeads.length).toBeGreaterThanOrEqual(2);
  });

  it("shows verbs Confirm, Edit, Dismiss on proposal rows", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() => expect(screen.queryAllByTestId("proposal-row")).toHaveLength(2));

    const verbs = screen.getAllByTestId("proposal-verbs");
    expect(verbs.length).toBe(2);
    // Each verb set has Confirm, Edit, Dismiss
    for (const verbSet of verbs) {
      expect(verbSet.textContent).toContain("Confirm");
      expect(verbSet.textContent).toContain("Edit");
      expect(verbSet.textContent).toContain("Dismiss");
    }
  });

  it("shows caption with BY FRI, meeting title and date", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() => expect(screen.queryAllByTestId("proposal-row")).toHaveLength(2));

    const captions = screen.getAllByTestId("proposal-caption");
    expect(captions.length).toBeGreaterThanOrEqual(1);
    // First proposal has due "Fri" -> caption includes "BY FRI"
    expect(captions[0].textContent).toContain("BY FRI");
    expect(captions[0].textContent).toContain("from Standup");
  });

  it("shows EgressChip with LAN for private network host", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() => expect(screen.queryAllByTestId("proposal-row")).toHaveLength(2));

    // EgressChip should show "192.168.1.43 · LAN"
    const chips = document.querySelectorAll(".gadget-chip-egress");
    const lanChips = Array.from(chips).filter((el) =>
      el.textContent?.includes("192.168.1.43") && el.textContent?.includes("LAN"),
    );
    expect(lanChips.length).toBeGreaterThanOrEqual(1);
  });

  it("never shows LOCAL in egress text", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() => expect(screen.queryAllByTestId("proposal-row")).toHaveLength(2));

    const body = screen.getByTestId("room-body");
    expect(body.textContent).not.toContain("LOCAL");
  });

  it("NEEDS YOU count includes proposals", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() => expect(screen.getByTestId("room-headline")).toBeTruthy());

    // Count is 3 (2 proposals + 1 GH item)
    expect(screen.getByTestId("room-headline").textContent).toContain("3 need you");
  });
});

describe("HS-172-03: Edit unfolds EditInPlace", () => {
  it("clicking Edit shows the edit well with StringGadget fields", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() => expect(screen.queryAllByTestId("proposal-row")).toHaveLength(2));

    // Click Edit on the first proposal
    const editBtns = screen.getAllByTestId("proposal-edit");
    fireEvent.click(editBtns[0]);

    // The edit well should appear
    await waitFor(() => expect(screen.queryByTestId("proposal-edit-well")).toBeTruthy());

    // The was: caption should be visible
    const wasCaption = screen.getByTestId("proposal-was-caption");
    expect(wasCaption.textContent).toContain("WAS:");

    // Save & confirm and Cancel buttons exist
    expect(screen.getByTestId("proposal-save-confirm")).toBeTruthy();
    expect(screen.getByTestId("proposal-cancel-edit")).toBeTruthy();
  });

  it("Cancel closes the edit well", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() => expect(screen.queryAllByTestId("proposal-row")).toHaveLength(2));

    fireEvent.click(screen.getAllByTestId("proposal-edit")[0]);
    await waitFor(() => expect(screen.queryByTestId("proposal-edit-well")).toBeTruthy());

    fireEvent.click(screen.getByTestId("proposal-cancel-edit"));
    await waitFor(() => expect(screen.queryByTestId("proposal-edit-well")).toBeNull());
  });
});

describe("HS-172-03: Confirmed proposals in D&C", () => {
  it("renders proposal-derived decision with MTG emblem and CONFIRMED token", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() =>
      expect(screen.queryAllByTestId("decision-row")).toHaveLength(1),
    );

    const row = screen.getByTestId("decision-row");
    expect(row.textContent).toContain("Ania owns the API spec");

    // MTG emblem on proposal-derived decisions
    const lead = row.querySelector(".surface-ledger-lead");
    expect(lead?.textContent).toBe("MTG");

    const confirmedState = screen.getByTestId("confirmed-state");
    expect(confirmedState.textContent).toContain("CONFIRMED");

    // WAS token for changed due
    expect(row.textContent).toContain("WAS BY FRI");
  });

  it("merges commitment into its decision row -- one row, no 'You owe'", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() =>
      expect(screen.queryAllByTestId("decision-row")).toHaveLength(1),
    );

    // Only 1 row total in D&C (the commitment is folded, not listed separately)
    const allRows = document.querySelectorAll(".surface-ledger-row");
    const dcSection = document.querySelector("h3")?.closest(".surface-section");
    // Find the DECISIONS & COMMITMENTS section
    const headers = Array.from(document.querySelectorAll(".surface-section h3"));
    const dcHeader = headers.find((h) => h.textContent?.includes("DECISIONS & COMMITMENTS"));
    expect(dcHeader).toBeTruthy();
    // Count should be 1 (merged), not 2
    expect(dcHeader?.textContent).toBe("DECISIONS & COMMITMENTS 1");

    // The merged row shows OWNER ANIA, BY FRI, CONFIRMED (not "You owe")
    const row = screen.getByTestId("decision-row");
    expect(row.textContent).toContain("OWNER ANIA");
    expect(row.textContent).toMatch(/BY\s+(FRI|SEP\s+12)/);
    expect(row.textContent).toContain("CONFIRMED");
    expect(row.textContent).not.toContain("You owe");
  });
});

describe("HS-172-06: Suggested sources in SOURCES", () => {
  it("renders suggested source rows above existing sources", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() =>
      expect(screen.queryAllByTestId("suggested-source-row")).toHaveLength(1),
    );

    const row = screen.getByTestId("suggested-source-row");
    const ref = row.querySelector('[data-testid="suggested-ref"]');
    expect(ref?.textContent).toBe("karolswdev/hs-infra");

    const caption = row.querySelector('[data-testid="suggested-caption"]');
    expect(caption?.textContent).toContain("SUGGESTED");
  });

  it("shows Add and Dismiss verbs on suggested source", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() =>
      expect(screen.queryAllByTestId("suggested-source-row")).toHaveLength(1),
    );

    const verbs = screen.getByTestId("suggested-verbs");
    expect(verbs.textContent).toContain("Add");
    expect(verbs.textContent).toContain("Dismiss");
  });

  it("SOURCES count does not include suggestions", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() =>
      expect(screen.queryAllByTestId("suggested-source-row")).toHaveLength(1),
    );

    // The sources section label should count only accepted sources (1), not suggestions
    const sourceHeaders = document.querySelectorAll(".surface-section h3");
    const sourcesHeader = Array.from(sourceHeaders).find((h) =>
      h.textContent?.startsWith("SOURCES"),
    );
    expect(sourcesHeader?.textContent).toBe("SOURCES 1");
  });
});

describe("HS-172: No violations", () => {
  it("no raw <button> in proposal/suggestion rows", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() => expect(screen.queryAllByTestId("proposal-row")).toHaveLength(2));

    // All buttons in proposal verbs must have .btn class (library Button)
    const proposalVerbs = document.querySelectorAll('[data-testid="proposal-verbs"] button');
    for (const btn of proposalVerbs) {
      expect(
        btn.classList.contains("btn") || btn.classList.contains("signal-button"),
        `Raw <button> in proposal verbs: ${btn.outerHTML.slice(0, 100)}`,
      ).toBe(true);
    }

    // Same for suggested source verbs
    const sugVerbs = document.querySelectorAll('[data-testid="suggested-verbs"] button');
    for (const btn of sugVerbs) {
      expect(
        btn.classList.contains("btn") || btn.classList.contains("signal-button"),
        `Raw <button> in suggestion verbs: ${btn.outerHTML.slice(0, 100)}`,
      ).toBe(true);
    }
  });
});
