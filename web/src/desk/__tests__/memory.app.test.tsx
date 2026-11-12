// The Memory app: Desk memory (the unscoped recall face), the Room's standing
// pages and the Brief's desk pages. The test diet (2026-10-11) moves the face
// facts of tests/e2e/test_hs526_desk_memory_glass.py and
// tests/e2e/test_memory_faces_glass.py here; the hub half (the edge, the
// beliefs and pages made by the real producers, the deletes) is
// tests/unit/test_desk_memory.py.
//
// The real faces with their real controllers; only apiFetch is mocked, by
// URL, with the hub's REAL answers: the recall and pages payloads below were
// read from the real producers on each e2e's own seed (recall_service.recall,
// memory_faces.standing_pages); the brief is a fresh hub's /api/brief/latest.
//
// Facts the existing fences already hold (cited, not written again):
//  * the Artifact over the edge, `Related · meeting artifact`, the mark:
//    web/src/pages/cores/__tests__/projectMemoryCore.test.tsx
//    "names evidence reached through a durable relationship"
//  * the miss reads `Nothing matches`, no card:
//    web/src/features/project-room/recall/__tests__/RecallFace.test.tsx
//    "the miss: Nothing matches, one true line, the filters kept, no Clear"
//  * beliefs CURRENT 1 / DISPUTED 2 / SUPERSEDED 1 in that order, the old
//    text struck through, `AGAINST · MTG ...` a Button, `SINCE`:
//    web/src/features/project-room/recall/__tests__/beliefCard.test.tsx
//    "CURRENT, then DISPUTED, then SUPERSEDED, each with its beliefs",
//    "current: ...", "disputed: ...", "superseded: ..."
//  * the faces follow the bus after a delete; a discarded refresh releases
//    nothing: web/src/desk/__tests__/memoryChanges.test.tsx
//    "standing pages follow the bus (P1)", "Desk memory beliefs follow the bus (P1)",
//    "Astra #877 iteration 2: a refresh a newer search superseded releases nothing ..."

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../ask", async () => {
  const actual = await vi.importActual<typeof import("../ask")>("../ask");
  return { ...actual, runAsk: vi.fn() };
});
const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../shell", async () => {
  const actual = await vi.importActual<typeof import("../shell")>("../shell");
  return { ...actual, openPrimitive: vi.fn(), openSurfaceOr: vi.fn() };
});
vi.mock("../intelligenceAttention", async () => {
  const actual = await vi.importActual<typeof import("../intelligenceAttention")>("../intelligenceAttention");
  return { ...actual, refreshIntelligenceAttention: vi.fn() };
});

import { EMPTY_ITEMS } from "../api";
import { __resetSurfaces } from "../shell";
import { useDesk } from "../store";
import { ProjectRoomCore } from "../../features/project-room/ProjectRoomCore";

// ── the hub's answers ───────────────────────────────────────────────────

/** GET /api/memory/recall?query=zephyr on the HS-526 seed (unscoped). */
const ZEPHYR = {
  query: "zephyr", recent: false, filter: "all", searched_at: "2026-10-11T15:12:53.612012+00:00",
  projects_searched: 0, current: [], superseded: [], disputed: [], owed: [],
  meetings: [{
    kind: "meeting", source_ref: "meeting:hs526-m1", title: "Launch review",
    snippet: "The <mark>zephyr</mark> rollout starts Friday", occurred_at: "2026-02-01T09:00:00",
    project_id: null, bm25: -1e-06, normalized_score: 1.0, kind_rank: 1, rank: 2,
    retrieval_origin: "lexical", related_to: null, relationship: null, graph_score: 0.0,
  }],
  briefs: [],
  also: [
    {
      kind: "note", source_ref: "note:hs526-n1", title: "Zephyr rollout note",
      snippet: "<mark>Zephyr</mark> rollout note", occurred_at: "2026-10-11T15:12:53Z",
      project_id: null, bm25: -1.54e-06, normalized_score: 1.0, kind_rank: 1, rank: 1,
      retrieval_origin: "lexical", related_to: null, relationship: null, graph_score: 0.0,
    },
    {
      kind: "artifact", source_ref: "artifact:hs526-a1", title: "Rollout checklist",
      snippet: "Owners and gates", occurred_at: "2026-02-02T09:00:00",
      project_id: null, bm25: 0.0, normalized_score: 0.8, kind_rank: 1, rank: 3,
      retrieval_origin: "relationship", related_to: "meeting:hs526-m1", relationship: "meeting_artifact",
      graph_score: 0.8,
    },
  ],
  beliefs: [], remembered: 3,
};
/** GET /api/memory/recall?query=unfindablequasar on the same seed. */
const QUASAR = {
  query: "unfindablequasar", recent: false, filter: "all", searched_at: "2026-10-11T15:12:53.657405+00:00",
  projects_searched: 0, current: [], superseded: [], disputed: [], owed: [], meetings: [], briefs: [],
  also: [], beliefs: [], remembered: 0,
};

const ref = (r: string, token: string) => ({ ref: r, opens: true, token });
const MAREK = { text: "Cutover rollback owner is Marek.", refs: [ref("meeting:m-0924", "MTG 09-24 · 10:00")] };
const DATE = { text: "Cutover date is 10-17.", refs: [ref("note:n-1001", "NOTE 10-11")] };
const PRIYA = { text: "Cutover rollback owner is Priya.", refs: [ref("meeting:m-0929", "MTG 09-29 · 10:00")] };
const page = (slug: string, question: string, sentences: unknown[], stale = false, newSources = 0) => ({
  slug, question, sentences, built_at: "2026-10-11T15:25:11+00:00", stale, new_sources: newSources,
  model: "pages", boundary: "local",
});
/** GET /api/memory/pages?project_id=atlas on the memory-faces seed: ONE page stale. */
const ATLAS_PAGES = {
  pages: [
    page("what-we-decided", "What did we decide?", [MAREK, DATE, PRIYA]),
    page("what-is-open", "What is open and who owes it?", [MAREK, DATE, PRIYA]),
    page("risks-and-disputes", "What are the risks and disputes?", [MAREK, PRIYA, DATE]),
    page("what-changed-this-week", "What changed this week?", [
      MAREK, DATE, PRIYA, { text: "Note n-1001 Cutover date is 10-17.", refs: [ref("note:n-1001", "NOTE 10-11")] },
    ], true, 1),
  ],
};
const OWE1 = { text: "Hiring loop reply is owed.", refs: [ref("note:n-desk-1", "NOTE 10-11")] };
const OWE2 = { text: "Billing contract is waiting.", refs: [ref("note:n-desk-2", "NOTE 10-11")] };
/** GET /api/memory/pages?scope=desk on the same seed. */
const DESK_PAGES = {
  pages: [
    page("what-i-owe", "What do I owe?", [OWE1, OWE2]),
    page("what-changed-this-week", "What changed this week?", [
      OWE1, OWE2,
      { text: "Note n-desk-1 Hiring loop reply is owed.", refs: [ref("note:n-desk-1", "NOTE 10-11")] },
      { text: "Note n-desk-2 Billing contract is waiting.", refs: [ref("note:n-desk-2", "NOTE 10-11")] },
    ]),
  ],
};
/** GET /api/brief/latest on a fresh hub after one Generate. */
const BRIEF = {
  id: "brief-61ab0dce53ac43e09b73e6fda8752103", period_start: "2026-10-09T00:00:00-06:00",
  period_end: "2026-10-11T09:26:36.820671-06:00", headline: "1 thing waiting.",
  sections: {
    this_week: [], changed: [], broke: [],
    waiting: [{
      id: "brief-item-1e1552191c0a41c096dc4f046526674d", section: "waiting", text: "No engine for summaries",
      detail: "Choose an engine", source_ref: "blocker:summary", priority: 120, created_at: null,
    }],
    decisions: [],
  },
  generated_at: "2026-10-11T09:26:36.820671-06:00", is_empty: false, shelf: {},
  ledger: { operations: 0, since: null }, period_label: "OCT 09-11", generated_label: "GENERATED OCT 11 09:26",
  title: "Brief · Sunday 11 Oct 2026", stale: false, person_sections_state: "unavailable",
};
/** The Room read for Atlas (the fixture shape of projectMemoryCore.test.tsx). */
const ROOM = {
  project_id: "atlas", revision: 1, observed_at: "2026-10-11T10:00:00",
  project: {
    id: "atlas", name: "Atlas cutover", description: null, is_archived: false, meeting_count: 2,
    created_at: "2026-09-01T00:00:00", updated_at: "2026-10-11T10:00:00", purpose: null, outcome_text: null,
    owner_ref: null, lifecycle: null, posture: null, posture_reason: null, start_at: null, target_at: null, revision: 1,
  },
  items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
  meetings: { state: "ok", count: 2, latest: { id: "m-0929", title: "Sync m-0929" } },
  resources: { state: "ok", count: 0, latest: null },
  changes: { state: "ok", recent: [] },
  review: { state: "absent", reason: "not_yet_built" },
  needsYou: { state: "ok", items: [], count: 0 },
  sources: { state: "ok", items: [], count: 0 },
  health: { state: "ok", assessment: "on_track", reason: null, inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false } },
  sinceRead: { state: "ok", readAt: null, groups: [] },
  decisions: { state: "ok", items: [] },
  commitments: { state: "ok", items: [] },
  target: { state: "absent", reason: "none" },
  updates: { state: "absent", reason: "not_yet_built" },
  steward: { state: "absent", reason: "not_yet_built" },
};

function hub(url: string): unknown {
  if (url.startsWith("/api/memory/recall")) return url.includes("unfindablequasar") ? QUASAR : url.includes("zephyr") ? ZEPHYR : QUASAR;
  if (url.startsWith("/api/memory/pages")) return url.includes("scope=desk") ? DESK_PAGES : url.includes("project_id=atlas") ? ATLAS_PAGES : { pages: [] };
  if (url.startsWith("/api/brief/latest") || url.startsWith("/api/brief/generate")) return BRIEF;
  if (url.includes("/room/read")) return { read_at: new Date().toISOString() };
  if (url.includes("/room")) return ROOM;
  if (url === "/api/projects/atlas") return { id: "atlas", name: "Atlas cutover" };
  if (url.includes("/meetings")) return { meetings: [] };
  if (url.startsWith("/api/decisions")) return { decisions: [] };
  if (url.includes("/artifacts")) return { artifacts: [] };
  return {};
}

beforeEach(() => {
  localStorage.clear();
  apiFetch.mockImplementation((url: string) => Promise.resolve(hub(String(url))));
  useDesk.setState({ windowsById: {}, items: { ...EMPTY_ITEMS }, projects: [], inferenceTargets: [] });
});
afterEach(() => {
  __resetSurfaces();
  vi.clearAllMocks();
});

async function search(query: string) {
  fireEvent.change(await screen.findByRole("textbox", { name: "Search memory" }), { target: { value: query } });
  fireEvent.click(screen.getByRole("button", { name: "Search" }));
  await waitFor(() => expect(apiFetch).toHaveBeenCalledWith(expect.stringContaining(new URLSearchParams({query}).toString())));
}

describe("Desk memory (HS-526): relationship-aware recall", () => {
  it("a transcript hit recalls its Meeting; the Artifact arrives over the edge, named; the marks are rendered, never injected", async () => {
    // replaces: tests/e2e/test_hs526_desk_memory_glass.py::test_desk_memory_results (face half)
    const { container } = render(<ProjectRoomCore />);
    await search("zephyr");
    expect(await screen.findByText("Launch review")).toBeTruthy();
    expect(screen.getByText("Rollout checklist")).toBeTruthy();
    fireEvent.click(screen.getByRole("row", { name: /Rollout checklist/ }));
    expect(screen.getByText(/meeting artifact/)).toBeTruthy();
    expect(container.querySelectorAll(".object-list-row").length).toBeGreaterThanOrEqual(2);
    fireEvent.click(screen.getByRole("row", { name: /Launch review/ }));
    const marks = container.querySelectorAll("mark");
    expect(marks.length).toBeGreaterThanOrEqual(1);
    expect([...marks].map((m) => m.textContent?.toLowerCase())).toContain("zephyr");
    expect(container.textContent).not.toContain("<mark>");
  });

  it("nothing behind the query: Nothing matches, no row, and Search memory is the library Button", async () => {
    // replaces: tests/e2e/test_hs526_desk_memory_glass.py::test_desk_memory_empty (face half)
    const { container } = render(<ProjectRoomCore />);
    await search("unfindablequasar");
    expect(await screen.findByText("Nothing matches")).toBeVisible();
    expect(container.querySelectorAll(".object-list-row")).toHaveLength(0);
    expect(screen.getByRole("button", {name:"Search"})).toHaveClass("btn");
  });
});

describe("Memory on the Desk: standing pages where the work lives", () => {
  it("the Atlas Room: History's Pages row names Open, Risks and Changed; a row opens its page, each sentence with its source", async () => {
    // replaces: tests/e2e/test_memory_faces_glass.py::test_memory_on_the_desk (face half: pages)
    // The language (2026-11-08): R1 took This week off the Now face (the
    // case was parked); the project's standing pages are History's head row.
    render(<ProjectRoomCore scope="project:atlas" />);
    fireEvent.click(await screen.findByRole("button", {name:"Project view"}));
    fireEvent.click(screen.getByRole("menuitem", {name:"Pages"}));
    const grid = await screen.findByRole("grid", {name:"Pages"});
    for (const name of ["What did we decide", "What is open and who owes it", "Risks and disputes", "What changed this week"]) expect(await within(grid).findByRole("row",{name:new RegExp(name)})).toBeInTheDocument();
    fireEvent.click(within(grid).getByRole("row",{name:/What changed this week/}));
    expect(await screen.findByText("Cutover rollback owner is Marek.")).toBeVisible();
    expect(screen.getByRole("combobox",{name:"Source"})).toHaveDisplayValue("MTG 09-24 · 10:00");
    expect(screen.getByRole("button",{name:"Open source"})).toBeEnabled();
    expect(grid.querySelectorAll(".object-list-row")).toHaveLength(ATLAS_PAGES.pages.length);
    expect(grid.textContent).not.toContain("Harbor");
    expect(screen.queryByText(/Rewrite/i)).toBeNull();
  });


  // Today desk pages are covered by today.app.test.tsx.

});

// ── HS-200-13: recall of a superseded chain, Carry, Name an owner ──────────
//
// The successor of tests/e2e/test_hs200_continuity_glass.py's recall legs
// (the test diet, 2026-10-11). fixtures/memory-continuity/recall.json holds
// the real hub's answers on that rig's own seed (two meetings, Saturday's
// decision superseded by Sunday's, one owed commitment), recorded by
// tests/unit/test_desk_memory.py::test_the_recall_minute_reads_the_current_decision_carries_it_and_names_an_owner:
// the recent read, the search, the carry and the follow-through answers, and
// the search after each press. A read the hub was not asked rejects.
import RECALL from "./fixtures/memory-continuity/recall.json";

const NEW_TEXT = "Freeze window is Sunday 02:00, not Saturday";
const OLD_TEXT = "Freeze window is Saturday 02:00";
const NEW_WHY = "Payments cannot drain the queue before 02:00 on a weekday.";
const CMT_TEXT = "Priya confirms the freeze window";

function replayRecall() {
  let after: "searched" | "after_carry" | "after_name" = "searched";
  const misses: string[] = [];
  const presses: { path: string; body: unknown }[] = [];
  apiFetch.mockImplementation((url: string, init: { method?: string; json?: unknown } = {}) => {
    const path = String(url);
    const method = (init.method ?? "GET").toUpperCase();
    if (method === "POST" && path === RECALL.carry.path) {
      presses.push({ path, body: init.json });
      after = "after_carry";
      return Promise.resolve(structuredClone(RECALL.carry.answer));
    }
    if (method === "POST" && path === "/api/follow-through/complete") {
      presses.push({ path, body: init.json });
      after = "after_name";
      return Promise.resolve(structuredClone(RECALL.name_owner.answer));
    }
    if (method === "GET" && path === "/api/coders/sessions?include_ended=false")
      return Promise.resolve(structuredClone(RECALL.coders_sessions));
    if (method === "GET" && path.startsWith("/api/memory/recall?")) {
      const q = new URLSearchParams(path.split("?")[1]);
      if (q.get("recent") === "1") return Promise.resolve(structuredClone(RECALL.recent));
      if (q.get("query") === "freeze window") return Promise.resolve(structuredClone(RECALL[after]));
      if (q.get("query") === "unfindablequasar") return Promise.resolve(structuredClone(RECALL.miss));
    }
    misses.push(`${method} ${path}`);
    return Promise.reject(new Error(`the hub recorded no answer for ${method} ${path}`));
  });
  return { misses, presses };
}

describe("Desk memory: the quiet open read says busy (PHILO-17 held read)", () => {
  it("busy while the recent read is out; the mark goes when it lands and the display line is drawn", async () => {
    // The sweep's held first read: the recent read landed after the window
    // read as settled and the display line moved the well 30 px.
    let land: (v: unknown) => void = () => {};
    apiFetch.mockImplementation((url: string) => String(url).startsWith("/api/memory/recall")
      ? new Promise((r) => { land = r; }) : Promise.resolve(hub(String(url))));
    const { container } = render(<ProjectRoomCore />);
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith(expect.stringContaining("recent=1")));
    expect(container.querySelector('[aria-busy="true"]')).not.toBeNull();
    land(QUASAR);
    expect(await screen.findByText("Nothing matches")).toBeInTheDocument();
    await waitFor(() => expect(container.querySelector('[aria-busy="true"]')).toBeNull());
  });
});

describe("Desk memory (HS-200-13): the current decision first, carried; the owed commitment named", () => {
  it("recent on open; the search: CURRENT first with its why and source, SUPERSEDED under it, OWED with typed unknowns; Carry; Name an owner; the miss", async () => {
    // replaces: tests/e2e/test_hs200_continuity_glass.py::TestContinuityGlass::test_recall_1440 (every leg but
    //   the computed opacity, the type steps, the 393 filter fold and the viewport measures, which stay in
    //   the browser file; the "recall minute" is a measurement, not a fence)
    const { presses, misses } = replayRecall();
    render(<ProjectRoomCore />);
    await screen.findByRole("grid",{name:"Recent on this desk"});
    await search("freeze window");
    const current = await screen.findByRole("row", {name:new RegExp(NEW_TEXT)});
    const old = screen.getByRole("row",{name:new RegExp(OLD_TEXT)});
    expect(current).toHaveTextContent("Current"); expect(old).toHaveTextContent("Superseded");
    expect([...screen.getByRole("grid",{name:"Memory"}).querySelectorAll(".object-list-row")].indexOf(current)).toBeLessThan([...screen.getByRole("grid",{name:"Memory"}).querySelectorAll(".object-list-row")].indexOf(old));
    fireEvent.click(current);
    expect(screen.getByText(NEW_WHY)).toBeInTheDocument();
    expect(screen.getByRole("button",{name:"Open source"})).toBeEnabled();
    expect(screen.getByRole("button",{name:"Open project"})).toBeEnabled();
    fireEvent.click(screen.getByRole("button",{name:"Carry into brief"}));
    await waitFor(()=>expect(screen.getByRole("button",{name:"Carried"})).toBeDisabled());
    expect(presses[0]).toEqual({path:RECALL.carry.path,body:RECALL.carry.body});
    fireEvent.click(old);
    expect(screen.getByRole("button",{name:"Carry into brief"})).toBeDisabled();
    expect(screen.getByRole("button",{name:"Open successor"})).toBeEnabled();
    fireEvent.click(screen.getByRole("row",{name:new RegExp(CMT_TEXT)}));
    expect(screen.getByRole("button",{name:"Done"})).toBeDisabled();
    fireEvent.click(screen.getByRole("button",{name:"Name an owner"}));
    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.change(screen.getByRole("textbox",{name:"Owner"}),{target:{value:"Priya"}});
    fireEvent.click(screen.getByRole("button",{name:"Save"}));
    await waitFor(()=>expect(screen.getByRole("button",{name:"Name an owner"})).toBeDisabled());
    expect(screen.getByRole("button",{name:"Set a date"})).toBeEnabled();
    expect(screen.getByText("Priya",{exact:true})).toBeInTheDocument();
    expect(presses[1]).toEqual({path:"/api/follow-through/complete",body:RECALL.name_owner.body});
    await search("unfindablequasar");
    expect(await screen.findByText("Nothing matches")).toBeVisible();
    expect(screen.getByRole("combobox",{name:"Memory kind"}).querySelectorAll("option").length).toBeGreaterThan(0);
    expect(screen.queryByRole("button",{name:"Clear"})).toBeNull();
    expect(screen.getByRole("grid",{name:"Memory"}).querySelectorAll(".object-list-row")).toHaveLength(0);
    expect(misses).toEqual([]);
  });
});
