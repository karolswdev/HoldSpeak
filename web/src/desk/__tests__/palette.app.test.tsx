/** The palette (⌘K), app file: what the browser walks of the palette proved,
 * moved here by the test diet (2026-10-11).
 *
 * Most palette facts already sit in paletteMemory.test.tsx,
 * paletteTwoLine.test.tsx and palette.philo1314.test.tsx; this file holds
 * only the legs those files did not assert. Real store, real palette, real
 * opener, real desk read (loadAll); the hub transport is the double, and
 * each wire shape below is the hub's own answer, copied from a run of the
 * real routes on an isolated hub (2026-10-11). */
import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
const openProjectRoom = vi.fn();
const openedSurfaces = vi.hoisted(() => ({ calls: [] as Array<[string, string | undefined]> }));
vi.mock("../shell", async () => {
  const actual = await vi.importActual<typeof import("../shell")>("../shell");
  return {
    ...actual,
    openSurface: () => true,
    openSurfaceOr: (key: string, _href: string, scope?: string) => { openedSurfaces.calls.push([key, scope]); },
    openProjectRoom: (...args: unknown[]) => openProjectRoom(...args),
  };
});
vi.mock("../setup", () => ({ loadSetup: vi.fn(() => Promise.resolve(null)) }));

import { EMPTY_ITEMS, __resetHeldObjects, fromWireMeeting, loadAll } from "../api";
import { ApiError } from "../../lib/api";
import type { Meeting, Note } from "../../lib/primitives";
import { useDesk } from "../store";
import { useNamePrompt, usePalette } from "../chromeState";
import { DeskToolShelf, MEMORY_DEBOUNCE_MS } from "../components/DeskToolShelf";
import { objectByRef } from "../world";
import { Pullout } from "../components/Pullout";
import enterHub from "./fixtures/palette-enter/recorded.json";
import { wireDayClock } from "../surface/format";

/* The hub's list row for a meeting whose speakers are Dana Okafor and Me
 * (GET /api/meetings?limit=24, `db.meetings.save_meeting`, intel off). */
const VENDOR_ROW = {
  id: "m-vendor", started_at: "2026-10-11T04:00:00", ended_at: "2026-10-11T04:30:00",
  title: "Vendor roadmap review", duration_seconds: 1800.0, segment_count: 2, action_item_count: 0, tags: [],
  intel_status: "disabled", intel_status_detail: null, intel_model_host: null, intel_duration_s: null,
  capture_status: "finalized", capture_failure: null, capture_checkpoint_seconds: 0.0,
  transcription_status: "active", transcription_status_detail: null, provenance: "desktop",
  calendar_event_id: null, attendees: ["Dana Okafor", "Me"], parked: false, transcriptWords: 9, unclearSpans: 0,
  needs_you_count: 0, has_summary: false,
  planned_route: { status: "unavailable", reason_code: "no assignment", selection_hash: null, legs: [] },
  run_receipt: null, last_refusal: null, intel_job: null,
};

/* The hub's read of one meeting by id (GET /api/meetings/m-old-00). */
const OLD_MEETING = {
  id: "m-old-00", parked: false, started_at: "2026-08-30T09:00:00", ended_at: "2026-08-30T09:20:00",
  duration: 1200.0, formatted_duration: "20:00", title: "Finance migration sync", tags: [],
  segments: [{ text: "The numbat migration waits for finance.", speaker: "Me", speaker_id: null,
    start_time: 1.0, end_time: 3.0, is_bookmarked: false, device_id: null }],
  bookmarks: [], intel: null,
  intel_status: { state: "disabled", detail: null, requested_at: null, completed_at: null },
  mic_label: "Me", remote_label: "Remote", web_url: null, capture_status: "finalized", capture_failure: null,
  transcription_status: "active", transcription_status_detail: null, capture_checkpoint_at: null,
  capture_checkpoint_seconds: 0.0, provenance: "desktop", calendar_event_id: null, transcriptWords: 6,
  unclearSpans: 0, sync_modified_at: "2026-10-11T09:26:30.286355", devices: [],
  planned_route: { status: "unavailable", reason_code: "no assignment", selection_hash: null, legs: [] },
  run_receipt: null, last_refusal: null, intel_job: null, intel_model_host: null,
};

/* The hub's memory hit for `numbat` (GET /api/memory/search). */
const NUMBAT_HIT = {
  kind: "meeting", source_ref: "meeting:m-old-00", title: "Finance migration sync",
  snippet: "The <mark>numbat</mark> migration waits for finance.", occurred_at: "2026-08-30T15:00:00+00:00",
  project_id: null, bm25: -0.4897364925095966, normalized_score: 1.0, kind_rank: 1, rank: 1,
  retrieval_origin: "lexical", related_to: null, relationship: null, graph_score: 0.0,
};

let routes: Record<string, () => unknown> = {};

beforeEach(() => {
  __resetHeldObjects();
  localStorage.clear();
  usePalette.setState({ open: false });
  useNamePrompt.setState({ prompt: null });
  routes = {};
  apiFetch.mockReset();
  openProjectRoom.mockReset();
  openedSurfaces.calls = [];
  apiFetch.mockImplementation((path: string) => {
    const hit = routes[path] ?? routes[path.split("?")[0]];
    return Promise.resolve(hit ? hit() : {});
  });
  useDesk.setState({
    items: { ...EMPTY_ITEMS },
    projects: [],
    inferenceTargets: [],
    models: [],
    setup: null,
    selectedIds: [],
    panelOrder: [],
    panelMin: [],
    openPullout: vi.fn(),
    refresh: vi.fn().mockResolvedValue(undefined),
    openToolInspector: vi.fn(),
    diveInto: vi.fn(),
    focusPanel: vi.fn(),
    restorePanel: vi.fn(),
  });
});

async function settle(ms = 0) {
  await act(async () => { await new Promise((r) => setTimeout(r, ms)); });
}

async function deck() {
  render(<MemoryRouter><DeskToolShelf /></MemoryRouter>);
  fireEvent.click(screen.getByRole("button", { name: /Search/ }));
  await settle();
  return screen.getByRole("combobox", { name: "Search tools and Desk items" });
}

async function type(input: HTMLElement, q: string, wait = 0) {
  fireEvent.change(input, { target: { value: q } });
  await settle(wait);
}

const rows = () => screen.queryAllByRole("option");
const top = () => rows().find((o) => o.className.includes("is-selected"));

describe("the palette's Close", () => {
  it("closes a typed search, returns focus to Search, and reopens with an empty query", async () => {
    const input = await deck();
    await type(input, "Vendor");
    const launcher = screen.getByRole("button", { name: /^Search/ });
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(usePalette.getState().open).toBe(false);
    expect(screen.queryByRole("region", { name: "Tools and Desk search" })).toBeNull();
    expect(document.activeElement).toBe(launcher);
    expect(useDesk.getState().openPullout).not.toHaveBeenCalled();
    fireEvent.click(launcher);
    expect((screen.getByRole("combobox", { name: "Search tools and Desk items" }) as HTMLInputElement).value).toBe("");
  });

  it("Enter on Close activates Close, runs no selected result, and restores launcher focus", async () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, meeting: [fromWireMeeting(VENDOR_ROW) as Meeting] } });
    const input = await deck();
    await type(input, "Vendor");
    expect(top()?.id).toBe("desk-palette-option-meeting:m-vendor");
    const launcher = screen.getByRole("button", { name: /^Search/ });
    screen.getByRole("button", { name: "Close" }).focus();
    await userEvent.keyboard("{Enter}");
    expect(usePalette.getState().open).toBe(false);
    expect(useDesk.getState().openPullout).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(launcher);
  });
});

describe("the palette finds the right row and opens it", () => {
  it("a word inside one of three thoughts lists that thought only", async () => {
    // replaces: tests/e2e/test_philo13_14_palette_glass.py::TestPaletteKnowsHisWeek::test_the_palette_knows_his_week_and_does_verbs (leg 3)
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [
      { kind: "note", id: "n-a", title: "Thought", bodyMarkdown: "Lunch on Friday with the team.", tags: [], createdAt: "" } as Note,
      { kind: "note", id: "n-b", title: "Thought", bodyMarkdown: "Ask Jordan about the Kafka offsets before the cutover.", tags: [], createdAt: "" } as Note,
      { kind: "note", id: "n-c", title: "Thought", bodyMarkdown: "Book the offsite room.", tags: [], createdAt: "" } as Note,
    ] } });
    const input = await deck();
    await type(input, "kafka");
    const ids = rows().map((o) => o.id.replace("desk-palette-option-", ""));
    expect(ids[0]).toBe("note:n-b");
    expect(ids).not.toContain("note:n-a");
    expect(ids).not.toContain("note:n-c");
    fireEvent.keyDown(input, { key: "Enter" });
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("note:n-b");
  });

  it("an attendee's name finds the meeting from the hub's list row, top, and one press opens it", async () => {
    // replaces: tests/e2e/test_philo13_14_palette_glass.py::TestPaletteKnowsHisWeek::test_a_meeting_is_found_by_an_attendee
    const meeting = fromWireMeeting(VENDOR_ROW) as Meeting;
    // The premise: her name is in no field of the row but `attendees`.
    const { attendees: _a, ...rest } = VENDOR_ROW;
    expect(JSON.stringify(rest).toLowerCase()).not.toContain("dana");
    useDesk.setState({ items: { ...EMPTY_ITEMS, meeting: [meeting] } });
    const input = await deck();
    await type(input, "Dana");
    const first = top();
    expect(first?.id).toBe("desk-palette-option-meeting:m-vendor");
    expect(first?.textContent).toContain("Vendor roadmap review");
    expect(first?.textContent).toContain("MEETING");
    fireEvent.keyDown(input, { key: "Enter" });
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("meeting:m-vendor");
  });

  it("same-title, same-time meetings show distinct attendees and open their exact identities", async () => {
    // Controlled identity/attendee variants of the recorded list row above.
    const other = { ...VENDOR_ROW, id: "m-vendor-other", attendees: ["Priya Shah", "Omar Haddad"] };
    useDesk.setState({ items: { ...EMPTY_ITEMS,
      meeting: [fromWireMeeting(VENDOR_ROW) as Meeting, fromWireMeeting(other) as Meeting],
      note: [{ kind: "note", id: VENDOR_ROW.id, title: VENDOR_ROW.title, bodyMarkdown: "", tags: [], createdAt: "" } as Note],
    } });
    let input = await deck();
    await type(input, "Vendor");
    const meetingRows = rows().filter((row) => row.id.startsWith("desk-palette-option-meeting:"));
    expect(meetingRows.map((row) => row.id)).toEqual([
      "desk-palette-option-meeting:m-vendor", "desk-palette-option-meeting:m-vendor-other",
    ]);
    expect(meetingRows.map((row) => row.querySelector(".desk-deck-title")?.textContent))
      .toEqual([VENDOR_ROW.title, VENDOR_ROW.title]);
    expect(meetingRows.map((row) => row.querySelector(".desk-deck-meeting-meta")?.textContent))
      .toEqual([
        `${wireDayClock(VENDOR_ROW.started_at)} · Dana Okafor, Me`,
        `${wireDayClock(VENDOR_ROW.started_at)} · Priya Shah, Omar Haddad`,
      ]);
    const note = document.getElementById("desk-palette-option-note:m-vendor");
    expect(note).toBeTruthy();
    expect(note?.querySelector(".desk-deck-meeting-meta")).toBeNull();
    fireEvent.click(meetingRows[0]);
    expect(useDesk.getState().openPullout).toHaveBeenLastCalledWith("meeting:m-vendor");
    fireEvent.click(screen.getByRole("button", { name: /Search/ }));
    input = screen.getByRole("combobox", { name: "Search tools and Desk items" });
    await type(input, "Vendor");
    fireEvent.click(document.getElementById("desk-palette-option-meeting:m-vendor-other")!);
    expect(useDesk.getState().openPullout).toHaveBeenLastCalledWith("meeting:m-vendor-other");
  });

  it("a meeting with no valid time or attendee names adds no empty metadata line", async () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, meeting: [
      fromWireMeeting({ ...VENDOR_ROW, started_at: "invalid", attendees: ["", " "] }) as Meeting,
    ] } });
    const input = await deck();
    await type(input, "Vendor");
    const meeting = document.getElementById("desk-palette-option-meeting:m-vendor");
    expect(meeting).toBeTruthy();
    expect(meeting?.querySelector(".desk-deck-meeting-meta")).toBeNull();
    expect(meeting?.textContent).not.toContain("invalid");
  });

  it("a meeting older than the desk's list opens from its MEMORY row, read by id first", async () => {
    // replaces: tests/e2e/test_palette_memory_glass.py::TestPaletteFindsAWordInsideAMeeting::test_a_thing_older_than_its_desk_list_opens_from_its_memory_row[numbat-memory:meeting:m-old-00-...]
    routes["/api/memory/search"] = () => ({ hits: [NUMBAT_HIT] });
    routes["/api/meetings?limit=24"] = () => ({ meetings: [VENDOR_ROW] });   // the list does not hold it
    routes["/api/meetings/m-old-00"] = () => OLD_MEETING;
    const order: string[] = [];
    const refresh = vi.fn(async () => {
      order.push("refresh");
      const { loadAll } = await import("../api");
      useDesk.setState({ items: (await loadAll()).items });
    });
    useDesk.setState({ refresh, openPullout: vi.fn(() => { order.push("open"); }) });
    const input = await deck();
    await type(input, "numbat", MEMORY_DEBOUNCE_MS + 60);
    fireEvent.click(screen.getByRole("option", { name: /Finance migration sync/ }));
    await vi.waitFor(() => expect(openedSurfaces.calls).toContainEqual([
      "review-meetings", "meeting:m-old-00",
    ]));
    expect(order).toEqual(["refresh"]);
    const held = useDesk.getState().items.meeting.find((m) => m.id === "m-old-00");
    // The window draws the object's own words.
    expect(held?.segments?.map((s) => s.text)).toEqual(["The numbat migration waits for finance."]);
    expect(apiFetch.mock.calls.map(([p]) => p)).toContain("/api/meetings/m-old-00");
  });
});

/* ── HS-171-07: the PROJECTS rows (the client's limit, filter and verb) ──
 * The rows are the desk store's projects; the hub's needs-you read answers
 * nothing here (no badge), so these legs are the palette's own logic
 * (DeskToolShelf.tsx: the PROJECTS rows and the section limit of 10). The
 * hub's badge and order are oneNumberFaces.test.tsx's (the real producers). */
describe("the palette's PROJECTS rows", () => {
  const ROOMS = Array.from({ length: 12 }, (_, i) => ({
    id: `proj-${String(i).padStart(2, "0")}`,
    name: `Room ${String(i).padStart(2, "0")}`,
  }));
  const projectRows = () => rows().filter((o) => o.id.startsWith("desk-palette-option-project.open."));

  it("twelve Rooms draw ten rows", async () => {
    // replaces: tests/e2e/test_hs171_command_deck_glass.py::test_command_deck_cap_1440
    useDesk.setState({ projects: ROOMS as never });
    await deck();
    expect(projectRows()).toHaveLength(10);
  });

  it("a Room's name filters the PROJECTS rows to that Room", async () => {
    // replaces: tests/e2e/test_hs171_command_deck_glass.py::test_command_deck_search_1440
    useDesk.setState({ projects: [
      { id: "p-q4", name: "Q4 Platform" }, { id: "p-gov", name: "Governance" }, { id: "p-data", name: "Data Platform" },
    ] as never });
    const input = await deck();
    expect(projectRows()).toHaveLength(3);
    await type(input, "Governance");
    expect(projectRows().map((o) => o.textContent)).toEqual([expect.stringContaining("Open Governance")]);
    await type(input, "");
    expect(projectRows()).toHaveLength(3);
  });

  it("a press on a Room row opens that Room and closes the palette", async () => {
    // replaces: tests/e2e/test_hs171_command_deck_glass.py::test_command_deck_projects_1440 (the press leg; the 393 twin is the same DOM)
    useDesk.setState({ projects: [{ id: "p-q4", name: "Q4 Platform" }] as never });
    await deck();
    fireEvent.click(screen.getByRole("option", { name: /Open Q4 Platform/ }));
    expect(openProjectRoom).toHaveBeenCalledWith("p-q4");
    expect(usePalette.getState().open).toBe(false);
    expect(screen.queryByRole("combobox", { name: "Search tools and Desk items" })).toBeNull();
  });
});

/* ── Enter on the first row opens THAT note (A-apps row 41, 2026-10-03) ──
 * The hub's answers are recorded by scripts/record_chrome_palette.py (one
 * boot: the note made by POST /api/notes, the reads before it is opened, the
 * window's open (POST /api/thoughts/open-note), the reads after, and a second
 * open). The palette opens the note the first row names; the window the desk
 * draws for that ref is the one note window (the sticky) OF THAT NOTE
 * (Betterment Q8). The open is the only write, and it makes no new note. */
describe("Enter on the first row opens the note it names", () => {
  const ref = `note:${enterHub.note_id}`;
  const writes = () => apiFetch.mock.calls
    .filter(([, init]) => ((init as RequestInit | undefined)?.method ?? "GET").toUpperCase() !== "GET")
    .map(([path]) => String(path));
  const unrouted: string[] = [];

  type Read = { status: number; body: unknown };
  const notesOf = (table: Record<string, Read>) => (table["/api/notes"].body as { notes: { id: string }[] }).notes.map((n) => n.id);

  /** The recorded reads, as the hub answered them (a refusal is replayed as
   * that refusal); a read the recorder did not make fails the test. */
  async function replay(table: Record<string, Read>) {
    unrouted.length = 0;
    apiFetch.mockImplementation((path: string, init?: RequestInit) => {
      const method = (init?.method ?? "GET").toUpperCase();
      // Betterment Q8: the window opens the note (the hub adopts a plain note
      // the first time; the second open gives the same thought).
      if (method === "POST" && path === "/api/thoughts/open-note") {
        const opened = apiFetch.mock.calls.filter(([p, i]) => p === path && ((i as RequestInit | undefined)?.method ?? "").toUpperCase() === "POST").length;
        return Promise.resolve(structuredClone(opened > 1 ? enterHub.reopen.answer : enterHub.open.answer));
      }
      // The developed Thought window now reads the canonical Engines
      // assignment while it paints its run line. This read is part of the
      // open, and carries no write or new object.
      if (method === "GET" && path === "/api/inference/assignments") {
        return Promise.resolve({ rows: [], task_overrides: [] });
      }
      const hit = method === "GET" ? table[path] ?? table[path.split("?")[0]] : undefined;
      if (!hit) {
        unrouted.push(`${method} ${path}`);
        return Promise.reject(new Error(`unrecorded ${method} ${path}`));
      }
      return hit.status < 300
        ? Promise.resolve(structuredClone(hit.body))
        : Promise.reject(new ApiError(hit.status, `HTTP ${hit.status}`, structuredClone(hit.body)));
    });
    // The desk's own read of the notes (the real loader, the recorded list).
    const { items } = await loadAll();
    useDesk.setState({ items });
    apiFetch.mockClear();
  }

  /** ⌘K, `ledger`, then Enter (1440) or a press on the first row (393). */
  async function pressEnterOnLedger(gesture: "enter" | "tap" = "enter") {
    const input = await deck();
    await type(input, "ledger");
    const first = rows()[0];
    expect(first?.id).toBe(`desk-palette-option-${ref}`);
    expect(first?.getAttribute("aria-selected")).toBe("true");
    expect(first?.textContent).toContain(enterHub.title);
    if (gesture === "enter") fireEvent.keyDown(input, { key: "Enter" });
    else fireEvent.click(first!);
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith(ref);
  }

  async function drawWindow() {
    const o = objectByRef(useDesk.getState().items, ref);
    expect(o, "the desk holds the note the row names").toBeTruthy();
    useDesk.setState({ profiles: [], closePullout: vi.fn() });
    const view = render(<MemoryRouter><Pullout o={o!} pulloutId={ref} /></MemoryRouter>);
    await settle(50);
    return view;
  }

  it("a plain note: Enter opens it in the one note window (the sticky); no new note is made", async () => {
    // replaces: tests/e2e/test_palette_enter_opens_the_note_glass.py::TestEnterOpensTheFirstRow::test_enter_opens_the_note_the_first_row_names (part 1, 1440 Enter; the 393 tap runs the same row)
    await replay({ ...enterHub.before, ...enterHub.after, "/api/notes": enterHub.before["/api/notes"] });
    await pressEnterOnLedger();
    const { container } = await drawWindow();
    await vi.waitFor(() => expect(container.querySelector(".thought-workspace-window"), "the sticky is drawn").toBeTruthy());
    expect(container.querySelectorAll(".thought-workspace-window")).toHaveLength(1);
    expect(screen.queryByRole("button", { name: "Develop this thought" })).toBeNull();
    const frame = container.querySelector(`[id="pullout:${ref}"]`);
    expect(frame?.getAttribute("aria-label")).toBe(enterHub.title);
    expect(apiFetch.mock.calls.find(([p]) => p === "/api/thoughts/open-note")?.[1]).toMatchObject({ method: "POST", json: enterHub.open.request });
    expect(unrouted).toEqual([]);
    expect(writes()).toEqual(["/api/thoughts/open-note"]);
  });

  it("Betterment AG4: the selected note offers Hand to agent; one press opens the sheet on it and closes Search", async () => {
    const { useAgentHand } = await import("../agentHand");
    useAgentHand.setState({ origin: null });
    await replay(enterHub.before);
    const input = await deck();
    await type(input, "ledger");
    expect(rows()[0]?.getAttribute("aria-selected")).toBe("true");
    // One Hand to agent, on the selected row only.
    expect(screen.getAllByTestId("palette-hand")).toHaveLength(1);
    fireEvent.click(screen.getByTestId("palette-hand"));
    expect(useAgentHand.getState().origin).toEqual({ kind: "note", id: enterHub.note_id, title: enterHub.title });
    expect(usePalette.getState().open).toBe(false);
    expect(useDesk.getState().openPullout).not.toHaveBeenCalled();
    expect(writes()).toEqual([]);
  });

  it("the phone's press on the first row opens the same note, and writes nothing", async () => {
    // replaces: tests/e2e/test_palette_enter_opens_the_note_glass.py::TestEnterOpensTheFirstRow::test_enter_opens_the_note_the_first_row_names[393] (part 1, the tap)
    await replay(enterHub.before);
    await pressEnterOnLedger("tap");
    expect(unrouted).toEqual([]);
    expect(writes()).toEqual([]);
  });

  it("an opened note: the same Enter opens the sticky OF THAT NOTE; no new note is made", async () => {
    // replaces: tests/e2e/test_palette_enter_opens_the_note_glass.py::TestEnterOpensTheFirstRow::test_enter_opens_the_note_the_first_row_names (part 3, after Develop this thought)
    await replay(enterHub.after);
    // The premise, from the hub's own reads: the open made no second note.
    expect(notesOf(enterHub.after)).toEqual(notesOf(enterHub.before));
    await pressEnterOnLedger();
    const { container } = await drawWindow();
    const thought = await vi.waitFor(() => {
      const node = container.querySelector(".thought-workspace-window");
      expect(node, "the Thought window is drawn").toBeTruthy();
      return node as HTMLElement;
    });
    expect(container.querySelectorAll(".thought-workspace-window")).toHaveLength(1);
    const named = container.querySelector(`[id="pullout:${ref}"]`);
    expect(named?.getAttribute("aria-label")).toBe(enterHub.title);
    expect(screen.queryByRole("button", { name: "Develop this thought" })).toBeNull();
    expect(unrouted).toEqual([]);
    expect(writes()).toEqual(["/api/thoughts/open-note"]);
  });
});

// ── Betterment shell S0: Search shows only rows that run (UX-CANON A.11) ──
import { announceLauncher, retractLauncher } from "../components/window/launcherRegistry";

describe("S0: Search lists no dead row", () => {
  it("\"agents\" lists no verb that waits for a selection", async () => {
    const input = await deck();
    await type(input, "agents");
    const opts = rows();
    expect(opts.length).toBeGreaterThan(0);
    for (const o of opts) {
      expect(o.textContent).not.toContain("Select an object");
      expect(o.getAttribute("aria-disabled")).not.toBe("true");
    }
    expect(opts.map((o) => o.id)).not.toContain("desk-palette-option-object.hand-to-agent");
  });

  // Betterment shell S1 (supersedes the S0 Terminals rule): the launchers
  // are builder rows, listed only when Builder tools is on.
  it("the launchers (Delivery, Terminals) are rows only when Builder tools is on", async () => {
    announceLauncher({ id: "panes", label: "Terminals", glyph: "⧉", open: false, activate: () => {} });
    announceLauncher({ id: "delivery-board", label: "Delivery", glyph: "▤", open: false, activate: () => {} });
    try {
      const input = await deck();
      await type(input, "terminals");
      expect(rows().map((o) => o.id)).not.toContain("desk-palette-option-drawer:panes");
      await type(input, "delivery");
      expect(rows().map((o) => o.id)).not.toContain("desk-palette-option-drawer:delivery-board");
      act(() => useBuilderTools.getState().setOn(true));
      await type(input, "terminals");
      expect(rows().map((o) => o.id)).toContain("desk-palette-option-drawer:panes");
      await type(input, "delivery");
      expect(rows().map((o) => o.id)).toContain("desk-palette-option-drawer:delivery-board");
    } finally {
      useBuilderTools.getState().setOn(false);
      retractLauncher("panes");
      retractLauncher("delivery-board");
    }
  });
});

// ── Betterment shell S1: Search finds every app; builder rows are gated ──
import { useBuilderTools } from "../builderTools";

describe("S1: Search lists Today, People and Components as apps", () => {
  const ids = () => rows().map((o) => o.id.replace("desk-palette-option-", ""));
  it("\"people\" finds People as an App, first, and one press opens it", async () => {
    const input = await deck();
    await type(input, "people");
    expect(ids()[0]).toBe("desk.open-people");
    expect(rows()[0].textContent).toContain("People");
    expect(ids()).not.toContain("go.open-people");
    fireEvent.keyDown(input, { key: "Enter" });
    expect(openedSurfaces.calls).toContainEqual(["open-people", undefined]);
  });

  it("\"today\" finds Today as an App", async () => {
    const input = await deck();
    await type(input, "today");
    const today = rows().find((o) => o.id === "desk-palette-option-desk.open-intelligence");
    expect(today?.textContent).toContain("Today");
  });

  it("builder apps and Refresh from hub are listed only when Builder tools is on", async () => {
    try {
      const input = await deck();
      for (const q of ["components", "activity", "calendar snapshot", "refresh"]) {
        await type(input, q);
        expect(ids(), q).not.toEqual(expect.arrayContaining(["go.design-components"]));
        expect(ids(), q).not.toContain("go.inspect-activity");
        expect(ids(), q).not.toContain("go.review-calendar-snapshot");
        expect(ids(), q).not.toContain("desk.refresh");
      }
      act(() => useBuilderTools.getState().setOn(true));
      await type(input, "components");
      expect(ids()).toContain("go.design-components");
      await type(input, "calendar snapshot");
      expect(ids()).toContain("go.review-calendar-snapshot");
      await type(input, "refresh");
      expect(ids()).toContain("desk.refresh");
    } finally {
      useBuilderTools.getState().setOn(false);
    }
  });
});

/* ── Betterment AG1: one name ──────────────────────────────────────── */

import { fromWireNote, fromWireRecipe } from "../api";
import type { Persona } from "../../lib/primitives";
import { hubWire } from "./wire/hubWire";

describe("Betterment AG1: Search \"agent\" finds Agents and Hand to agent, never the thread modes", () => {
  it("a saved persona is a Mode; the Agents app and Hand to agent (on the selected note) lead", async () => {
    // The hub's own recipe list (the product seed: Chase, Desk, Draft, ...).
    const recipes = hubWire<{ recipes: unknown[] }>("recipes.seed").wire.recipes
      .map((r) => fromWireRecipe(r)).filter((r): r is Persona => r !== null);
    expect(recipes.length).toBeGreaterThanOrEqual(5);
    const note = fromWireNote({ id: "note_cutover", title: "Cutover checklist", body_markdown: "", tags: [] }) as Note;
    useDesk.setState({ items: { ...EMPTY_ITEMS, recipe: recipes, note: [note] }, selectedIds: ["note:note_cutover"] });
    const input = await deck();
    await type(input, "agent");
    const shown = rows().map((o) => o.textContent ?? "");
    expect(shown.some((t) => /^Agents/.test(t.replace(/^\W+/, "")) || t.includes("Agents"))).toBe(true);
    expect(shown.some((t) => t.includes("Hand to agent"))).toBe(true);
    // No row names a saved persona an AGENT, and no row says coder or Conductor.
    for (const recipe of recipes) {
      const row = shown.find((t) => t.includes(recipe.name));
      if (row) expect(row, recipe.name).not.toMatch(/AGENT/);
    }
    for (const t of shown) expect(t).not.toMatch(/Conductor|[Cc]oder|CODER/);
    // A persona typed by name is a MODE row.
    await type(input, recipes[0].name);
    const persona = rows().find((o) => (o.textContent ?? "").includes(recipes[0].name));
    expect(persona?.textContent).toContain("MODE");
  });
});
