// Needs you (the Chair's arrival app): the faces' half of the Needs-you browser
// tests (the test diet, 2026-10-11). The hub's half is
// tests/unit/test_desk_needs_you.py. Each test renders the real component with
// its real store; only `apiFetch` is mocked, with the hub's own answer shape
// (the producer's cards, the oracle week minted by the real producers).
// Every test names the browser test it replaces (`replaces:`).
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { asHub } from "../../test/hubNeedsYou";
import { ChairHome } from "../chair/ChairHome";
import { openChairWindows } from "../chair/__tests__/fixtures/openChairWindows";
import { openIntelligence } from "../intelligenceNavigation";
import { IntelligencePullout } from "../pullouts/IntelligencePullout";
import { openPrimitive } from "../shell";
import { useDesk } from "../store";

vi.mock("../../lib/api", async (original) => ({
  ...await original<typeof import("../../lib/api")>(),
  apiFetch: vi.fn(),
}));
vi.mock("../shell", async (original) => ({
  ...(await original<typeof import("../shell")>()),
  openPrimitive: vi.fn(),
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

const ROSTER = { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 };

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  vi.mocked(openPrimitive).mockReset();
  (globalThis as { __resetNeedsYou?: () => void }).__resetNeedsYou?.();
  openChairWindows();
});

const needsRows = () => [...document.querySelectorAll<HTMLElement>('[data-testid="needs-drawer"] [data-testid="needs-row"]')];
const rowNamed = (text: string) => needsRows().find((r) => r.querySelector(".needs-row-name")?.textContent === text);
const lampOf = (r: HTMLElement) => r.querySelector(".gadget-lamp")?.textContent ?? "";
const head = () => screen.getByTestId("arrival-display").textContent ?? "";

/** The REAL producer's Door/Follow-through card (`DoorService._follow_through_card`,
 *  the same card shape arrivalAttention.test.tsx draws). */
const producerCard = (id: string, text: string, owner: string | null) => ({
  id, text, owner, due: null, status: "pending", meeting_id: "m-owner-verb", decision_id: null,
  stale_score: null, source: "action_item", lane: "unassigned", provenance: null,
  delegated_at: null, created_at: "2026-10-03T09:00:00",
  target_ref: `action_item:${id}`,
  lawful_verbs: [
    { name: "done", arguments: { card_id: id, verb: "done" }, required_arguments: [] },
    { name: "delegate", arguments: { card_id: id, verb: "delegate" }, required_arguments: ["to"] },
  ],
});

describe("Needs you: Name an owner and Review on a meeting's action items", () => {
  const OWNED = "Draft the migration runbook";
  const UNOWNED = "Book the dry run";

  it("the owner well saves; the row stays, reads TO REVIEW and drops Name an owner", async () => {
    // replaces: tests/e2e/test_chair_owner_verb_glass.py::test_owner_verb_only_where_no_owner_exists
    let avery: string | null = null;
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string, init?: unknown) => {
      const value = String(path);
      if (value === "/api/inference/assignments") return ROSTER;
      if (value.startsWith("/api/desk/needs-you")) return { count: 0, projects: [], items: [], next: null, coverage: [], complete: true };
      if (value === "/api/follow-through/complete") {
        const body = (init as { json?: { card_id?: string; verb?: string; payload?: { to?: string } } }).json;
        if (body?.card_id === "ai-unowned" && body.verb === "delegate") avery = body.payload?.to ?? null;
        return { card_id: body?.card_id, verb: body?.verb };
      }
      if (value.startsWith("/api/door")) {
        // Not reviewed yet: the item stays in `unassigned`, now with its owner
        // (tests/unit/test_desk_needs_you.py proves the hub does this).
        return { board: { unassigned: [producerCard("ai-owned", OWNED, "Priya"), producerCard("ai-unowned", UNOWNED, avery)] },
          counts: {}, upcoming: [], calendar_configured: false };
      }
      return null;
    }));
    render(<ChairHome />);
    await waitFor(() => expect(rowNamed(UNOWNED)).toBeTruthy());
    const owned = rowNamed(OWNED)!;
    expect(lampOf(owned)).toBe("TO REVIEW");
    expect(owned.querySelector('[data-verb="name-owner"]')).toBeNull();
    expect(lampOf(rowNamed(UNOWNED)!)).toBe("UNASSIGNED");

    fireEvent.click(rowNamed(UNOWNED)!.querySelector('[data-verb="name-owner"]') as HTMLElement);
    const well = await screen.findByTestId("needs-well");
    fireEvent.change(within(well).getByRole("textbox", { name: "Owner" }), { target: { value: "Avery" } });
    fireEvent.click(within(well).getByRole("button", { name: /Save owner/ }));
    await waitFor(() => expect(screen.queryByTestId("needs-well")).toBeNull());

    // The hub's board is the truth the row settles on.
    await waitFor(() => expect(lampOf(rowNamed(UNOWNED)!)).toBe("TO REVIEW"));
    expect(needsRows().filter((r) => r.querySelector(".needs-row-name")?.textContent === UNOWNED)).toHaveLength(1);
    expect(document.querySelector('[data-testid="needs-drawer"] [data-verb="name-owner"]')).toBeNull();
    expect(rowNamed(UNOWNED)!.textContent).not.toContain("UNASSIGNED");
  });

  it("Review's destination: Follow-through opens ON that card, its verbs showing", async () => {
    // replaces: tests/e2e/test_chair_review_verb_glass.py::test_review_opens_the_card_in_follow_through
    // (the press dispatching { view: "follow-through", followThroughId } is
    // arrivalAttention.test.tsx "an owned item not reviewed yet reads TO REVIEW, and Review opens it".)
    const board = {
      now: [], waiting: [], overdue: [],
      unassigned: [producerCard("ai-owned", OWNED, "Priya"), producerCard("ai-other", "Book the room", null)],
    };
    vi.mocked(apiFetch).mockImplementation(async (path: string) =>
      (String(path) === "/api/follow-through/board" ? board : null) as never);
    const openPullout = vi.fn();
    const realOpen = useDesk.getState().openPullout;
    useDesk.setState({ openPullout } as never);
    try {
      render(<IntelligencePullout object={{ kind: "intelligence", id: "desk", title: "Intelligence",
        ref: { kind: "intelligence", id: "desk", name: "Intelligence" } } as never} onClose={() => {}} />);
      expect(screen.queryByLabelText(`Verbs for ${OWNED}`)).toBeNull();
      act(() => openIntelligence({ view: "follow-through", followThroughId: "ai-owned" }));
      expect(openPullout).toHaveBeenCalledWith("intelligence:desk");
      const verbs = await screen.findByLabelText(`Verbs for ${OWNED}`);
      expect(within(verbs).getByRole("button", { name: "Mark done" })).toBeTruthy();
      expect(within(verbs).getByRole("button", { name: "Delegate" })).toBeTruthy();
      // Only that card is open.
      expect(screen.queryByLabelText("Verbs for Book the room")).toBeNull();
    } finally {
      useDesk.setState({ openPullout: realOpen } as never);
    }
  });
});

// ── The oracle week, minted by the real producers ─────────────────────────
// scripts/philo13_needs_you_fixture.py (as chair/__tests__/oneNeedsYou.philo1303.test.tsx):
// six members; A3 names another owner (Priya) and waits; one Desk decision
// waits for review.
const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../../..");
type Wire = Record<string, any>;
let home = "";
let week: Wire;

describe("Needs you: the head counts what needs him; Waiting lists the rest", () => {
  beforeAll(() => {
    home = mkdtempSync(join(tmpdir(), "needs-you-app-"));
    const db = join(home, ".local", "share", "holdspeak", "holdspeak.db");
    const run = (mode: string) => JSON.parse(execFileSync(resolve(REPO_ROOT, ".venv/bin/python"),
      [resolve(REPO_ROOT, "scripts/philo13_needs_you_fixture.py"), mode, "--db", db, "--home", home],
      { cwd: REPO_ROOT, env: { ...process.env, HOME: home }, encoding: "utf8", maxBuffer: 32 * 1024 * 1024 }));
    run("seed");
    week = run("export");
  }, 60_000);
  afterAll(() => { if (home) rmSync(home, { recursive: true, force: true }); });

  function installWeek() {
    const wire = week.before as Wire;
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const value = String(path);
      if (value === "/api/door") return wire.door as never;
      if (value.startsWith("/api/desk/needs-you")) return wire.needsYou as never;
      if (value === "/api/inference/assignments") return wire.assignments as never;
      if (value === "/api/settings/heartbeat") return wire.heartbeat as never;
      if (value.startsWith("/api/meetings?summary_attention=true")) {
        const rows = (wire.meetingsWire.meetings as Wire[]).filter((row) => row.id === "philo13-a2-failed-meeting");
        return { meetings: rows, total: rows.length } as never;
      }
      // GET /api/decisions/{id}: a Desk decision (PrimitiveService.decision.read;
      // a Desk decision has no source meeting).
      if (value === "/api/decisions/philo13-a2-decision")
        return { decision: { id: "philo13-a2-decision", title: "R1 adopt the release checklist", status: "proposed" } } as never;
      return null as never;
    });
  }

  it("6 with A3 not among the rows; Waiting lists A3 waiting on Priya; Review opens the decision", async () => {
    // replaces: tests/e2e/test_needs_you_means_you_glass.py::TestNeedsYouMeansYou::test_the_head_counts_what_needs_him_and_waiting_lists_the_rest
    // (the A4-named -> 5 and decision-accepted -> 4 legs are the hub's: tests/unit/test_desk_needs_you.py)
    installWeek();
    useDesk.setState({ items: { ...useDesk.getState().items, meeting: [] } } as never);
    render(<ChairHome />);
    await waitFor(() => expect(head()).toMatch(/^6 need you/), { timeout: 3000 });
    const ranked = needsRows().map((r) => r.textContent ?? "");
    expect(ranked).toHaveLength(6);
    expect(ranked.some((t) => t.includes("A3 wait for Priya's review") || t.includes("WAITING ON"))).toBe(false);

    fireEvent.click(within(screen.getByTestId("needs-filter")).getByRole("button", { name: "Waiting" }));
    const waiting = await screen.findByTestId("needs-waiting");
    const waitingRows = [...waiting.querySelectorAll<HTMLElement>('[data-testid="needs-row"]')].map((r) => r.textContent ?? "");
    expect(waitingRows.some((t) => t.includes("A3 wait for Priya's review") && t.includes("WAITING ON PRIYA"))).toBe(true);
    expect(waitingRows.some((t) => t.includes("A4 assign the owner"))).toBe(false);
    expect(head()).toMatch(/^6 need you/);

    fireEvent.click(within(screen.getByTestId("needs-filter")).getByRole("button", { name: "Ranked" }));
    const decision = rowNamed("R1 adopt the release checklist")!;
    fireEvent.click(within(decision).getByRole("button", { name: "Review: R1 adopt the release checklist" }));
    await waitFor(() => expect(openPrimitive).toHaveBeenCalledWith("decision:philo13-a2-decision"));
  });
});

// ── Arrival: proposal rows (HS-172) ───────────────────────────────────────
// The row fields are the hub's (`needs_you_aggregate._proposal_fields`), the
// values the browser test's seed gives (tests/unit/test_desk_needs_you.py
// reads the same seed through the real route).
describe("Needs you: proposal rows on arrival", () => {
  // The row as the hub answers it, captured from GET /api/desk/needs-you on
  // the browser test's seed (tests/unit/test_desk_needs_you.py::_seed_hs172).
  const proposal = (id: string, kind: "action" | "decision", title: string, due: string | null) => ({
    projectId: "proj-a", projectName: "Q4 Platform", ref: title, title,
    why: "PROPOSED · Standup", ageToken: "2026-10-11T09:36:11.666763", since: "2026-10-11T09:36:11.666763",
    dueAt: null, kind: "proposal", source: "proposal", verbHref: `/api/proposals/${id}/confirm`, severity: "info",
    proposalId: id, proposalKind: kind, proposalHost: "192.168.1.43", proposalDue: due,
    meetingTitle: "Standup", meetingId: "m-standup", id: `proposal:${id}`,
    dedupCount: 1, rankClass: "no_due_date", waiting: false, muted: false,
  });

  it("each proposal names its meeting and act, has one Confirm, and Confirm takes exactly that row away", async () => {
    // replaces: tests/e2e/test_hs172_arrival_glass.py::TestArrivalProposals::test_arrival_proposals
    // replaces: tests/e2e/test_hs172_arrival_glass.py::TestArrivalProposals::test_arrival_confirm_fires (the face half)
    let items = [
      proposal("prop-a", "action", "Marek owns the PostgreSQL migration", "Fri"),
      proposal("prop-d", "decision", "cut-over on the 12th", null),
    ];
    const posted: string[] = [];
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
      const value = String(path);
      if (value === "/api/inference/assignments") return ROSTER;
      if (value.startsWith("/api/desk/needs-you"))
        return { count: items.length, projects: ["proj-a"], items, next: null, coverage: [], complete: true };
      if (value.startsWith("/api/proposals/")) {
        posted.push(value);
        items = items.filter((row) => !value.includes(`/${row.proposalId}/`));
        return { ok: true };
      }
      if (value.startsWith("/api/door")) return { board: {}, counts: {}, upcoming: [], calendar_configured: false };
      return null;
    }));
    render(<ChairHome />);
    await waitFor(() => expect(head()).toMatch(/^2 need you/));
    const rows = needsRows().filter((r) => r.getAttribute("data-object-id")?.startsWith("proposal:"));
    expect(rows).toHaveLength(2);
    for (const r of rows) {
      expect(r.querySelector(".needs-row-fact")?.textContent).toMatch(/^from Standup/);
      expect(r.querySelectorAll('[data-verb="confirm"]')).toHaveLength(1);
      expect(r.getAttribute("data-opens")).toBe("true");
    }
    expect(rows.map(lampOf).sort()).toEqual(["TO CONFIRM", "TO DECIDE"]);
    const face = document.querySelector('[data-testid="needs-drawer"]')?.textContent ?? "";
    expect(face).not.toContain("LOCAL");
    expect(face).not.toContain("0 NEEDS");

    fireEvent.click(screen.getByRole("button", { name: "Confirm: Marek owns the PostgreSQL migration" }));
    await waitFor(() => expect(head()).toMatch(/^1 needs you/));
    expect(posted).toEqual(["/api/proposals/prop-a/confirm"]);
    expect(rowNamed("Marek owns the PostgreSQL migration")).toBeUndefined();
    expect(rowNamed("cut-over on the 12th")).toBeTruthy();
  });
});
