// The Rhythm app (CadenceCore) and the Brief detail it names (BriefView).
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
import { BriefView } from "../../../desk/pullouts/views/BriefView";
import { CadenceCore } from "../CadenceCore";

function json(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
}

const HEARTBEAT = {
  sweep_every_minutes: 15, quiet_hours: { start: 22, end: 8 }, notify: "edge",
  muted_projects: [], last_sweep_at: null, next_sweep_at: null, runs_on: null, last_remote_run_at: null,
};

const STATUS = {
  enabled: false, pressure: "normal", tick_interval_seconds: 60,
  quiet_hours: { start: 22, end: 8 }, max_nudges_per_day: 3,
  brief_job: { enabled: true, hour: 6 }, policies: 0, counts: {}, egress: "local",
};

function item(id: string, section: string, text: string, sourceRef: string | null, detail: string | null = null) {
  return { id, section, text, detail, source_ref: sourceRef, priority: 50, created_at: null };
}

/** The glass rig's seed after `POST /api/brief/generate`: 4 events this local
 *  week, one armed, one commitment due today; one SINCE FRIDAY item. */
function brief(thisWeek: unknown[]) {
  return {
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
    shelf: {},
    ledger: { operations: 0 },
    period_label: "OCT 02-07",
    generated_label: "GENERATED OCT 07 15:30",
    title: "Brief · Wednesday 7 Oct 2026",
    stale: false,
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
    if (url.includes("/api/door")) return json(over.door ?? { calendar_configured: false });
    if (url.includes("/api/projects")) return json({ projects: [] });
    if (url.includes("/api/cadence/status")) return json(STATUS);
    if (url.includes("/api/cadence/loops")) return json({ loops: [] });
    if (url.includes("/api/cadence/history")) return json({ nudges: [] });
    return json({});
  }));
}

/** `door_service.get` with a calendar source (the strip parts the Rhythm ignores). */
const DOOR_WITH_CALENDAR = {
  board: { overdue: [], now: [], waiting: [], active: [] },
  upcoming: [],
  counts: { overdue: 0, now: 0, waiting: 0, active: 0, upcoming_today: 0 },
  calendar_configured: true,
  week: { days: [], total: 0, has_calendar: true, starts_at: "2026-10-05T06:00:00+00:00", ends_at: "2026-10-12T06:00:00+00:00" },
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

describe("The Brief detail the Rhythm row names", () => {
  it("shows THIS WEEK before SINCE FRIDAY, one period, no headline, counted rows and NEXT inside MEETINGS", async () => {
    // replaces: tests/e2e/test_hs175_rhythm_brief_glass.py::TestRhythmWeeklyBrief::test_brief_this_week_section
    // (all but the ONE GUTTER check, which measures left edges: real layout)
    hub({ brief: brief(THIS_WEEK) });
    const { container } = render(<BriefView header={<div>Header</div>} />);
    const thisWeek = await screen.findByTestId("brief-this-week");
    const since = screen.getByTestId("brief-since-friday");
    expect(thisWeek.compareDocumentPosition(since) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    expect(container.querySelectorAll(".intelligence-brief-period")).toHaveLength(1);
    expect(container.querySelector(".intelligence-brief-headline")).toBeNull();

    for (const id of ["brief-tw-meetings", "brief-tw-armed", "brief-tw-due"]) {
      const row = screen.getByTestId(id);
      const primary = row.querySelectorAll(".intelligence-brief-tw-primary");
      expect(primary).toHaveLength(1);
      expect(primary[0].textContent?.trim()).toMatch(/^[1-9]\d* /);
    }
    expect(screen.getByTestId("brief-tw-meetings").textContent).toContain("4 MEETINGS");
    const next = within(screen.getByTestId("brief-tw-meetings")).getByTestId("brief-tw-next");
    expect(next.textContent).toContain("NEXT");
    const day = screen.queryByTestId("brief-tw-due-day");
    if (day) expect(day.textContent).toHaveLength(3);

    for (const p of Array.from(container.querySelectorAll(".intelligence-brief-tw-primary, .intelligence-brief-sf-primary"))) {
      expect((p.textContent || "").trim().endsWith(".")).toBe(false);
    }
    for (const kind of screen.queryAllByTestId("brief-sf-kind")) {
      expect(kind.textContent).toBe(kind.textContent?.toUpperCase());
    }
    for (const emblem of screen.queryAllByTestId("brief-source-emblem")) {
      const t = emblem.textContent || "";
      expect(t === t.toUpperCase() && t.length >= 1 && t.length <= 4).toBe(true);
    }
    const clone = container.cloneNode(true) as HTMLElement;
    clone.querySelectorAll(".send-preview-body").forEach((n) => n.remove());
    expect(clone.textContent).not.toMatch(/\d{4}-\d{2}-\d{2}/);
  });
});
