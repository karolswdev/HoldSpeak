// The Rhythm app (CadenceCore). Betterment setup ST1: the Rhythm WINDOW is
// parked; Rhythm's one home is Settings ▸ Rhythm, which reads Notify and
// quiet hours from the heartbeat (settings.app.test.tsx, "Settings › Rhythm")
// and embeds this face under its Advanced fold (`embedded`: no headline, no
// Notify row, no foot). The face's own behaviour is fenced here.
// The Brief detail it named (the Brief wing)
// is parked by Betterment daily D4: _parked/rhythmBriefWing.app.test.tsx.
// The test diet (2026-10-11) moves tests/e2e/test_hs175_rhythm_brief_glass.py
// and the Rhythm leg of tests/e2e/test_times_local_zone_glass.py here.
//
// Only `fetch` is stubbed (the way rhythmBriefJob.philo1505.test.tsx does it),
// with the hub's real shapes: `/api/cadence/status` (cadence_service.status,
// `brief_job`), `/api/settings/heartbeat` (heartbeat_service settings; the
// sweep stamps are `now.isoformat()` in UTC), `/api/door` (door_service.get)
// and `/api/brief/latest` (asdict(MondayBrief) plus the route's
// `period_label`, `generated_label`, `title`, `stale`; this_week items as
// monday_brief_service writes them: "4 meetings this week" / calendar:week,
// "Next: <title> at HH:MM", "1 armed" / calendar:armed, "1 commitment due
// this week" / meeting_watch:commitments_due).
//
// Already asserted elsewhere (cited, not repeated): the summary line's plurals
// (RhythmBriefSummary.test.ts) and the DAILY token's three states
// (rhythmBriefJob.philo1505.test.tsx).
//
// The zone is pinned to America/Denver at module top, the way
// peoplePrepB4.test.tsx pins it.
process.env.TZ = "America/Denver";

import { render, screen, waitFor, within } from "@testing-library/react";
import { afterAll, afterEach, describe, expect, it, vi } from "vitest";
import { CadenceCore } from "../CadenceCore";
import { inventedFields, recorded } from "../../../test/wireShape";
import BRIEF_WIRE from "../../../test/wire/brief-latest.generated.wire.json";
// One recorded source for the Rhythm's reads (scripts/record_chair_rhythm_fixture.py):
// the cold hub's heartbeat, cadence status, Door, loops, history and projects.
import RHYTHM from "./fixtures/rhythm-wire/rhythm.recorded.json";

function json(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
}

type Json = Record<string, any>;
const COLD = (RHYTHM.change.steps[0] as unknown as { gets: Record<string, Json> }).gets;
const HEARTBEAT = structuredClone(COLD["/api/settings/heartbeat"]);
const STATUS = structuredClone(COLD["/api/cadence/status"]);

/** A Brief row: the recorded Brief's own row with these values. */
function item(id: string, section: string, text: string, sourceRef: string | null, detail: string | null = null) {
  const row = recorded<{ sections: { waiting: Json[] } }>(BRIEF_WIRE).sections.waiting[0];
  return { ...row, id, section, text, detail, source_ref: sourceRef, priority: 50, created_at: null };
}

/** The glass rig's seed after `POST /api/brief/generate`: 4 events this local
 *  week, one armed, one commitment due today; one SINCE FRIDAY item. The
 *  hub's recorded Brief (tests/integration/test_face_wire_fences.py) with
 *  these values. */
function brief(thisWeek: unknown[]) {
  return {
    ...recorded<Json>(BRIEF_WIRE),
    id: "brief-1",
    period_start: "2026-10-02T17:00:00+00:00",
    period_end: "2026-10-07T16:00:00+00:00",
    headline: "4 meetings this week, 1 armed, 1 commitment due.",
    sections: {
      this_week: thisWeek,
      changed: [item("item-sf-1", "changed", "Meeting recorded: Standup", "meeting:m-1")],
      broke: [],
      waiting: [],
      decisions: [],
    },
    generated_at: "2026-10-07T15:30:00+00:00",
    is_empty: false,
    period_label: "OCT 02-07",
    generated_label: "GENERATED OCT 07 15:30",
  };
}

const THIS_WEEK = [
  item("tw-1", "this_week", "4 meetings this week", "calendar:week"),
  item("tw-2", "this_week", "Next: Sprint Planning at 10:00", "calendar_event:evt-glass-3"),
  item("tw-3", "this_week", "1 armed", "calendar:armed"),
  item("tw-4", "this_week", "1 commitment due this week", "meeting_watch:commitments_due",
    "Ania owns the API spec | 2026-10-07"),
];

function hub(over: { door?: unknown; brief?: unknown; heartbeat?: unknown } = {}) {
  vi.stubGlobal("fetch", vi.fn(async (input: string) => {
    const url = String(input);
    if (url.includes("/api/settings/heartbeat")) return json(over.heartbeat ?? HEARTBEAT);
    if (url.includes("/api/brief/latest")) return json(over.brief ?? null);
    if (url.includes("/api/door")) return json(over.door ?? COLD["/api/door"]);
    if (url.includes("/api/projects")) return json(COLD["/api/projects"]);
    if (url.includes("/api/cadence/status")) return json(STATUS);
    if (url.includes("/api/cadence/loops")) return json(COLD["/api/cadence/loops"]);
    if (url.includes("/api/cadence/history")) return json(COLD["/api/cadence/history?limit=20"]);
    return json({});
  }));
}

/** The recorded cold Door with a calendar source (the strip parts the Rhythm ignores). */
const DOOR_WITH_CALENDAR = {
  ...structuredClone(COLD["/api/door"]),
  calendar_configured: true,
  week: { ...COLD["/api/door"].week, has_calendar: true },
};

afterEach(() => vi.unstubAllGlobals());
afterAll(() => {
  delete process.env.TZ;
});

describe("Rhythm: the brief row", () => {
  it("with a calendar reads Weekly brief, DAILY HH:00, LAST, the summary and Generate", async () => {
    // replaces: tests/e2e/test_hs175_rhythm_brief_glass.py::TestRhythmWeeklyBrief::test_rhythm_brief_row_with_calendar
    hub({ door: DOOR_WITH_CALENDAR, brief: brief(THIS_WEEK) });
    render(<CadenceCore />);
    const row = await screen.findByTestId("rhythm-brief-row");
    await waitFor(() => expect(row.textContent).toContain("Weekly brief"));
    expect(row.textContent).not.toContain("Daily brief");

    const cadence = screen.getByTestId("rhythm-brief-cadence").textContent?.trim() ?? "";
    expect(cadence).toMatch(/^DAILY \d{2}:00$/);
    expect(cadence).not.toMatch(/WEEKLY|MON/);
    await waitFor(() => expect(screen.getByTestId("rhythm-brief-last").textContent).toContain("LAST OCT 07"));

    const summary = await screen.findByTestId("rhythm-brief-summary");
    expect(summary.textContent).toBe("4 MEETINGS · 1 ARMED · 1 COMMITMENT DUE");
    expect(summary.textContent).not.toContain("WATCH ITEM");
    expect(within(row).getByTestId("rhythm-generate-now").textContent).toContain("Generate");
  });

  it("without a calendar reads Daily brief and DAILY", async () => {
    // replaces: tests/e2e/test_hs175_rhythm_brief_glass.py::TestRhythmMondayBrief::test_no_calendar_monday_brief
    // The wire half (no calendar rows, no this_week items) is
    // tests/unit/test_hs175_week_brief.py::TestCollectCalendarEvents::test_empty_when_no_events.
    hub({ door: { ...DOOR_WITH_CALENDAR, calendar_configured: false }, brief: brief([]) });
    render(<CadenceCore />);
    const row = await screen.findByTestId("rhythm-brief-row");
    await waitFor(() => expect(row.textContent).toContain("Daily brief"));
    expect(row.textContent).not.toContain("Weekly brief");
    expect(screen.getByTestId("rhythm-brief-cadence").textContent).toContain("DAILY");
    expect(screen.queryByTestId("rhythm-brief-summary")).toBeNull();
  });
});

describe("Rhythm: the local clock", () => {
  it("prints LAST and NEXT sweep in the viewer's zone, not the hub's UTC stamp", async () => {
    // replaces: tests/e2e/test_times_local_zone_glass.py::test_rhythm_prints_the_local_clock
    // The parse itself: web/src/desk/surface/__tests__/wireTime.test.ts ("reads a UTC ISO stamp and prints the local clock").
    expect(Intl.DateTimeFormat().resolvedOptions().timeZone).toBe("America/Denver");
    hub({
      heartbeat: { ...HEARTBEAT, last_sweep_at: "2026-10-04T03:06:10+00:00", next_sweep_at: "2026-10-04T03:21:10+00:00" },
    });
    render(<CadenceCore />);
    const facts = await screen.findByTestId("rhythm-sweep-facts");
    await waitFor(() => expect(facts.textContent).toMatch(/LAST \d{2}:\d{2}/));
    expect(facts.textContent).toContain("LAST 21:06");
    expect(facts.textContent).toContain("NEXT 21:21");
    expect(facts.textContent).not.toContain("03:06");
  });
});

describe("The typed hub bodies carry only the hub's fields (the SCAR LAW)", () => {
  // Heartbeat, status, loops, history and projects are the recorded answers
  // themselves; the Door and the Brief carry typed values on recorded rows.
  it("the Door with a calendar and the Brief", () => {
    expect(inventedFields(DOOR_WITH_CALENDAR, COLD["/api/door"])).toEqual([]);
    expect(inventedFields(brief(THIS_WEEK), recorded(BRIEF_WIRE))).toEqual([]);
    const hubBrief = recorded<{ sections: { waiting: unknown[] } }>(BRIEF_WIRE);
    expect(inventedFields(item("x", "waiting", "t", "blocker:summary", "d"), hubBrief.sections.waiting[0])).toEqual([]);
  });
});

// ── HS-171-02 and HS-174-08: the Rhythm face over the hub's RECORDED answers ──
// scripts/record_chair_rhythm_fixture.py boots the real hub on an isolated
// HOME (the browser tests' seeds), and records, in one boot per scenario,
// every read CadenceCore makes, each press with the hub's answer, and the
// reads after it. Only `fetch` is stubbed; it serves those answers in order,
// and a press the recording does not hold (another path, method or body)
// fails the test. The clock is faked for Date only and pinned in Denver.
import { act, fireEvent } from "@testing-library/react";
import { beforeEach } from "vitest";

type Step = { name: string; gets: Record<string, unknown>; method?: string; path?: string; body?: unknown; answer?: unknown };

function replay(steps: Step[]) {
  let at = 0;
  const presses: string[] = [];
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const url = new URL(String(input), "http://hub.test");
    const path = url.pathname + url.search;
    const method = (init?.method ?? "GET").toUpperCase();
    if (method !== "GET") {
      const body = init?.body ? JSON.parse(String(init.body)) : undefined;
      const next = steps.findIndex((s, i) => i > at && s.method === method && s.path === path
        && JSON.stringify(s.body) === JSON.stringify(body));
      if (next < 0) throw new Error(`unrecorded press ${method} ${path} ${JSON.stringify(body)}`);
      at = next;
      presses.push(`${method} ${path}`);
      return json(structuredClone(steps[next].answer));
    }
    if (!(path in steps[at].gets)) throw new Error(`unrecorded read ${path}`);
    return json(structuredClone(steps[at].gets[path]));
  }));
  return presses;
}

/** A Wednesday in Denver at the given local hour (the recorded quiet hours
 *  are 22-08 by default and 09-11 in `quiet`). */
function clockAt(hour: number) {
  vi.useFakeTimers({ toFake: ["Date"], now: new Date(`2026-10-07T${String(hour + 6).padStart(2, "0")}:00:00Z`) });
}

describe("Rhythm (recorded hub): the sweep, the mute tokens and quiet hours", () => {
  beforeEach(() => clockAt(12));
  afterEach(() => vi.useRealTimers());

  it("cold: Every 15 min, the Sweep, Brief and Notify rows, Run now and Generate", async () => {
    // replaces: tests/e2e/test_hs171_rhythm_glass.py::TestRhythmFace::test_cold_state_1440
    // replaces: tests/e2e/test_hs171_rhythm_glass.py::TestRhythmFace::test_phone_width (a shot and a clean page; the 393 fit and clean fences are the sweep's surface-cadence case at 393)
    replay(RHYTHM.change.steps as Step[]);
    render(<CadenceCore />);
    await waitFor(() => expect(screen.getByTestId("rhythm-headline").textContent).toBe("Every 15 min"));
    for (const id of ["rhythm-sweep-row", "rhythm-brief-row", "rhythm-notify-row"]) expect(screen.getByTestId(id), id).toBeTruthy();
    expect(screen.getByTestId("rhythm-run-now").textContent).toBe("Run now");
    expect(screen.getByTestId("rhythm-generate-now").textContent).toBe("Generate");
    expect(screen.getByTestId("rhythm-sweep-facts").textContent).not.toContain("HELD");
  });

  it("the Sweep interval set to 30 puts it on the hub and the headline reads Every 30 min", async () => {
    // replaces: tests/e2e/test_hs171_rhythm_glass.py::TestRhythmFace::test_change_cadence
    const steps = RHYTHM.change.steps as Step[];
    expect((steps[1].gets["/api/settings/heartbeat"] as { sweep_every_minutes: number }).sweep_every_minutes).toBe(30);
    const presses = replay(steps);
    render(<CadenceCore />);
    await waitFor(() => expect(screen.getByTestId("rhythm-headline").textContent).toBe("Every 15 min"));
    fireEvent.change(screen.getByLabelText("Sweep interval"), { target: { value: "30" } });
    await waitFor(() => expect(screen.getByTestId("rhythm-headline").textContent).toBe("Every 30 min"));
    expect(presses).toEqual(["PUT /api/settings/heartbeat"]);
  });

  it("Run now sweeps once on the hub and the facts read LAST and the receipt's rooms and time", async () => {
    // replaces: tests/e2e/test_hs171_rhythm_glass.py::TestRhythmFace::test_run_now
    const steps = RHYTHM.runNow.steps as Step[];
    const presses = replay(steps);
    render(<CadenceCore />);
    const facts = await screen.findByTestId("rhythm-sweep-facts");
    await waitFor(() => expect(screen.getByTestId("rhythm-headline").textContent).toBe("Every 15 min"));
    expect(facts.textContent).not.toContain("LAST");
    fireEvent.click(screen.getByTestId("rhythm-run-now"));
    await waitFor(() => expect(screen.getByTestId("rhythm-sweep-facts").textContent).toMatch(/LAST \d{2}:\d{2}/));
    const receipt = steps[1].answer as { rooms: number; duration_ms: number };
    expect(screen.getByTestId("rhythm-sweep-facts").textContent).toContain(`${Math.round(receipt.duration_ms)} MS`);
    expect(screen.getByTestId("rhythm-sweep-facts").textContent).toContain(`${receipt.rooms} ROOM`);
    expect(presses).toEqual(["POST /api/settings/heartbeat/run-now"]);
  });

  it("a Project's mute token: off mutes it on the hub, on again clears it", async () => {
    // replaces: tests/e2e/test_hs171_rhythm_glass.py::TestRhythmFace::test_mute_toggle
    const presses = replay(RHYTHM.mute.steps as Step[]);
    render(<CadenceCore />);
    const token = await screen.findByRole("checkbox", { name: "Q4 PLATFORM" });
    expect((token as HTMLInputElement).checked).toBe(true);
    fireEvent.click(token);
    await waitFor(() => expect((screen.getByRole("checkbox", { name: "Q4 PLATFORM" }) as HTMLInputElement).checked).toBe(false));
    fireEvent.click(screen.getByRole("checkbox", { name: "Q4 PLATFORM" }));
    await waitFor(() => expect((screen.getByRole("checkbox", { name: "Q4 PLATFORM" }) as HTMLInputElement).checked).toBe(true));
    expect(presses).toEqual(["PUT /api/settings/heartbeat", "PUT /api/settings/heartbeat"]);
  });

  it("quiet hours around now: the Sweep reads HELD · QUIET UNTIL 11:00 and Notify reads HELD", async () => {
    // replaces: tests/e2e/test_hs171_rhythm_glass.py::TestRhythmFace::test_quiet_hours_held
    // The hub's answer after PUT quiet_hours 09-11; the viewer's clock is 10:00.
    vi.useRealTimers();
    clockAt(10);
    const steps = RHYTHM.quiet.steps as Step[];
    replay([{ ...steps[1], name: "after" }]);
    render(<CadenceCore />);
    await waitFor(() => expect(screen.getByTestId("rhythm-sweep-facts").textContent).toContain("HELD · QUIET UNTIL 11:00"));
    expect(screen.getByTestId("rhythm-notify-row").textContent).toContain("HELD");
  });
});

describe("Rhythm (recorded hub): Runs on", () => {
  beforeEach(() => clockAt(12));
  afterEach(() => vi.useRealTimers());

  it("THIS DEVICE: the Runs on row, no caption; Run now once, on the Sweep row only", async () => {
    // replaces: tests/e2e/test_hs174_rhythm_runs_on_glass.py::test_runs_on_local_1440
    // replaces: tests/e2e/test_hs174_rhythm_runs_on_glass.py::test_run_now_once
    replay(RHYTHM.change.steps as Step[]);
    render(<CadenceCore />);
    const row = await screen.findByTestId("rhythm-runs-on-row");
    await waitFor(() => expect(screen.getByTestId("rhythm-headline").textContent).toBe("Every 15 min"));
    expect(screen.queryByTestId("rhythm-runs-on-caption")).toBeNull();
    expect(screen.getAllByTestId("rhythm-run-now")).toHaveLength(1);
    expect(row.textContent).not.toContain("Run now");
    expect(within(screen.getByTestId("rhythm-sweep-row")).getByTestId("rhythm-run-now")).toBeTruthy();
  });

  it("a remote run seen, Runs on set to that host: WHILE THIS MAC IS AWAKE and LAST RUN", async () => {
    // replaces: tests/e2e/test_hs174_rhythm_runs_on_glass.py::test_runs_on_remote_1440
    // (test_runs_on_remote_393 stays in the browser suite: its fit at 393 with the remote caption is layout, and the sweep's seed sets no runs_on)
    const steps = RHYTHM.runsOn.steps as Step[];
    const presses = replay(steps);
    render(<CadenceCore />);
    const gadget = await screen.findByLabelText("Runner host");
    await waitFor(() => expect([...(gadget as HTMLSelectElement).options].map((o) => o.value)).toEqual(["local", "192.168.1.43"]));
    expect(screen.queryByTestId("rhythm-runs-on-caption")).toBeNull();
    await act(async () => { fireEvent.change(gadget, { target: { value: "192.168.1.43" } }); });
    await waitFor(() => expect(screen.getByTestId("rhythm-runs-on-caption").textContent).toBe("WHILE THIS MAC IS AWAKE"));
    expect(screen.getByTestId("rhythm-runs-on-facts").textContent).toContain("LAST RUN");
    expect(presses).toEqual(["PUT /api/settings/heartbeat"]);
  });
});

describe("Rhythm embedded in Settings ▸ Rhythm (Betterment setup ST1)", () => {
  beforeEach(() => clockAt(12));
  afterEach(() => vi.useRealTimers());

  it("keeps the sweep, Run now, Where it runs and the mutes; leaves the headline, Notify and the foot to Settings", async () => {
    const presses = replay(RHYTHM.mute.steps as Step[]);
    render(<CadenceCore embedded />);
    await screen.findByTestId("rhythm-sweep-row");
    expect(screen.getByTestId("rhythm-run-now").textContent).toBe("Run now");
    expect(screen.getByTestId("rhythm-runs-on-row")).toBeTruthy();
    expect(screen.queryByTestId("rhythm-headline")).toBeNull();
    expect(screen.queryByTestId("rhythm-notify-row")).toBeNull();
    expect(document.querySelector(".surface-footer-layout")).toBeNull();
    const token = await screen.findByRole("checkbox", { name: "Q4 PLATFORM" });
    fireEvent.click(token);
    await waitFor(() => expect((screen.getByRole("checkbox", { name: "Q4 PLATFORM" }) as HTMLInputElement).checked).toBe(false));
    expect(presses).toEqual(["PUT /api/settings/heartbeat"]);
  });
});
