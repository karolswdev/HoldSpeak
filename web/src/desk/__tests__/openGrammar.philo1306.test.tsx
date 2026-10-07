/* PHILO-13-06 (B1) — one open grammar: every named row opens its object in
 * its own window (the owner's fork 2, "Opens its own window", 2026-10-01).
 *
 * Red on b3805b73: the Chair's brief, calendar and commitment rows opened
 * nothing (`expands={false}`, no open); Intelligence BRIEF only selected and
 * printed a raw id; "Open person" asked for the key `people`, which
 * dispatches nowhere; Acknowledge/Defer/Speak stood beside a failed read.
 */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../lib/api";
import { openPrimitive, openProjectRoom, openSurfaceOr } from "../shell";
import { ChairHome } from "../chair/ChairHome";
import { BriefView } from "../pullouts/views/BriefView";
import { __resetOwnerCache, takeRoomProposalRequest } from "../openObject";
import { useDrawers } from "../drawer/store";
import { asHub } from "../../test/hubNeedsYou";
import { openChairWindows } from "../chair/__tests__/fixtures/openChairWindows";

// PHILO-14 A1: the Chair is the screen; these specs read its windows, so they open them first.
beforeEach(() => openChairWindows());

vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../shell", async (original) => ({
  ...(await original<typeof import("../shell")>()),
  openPrimitive: vi.fn(),
  openSurfaceOr: vi.fn(),
  openProjectRoom: vi.fn(),
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

/* The shapes the real producers write (monday_brief_service.py source_refs;
 * door_service.py upcoming + people_commitment cards; needs_you_aggregate.py
 * commitment rows). */
const BRIEF = {
  id: "brief-1",
  headline: "1 thing changed, 2 decisions waiting.",
  generated_at: "2026-10-01T08:00:00",
  is_empty: false,
  shelf: {},
  sections: {
    decisions: [
      { id: "bi-dec", section: "decisions", text: "Review decision: Freeze the old ledger on Nov 5", source_ref: "decision:decision_9458", priority: 200, created_at: "2026-10-01T07:00:00" },
      { id: "bi-cov", section: "decisions", text: "Review decision: Coverage line", source_ref: "coverage:aggregate", priority: 100, created_at: "2026-10-01T06:00:00" },
    ],
    changed: [
      { id: "bi-mtg", section: "changed", text: "Meeting recorded: Ledger cutover sync", source_ref: "meeting:p13-cutover-sync", priority: 150, created_at: "2026-10-01T06:30:00" },
    ],
  },
  person_sections: [
    { relationship_id: "rel-priya", display_name: "Priya Nair", they_owe_count: 1, stalest_age_days: 2, you_owe_count: 1, agenda_backlog: 2, next_one_on_one: null },
  ],
};

const today = new Date();
const at = (h: number) => new Date(today.getFullYear(), today.getMonth(), today.getDate(), h, 0).toISOString();

const DOOR = {
  board: {
    now: [
      { id: "people:com-1", source: "people_commitment", target_ref: "people:rel-priya", title: "Review the rollout plan before Friday",
        lawful_verbs: [{ name: "people.commitment.transition", arguments: { card_id: "people:com-1", verb: "done" } }] },
    ],
  },
  counts: {},
  calendar_configured: true,
  upcoming: [
    { id: "ev-1on1", source: "calendar_event", title: "1:1 Priya / Karol", starts_at: at(23), person_relationship_id: "rel-priya", person_label: "Priya Nair" },
    { id: "ev-sync", source: "calendar_event", title: "Ledger cutover sync", starts_at: at(23), project_id: "proj-ledger", project_name: "Payments ledger cutover" },
    { id: "ev-arch", source: "calendar_event", title: "Architecture review", starts_at: at(23) },
  ],
};

const NEEDS_YOU = {
  count: 1,
  items: [
    { id: "c1", projectId: "proj-ledger", projectName: "Payments ledger cutover", ref: "Send the dry-run report", title: "Send the dry-run report",
      why: "NO DUE DATE", ageToken: "", source: "commitment", verbHref: null, severity: "info",
      commitmentId: "com-a", actionItemId: "ai-1", owner: "Priya", unknowns: ["due"], nextAction: "set_date" },
  ],
  projects: ["proj-ledger"],
  next: null,
  coverage: [],
  complete: true,
};

/** GET /api/decisions/{id}: a Desk decision, or one a meeting recorded. */
function decisionRead(url: string): unknown {
  if (url === "/api/decisions/decision_9458") return { decision: { id: "decision_9458", title: "Freeze the old ledger on Nov 5" } };
  if (url === "/api/decisions/mdec-cursor") return { decision: { id: "mdec-cursor", source_meeting_id: "p13-api-review" }, lineage: {} };
  return null;
}

let chairBrief: unknown = BRIEF;
let chairNeeds: unknown = NEEDS_YOU;

function wireChair() {
  vi.mocked(apiFetch).mockImplementation(asHub(async (path: string, init?: unknown) => {
    const url = String(path);
    const body = (init as { json?: { identity?: string } } | undefined)?.json;
    if (url === "/api/inference/assignments") return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 } as never;
    if (url.startsWith("/api/desk/needs-you")) return chairNeeds as never;
    if (url === "/api/door") return DOOR as never;
    if (url.startsWith("/api/brief/latest")) return chairBrief as never;
    if (url === "/api/people/resolve") return { relationship_id: body?.identity === "Priya" ? "rel-priya" : null } as never;
    return decisionRead(url) as never;
  }));
}

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  vi.mocked(openPrimitive).mockReset();
  vi.mocked(openSurfaceOr).mockReset();
  vi.mocked(openProjectRoom).mockReset();
  __resetOwnerCache();
  chairBrief = BRIEF;
  chairNeeds = NEEDS_YOU;
});

describe("PHILO-13-06: the Chair rows open their objects", () => {
  beforeEach(wireChair);

  it("a brief row opens its decision; a row with nothing to open draws no open", async () => {
    render(<ChairHome />);
    const rows = await screen.findAllByTestId("arrival-brief-row");
    const decision = rows.find((r) => r.textContent?.includes("Freeze the old ledger"))!;
    expect(decision.getAttribute("role")).toBe("button");
    fireEvent.click(decision);
    await waitFor(() => expect(openPrimitive).toHaveBeenCalledWith("decision:decision_9458"));

    const meeting = rows.find((r) => r.textContent?.includes("Ledger cutover sync"))!;
    fireEvent.click(meeting);
    expect(openSurfaceOr).toHaveBeenCalledWith("review-meetings", "/history", "meeting:p13-cutover-sync");

    const coverage = rows.find((r) => r.textContent?.includes("Coverage line"))!;
    expect(coverage.getAttribute("role")).toBeNull();
    expect(coverage.getAttribute("tabindex")).toBeNull();
    expect(coverage.hasAttribute("data-inert")).toBe(true);
    vi.mocked(openPrimitive).mockReset();
    vi.mocked(openSurfaceOr).mockReset();
    fireEvent.click(coverage);
    expect(openPrimitive).not.toHaveBeenCalled();
    expect(openSurfaceOr).not.toHaveBeenCalled();
  });

  it("a decision a meeting recorded opens its meeting (no Desk window exists for it)", async () => {
    const meetingBorn = { id: "bi-mdec", section: "decisions", text: "Review decision: Cursor pagination for every list endpoint", source_ref: "decision:mdec-cursor", priority: 300, created_at: "2026-10-01T07:30:00" };
    chairBrief = { ...BRIEF, sections: { ...BRIEF.sections, decisions: [meetingBorn, ...BRIEF.sections.decisions] } };
    render(<ChairHome />);
    const rows = await screen.findAllByTestId("arrival-brief-row");
    fireEvent.click(rows.find((r) => r.textContent?.includes("Cursor pagination"))!);
    await waitFor(() => expect(openSurfaceOr).toHaveBeenCalledWith("review-meetings", "/history", "meeting:p13-api-review"));
    expect(openPrimitive).not.toHaveBeenCalled();
  });

  it("Ack on a brief row triages only; it does not open the row", async () => {
    render(<ChairHome />);
    const rows = await screen.findAllByTestId("arrival-brief-row");
    const decision = rows.find((r) => r.textContent?.includes("Freeze the old ledger"))!;
    fireEvent.click(within(decision).getByRole("button", { name: "Ack" }));
    expect(openPrimitive).not.toHaveBeenCalled();
  });

  it("a calendar row opens its person at Prep, else its Project's drawer, else nothing", async () => {
    useDrawers.setState({ drawers: [], infos: [] });
    render(<ChairHome />);
    const rows = await screen.findAllByTestId("arrival-meeting-row");
    const oneOnOne = rows.find((r) => r.textContent?.includes("1:1 Priya"))!;
    fireEvent.click(oneOnOne);
    expect(openSurfaceOr).toHaveBeenCalledWith("open-people", "/", "people:rel-priya:prep");

    const sync = rows.find((r) => r.textContent?.includes("Ledger cutover sync"))!;
    fireEvent.click(sync);
    // PHILO-14 A2: a Project opens as its drawer.
    expect(useDrawers.getState().drawers.map((d) => d.projectId)).toEqual(["proj-ledger"]);

    // Unlink beside the ROOM token is its own verb, never the row's open.
    useDrawers.setState({ drawers: [] });
    fireEvent.click(within(sync).getByTestId("arrival-unlink-room"));
    expect(useDrawers.getState().drawers).toEqual([]);

    const arch = rows.find((r) => r.textContent?.includes("Architecture review"))!;
    expect(arch.hasAttribute("data-inert")).toBe(true);
    expect(arch.getAttribute("role")).toBeNull();
  });

  it("a commitment row is its object in the Needs-you drawer: no row open; Open opens its person", async () => {
    // PHILO-14 A5 (board A-5): a Needs-you row is the object with its own
    // verbs; the row itself is not a button (the Chair row's open moved to
    // the object's own window). Rows the Brief and the week draw still open.
    render(<ChairHome />);
    const name = await screen.findByText("Review the rollout plan before Friday");
    const row = name.closest(".needs-row") as HTMLElement;
    expect(row).toBeTruthy();
    expect(row.getAttribute("role")).toBeNull();
    // The card names its person and the Desk cannot run its verb: Open opens the person.
    fireEvent.click(within(row).getByRole("button", { name: "Open: Review the rollout plan before Friday" }));
    expect(openSurfaceOr).toHaveBeenCalledWith("open-people", "/", "people:rel-priya");
  });
});

describe("PHILO-14 A2b: every generic open of a Project opens its drawer", () => {
  beforeEach(wireChair);

  // Two Projects, so the row names its Project (ProjectButton); a watch row
  // names only its Project, so the row itself opens the Project.
  const twoProjects = {
    ...NEEDS_YOU,
    count: 2,
    items: [
      ...NEEDS_YOU.items,
      { id: "w1", projectId: "proj-infra", projectName: "Infra budget", ref: "Budget watch is stale", title: "Budget watch is stale",
        why: "STALE", ageToken: "", source: "watch", verbHref: null, severity: "info" },
    ],
    projects: ["proj-ledger", "proj-infra"],
  };

  it("the Needs you row's Project button opens the drawer, never the Room", async () => {
    chairNeeds = twoProjects;
    useDrawers.setState({ drawers: [], infos: [] });
    render(<ChairHome />);
    const button = await screen.findByRole("button", { name: "Open the Project: Payments ledger cutover" });
    fireEvent.click(button);
    expect(useDrawers.getState().drawers.map((d) => d.projectId)).toEqual(["proj-ledger"]);
    expect(openProjectRoom).not.toHaveBeenCalled();
  });

  it("a proposal row opens the Room with that proposal selected; its verb says Room", async () => {
    chairNeeds = {
      ...twoProjects,
      items: [...twoProjects.items, { id: "pr1", projectId: "proj-ledger", projectName: "Payments ledger cutover",
        ref: "Run the dry run", title: "Run the dry run", why: "PROPOSED", ageToken: "", source: "proposal",
        verbHref: "/api/proposals/prop-7/confirm", severity: "info", proposalId: "prop-7", proposalKind: "action" }],
    };
    useDrawers.setState({ drawers: [], infos: [] });
    render(<ChairHome />);
    const row = (await screen.findByText("Run the dry run")).closest(".surface-ledger-line") as HTMLElement;
    await waitFor(() => expect(row.getAttribute("role")).toBe("button"));
    fireEvent.click(row);
    expect(openProjectRoom).toHaveBeenCalledWith("proj-ledger");
    expect(takeRoomProposalRequest("proj-ledger")).toBe("prop-7");
    expect(useDrawers.getState().drawers).toEqual([]);
    // The shortcut inside MORE is the explicit Room path, with the proposal.
    vi.mocked(openProjectRoom).mockClear();
    fireEvent.click(within(row.closest("li") as HTMLElement).getByRole("button", { name: "More: Run the dry run" }));
    fireEvent.click(screen.getByRole("button", { name: "Room: Run the dry run" }));
    expect(openProjectRoom).toHaveBeenCalledWith("proj-ledger");
    expect(takeRoomProposalRequest("proj-ledger")).toBe("prop-7");
  });

  it("a row that names only its Project opens the drawer, never the Room", async () => {
    chairNeeds = twoProjects;
    useDrawers.setState({ drawers: [], infos: [] });
    render(<ChairHome />);
    const row = (await screen.findByText("Budget watch is stale")).closest(".surface-ledger-line") as HTMLElement;
    await waitFor(() => expect(row.getAttribute("role")).toBe("button"));
    fireEvent.click(row);
    expect(useDrawers.getState().drawers.map((d) => d.projectId)).toEqual(["proj-infra"]);
    expect(openProjectRoom).not.toHaveBeenCalled();
  });
});

describe("PHILO-13-06: Intelligence BRIEF opens its rows; Brief → People works", () => {
  it("a row opens its decision and names the selection in words, not a raw id", async () => {
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) =>
      (String(path).startsWith("/api/brief/latest") ? BRIEF : decisionRead(String(path))) as never));
    render(<BriefView header={null} />);
    const row = await screen.findByText("Freeze the old ledger on Nov 5");
    fireEvent.click(row);
    await waitFor(() => expect(openPrimitive).toHaveBeenCalledWith("decision:decision_9458"));
    expect(document.body.textContent).toContain("SELECTED · REVIEW DECISION");
    expect(document.body.textContent).not.toContain("decision_9458");
    expect(screen.getByRole("button", { name: "Acknowledge" })).toBeTruthy();
  });

  it("Open person opens People on that relationship", async () => {
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) =>
      (String(path).startsWith("/api/brief/latest") ? BRIEF : null) as never));
    render(<BriefView header={null} />);
    fireEvent.click(await screen.findByTestId("person-row-rel-priya"));
    fireEvent.click(screen.getByTestId("verb-open-person"));
    expect(openSurfaceOr).toHaveBeenCalledWith("open-people", "/", "people:rel-priya");
    expect(openSurfaceOr).not.toHaveBeenCalledWith("people", "/people", expect.anything());
  });

  it("a failed read withholds Acknowledge, Defer and Speak (A.11)", async () => {
    vi.mocked(apiFetch).mockImplementation(asHub(async () => {
      throw new ApiError(500, "injected", null);
    }));
    render(<BriefView header={null} />);
    await screen.findByText(/BRIEF DID NOT LOAD/);
    expect(screen.queryByRole("button", { name: "Acknowledge" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Defer" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Speak" })).toBeNull();
    expect(document.body.textContent).not.toContain("injected");
    await act(async () => undefined);
  });
});
