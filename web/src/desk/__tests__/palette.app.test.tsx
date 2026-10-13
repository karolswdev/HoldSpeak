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
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
const openProjectRoom = vi.fn();
vi.mock("../shell", async () => {
  const actual = await vi.importActual<typeof import("../shell")>("../shell");
  return {
    ...actual, openSurface: () => true, openSurfaceOr: () => {},
    openProjectRoom: (...args: unknown[]) => openProjectRoom(...args),
  };
});
vi.mock("../setup", () => ({ loadSetup: vi.fn(() => Promise.resolve(null)) }));

import { EMPTY_ITEMS, __resetHeldObjects, fromWireMeeting, loadAll } from "../api";
import { ApiError } from "../../lib/api";
import type { Meeting, Note } from "../../lib/primitives";
import { useDesk } from "../store";
import { usePalette } from "../chromeState";
import { DeskToolShelf, MEMORY_DEBOUNCE_MS } from "../components/DeskToolShelf";
import { objectByRef } from "../world";
import { Pullout } from "../components/Pullout";
import enterHub from "./fixtures/palette-enter/recorded.json";

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
  routes = {};
  apiFetch.mockReset();
  openProjectRoom.mockReset();
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
    await vi.waitFor(() => expect(useDesk.getState().openPullout).toHaveBeenCalledWith("meeting:m-old-00"));
    expect(order).toEqual(["refresh", "open"]);
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
 * boot: the note made by POST /api/notes, the reads before Develop, the
 * owner's Develop, the reads after). The palette opens the note the first
 * row names; the window the desk draws for that ref is the note's own
 * window, or, once developed, the Thought window OF THAT NOTE. No press and
 * no read writes anything (no thought, no note). */
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

  it("an ordinary note: Enter opens the note's own window; no thought is made", async () => {
    // replaces: tests/e2e/test_palette_enter_opens_the_note_glass.py::TestEnterOpensTheFirstRow::test_enter_opens_the_note_the_first_row_names (part 1, 1440 Enter; the 393 tap runs the same row)
    await replay(enterHub.before);
    await pressEnterOnLedger();
    const { container } = await drawWindow();
    expect(await screen.findByRole("button", { name: "Develop this thought" })).toBeTruthy();
    const frame = container.querySelector(`[id="pullout:${ref}"]`);
    expect(frame?.getAttribute("aria-label")).toBe(enterHub.title);
    expect(container.querySelector(".thought-workspace-window")).toBeNull();
    expect(unrouted).toEqual([]);
    expect(writes()).toEqual([]);
  });

  it("the phone's press on the first row opens the same note, and writes nothing", async () => {
    // replaces: tests/e2e/test_palette_enter_opens_the_note_glass.py::TestEnterOpensTheFirstRow::test_enter_opens_the_note_the_first_row_names[393] (part 1, the tap)
    await replay(enterHub.before);
    await pressEnterOnLedger("tap");
    expect(unrouted).toEqual([]);
    expect(writes()).toEqual([]);
  });

  it("a developed note: the same Enter opens the Thought window OF THAT NOTE; no new note is made", async () => {
    // replaces: tests/e2e/test_palette_enter_opens_the_note_glass.py::TestEnterOpensTheFirstRow::test_enter_opens_the_note_the_first_row_names (part 3, after Develop this thought)
    await replay(enterHub.after);
    // The premise, from the hub's own reads: Develop made no second note.
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
    expect(container.querySelector(".thought-note-title")?.textContent).toContain(enterHub.title);
    expect(screen.queryByRole("button", { name: "Develop this thought" })).toBeNull();
    expect(unrouted).toEqual([]);
    expect(writes()).toEqual([]);
  });
});
