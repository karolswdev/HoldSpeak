// HS-200-13: the recall face against the ratified boards (P5Recall,
// P5RecallPhone, P5RecallQuiet): the current decision accented with its
// rationale, source and Project; the superseded one dimmed and named
// `SUPERSEDED BY DEC 09-07`; the disputed one never accented; the OWED
// row with typed unknowns and ONE verb; the miss; the empty; the failure;
// Carry into brief keeping focus and reading CARRIED; the query resumed.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../../lib/api";
import { openSurfaceOr } from "../../../../desk/shell";
import { RecallFace } from "../RecallFace";
import { displayLine, missLine, searchedToken } from "../model";

vi.mock("../../../../lib/api", async (original) => ({
  ...await original<typeof import("../../../../lib/api")>(),
  apiFetch: vi.fn(),
}));
vi.mock("../../../../desk/shell", async (original) => ({
  ...await original<typeof import("../../../../desk/shell")>(),
  openSurfaceOr: vi.fn(),
}));
vi.mock("../../../../desk/components/MicButton", () => ({
  MicButton: ({ label }: { label: string }) => (
    <button type="button" className="desk-mic" aria-label={label} />
  ),
}));
vi.mock("../../../../desk/surface/SurfaceFooter", () => ({
  SurfaceFooter: ({ receipt }: { receipt?: React.ReactNode }) => <footer>{receipt}</footer>,
}));

const PROJECT = { id: "p-q4", name: "Q4 platform" };
const CURRENT = {
  id: "rec-new", ref: "decision_record:rec-new",
  text: "Freeze window is Sunday 02:00, not Saturday",
  rationale: "Payments cannot drain the queue before 02:00 on a weekday.",
  lifecycle: "active", state: "current", dec_token: "DEC 09-07", decided_at: "2026-09-07T11:00:00",
  axes: ["DECISION", "SUPPORTED", "ACCEPTED"], support: "SUPPORTED", acceptance: "ACCEPTED",
  successor: null, predecessor_id: "rec-old", supersession_reason: null, dispute_reason: null,
  project: PROJECT,
  source: { kind: "meeting", meeting_id: "m-sun", title: "Architecture review", started_at: "2026-09-07T11:00:00",
    offset_seconds: 1860, segment_index: 2, token: "MTG 09-07 · 11:31", scope: "meeting:m-sun?segment=2" },
  carried: false, commitment_ids: [],
};
const SUPERSEDED = {
  ...CURRENT, id: "rec-old", ref: "decision_record:rec-old", text: "Freeze window is Saturday 02:00",
  rationale: "", lifecycle: "superseded", state: "superseded", dec_token: "DEC 09-02",
  axes: ["DECISION", "SUPPORTED", "SUPERSEDED"], acceptance: "SUPERSEDED",
  successor: { id: "rec-new", dec_token: "DEC 09-07", text: CURRENT.text }, predecessor_id: null,
  source: { ...CURRENT.source, meeting_id: "m-sat", token: "MTG 09-02 · 11:31", scope: "meeting:m-sat?segment=2" },
};
const DISPUTED = {
  ...CURRENT, id: "rec-dis", ref: "decision_record:rec-dis", text: "Freeze window is Sunday 03:00",
  lifecycle: "disputed", state: "disputed", axes: ["DECISION", "LINKED", "DISPUTED"], acceptance: "DISPUTED",
  dispute_reason: "Priya disagrees with the window",
};
const OWED = {
  id: "cmt-1", ref: "commitment:cmt-1", action_item_id: "action-1",
  text: "Priya confirms the freeze window", owner: null, owner_token: "OWNER · UNKNOWN",
  due_at: null, due_token: "DUE · UNKNOWN", due_tone: "idle", status: "open",
  unknowns: ["owner", "due"], next_action: "name_owner", project: PROJECT,
  decision_record_id: "rec-new", decision_state: "current",
};

function result(over: Record<string, unknown> = {}) {
  return {
    query: "freeze window", filter: "all", searched_at: "2026-09-07T09:20:00", projects_searched: 4,
    current: [CURRENT], superseded: [SUPERSEDED], disputed: [], owed: [OWED],
    meetings: [], briefs: [], also: [], remembered: 3, ...over,
  };
}

function wire(payload: unknown | (() => unknown)) {
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: { json?: unknown }) => {
    const p = String(path);
    if (p.startsWith("/api/memory/recall")) return typeof payload === "function" ? (payload as () => unknown)() : payload;
    if (p.includes("/carry")) return { id: "carry-1", replayed: false };
    if (p === "/api/follow-through/complete") return { card_id: (init?.json as { card_id: string }).card_id };
    return null;
  });
}

async function search(query = "freeze window") {
  fireEvent.change(screen.getByRole("searchbox", { name: "Search the Desk" }), { target: { value: query } });
  fireEvent.click(screen.getByRole("button", { name: "Search desk memory" }));
  await screen.findByTestId("recall-results");
}

describe("RecallFace (HS-200-13)", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    vi.mocked(openSurfaceOr).mockReset();
    localStorage.clear();
  });
  afterEach(() => localStorage.clear());

  it("the pure tokens", () => {
    expect(displayLine(3)).toBe("3 remembered");
    expect(displayLine(0)).toBe("Nothing matches");
    expect(missLine(4)).toBe("Four projects searched, none holds this");
    expect(missLine(1)).toBe("One project searched, it does not hold this");
    expect(missLine(0)).toBe("Nothing on the desk holds this");
    expect(searchedToken("2026-09-07T09:20:00")).toBe("SEARCHED 09:20");
  });

  /* HS-202-02 — the cold face is no longer a blank field: it asks the hub
     for the desk's RECENT memory on open (03-interaction-walk.md finding
     7). The well, the mic, the five filters and the token are unchanged
     at the first instant, before that read lands; what the read then
     draws is fenced in `recentMemory202.test.tsx`. */
  it("empty: the well, the mic, the five filters and one token; no results region yet", () => {
    wire(result());
    render(<RecallFace />);
    expect(screen.getByTestId("recall-empty-token").textContent).toBe("SEARCH THE DESK");
    expect(screen.queryByTestId("recall-display")).toBeNull();
    expect(screen.queryByTestId("recall-results")).toBeNull();
    expect(screen.getByRole("button", { name: "Dictate into the search" })).toBeTruthy();
    const group = screen.getByRole("group", { name: "Filter the memory" });
    expect(within(group).getAllByRole("button").map((b) => b.textContent)).toEqual(
      ["All", "Decisions", "Commitments", "Briefs", "Meetings"],
    );
    expect(within(group).getByRole("button", { name: "Filter: Decisions" }).getAttribute("aria-pressed")).toBe("false");
    expect(screen.getByRole("button", { name: "Search desk memory" })).toHaveProperty("disabled", true);
  });

  it("recall: the current decision accented with rationale, source, Project and Carry; the superseded one under it, dimmed and named", async () => {
    wire(result());
    render(<RecallFace />);
    await search();

    expect(screen.getByTestId("recall-display").textContent).toBe("3 remembered");
    expect(screen.getByTestId("recall-display").getAttribute("data-accent")).toBe("true");
    expect(screen.getByTestId("recall-ref-token").textContent).toBe("REF · FREEZE WINDOW");
    expect(screen.getByTestId("recall-searched-token").textContent).toBe("SEARCHED 09:20");

    const cards = screen.getAllByTestId("recall-card");
    expect(cards.map((c) => c.getAttribute("data-state"))).toEqual(["current", "superseded"]);
    const current = cards[0];
    expect(within(current).getByTestId("recall-card-title").textContent).toBe(CURRENT.text);
    expect(within(current).getAllByTestId("recall-axis").map((c) => c.textContent)).toEqual(["DECISION", "SUPPORTED", "ACCEPTED"]);
    expect(within(current).getByTestId("recall-rationale").textContent).toBe(CURRENT.rationale);
    expect(within(current).getByTestId("recall-source-token").textContent).toBe("MTG 09-07 · 11:31");
    expect(within(current).getByRole("button", { name: "Open the Project: Q4 platform" })).toBeTruthy();
    expect(within(current).getByRole("group", { name: "Project" })).toBeTruthy();
    expect(within(current).getByRole("button", { name: "Carry into brief" }).className).toContain("btn--primary");

    const superseded = cards[1];
    expect(within(superseded).getByTestId("recall-superseded-by").textContent).toBe("SUPERSEDED BY DEC 09-07");
    expect(within(superseded).getAllByTestId("recall-axis").map((c) => c.textContent)).toContain("SUPERSEDED");
    expect(within(superseded).queryByRole("button", { name: "Carry into brief" })).toBeNull();
    expect(within(superseded).getByRole("button", { name: "Open source: MTG 09-02" })).toBeTruthy();

    // ONE filled primary on the whole face.
    expect(document.querySelectorAll(".btn--primary")).toHaveLength(1);
    // Every button is the library Button or the mic.
    const raw = Array.from(document.querySelectorAll("button")).filter(
      (b) => !b.className.includes("btn") && !b.className.includes("desk-mic"),
    );
    expect(raw).toEqual([]);
    // Section captions carry their counts; no zero is drawn.
    expect(screen.getByText("CURRENT 1")).toBeTruthy();
    expect(screen.getByText("SUPERSEDED 1")).toBeTruthy();
    expect(screen.getByText("OWED 1")).toBeTruthy();
    expect(screen.queryByText(/DISPUTED 0|MEETINGS 0|ALSO 0/)).toBeNull();
  });

  it("Open source opens the transcript at the moment; the Project button opens the Room", async () => {
    wire(result());
    render(<RecallFace />);
    await search();
    fireEvent.click(screen.getByRole("button", { name: "Open source: MTG 09-07" }));
    expect(openSurfaceOr).toHaveBeenCalledWith("review-meetings", "/meetings", "meeting:m-sun?segment=2");
    fireEvent.click(screen.getAllByRole("button", { name: "Open the Project: Q4 platform" })[0]);
    expect(openSurfaceOr).toHaveBeenCalledWith("project-room", "/projects", "project:p-q4");
  });

  it("a disputed decision is drawn under DISPUTED, never accented, never carried", async () => {
    wire(result({ current: [], disputed: [DISPUTED], remembered: 3 }));
    render(<RecallFace />);
    await search();
    const card = screen.getAllByTestId("recall-card").find((c) => c.getAttribute("data-state") === "disputed")!;
    expect(card).toBeTruthy();
    expect(within(card).getAllByTestId("recall-axis").map((c) => c.textContent)).toContain("DISPUTED");
    expect(within(card).getByTestId("recall-dispute-reason").textContent).toBe("Priya disagrees with the window");
    expect(within(card).queryByRole("button", { name: "Carry into brief" })).toBeNull();
    expect(document.querySelectorAll(".btn--primary")).toHaveLength(0);
    expect(screen.getByText("DISPUTED 1")).toBeTruthy();
  });

  it("Carry into brief posts the carry by reference, reads CARRIED and keeps focus", async () => {
    wire(result());
    render(<RecallFace />);
    await search();
    const carry = screen.getByRole("button", { name: "Carry into brief" });
    carry.focus();
    fireEvent.click(carry);
    await waitFor(() => expect(screen.getByTestId("recall-carry").textContent).toBe("CARRIED"));
    expect(apiFetch).toHaveBeenCalledWith("/api/decision-records/rec-new/carry", { method: "POST", json: { project_id: "p-q4" } });
    expect(document.activeElement).toBe(screen.getByTestId("recall-carry"));
    expect(screen.getByTestId("recall-carry").getAttribute("aria-pressed")).toBe("true");
    // A second press replays nothing new.
    fireEvent.click(screen.getByTestId("recall-carry"));
    expect(vi.mocked(apiFetch).mock.calls.filter(([p]) => String(p).includes("/carry"))).toHaveLength(1);
  });

  it("OWED: typed unknowns and ONE verb; Name an owner unfolds a well and saves through the follow-through verb", async () => {
    let owed: Record<string, unknown> = OWED;
    wire(() => result({ owed: [owed] }));
    render(<RecallFace />);
    await search();
    const row = screen.getByTestId("recall-owed-row");
    expect(within(row).getByTestId("recall-due-token").textContent).toBe("DUE · UNKNOWN");
    expect(within(row).getByTestId("recall-owner-token").textContent).toBe("OWNER · UNKNOWN");
    expect(within(row).getAllByRole("button").map((b) => b.getAttribute("aria-label"))).toEqual([
      "Open the Project: Q4 platform", "Name an owner: Priya confirms the freeze window",
    ]);
    expect(within(row).queryByRole("button", { name: /Mark done/ })).toBeNull();

    fireEvent.click(within(row).getByRole("button", { name: /Name an owner/ }));
    const well = await screen.findByTestId("recall-owed-well");
    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.change(within(well).getByRole("textbox", { name: "Owner" }), { target: { value: "Priya" } });
    owed = { ...OWED, owner: "Priya", owner_token: "OWNER · PRIYA", unknowns: ["due"], next_action: "set_date" };
    fireEvent.click(within(well).getByRole("button", { name: /Save owner/ }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST", json: { card_id: "action-1", verb: "delegate", payload: { to: "Priya" } },
    }));
    await waitFor(() => expect(screen.getByTestId("recall-owed-verb").textContent).toBe("Set a date"));
    expect(screen.queryByTestId("recall-owner-token")).toBeNull();
  });

  it("Mark done is the verb only when owner and date are known, and it is the explicit act", async () => {
    const known = { ...OWED, owner: "Priya", owner_token: "OWNER · PRIYA", due_at: "2026-09-07",
      due_token: "DUE TODAY", due_tone: "warn", unknowns: [], next_action: "mark_done" };
    let owed: unknown[] = [known];
    wire(() => result({ owed }));
    render(<RecallFace />);
    await search();
    const row = screen.getByTestId("recall-owed-row");
    expect(within(row).getByTestId("recall-due-token").textContent).toBe("DUE TODAY");
    expect(within(row).queryByTestId("recall-owner-token")).toBeNull();
    owed = [];
    fireEvent.click(within(row).getByRole("button", { name: "Mark done: Priya confirms the freeze window" }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST", json: { card_id: "action-1", verb: "done", payload: {} },
    }));
    await waitFor(() => expect(screen.queryByTestId("recall-owed-row")).toBeNull());
  });

  it("the miss: Nothing matches, one true line, the filters kept, no Clear", async () => {
    wire(result({ current: [], superseded: [], owed: [], remembered: 0 }));
    render(<RecallFace />);
    await search("unfindablequasar");
    expect(screen.getByTestId("recall-display").textContent).toBe("Nothing matches");
    expect(screen.getByTestId("recall-display").getAttribute("data-accent")).toBeNull();
    expect(screen.getByTestId("recall-miss").textContent).toContain("Four projects searched, none holds this");
    expect(screen.getByRole("group", { name: "Filter the memory" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Clear/ })).toBeNull();
    expect(screen.queryByTestId("recall-card")).toBeNull();
  });

  it("failed: CANT SEARCH with the reason and Retry; the query stays in the well", async () => {
    // HS-202-02: the face opens with a RECENT read, so the refusal is
    // wired for every call until the Retry re-wires a good one.
    vi.mocked(apiFetch).mockRejectedValue(new Error("memory index locked"));
    render(<RecallFace />);
    fireEvent.change(screen.getByRole("searchbox", { name: "Search the Desk" }), { target: { value: "freeze window" } });
    fireEvent.click(screen.getByRole("button", { name: "Search desk memory" }));
    expect((await screen.findByTestId("recall-failed-token")).textContent).toBe("CANT SEARCH · MEMORY INDEX LOCKED");
    expect((screen.getByRole("searchbox", { name: "Search the Desk" }) as HTMLInputElement).value).toBe("freeze window");
    wire(result());
    fireEvent.click(screen.getByRole("button", { name: "Retry the search" }));
    expect(await screen.findByTestId("recall-results")).toBeTruthy();
  });

  it("a filter re-runs the search with its value; Escape clears the well and keeps the last results", async () => {
    wire(result());
    render(<RecallFace />);
    await search();
    fireEvent.click(screen.getByRole("button", { name: "Filter: Commitments" }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/memory/recall?query=freeze+window&filter=commitments"));
    const box = screen.getByRole("searchbox", { name: "Search the Desk" }) as HTMLInputElement;
    fireEvent.keyDown(box, { key: "Escape" });
    expect(box.value).toBe("");
    expect(screen.getByTestId("recall-results")).toBeTruthy();
  });

  it("opened with a sentence (HS-200-11 `q:` scope): prefilled in the well and searched", async () => {
    localStorage.setItem("hs.desk-memory.recall.v1", JSON.stringify({ query: "freeze window", filter: "decisions" }));
    wire(result({ query: "Sprint velocity is 40 points", remembered: 0, current: [], superseded: [], owed: [] }));
    render(<RecallFace initialQuery="Sprint velocity is 40 points" />);
    await screen.findByTestId("recall-results");
    expect(apiFetch).toHaveBeenCalledWith("/api/memory/recall?query=Sprint+velocity+is+40+points&filter=all");
    const box = screen.getByRole("searchbox", { name: "Search the Desk" }) as HTMLInputElement;
    expect(box.value).toBe("Sprint velocity is 40 points");
    expect(box.closest('[data-testid="desk-memory-body"]')).not.toBeNull();
  });

  it("resumed: the query and its filter survive a restart", async () => {
    localStorage.setItem("hs.desk-memory.recall.v1", JSON.stringify({ query: "freeze window", filter: "decisions" }));
    wire(result({ filter: "decisions", owed: [] , remembered: 2 }));
    render(<RecallFace />);
    await screen.findByTestId("recall-results");
    expect(apiFetch).toHaveBeenCalledWith("/api/memory/recall?query=freeze+window&filter=decisions");
    expect((screen.getByRole("searchbox", { name: "Search the Desk" }) as HTMLInputElement).value).toBe("freeze window");
    expect(screen.getByRole("button", { name: "Filter: Decisions" }).getAttribute("aria-pressed")).toBe("true");
  });
});
