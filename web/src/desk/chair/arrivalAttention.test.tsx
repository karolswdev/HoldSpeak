// HS-200-15, re-faced by PHILO-14 A5 (board A-5): the Needs-you window body
// is the smart drawer. Every member is a row that IS its object (icon, name,
// one fact line, ONE lamp + word, its own verbs), in the hub's rank order; a
// source the hub could not read leads as a row of its own; the head is the
// number once; never an all-clear over a partial result. Retired by the
// board: the five-row cap, the ranking strip, the dedup disclosure and the
// coverage chip. The Project button stays on the fact line (A5b, A2b ruling).
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { ChairHome, headlineFor } from "./ChairHome";
import { asHub } from "../../test/hubNeedsYou";
import { useDesk } from "../store";
import { whenWord } from "../needs/needsFace";
import { wireDate } from "../surface/format";
import { openChairWindows } from "./__tests__/fixtures/openChairWindows";

// PHILO-14 A1: the Chair is the screen; these specs read its windows, so they open them first.
beforeEach(() => openChairWindows());

vi.mock("../../lib/api", async (original) => ({
  ...await original<typeof import("../../lib/api")>(),
  apiFetch: vi.fn(),
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

/** Days relative to the real clock: the face reads `new Date()`. */
function daysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}

const AVAILABLE = (pid: string, label: string) => ({
  source_id: `project:${pid}`, kind: "project", state: "available",
  observed_at: new Date().toISOString(), label, project_id: pid, reason: null, repair: null,
});
const FAILED_WATCH = {
  source_id: "watch:w-kan", kind: "watch", state: "failed",
  observed_at: "2026-09-07T08:41:00", label: "jira KAN", project_id: "p1",
  reason: "Jira rejected the query",
  repair: { token: "CANT CHECK", verb: "Reconnect", href: "/settings" },
};

function row(id: string, extra: Record<string, unknown> = {}) {
  return {
    id, projectId: "p1", projectName: "Q4 Platform", ref: id, title: id,
    why: "WAITING ON YOUR REVIEW · 3d", ageToken: "", since: "2026-09-04T09:00:00",
    source: "github", verbHref: `https://x/${id}`, severity: "warning",
    rankClass: "waiting", ...extra,
  };
}

function wire(payload: unknown) {
  vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
    // HS-201-01 (counsel fix round): the Chair re-reads the assignment
    // roster, and an UNREAD roster is now its own row. This face is not
    // about the meeting path, so the roster read lands and names nothing.
    if (String(path) === "/api/inference/assignments")
      return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 };
    if (String(path).startsWith("/api/desk/needs-you")) return payload;
    if (String(path).startsWith("/api/door")) {
      return { board: {}, counts: {}, upcoming: [], calendar_configured: false };
    }
    return null;
  }));
}

const SEVENTEEN = Array.from({ length: 17 }, (_, i) => {
  const n = String(i + 1).padStart(2, "0");
  const pid = ["p1", "p2", "p3"][i % 3];
  return row(`item-${n}`, {
    projectId: pid, projectName: { p1: "Q4 Platform", p2: "Governance", p3: "Payments" }[pid],
    ...(i === 0 ? { why: "OVERDUE · 2 DAYS", dueAt: daysAgo(2), rankClass: "overdue", severity: "danger", source: "jira", title: "KAN-7 Payments cut-over runbook" } : {}),
    ...(i === 1 ? { why: "DUE TODAY", dueAt: new Date().toISOString().slice(0, 10), rankClass: "due_today", title: "Priya confirms the freeze window", source: "commitment",
      sources: [{ id: "p1:commitment:freeze", source: "commitment", title: "Priya confirms the freeze window", why: "DUE TODAY", verbHref: "https://x/freeze" }, { id: "proposal:1", source: "proposal", title: "Priya confirms the freeze window", why: "PROPOSED · STANDUP" }], dedupCount: 2 } : {}),
  });
});

// The drawer's stable testids: `needs-drawer`, `needs-row` (a member),
// `needs-source-row` (a source not read, no calendar), `needs-row-verb`
// (with `data-verb`).
const needsRows = () => [...document.querySelectorAll<HTMLElement>('[data-testid="needs-drawer"] [data-testid="needs-row"]')];
const sourceRows = () => [...document.querySelectorAll<HTMLElement>('[data-testid="needs-drawer"] [data-testid="needs-source-row"]')];
const rowNamed = (text: string) => needsRows().find((r) => r.querySelector(".needs-row-name")?.textContent === text)!;
const lampOf = (r: HTMLElement) => r.querySelector(".gadget-lamp")?.textContent ?? "";
const factOf = (r: HTMLElement) => r.querySelector(".needs-row-fact")?.textContent ?? "";

describe("Arrival attention (HS-200-15)", () => {
  beforeEach(() => vi.mocked(apiFetch).mockReset());

  it("headline: the true total; the Project clause only over several Projects", () => {
    expect(headlineFor(17, 3)).toBe("17 need you across 3 projects");
    expect(headlineFor(3, 1)).toBe("3 need you");
    expect(headlineFor(3, 0)).toBe("3 need you");
    expect(headlineFor(0, 1, true)).toBe("Nothing needs you");
    expect(headlineFor(0, 1, false)).toBe("Coverage incomplete");
  });

  it("draws every member as its object in rank order: one lamp, one verb, the egress named", async () => {
    wire({ count: 17, projects: ["p1", "p2", "p3"], items: SEVENTEEN, next: null,
           coverage: [AVAILABLE("p1", "Q4 Platform"), AVAILABLE("p2", "Governance"), AVAILABLE("p3", "Payments"), FAILED_WATCH],
           complete: false });
    render(<ChairHome />);
    await waitFor(() => expect(needsRows().length).toBe(17), { timeout: 5000 });

    // PHILO-15-09 (B11): every row counts, the unread source too.
    expect(screen.getByTestId("arrival-display").textContent).toBe("18 need you");
    // The unread source leads (above every member), then the members in rank order.
    const gap = sourceRows()[0];
    expect(gap.getAttribute("data-object-id")).toBe("coverage:watch:w-kan");
    expect(gap.compareDocumentPosition(needsRows()[0]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const rows = [gap, ...needsRows()];
    expect(rows[1].textContent).toContain("KAN-7 Payments cut-over runbook");
    expect(lampOf(rows[1])).toBe("OVERDUE · 2 DAYS");
    expect(lampOf(rows[2])).toBe("DUE TODAY");
    for (const r of rows.slice(1)) {
      expect(r.querySelectorAll(".gadget-lamp")).toHaveLength(1);
      expect(within(r).getByRole("button", { name: /^Open: / })).toBeTruthy();
      expect(r.textContent).toContain("X");
    }
    // One filled primary per face: the top member's verb.
    expect(within(rows[1]).getByRole("button", { name: /^Open: / }).className).toContain("btn--primary");
    expect(within(rows[2]).getByRole("button", { name: /^Open: / }).className).toContain("btn--secondary");
    // No cap, no filter strip.
    expect(screen.queryByRole("group", { name: "Ranking" })).toBeNull();
    // PHILO-14 A5b (A2b ruling): over several Projects each row names its
    // Project ONCE, as the Project's Button on the fact line (a generic open:
    // the drawer); the fact text does not repeat the name.
    for (const r of needsRows()) {
      const name = r.querySelector(".needs-row-name")?.textContent ?? "";
      const project = SEVENTEEN.find((x) => x.title === name)!.projectName;
      expect(within(r).getAllByRole("group", { name: "Project" })).toHaveLength(1);
      expect(within(r).getByRole("button", { name: `Open the Project: ${project}` })).toBeTruthy();
      expect(factOf(r)).not.toContain(project);
    }
    expect(screen.queryByTestId("arrival-needs-you-remainder")).toBeNull();
  });

  it("a merged row is ONE row with ONE fact line (the board retires the sources disclosure)", async () => {
    wire({ count: 17, projects: ["p1", "p2", "p3"], items: SEVENTEEN, next: null,
           coverage: [AVAILABLE("p1", "Q4 Platform")], complete: true });
    render(<ChairHome />);
    await waitFor(() => expect(needsRows().length).toBe(17), { timeout: 5000 });
    expect(needsRows().filter((r) => r.textContent?.includes("Priya confirms the freeze window"))).toHaveLength(1);
    expect(screen.queryByRole("button", { name: /^Sources: / })).toBeNull();
  });

  it("draws exactly ONE filled primary on the whole face", async () => {
    wire({ count: 17, projects: ["p1", "p2", "p3"], items: SEVENTEEN, next: null,
           coverage: [AVAILABLE("p1", "Q4 Platform")], complete: true });
    const { container } = render(<ChairHome />);
    await waitFor(() => expect(needsRows().length).toBe(17), { timeout: 5000 });
    expect(container.querySelectorAll("[data-testid='needs-drawer'] .btn--primary")).toHaveLength(1);
  });

  it("keeps an unreadable source ABOVE the answer as its own row: reason, token, verb", async () => {
    wire({ count: 3, projects: ["p1"], items: SEVENTEEN.slice(0, 3), next: null,
           coverage: [AVAILABLE("p1", "Q4 Platform"), FAILED_WATCH], complete: false });
    render(<ChairHome />);
    await waitFor(() => expect(needsRows().length).toBe(3), { timeout: 5000 });
    // PHILO-15-09 (B11): every row counts, the unread source too.
    expect(screen.getByTestId("arrival-display").textContent).toBe("4 need you");
    const gap = sourceRows()[0];
    expect(gap.compareDocumentPosition(needsRows()[0]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(gap.querySelector(".needs-row-name")?.textContent).toBe("jira KAN");
    // PHILO-15 B74: a time from another day carries its day.
    expect(factOf(gap)).toBe(`Jira rejected the query · observed ${whenWord(wireDate("2026-09-07T08:41:00")!)}`);
    expect(lampOf(gap)).toBe("CANT CHECK");
    const verb = within(gap).getByRole("button", { name: "Reconnect: jira KAN" });
    expect(verb.className).toContain("btn");
    expect(verb.className).not.toContain("btn--primary");
  });

  it("marks a remembered row with its observation, and never speaks the all-clear over a partial result", async () => {
    wire({ count: 0, projects: [], items: [], next: null,
           coverage: [AVAILABLE("p1", "Q4 Platform"), FAILED_WATCH], complete: false });
    render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-display").textContent).toBe("Coverage incomplete"), { timeout: 5000 });
    expect(screen.queryByText("Nothing needs you")).toBeNull();
  });

  it("marks a row kept from the last read with the time it was observed", async () => {
    wire({ count: 1, projects: ["p1"], items: [row("KAN-7 Runbook", {
      fromLastObservation: true, observedAt: "2026-09-07T08:41:00",
      why: "OVERDUE · 2 DAYS", dueAt: daysAgo(2), rankClass: "overdue", severity: "danger",
    })], next: null, coverage: [{ ...AVAILABLE("p1", "Q4 Platform"), state: "failed", observed_at: "2026-09-07T08:41:00",
      reason: "jira rejected the query", repair: { token: "READ FAILED", verb: "Retry", href: "/projects/p1" } }], complete: false });
    render(<ChairHome />);
    await waitFor(() => expect(rowNamed("KAN-7 Runbook")).toBeTruthy(), { timeout: 5000 });
    expect(factOf(rowNamed("KAN-7 Runbook"))).toContain(`observed ${whenWord(wireDate("2026-09-07T08:41:00")!)}`);
    expect(lampOf(rowNamed("KAN-7 Runbook"))).toBe("OVERDUE · 2 DAYS");
  });

  it("speaks the all-clear once on a complete read, with no chip and no strip", async () => {
    wire({ count: 0, projects: [], items: [], next: null, computedAt: new Date().toISOString(),
           coverage: [AVAILABLE("p1", "Q4 Platform"), AVAILABLE("p2", "Governance")], complete: true });
    render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"), { timeout: 5000 });
    expect(screen.getAllByText("Nothing needs you")).toHaveLength(1);
    expect(screen.queryByTestId("arrival-coverage-complete")).toBeNull();
    expect(screen.queryByRole("group", { name: "Ranking" })).toBeNull();
    expect(needsRows()).toHaveLength(0);
  });

  // HS-200-13 (AC3/AC4): a commitment the Room emits is ONE row with ONE
  // lawful next action; the Door's card for the same action item is not
  // drawn a second time; Name an owner unfolds the well in place.
  it("a Room commitment is one row with one lawful verb; the Door's card for it is not drawn twice", async () => {
    const commitment = row("p1:commitment:Priya confirms the freeze window", {
      title: "Priya confirms the freeze window", source: "commitment", kind: "commitment",
      why: "OWNER · UNKNOWN", severity: "warning", rankClass: "no_due_date", dueAt: null,
      commitmentId: "cmt-1", actionItemId: "action-1", owner: null, unknowns: ["owner", "due"],
      nextAction: "name_owner", verbHref: null,
    });
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you")) {
        return { count: 1, projects: ["p1"], items: [commitment], next: null,
          coverage: [AVAILABLE("p1", "Q4 Platform")], complete: true };
      }
      if (String(path).startsWith("/api/door")) {
        return { board: { unassigned: [{ id: "action-1", title: "Priya confirms the freeze window",
          source: "action_item", lawful_verbs: ["done"], open_ref: "action:action-1" }] },
          counts: {}, upcoming: [], calendar_configured: false };
      }
      if (String(path) === "/api/follow-through/complete") return { card_id: "action-1", verb: "delegate" };
      return null;
    }));
    render(<ChairHome />);
    // The commitment is one row (a SETUP row for the unread roster may stand beside it).
    const work = () => needsRows().filter((r) => !r.getAttribute("data-object-id")?.startsWith("blocker:"));
    await waitFor(() => expect(work()).toHaveLength(1));
    const only = work()[0];
    expect(only.getAttribute("data-kind")).toBe("action");
    const verbs = only.querySelectorAll(".needs-row-verbs button");
    expect(verbs).toHaveLength(1);
    expect(verbs[0].textContent).toBe("Name an owner");
    fireEvent.click(verbs[0]);
    // No detour: the well unfolds under the row (no modal), and Save writes
    // through the follow-through verb.
    const well = await screen.findByTestId("needs-well");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(vi.mocked(apiFetch).mock.calls.some(([p]) => String(p) === "/api/follow-through/complete")).toBe(false);
    fireEvent.change(within(well).getByRole("textbox", { name: "Owner" }), { target: { value: "Priya" } });
    fireEvent.click(within(well).getByRole("button", { name: /Save owner/ }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST", json: { card_id: "action-1", verb: "delegate", payload: { to: "Priya" } },
    }));
    await waitFor(() => expect(screen.queryByTestId("needs-well")).toBeNull());
  });

  // Inventory 2026-10-03: a meeting action item with no owner is an
  // UNASSIGNED Door card with NO `open_ref`. The card shape below is what
  // `DoorService._action_verbs` emits.
  const doorVerbs = (id: string) => ["done", "dismiss", "snooze", "delegate"].map((verb) => ({
    name: "follow_through.complete", arguments: { card_id: id, verb },
    ...(verb === "delegate" ? { required_arguments: ["payload.to"] } : {}),
    ...(verb === "snooze" ? { required_arguments: ["payload.until"] } : {}),
  }));
  it("Name an owner on an UNASSIGNED Door row unfolds the owner well and saves through delegate", async () => {
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
      if (String(path) === "/api/inference/assignments")
        return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 };
      if (String(path).startsWith("/api/desk/needs-you")) {
        return { count: 0, projects: ["p1"], items: [], next: null,
          coverage: [AVAILABLE("p1", "Q4 Platform")], complete: true };
      }
      if (String(path).startsWith("/api/door")) {
        return { board: { unassigned: [{ id: "action-9", title: "Pilot OTel in billing",
          source: "action_item", target_ref: "action_item:action-9", owner: null, due: null,
          lawful_verbs: doorVerbs("action-9") }] },
          counts: {}, upcoming: [], calendar_configured: false };
      }
      if (String(path) === "/api/follow-through/complete") return { card_id: "action-9", verb: "delegate" };
      return null;
    }));
    render(<ChairHome />);
    await waitFor(() => expect(rowNamed("Pilot OTel in billing")).toBeTruthy());
    const line = rowNamed("Pilot OTel in billing");
    expect(lampOf(line)).toBe("UNASSIGNED");
    const verb = (line.querySelector('[data-verb="name-owner"]') as HTMLElement);
    expect(verb.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(verb);
    const well = await screen.findByTestId("needs-well");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(verb.getAttribute("aria-expanded")).toBe("true");
    fireEvent.change(within(well).getByRole("textbox", { name: "Owner" }), { target: { value: "Avery" } });
    fireEvent.click(within(well).getByRole("button", { name: /Save owner/ }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST", json: { card_id: "action-9", verb: "delegate", payload: { to: "Avery" } },
    }));
    await waitFor(() => expect(screen.queryByTestId("needs-well")).toBeNull());
  });

  it("an UNASSIGNED Door row that can take no owner and has nothing to open draws no Name an owner (A.11)", async () => {
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
      if (String(path) === "/api/inference/assignments")
        return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 };
      if (String(path).startsWith("/api/desk/needs-you")) {
        return { count: 0, projects: ["p1"], items: [], next: null,
          coverage: [AVAILABLE("p1", "Q4 Platform")], complete: true };
      }
      if (String(path).startsWith("/api/door")) {
        return { board: { unassigned: [{ id: "loop-1", title: "Decide the freeze date",
          source: "cadence_loop", target_ref: "cadence_loop:loop-1",
          lawful_verbs: [{ name: "cadence.set_status", arguments: { loop_id: "loop-1", status: "closed" } }] }] },
          counts: {}, upcoming: [], calendar_configured: false };
      }
      return null;
    }));
    render(<ChairHome />);
    await waitFor(() => expect(rowNamed("Decide the freeze date")).toBeTruthy());
    const line = rowNamed("Decide the freeze date");
    expect(within(line).queryByRole("button", { name: /Name an owner/ })).toBeNull();
  });

  // Inventory gap 11: Dana's item is pending review and HAS an owner. The
  // drawer says TO REVIEW and offers Review; only an item with no owner reads
  // UNASSIGNED and offers Name an owner. The cards are the REAL producer's
  // shape (`DoorService._follow_through_card`).
  it("an owned item not reviewed yet reads TO REVIEW, and Review opens it in Follow-through", async () => {
    const producerCard = (id: string, text: string, owner: string | null) => ({
      id, text, owner, due: null, status: "pending", meeting_id: "m-1", decision_id: null,
      stale_score: null, source: "action_item", lane: "unassigned", provenance: null,
      delegated_at: null, created_at: "2026-10-03T09:00:00",
      target_ref: `action_item:${id}`,
      lawful_verbs: [
        { name: "done", arguments: { card_id: id, verb: "done" }, required_arguments: [] },
        { name: "delegate", arguments: { card_id: id, verb: "delegate" }, required_arguments: ["to"] },
      ],
    });
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you")) {
        return { count: 0, projects: [], items: [], next: null, coverage: [], complete: true };
      }
      if (String(path) === "/api/inference/assignments")
        return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 };
      if (String(path).startsWith("/api/door")) {
        return { board: { unassigned: [
          producerCard("ai-owned", "Draft the onboarding checklist", "Dana"),
          producerCard("ai-no-owner", "Book the room", null),
        ] }, counts: {}, upcoming: [], calendar_configured: false };
      }
      return null;
    }));
    const openPullout = vi.fn();
    const navigations: unknown[] = [];
    const onNavigate = (event: Event) => navigations.push((event as CustomEvent).detail);
    window.addEventListener("holdspeak:intelligence-navigate", onNavigate);
    const realOpen = useDesk.getState().openPullout;
    useDesk.setState({ openPullout } as never);
    try {
      render(<ChairHome />);
      await waitFor(() => expect(rowNamed("Draft the onboarding checklist")).toBeTruthy());
      const owned = rowNamed("Draft the onboarding checklist");
      const bare = rowNamed("Book the room");
      expect(lampOf(owned)).toBe("TO REVIEW");
      expect(factOf(owned)).toContain("Dana");
      expect(owned.textContent).not.toContain("UNASSIGNED");
      expect(owned.querySelector('[data-verb="name-owner"]')).toBeNull();
      expect(lampOf(bare)).toBe("UNASSIGNED");
      expect((bare.querySelector('[data-verb="name-owner"]') as HTMLElement).textContent).toBe("Name an owner");
      expect(bare.querySelector('[data-verb="review"]')).toBeNull();

      const review = (owned.querySelector('[data-verb="review"]') as HTMLElement);
      expect(review.textContent).toBe("Review");
      fireEvent.click(review);
      expect(openPullout).toHaveBeenCalledWith("intelligence:desk");
      await waitFor(() => expect(navigations).toEqual([
        { view: "follow-through", followThroughId: "ai-owned" },
      ]));
    } finally {
      window.removeEventListener("holdspeak:intelligence-navigate", onNavigate);
      useDesk.setState({ openPullout: realOpen } as never);
    }
  });

  it("Done is the verb only when owner and date are known, and it posts the explicit act", async () => {
    const commitment = row("p1:commitment:Priya confirms the freeze window", {
      title: "Priya confirms the freeze window", source: "commitment", kind: "commitment",
      why: "DUE TODAY", severity: "warning", rankClass: "due_today", dueAt: new Date().toISOString().slice(0, 10),
      commitmentId: "cmt-1", actionItemId: "action-1", owner: "Priya", unknowns: [],
      nextAction: "mark_done", verbHref: null,
    });
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you")) {
        return { count: 1, projects: ["p1"], items: [commitment], next: null,
          coverage: [AVAILABLE("p1", "Q4 Platform")], complete: true };
      }
      if (String(path).startsWith("/api/door")) return { board: {}, counts: {}, upcoming: [], calendar_configured: false };
      if (String(path) === "/api/follow-through/complete") return { card_id: "action-1", verb: "done" };
      return null;
    }));
    render(<ChairHome />);
    await waitFor(() => expect(rowNamed("Priya confirms the freeze window")).toBeTruthy());
    const verb = (rowNamed("Priya confirms the freeze window").querySelector('[data-verb="done"]') as HTMLElement);
    expect(verb.textContent).toBe("Done");
    fireEvent.click(verb);
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST", json: { card_id: "action-1", verb: "done", payload: {} },
    }));
  });
});
