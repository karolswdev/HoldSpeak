// The Chair app, The week window (HS-175-02 and its counsel C2, C5, C8, C9).
// Betterment daily D5: The week and Brief windows retired into Today; their
// cases are parked in __tests__/_parked/chairWeekBrief.d5.app.test.tsx. What
// stays: the typed door rows, the NO CALENDAR offer, the NEXT clock, Coming up.
//
// The test diet (2026-10-11) moves the arrival glass rig here. The real
// ChairHome renders with its real desk store; only `apiFetch` is mocked, and
// it answers with the hub's real `/api/door` shape (copied from
// holdspeak/services/door_service.py: `get`, `_week_strip`,
// `_calendar_event_item`, `_scheduled_recording_item`). The Python half
// (tests/unit/test_desk_chair.py) proves the projection carries exactly these
// fields for the same seed.
//
// The zone is pinned to America/Denver (-06:00 in October, the same offset
// the glass rig gave its browser with Etc/GMT+6) the way
// web/src/pages/cores/__tests__/peoplePrepB4.test.tsx pins it: at module top,
// before any Date is made. The clock is faked for Date only, so "today" is
// a fixed Wednesday and no week edge can move a row.
process.env.TZ = "America/Denver";

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterAll, afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../lib/api";
import { ChairHome } from "../chair/ChairHome";
import { openChairWindows } from "../chair/__tests__/fixtures/openChairWindows";
import { claimThoughtKeys } from "../thoughtKeys";
import { nextWord } from "../needs/needsFace";
import WEEK_STRIP from "./wire/door.week-strip.wire.json";
import { unfinishedThoughts } from "../thoughts";
import THOUGHTS_ONE from "../../test/wire/thoughts-unfinished.one.wire.json";
import THOUGHTS_NONE from "../../test/wire/thoughts-unfinished.none.wire.json";

vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));
// The THOUGHTS block below swaps in the hub's recorded answer; every other test reads none.
vi.mock("../thoughts", () => ({ unfinishedThoughts: vi.fn(async () => ({ items: [] })) }));
vi.mock("../components/MicButton", () => ({
  MicButton: ({ label = "Speak", onText }: { label?: string; onText: (text: string) => void }) => {
    return <button data-testid={`mock-mic-${label}`} onClick={() => onText("Words from Talk")}>{label}</button>;
  },
}));

// Wednesday 2026-10-07 10:00 in Denver (16:00 UTC).
const NOW = new Date("2026-10-07T16:00:00Z");

type Json = Record<string, any>;

/** `_week_strip`: Mon-Sun local days, UTC bounds as `isoformat()` writes them. */
function week(counts: Partial<Record<string, number>>, hasCalendar = true): Json {
  const dows = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"];
  const bounds = { starts_at: "2026-10-05T06:00:00+00:00", ends_at: "2026-10-12T06:00:00+00:00" };
  if (!hasCalendar) return { days: [], total: 0, has_calendar: false, ...bounds };
  const days = dows.map((dow, i) => ({
    date: `2026-10-${String(5 + i).padStart(2, "0")}`,
    dow,
    count: counts[dow] ?? 0,
  }));
  return { days, total: days.reduce((n, d) => n + d.count, 0), has_calendar: true, ...bounds };
}

/** `_calendar_event_item`, with the armed and Room parts only when present. */
function event(id: string, title: string, startsAt: string, extra: Json = {}): Json {
  return {
    id,
    uid: `uid-${id}`,
    source: "calendar_event",
    target_ref: `calendar_event:${id}`,
    title,
    starts_at: startsAt,
    ends_at: startsAt,
    location: null,
    meeting_url: null,
    state: "scheduled",
    source_id: "src-work",
    source_label: "WORK",
    ...extra,
  };
}

function armed(recordingId: string, armsAt: string, state = "idle"): Json {
  return { armed_schedule_id: recordingId, armed: { recording_id: recordingId, arms_at: armsAt, state } };
}

const ROOM = { project_id: "proj-q4", project_name: "Q4 Platform" };

/** The glass rig's `_seed_week_strip`: three events today, one armed and
 *  linked. The hub's own answer for that seed (the real DoorService at the
 *  same clock), recorded and fenced by tests/unit/test_desk_chair.py (the
 *  test diet's SCAR LAW). */
function weekStripDoor(): Json {
  return structuredClone(WEEK_STRIP.wire) as Json;
}

function door(upcoming: Json[], weekData: Json, calendarConfigured = true): Json {
  return {
    board: { overdue: [], now: [], waiting: [], active: [], unassigned: [] },
    upcoming,
    counts: { overdue: 0, now: 0, waiting: 0, active: 0, upcoming_today: upcoming.length },
    calendar_configured: calendarConfigured,
    week: weekData,
  };
}

let wire: { door: Json; paths: Array<[string, unknown]> };

function hub(initial: Json, onCall?: (path: string, init: any) => unknown) {
  wire = { door: initial, paths: [] };
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
    wire.paths.push([String(path), init]);
    const answer = onCall?.(String(path), init);
    if (answer !== undefined) return answer as never;
    if (path === "/api/door") return wire.door as never;
    if (path === "/api/scheduled-recordings") return { success: true, schedules: [] } as never;
    return null as never;
  });
}

function weekBody(): HTMLElement {
  return screen.getByTestId("chair-window-body-week");
}

function rowOf(title: string): HTMLElement {
  const rows = screen.getAllByTestId("arrival-meeting-row");
  const row = rows.find((r) => (r.textContent || "").includes(title));
  if (!row) throw new Error(`no row ${title}`);
  return row;
}

function totalOf(): number {
  const text = screen.getByTestId("arrival-week-total").textContent || "";
  const m = /^(\d+)\s+MEETING/.exec(text);
  return m ? Number(m[1]) : -1;
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"], now: NOW });
  openChairWindows();
  vi.mocked(apiFetch).mockReset();
});

afterEach(() => {
  vi.useRealTimers();
});

afterAll(() => {
  delete process.env.TZ;
});

describe("The typed rows have the hub's fields (the SCAR LAW)", () => {
  it("event(), armed() and door() carry exactly the recorded answer's keys", () => {
    const keys = (o: Json) => Object.keys(o).sort();
    const recorded = WEEK_STRIP.wire as Json;
    const [standup, design] = recorded.upcoming as Json[];
    expect(keys(event("x", "X", "2026-10-07T17:00:00+00:00", { ...armed("r", "2026-10-07T16:55:00Z"), ...ROOM })))
      .toEqual(keys(standup));
    expect(keys(event("x", "X", "2026-10-07T19:00:00+00:00"))).toEqual(keys(design));
    expect(keys(standup.armed)).toEqual(keys(armed("r", "t").armed));
    const typed = door([], week({ WED: 3 }));
    expect(keys(typed)).toEqual(keys(recorded));
    expect(keys(typed.board)).toEqual(keys(recorded.board));
    expect(keys(typed.counts)).toEqual(keys(recorded.counts));
    expect(keys(typed.week)).toEqual(keys(recorded.week));
    expect(keys(typed.week.days[0])).toEqual(keys(recorded.week.days[0]));
  });
});

describe("The week: the zone pin holds", () => {
  it("runs in America/Denver", () => {
    expect(Intl.DateTimeFormat().resolvedOptions().timeZone).toBe("America/Denver");
    expect(new Date().getHours()).toBe(10);
  });
});

describe("The week: the strip and the THIS WEEK rows", () => {

  it("no calendar: no strip and no THIS WEEK section", async () => {
    // replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_no_calendar
    // The NO CALENDAR offer and its Connect calendar verb are asserted by
    // web/src/desk/needs/__tests__/NeedsDrawer.test.tsx
    // ("NEXT is a quiet footer line; no calendar is an offer in the foot, never a row").
    hub(door([], week({}, false), false));
    render(<ChairHome />);
    await waitFor(() => expect(wire.paths.some(([p]) => p === "/api/door")).toBe(true));
    await waitFor(() => expect(screen.getByTestId("needs-no-calendar").textContent).toContain("No calendar"));
    expect(screen.queryByTestId("arrival-week-strip")).toBeNull();
    expect(screen.queryByTestId("arrival-this-week")).toBeNull();
  });

});

describe("The week: the viewer's local clock", () => {

  it("the NEXT line prints a scheduled recording's local wall clock", () => {
    // replaces: tests/e2e/test_times_local_zone_glass.py::test_chair_next_shows_the_scheduled_local_time (face half)
    // The hub half (the fire instant is the wall clock in the schedule's zone):
    // tests/unit/test_desk_speak.py::test_scheduled_recording_fires_at_the_wall_clock_of_its_zone.
    // `_scheduled_recording_item` stamps starts_at with `_utc_iso` (`...Z`).
    expect(nextWord({ label: "Cutover dry run", at: "2026-10-08T03:32:00Z" })).toBe("NEXT · 21:32 · Cutover dry run");
  });
});

// ── PHILO-15 05: the Brief generated itself; an unread source says PARTIAL ──
// The hub's own answers (scripts/record_chair_brief_fixture.py, run in
// America/Denver): `scheduled` after the real cadence tick at 06:00 on the
// shipped defaults; `partial` after MondayBriefService.generate for SERVICE
// heartbeat (two sources the rule cannot read). The hub halves are
// tests/unit/test_philo15_05_brief_generates_itself.py:56 and :164.
import { recordedGet } from "../../test/recordedHub";
import BRIEF from "./fixtures/chair-brief/brief.recorded.json";

// ── Capture C7: Coming up replaces the old Schedule rail ─────────────────
// The hub's own answers (tests/unit/test_desk_chair.py:
// test_coming_up_arms_cancels_and_names_a_failed_fire) cover the same
// failed-fire reason and armed follow-up at the service boundary.
import { useDesk } from "../store";
import COMING_UP from "./fixtures/coming-up/coming-up.json";

const pad2 = (n: number) => String(n).padStart(2, "0");
const hhmm = (iso: string) => {
  const d = new Date(iso);
  return `${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
};

describe("Capture: Coming up in place of Schedule", () => {
  it("shows a failed fire with Record now and an armed meeting with its cancel action", async () => {
    vi.setSystemTime(new Date(COMING_UP._now));
    let phase: "before" | "armed" = "before";
    const posts: string[] = [];
    useDesk.setState({ comingUp: null, scheduledRecordings: [] } as never);
    hub(COMING_UP["GET /api/door (before)"] as Json, (path, init) => {
      if (init?.method === "POST") {
        posts.push(path);
        if (path === "/api/scheduled-recordings") {
          phase = "armed";
          return structuredClone(COMING_UP["POST /api/scheduled-recordings"]);
        }
      }
      if (path === "/api/door") {
        return structuredClone(COMING_UP[phase === "armed" ? "GET /api/door (armed)" : "GET /api/door (before)"]);
      }
      if (path === "/api/scheduled-recordings") {
        return structuredClone(COMING_UP["GET /api/scheduled-recordings (before)"]);
      }
      return undefined;
    });
    render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-coming-up").getAttribute("aria-busy")).toBeNull());
    const list = screen.getByTestId("arrival-coming-up");
    await waitFor(() => expect(within(list).getAllByRole("listitem")).toHaveLength(2));
    const [failed, next] = within(list).getAllByRole("listitem");
    const sync = (COMING_UP["GET /api/scheduled-recordings (before)"] as Json).schedules
      .find((s: Json) => s.id === "rec-sync");
    expect(failed.textContent).toContain("Payments platform sync");
    expect(within(failed).getByTestId("coming-up-state").textContent)
      .toBe(`Did not record · ${hhmm(sync.did_not_record.at)} · ${sync.did_not_record.reason}`);
    expect(within(failed).getByRole("button", { name: "Record now" })).toBeTruthy();
    expect(next.textContent).toContain("Platform design follow-up");

    fireEvent.click(within(next).getByRole("button", { name: "Record Platform design follow-up when it starts" }));
    await waitFor(() => expect(within(list).getAllByTestId("coming-up-state")[1]?.textContent ?? "").toMatch(/^Records at /));
    const armed = (COMING_UP["GET /api/door (armed)"] as Json).upcoming.find((r: Json) => r.id === "ev-followup");
    expect(within(list).getAllByTestId("coming-up-state")[1].textContent).toBe(`Records at ${hhmm(armed.armed.arms_at)}`);
    expect(within(list).getByRole("button", { name: "Cancel the recording of Platform design follow-up" })).toBeTruthy();
    expect(posts).toEqual(["/api/scheduled-recordings"]);
  });
});

// HS-170-04 (the arrival glass) and HS-141 (the Chair geometry): The week
// lists an unfinished thought in THOUGHTS, and has no THOUGHTS section with
// none. The hub's own answers to GET /api/thoughts?state=unfinished&limit=3
// before and after one typed thought (tests/integration/test_face_wire_fences.py).

// ── Betterment capture C8: Capture in plain words ─────────────────────────
// The hub's own answers: GET /api/setup/local-ai with no speech model
// (test/wire/setup-local-ai.wire.json), POST /api/notes
// (test/wire/notes-create.wire.json) and the note's thought open
// (test/wire/note.one-note.wire.json), all from
// tests/integration/test_face_wire_fences.py / tests/unit/test_desk_note.py.
import LOCAL_AI_WIRE from "../../test/wire/setup-local-ai.wire.json";
import NOTE_CREATED from "../../test/wire/notes-create.wire.json";
import ONE_NOTE from "../../test/wire/note.one-note.wire.json";

function captureHub(posts: Array<[string, any]>) {
  hub(weekStripDoor(), (path, init) => {
    if (init?.method && init.method !== "GET") posts.push([path, init]);
    if (path === "/api/setup/local-ai") return structuredClone(LOCAL_AI_WIRE.wire);
    if (path === "/api/notes" && init?.method === "POST") return structuredClone(NOTE_CREATED.wire);
    if (path === "/api/thoughts/open-note" && init?.method === "POST") return structuredClone(ONE_NOTE.open);
    return undefined;
  });
}

function readySpeechWire(): Json {
  const ready = structuredClone(LOCAL_AI_WIRE.wire) as Json;
  ready.files = (ready.files as Json[]).map((file) =>
    file.key === "whisper" ? { ...file, on_device: true } : file,
  );
  ready.speech = { ...ready.speech, ready: true, state: "on_device" };
  return ready;
}

describe("C8: Capture — three large verbs, the one Talk rule, New note on the first character", () => {
  it("Talk, New note, Record from the top; no `Write a thought`, no `Record meeting`", async () => {
    captureHub([]);
    render(<ChairHome />);
    const bar = await screen.findByTestId("arrival-capture-bar");
    await within(bar).findByTestId("arrival-talk-setup-key");
    const big = Array.from(bar.querySelectorAll(".arrival-capture-big")).map((el) => el.textContent?.trim());
    expect(big).toEqual(["Talk", "New note", "Record"]);
    expect(bar.textContent).not.toMatch(/Write a thought|Record meeting/);
  });

  it("no speech model: Capture's Talk and the floor TALK open the same Set up speech in place", async () => {
    captureHub([]);
    // The Chair draws the floor (desk/screen/Screen.tsx) with its TALK.
    render(<ChairHome />);
    const bar = await screen.findByTestId("arrival-capture-bar");
    const capture = await within(bar).findByTestId("arrival-talk-setup-key");
    const floor = await within(await screen.findByTestId("desk-screen-talk")).findByTestId("desk-screen-talk-setup-key");
    for (const key of [capture, floor]) expect(key).not.toBeDisabled();
    fireEvent.click(capture);
    fireEvent.click(floor);
    const verbs = [
      await within(bar).findByTestId("arrival-talk-setup-verb"),
      await within(screen.getByTestId("desk-screen-talk")).findByTestId("desk-screen-talk-setup-verb"),
    ];
    for (const verb of verbs) expect(verb.textContent?.trim()).toMatch(/^Set up speech · 144 MB$/);
    // Pressing Talk asks nothing of the hub: setup waits for its own press.
    expect(wire.paths.filter(([, init]) => (init as any)?.method === "POST")).toEqual([]);
  });

  async function spokenWordsReachNote(surface: "capture" | "floor") {
    const posts: Array<[string, any]> = [];
    hub(weekStripDoor(), (path, init) => {
      if (init?.method && init.method !== "GET") posts.push([path, init]);
      if (path === "/api/setup/local-ai") return readySpeechWire();
      if (path === "/api/notes" && init?.method === "POST") return structuredClone(NOTE_CREATED.wire);
      if (path === "/api/thoughts/open-note" && init?.method === "POST") return structuredClone(ONE_NOTE.open);
      return undefined;
    });
    useDesk.setState({ pullouts: [], items: { note: [] } } as never);
    let received = "";
    const releaseKeys = claimThoughtKeys(String(NOTE_CREATED.wire.note.id), (text) => {
      received = text;
    });
    render(<ChairHome />);
    try {
      const host = surface === "capture"
        ? within(await screen.findByTestId("arrival-capture-bar"))
        : within(await screen.findByTestId("desk-screen-talk"));
      await act(async () => {
        fireEvent.click(await host.findByTestId("mock-mic-Talk"));
      });
      await waitFor(() => expect(received).toBe("Words from Talk"));
      expect(posts.map(([path]) => path)).toContain("/api/notes");
      expect(posts.find(([path]) => path === "/api/notes")?.[1].json).toEqual({
        title: "Thought",
        body_markdown: "",
        tags: [],
      });
    } finally {
      releaseKeys();
    }
  }

  it("spoken Capture words reach the New note editor handoff", async () => {
    await spokenWordsReachNote("capture");
  });

  it("spoken floor Talk words reach the New note editor handoff", async () => {
    await spokenWordsReachNote("floor");
  });

  it("New note: a press with no typing leaves no record; the first character makes it and opens it", async () => {
    const posts: Array<[string, any]> = [];
    captureHub(posts);
    useDesk.setState({ pullouts: [] } as never);
    render(<ChairHome />);
    const press = await screen.findByTestId("arrival-develop-thought");
    fireEvent.click(press);
    const note = await screen.findByTestId("arrival-new-note");
    const words = within(note).getByRole("textbox", { name: "New note" });
    expect(words).toHaveValue("");
    // Escape folds it; a press again unfolds it. Nothing was written.
    fireEvent.keyDown(words, { key: "Escape" });
    await waitFor(() => expect(screen.queryByTestId("arrival-new-note")).toBeNull());
    fireEvent.click(press);
    fireEvent.click(press);
    await waitFor(() => expect(screen.queryByTestId("arrival-new-note")).toBeNull());
    expect(posts.filter(([p]) => p === "/api/notes")).toEqual([]);

    fireEvent.click(press);
    fireEvent.change(within(await screen.findByTestId("arrival-new-note")).getByRole("textbox", { name: "New note" }), {
      target: { value: "P" },
    });
    await waitFor(() => expect(posts.filter(([p]) => p === "/api/notes")).toHaveLength(1));
    expect(posts.find(([p]) => p === "/api/notes")![1].json).toEqual({ title: "Thought", body_markdown: "", tags: [] });
    await waitFor(() =>
      expect(JSON.stringify(useDesk.getState().pullouts)).toContain(NOTE_CREATED.wire.note.id));
    expect(screen.queryByTestId("arrival-new-note")).toBeNull();
  });
});
