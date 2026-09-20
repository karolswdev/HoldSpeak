// HS-200-15: the arrival's attention face: five in the first view with
// reason, source and one action; the true total on the display line and
// the cap in the caption; the remainder revealed in place; the ranking
// strip as a real filter; the dedup disclosure; the Project button; the
// coverage ledger above the answer; STILL TRUE on a remembered row; and
// never an all-clear over a partial result.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { ChairHome, headlineFor } from "./ChairHome";

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
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
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
  });
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

describe("Arrival attention (HS-200-15)", () => {
  beforeEach(() => vi.mocked(apiFetch).mockReset());

  it("headline: the true total; the Project clause only over several Projects", () => {
    expect(headlineFor(17, 3)).toBe("17 need you across 3 projects");
    expect(headlineFor(3, 1)).toBe("3 need you");
    expect(headlineFor(3, 0)).toBe("3 need you");
    expect(headlineFor(0, 1, true)).toBe("Nothing needs you");
    expect(headlineFor(0, 1, false)).toBe("Coverage incomplete");
  });

  it("shows five rows with reason, source and one action; the caption carries the cap; the rest is reachable", async () => {
    wire({ count: 17, projects: ["p1", "p2", "p3"], items: SEVENTEEN, next: null,
           coverage: [AVAILABLE("p1", "Q4 Platform"), AVAILABLE("p2", "Governance"), AVAILABLE("p3", "Payments"), FAILED_WATCH],
           complete: false });
    render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-needs-you")).toBeTruthy(), { timeout: 5000 });

    expect(screen.getByTestId("arrival-display").textContent).toBe("17 need you across 3 projects");
    const section = screen.getByTestId("arrival-needs-you");
    expect(section.textContent).toContain("NEEDS YOU 5 OF 17");
    const rows = within(section).getAllByTestId("arrival-needs-you-row");
    expect(rows).toHaveLength(5);
    // Ranked: the overdue row first, then due today.
    expect(rows[0].textContent).toContain("KAN-7 Payments cut-over runbook");
    expect(within(rows[0]).getByTestId("arrival-why").textContent).toBe("OVERDUE · 2 DAYS");
    expect(within(rows[1]).getByTestId("arrival-why").textContent).toBe("DUE TODAY");
    // Every row: an emblem (the source), a reason, one verb, the Project button.
    for (const r of rows) {
      expect(within(r).getByTestId("arrival-source-emblem").textContent).not.toBe("");
      expect(within(r).getByTestId("arrival-why").textContent).not.toBe("");
      expect(within(r).getByRole("group", { name: "Project" })).toBeTruthy();
      expect(within(r).getByRole("button", { name: /^Open: / })).toBeTruthy();
    }
    // One filled primary per face: the top row's verb.
    expect(within(rows[0]).getByRole("button", { name: /^Open: / }).className).toContain("btn--primary");
    expect(within(rows[1]).getByRole("button", { name: /^Open: / }).className).toContain("btn--ghost");

    // The remainder: a real count and a real verb, in place.
    expect(screen.getByTestId("arrival-needs-you-remainder-count").textContent).toBe("12 MORE");
    fireEvent.click(screen.getByRole("button", { name: "Show all: the remaining 12" }));
    expect(within(section).getAllByTestId("arrival-needs-you-row")).toHaveLength(17);
    expect(section.textContent).toContain("NEEDS YOU 17");
    expect(screen.queryByTestId("arrival-needs-you-remainder-count")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /^Show fewer/ }));
    expect(within(section).getAllByTestId("arrival-needs-you-row")).toHaveLength(5);
  });

  it("draws the dedup disclosure naming every source of a merged row", async () => {
    wire({ count: 17, projects: ["p1", "p2", "p3"], items: SEVENTEEN, next: null,
           coverage: [AVAILABLE("p1", "Q4 Platform")], complete: true });
    render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-needs-you")).toBeTruthy(), { timeout: 5000 });
    const trigger = screen.getByRole("button", { name: "Sources: Priya confirms the freeze window" });
    expect(trigger.textContent).toContain("2 SOURCES");
    fireEvent.click(trigger);
    const list = screen.getByTestId("arrival-sources");
    const entries = within(list).getAllByTestId("arrival-source");
    expect(entries).toHaveLength(2);
    expect(list.textContent).toContain("PROPOSED · STANDUP");
    // Each projection: emblem, its own title, its why, its own Open (A.11).
    for (const entry of entries) {
      expect(entry.querySelector(".arrival-source-emblem")?.textContent).not.toBe("");
      expect(entry.querySelector(".arrival-source-title")?.textContent).toBe("Priya confirms the freeze window");
      expect(within(entry).getByRole("button", { name: "Open: Priya confirms the freeze window" })).toBeTruthy();
    }
  });

  it("draws exactly ONE filled primary on the whole face, and the selected filter is not it", async () => {
    wire({ count: 17, projects: ["p1", "p2", "p3"], items: SEVENTEEN, next: null,
           coverage: [AVAILABLE("p1", "Q4 Platform")], complete: true });
    const { container } = render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-needs-you")).toBeTruthy(), { timeout: 5000 });
    expect(container.querySelectorAll(".btn--primary")).toHaveLength(1);
    const strip = screen.getByRole("group", { name: "Ranking" });
    fireEvent.click(within(strip).getByRole("button", { name: "OVERDUE" }));
    expect(container.querySelectorAll(".btn--primary")).toHaveLength(1);
    expect(within(strip).getByRole("button", { name: "OVERDUE" }).className).toContain("btn--secondary");
  });

  it("states the ranking key on the face as a filter strip and filters by class", async () => {
    wire({ count: 17, projects: ["p1", "p2", "p3"], items: SEVENTEEN, next: null,
           coverage: [AVAILABLE("p1", "Q4 Platform")], complete: true });
    render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-needs-you")).toBeTruthy(), { timeout: 5000 });
    const strip = screen.getByRole("group", { name: "Ranking" });
    expect(within(strip).getAllByRole("button").map((b) => b.textContent)).toEqual([
      "RANKED", "OVERDUE", "DUE TODAY", "NOT RUN", "NO DUE DATE", "WAITING",
    ]);
    fireEvent.click(within(strip).getByRole("button", { name: "OVERDUE" }));
    const section = screen.getByTestId("arrival-needs-you");
    expect(within(section).getAllByTestId("arrival-needs-you-row")).toHaveLength(1);
    expect(section.textContent).toContain("NEEDS YOU 1");
    fireEvent.click(within(strip).getByRole("button", { name: "NOT RUN" }));
    expect(screen.getByTestId("arrival-needs-you-none").textContent).toBe("NOTHING NOT RUN");
    fireEvent.click(within(strip).getByRole("button", { name: "RANKED" }));
    expect(within(section).getAllByTestId("arrival-needs-you-row")).toHaveLength(5);
  });

  it("withholds the Project button over one Project and says `3 need you`", async () => {
    wire({ count: 3, projects: ["p1"], items: SEVENTEEN.slice(0, 3), next: null,
           coverage: [AVAILABLE("p1", "Q4 Platform"), FAILED_WATCH], complete: false });
    render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-needs-you")).toBeTruthy(), { timeout: 5000 });
    expect(screen.getByTestId("arrival-display").textContent).toBe("3 need you");
    expect(screen.queryByRole("group", { name: "Project" })).toBeNull();
    expect(screen.getByTestId("arrival-needs-you").textContent).toContain("NEEDS YOU 3");
    expect(screen.queryByTestId("arrival-needs-you-remainder")).toBeNull();
  });

  it("keeps coverage ABOVE the answer: each unreadable source with its reason, token, observation and verb", async () => {
    wire({ count: 3, projects: ["p1"], items: SEVENTEEN.slice(0, 3), next: null,
           coverage: [AVAILABLE("p1", "Q4 Platform"), FAILED_WATCH], complete: false });
    const { container } = render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-coverage")).toBeTruthy(), { timeout: 5000 });
    const coverage = screen.getByTestId("arrival-coverage");
    expect(coverage.textContent).toContain("COVERAGE · 1 OF 2");
    const gap = within(coverage).getByTestId("arrival-coverage-row");
    expect(within(gap).getByTestId("arrival-coverage-reason").textContent).toBe("JIRA REJECTED THE QUERY");
    expect(within(gap).getByTestId("arrival-coverage-token").textContent).toContain("CANT CHECK");
    expect(within(gap).getByTestId("arrival-coverage-observed").textContent).toBe("OBSERVED 09-07 08:41");
    const verb = within(gap).getByRole("button", { name: "Reconnect: jira KAN" });
    expect(verb.className).toContain("btn");
    // Above the answer: the coverage section precedes the NEEDS YOU section.
    const order = Array.from(container.querySelectorAll("[data-testid='arrival-coverage'], [data-testid='arrival-needs-you']"))
      .map((el) => el.getAttribute("data-testid"));
    expect(order).toEqual(["arrival-coverage", "arrival-needs-you"]);
    // The head does not repeat the fraction while the read is incomplete.
    expect(screen.queryByTestId("arrival-coverage-complete")).toBeNull();
  });

  it("stamps a remembered row STILL TRUE with its observation, and never speaks the all-clear over a partial result", async () => {
    wire({ count: 0, projects: [], items: [], next: null,
           coverage: [AVAILABLE("p1", "Q4 Platform"), FAILED_WATCH], complete: false });
    render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-coverage")).toBeTruthy(), { timeout: 5000 });
    expect(screen.getByTestId("arrival-display").textContent).toBe("Coverage incomplete");
    expect(screen.queryByText("Nothing needs you")).toBeNull();

    vi.mocked(apiFetch).mockReset();
    wire({ count: 1, projects: ["p1"], items: [row("KAN-7 Runbook", {
      fromLastObservation: true, observedAt: "2026-09-07T08:41:00",
      why: "OVERDUE · 2 DAYS", dueAt: daysAgo(2), rankClass: "overdue", severity: "danger",
    })], next: null, coverage: [{ ...AVAILABLE("p1", "Q4 Platform"), state: "failed", observed_at: "2026-09-07T08:41:00",
      reason: "jira rejected the query", repair: { token: "READ FAILED", verb: "Retry", href: "/projects/p1" } }], complete: false });
    render(<ChairHome />);
    await waitFor(() => expect(screen.getAllByTestId("arrival-remembered").length).toBeGreaterThan(0), { timeout: 5000 });
    expect(screen.getAllByTestId("arrival-remembered")[0].textContent).toBe("STILL TRUE · OBSERVED 09-07 08:41");
    expect(screen.getAllByTestId("arrival-why").at(-1)?.textContent).toBe("OVERDUE · 2 DAYS");
  });

  it("speaks the all-clear with the coverage chip only when complete", async () => {
    wire({ count: 0, projects: [], items: [], next: null, computedAt: new Date().toISOString(),
           coverage: [AVAILABLE("p1", "Q4 Platform"), AVAILABLE("p2", "Governance")], complete: true });
    render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"), { timeout: 5000 });
    expect(screen.getByTestId("arrival-coverage-complete").textContent).toContain("2 OF 2 AVAILABLE");
    expect(screen.getByTestId("arrival-checked").textContent).toBe("CHECKED JUST NOW");
    expect(screen.queryByTestId("arrival-coverage")).toBeNull();
    expect(screen.queryByRole("group", { name: "Ranking" })).toBeNull();
    expect(screen.getByTestId("arrival-no-calendar").textContent).toContain("NO CALENDAR");
  });
  // HS-200-13 (AC3/AC4): a commitment the Room emits is an attention row
  // with the CMT emblem, its due-driven class, and ONE lawful next action;
  // the Door's card for the same action item is not drawn a second time;
  // `Mark done` is the explicit act, `Name an owner` opens the recall face.
  it("a Room commitment is one row with one lawful verb; the Door's card for it is not drawn twice", async () => {
    const commitment = row("p1:commitment:Priya confirms the freeze window", {
      title: "Priya confirms the freeze window", source: "commitment", kind: "commitment",
      why: "OWNER · UNKNOWN", severity: "warning", rankClass: "no_due_date", dueAt: null,
      commitmentId: "cmt-1", actionItemId: "action-1", owner: null, unknowns: ["owner", "due"],
      nextAction: "name_owner", verbHref: null,
    });
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
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
    });
    render(<ChairHome />);
    const section = await screen.findByTestId("arrival-needs-you");
    const rows = within(section).getAllByTestId("arrival-needs-you-row");
    expect(rows).toHaveLength(1);
    expect(within(rows[0]).getByTestId("arrival-source-emblem").textContent).toBe("CMT");
    const verb = within(rows[0]).getByTestId("arrival-commitment-verb");
    expect(verb.textContent).toBe("Name an owner");
    expect(verb.getAttribute("data-next-action")).toBe("name_owner");
    expect(within(rows[0]).queryByTestId("arrival-name-owner")).toBeNull();
    fireEvent.click(verb);
    // Counsel P2: no detour -- the well unfolds under the row (no modal), and
    // Save writes through the follow-through verb; the verb becomes Set a date.
    const well = await screen.findByTestId("arrival-commit-well");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(vi.mocked(apiFetch).mock.calls.some(([p]) => String(p) === "/api/follow-through/complete")).toBe(false);
    fireEvent.change(within(well).getByRole("textbox", { name: "Owner" }), { target: { value: "Priya" } });
    fireEvent.click(within(well).getByRole("button", { name: /Save owner/ }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST", json: { card_id: "action-1", verb: "delegate", payload: { to: "Priya" } },
    }));
    await waitFor(() => expect(within(rows[0]).getByTestId("arrival-commitment-verb").textContent).toBe("Set a date"));
    expect(screen.queryByTestId("arrival-commit-well")).toBeNull();
  });

  it("Mark done is the verb only when owner and date are known, and it posts the explicit act", async () => {
    const commitment = row("p1:commitment:Priya confirms the freeze window", {
      title: "Priya confirms the freeze window", source: "commitment", kind: "commitment",
      why: "DUE TODAY", severity: "warning", rankClass: "due_today", dueAt: new Date().toISOString().slice(0, 10),
      commitmentId: "cmt-1", actionItemId: "action-1", owner: "Priya", unknowns: [],
      nextAction: "mark_done", verbHref: null,
    });
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you")) {
        return { count: 1, projects: ["p1"], items: [commitment], next: null,
          coverage: [AVAILABLE("p1", "Q4 Platform")], complete: true };
      }
      if (String(path).startsWith("/api/door")) return { board: {}, counts: {}, upcoming: [], calendar_configured: false };
      if (String(path) === "/api/follow-through/complete") return { card_id: "action-1", verb: "done" };
      return null;
    });
    render(<ChairHome />);
    const section = await screen.findByTestId("arrival-needs-you");
    const verb = within(section).getByTestId("arrival-commitment-verb");
    expect(verb.textContent).toBe("Mark done");
    fireEvent.click(verb);
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST", json: { card_id: "action-1", verb: "done", payload: {} },
    }));
  });
});
