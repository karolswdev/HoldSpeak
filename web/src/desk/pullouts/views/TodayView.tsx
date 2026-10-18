/** PHILO-17 (owner pick 2026-10-11, concept C): the day as a timeline, in
 *  the desk's own material. Betterment daily D4: Today is ONE page, no
 *  wings. In order: the head (the date, Record now), the top of Needs you
 *  (the same rows and verbs as the Needs-you window, `All` opens it), the
 *  day, Since yesterday (the brief, made when Today opens, folded to one
 *  line of counts) and This week (folded to a count per day). Every fact is
 *  a read the hub already serves: `/api/door` (the calendar, armed
 *  recordings, the week), `/api/meetings` (the meetings still to finish),
 *  `/api/desk/needs-you` (the one list) and `/api/brief/latest?ensure=1`
 *  (the brief, made by the hub off its event loop when none is current). */
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { openSurfaceOr } from "../../shell";
import { openSourceRef } from "../../surface/citations";
import { calendarOpener } from "../../openObject";
import { useDesk } from "../../store";
import { useNeedFaces, NeedsDroppedReceipt } from "../../needs/NeedsDrawer";
import { TodayNeeds } from "../../needs/TodayNeeds";
import type { NeedFace } from "../../needs/needsFace";
import { SinceYesterday, type MondayBrief } from "./BriefView";
import { useOnDeskChanged } from "../../useDeskChangedRefresh";
import { SurfaceFooter } from "../../surface/SurfaceFooter";
import { Avatar, Steps } from "../../surface/kit";
import { meetingRowState } from "../../../pages/cores/history/helpers";
import { useSummaryRun } from "../../../pages/cores/history/useSummaryRun";
import { executedReceipt, readPlannedRoute, readRunReceipt, routeReady } from "../../../meetings/summaryRoute";
import { RouteDisclosure, RunAttempts } from "../../../meetings/RouteDisclosure";
import "./today.css";

const SPRITES = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/32/`;

/** One row of the Door's `upcoming` (a calendar event or an armed recording). */
export type DayEvent = {
  id: string;
  source?: string;
  title?: string;
  event_title?: string;
  starts_at: string;
  ends_at?: string | null;
  person_label?: string;
  person_relationship_id?: string;
  project_id?: string;
  project_name?: string;
  armed?: { recording_id: string; arms_at?: string | null; state?: string } | null;
  armed_schedule_id?: string;
};
type WeekDay = { date: string; dow: string; count: number };
type DoorRead = { upcoming?: DayEvent[]; calendar_configured?: boolean; week?: { days?: WeekDay[]; has_calendar?: boolean } };
type MeetingRow = Record<string, unknown>;

const DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const SHORT_DAYS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
const WEEK_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
/** Today's rows of Needs you: five at 1440, three at 393 (the design). */
const NEEDS_TOP = 5;
const NEEDS_TOP_PHONE = 3;

const pad = (n: number) => String(n).padStart(2, "0");
const clock = (d: Date) => `${pad(d.getHours())}:${pad(d.getMinutes())}`;
const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
function when(value: unknown): Date | null {
  const d = new Date(String(value ?? ""));
  return Number.isNaN(d.getTime()) ? null : d;
}

/** `in 68 min`, `in 2 h 05 min`, `now`. */
export function countdown(start: Date, now: Date): string {
  const minutes = Math.ceil((start.getTime() - now.getTime()) / 60_000);
  if (minutes <= 0) return "now";
  if (minutes < 60) return `in ${minutes} min`;
  return `in ${Math.floor(minutes / 60)} h ${pad(minutes % 60)} min`;
}

/** The meetings still to finish: a recorded meeting whose summary is not
 *  made (or failed) from the last seven days, newest first. */
export function toFinish(rows: MeetingRow[], now: Date): MeetingRow[] {
  const since = now.getTime() - 7 * 86_400_000;
  return rows.filter((row) => {
    const at = when(row.started_at ?? row.created_at);
    if (!at || at.getTime() < since) return false;
    const verb = meetingRowState(row).verb;
    return verb === "Run summary" || verb === "Retry";
  });
}

/** The step of the next meeting: 0 Prep, 1 Record, 2 Summary, 3 Send. */
export function currentStep(event: DayEvent, now: Date): number {
  const start = when(event.starts_at);
  if (start && start.getTime() <= now.getTime()) return 1;
  if (event.armed || event.source === "scheduled_recording") return 1;
  return 0;
}

const STEPS = ["Prep", "Record", "Summary", "Send follow-up"];

function Stepper({ step }: { step: number }) {
  return (
    <Steps
      label="Meeting steps"
      steps={STEPS.map((label, index) => ({
        key: label, label, state: index < step ? "done" : index === step ? "now" : "later",
      }))}
    />
  );
}

/** One node of the spine: the time in the gutter, a bead on the rail. */
function SpineNode({ time, kind, children, testId }: { time: ReactNode; kind: string; children: ReactNode; testId?: string }) {
  return (
    <li className="today-node" data-kind={kind} data-testid={testId}>
      <span className="today-time">{time}</span>
      <span className="today-bead" aria-hidden="true" />
      <div className="today-node-body">{children}</div>
    </li>
  );
}

/** A source that could not be read: one quiet line and Retry. */
function ReadFailed({ what, onRetry, testId }: { what: string; onRetry: () => void; testId: string }) {
  return (
    <div className="today-failed" data-testid={testId} role="status">
      <span className="kit-pill" data-tone="danger">{`Could not read ${what}`}</span>
      <Button dense variant="ghost" onClick={onRetry}>Retry</Button>
    </div>
  );
}

/** The local day of `d`, `YYYY-MM-DD`. */
function localDay(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** The seven local days of `now`'s week, Monday first. */
export function weekDays(now: Date): Date[] {
  const monday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - ((now.getDay() + 6) % 7));
  return Array.from({ length: 7 }, (_, i) => new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + i));
}

/** One day of This week: its meetings (the calendar's count) and the rows
 *  of Needs you due that day. */
export type WeekCount = { day: Date; meetings: number; due: NeedFace[]; events: DayEvent[] };

export function weekCounts(now: Date, door: DoorRead | null, work: readonly NeedFace[]): WeekCount[] {
  const calendar = new Map((door?.week?.days ?? []).map((d) => [d.date, d.count]));
  return weekDays(now).map((day) => {
    const key = localDay(day);
    const events = (door?.upcoming ?? []).filter((event) => {
      const start = when(event.starts_at);
      return start && localDay(start) === key && event.source !== "scheduled_recording";
    });
    const due = work.filter((face) => {
      const at = face.due ? when(face.due.length === 10 ? `${face.due}T00:00:00` : face.due) : null;
      return at && localDay(at) === key;
    });
    return { day, meetings: Math.max(calendar.get(key) ?? 0, events.length), due, events };
  });
}

/** `Mon 3 · Tue 2 · Thu 1`: the days with something, never a zero. */
export function weekLine(days: readonly WeekCount[]): string {
  return days
    .map((d) => ({ d, n: d.meetings + d.due.length }))
    .filter(({ n }) => n > 0)
    .map(({ d, n }) => `${WEEK_DAYS[d.day.getDay()]} ${n}`)
    .join(" · ");
}

/** This week, folded to a count per day; unfolded, each day's meetings and
 *  the rows due that day. It replaces The week window (D5 parks it). */
function ThisWeek({ days }: { days: readonly WeekCount[] }) {
  const [open, setOpen] = useState(false);
  const line = weekLine(days);
  const shown = days.filter((d) => d.events.length || d.due.length);
  return (
    <section className="today-fold" data-testid="today-week" aria-label="This week">
      <Button variant="chrome" className="today-fold-head" aria-expanded={open} data-testid="today-week-toggle"
        onClick={() => setOpen((value) => !value)} disabled={!line}>
        <span className="today-fold-mark" aria-hidden="true">{line ? (open ? "▾" : "▸") : ""}</span>
        <span className="today-fold-label">This week</span>
        <span className="today-fold-counts" data-testid="today-week-counts">{line || "Nothing this week"}</span>
      </Button>
      {open && line ? (
        <div className="today-fold-body" data-testid="today-week-days">
          {shown.map((d) => (
            <div key={localDay(d.day)} className="today-week-day">
              <span className="today-fold-kind">{`${WEEK_DAYS[d.day.getDay()]} ${d.day.getDate()}`}</span>
              <ul className="today-week-items">
                {d.events.map((event) => {
                  const start = when(event.starts_at);
                  return <li key={event.id}><span className="today-week-time">{start ? clock(start) : ""}</span>{event.title || event.event_title || "Meeting"}</li>;
                })}
                {d.due.map((face) => (
                  <li key={face.id}><span className="today-week-time">DUE</span>{face.personName && face.direction === "theirs" ? `${face.personName}: ${face.name}` : face.name}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}

export function TodayView({ sinceRequest = 0 }: { sinceRequest?: number }) {
  const [now, setNow] = useState(() => new Date());
  const [door, setDoor] = useState<DoorRead | null>(null);
  const [meetings, setMeetings] = useState<MeetingRow[]>([]);
  const [brief, setBrief] = useState<MondayBrief | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const rows = useNeedFaces();
  const [loaded, setLoaded] = useState(false);
  // MUST 1 (Astra r1 on #1111): the last summary made from here keeps its
  // receipt (every place the run reached) after its row leaves the spine.
  const [justMade, setJustMade] = useState<{ id: string; title: string } | null>(null);

  // PHILO-17 (Astra r1 on #1110, MUST 3): a source that could not be read
  // says so (with Retry); it never reads as empty.
  const [failed, setFailed] = useState<{ door: boolean; meetings: boolean; brief: boolean }>(
    { door: false, meetings: false, brief: false });
  const [actError, setActError] = useState<{ key: string; text: string } | null>(null);

  // One load at a time: a desk change while a load runs asks for ONE more
  // load after it (MUST 4: coalesced).
  const loading = useRef(false);
  const again = useRef(false);
  const load = useCallback(async () => {
    if (loading.current) { again.current = true; return; }
    loading.current = true;
    try {
      do {
        again.current = false;
        // Betterment D4: the brief is made by the hub when none is current
        // (`ensure`), so Since yesterday needs no press.
        const [doorRead, meetingRead, briefRead] = await Promise.all([
          apiFetch<DoorRead>("/api/door").then((v) => ({ ok: true as const, v }), () => ({ ok: false as const })),
          apiFetch<{ meetings?: MeetingRow[] }>("/api/meetings?limit=40").then((v) => ({ ok: true as const, v }), () => ({ ok: false as const })),
          apiFetch<MondayBrief | null>("/api/brief/latest?ensure=1").then((v) => ({ ok: true as const, v }), () => ({ ok: false as const })),
        ]);
        if (doorRead.ok) setDoor(doorRead.v);
        else setDoor((current) => current);
        if (meetingRead.ok) setMeetings(meetingRead.v.meetings ?? []);
        if (briefRead.ok) setBrief(briefRead.v ?? null);
        setFailed({ door: !doorRead.ok, meetings: !meetingRead.ok, brief: !briefRead.ok });
        setLoaded(true);
      } while (again.current);
    } finally {
      loading.current = false;
    }
  }, []);
  useEffect(() => { void load(); }, [load]);
  useOnDeskChanged(() => void load());
  // The countdown ticks; nothing moves (the words change in a fixed box).
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 30_000);
    return () => window.clearInterval(timer);
  }, []);

  const summary = useSummaryRun(
    (id) => readPlannedRoute(meetings.find((row) => String(row.id) === id)),
    () => void load(),
  );

  const today = startOfDay(now);
  const events = useMemo(() => (door?.upcoming ?? [])
    .filter((event) => {
      const start = when(event.starts_at);
      const end = when(event.ends_at) ?? start;
      return start && end && startOfDay(start) === today && end.getTime() >= now.getTime();
    }), [door, today, now]);
  // Late in the day the next meeting may be after midnight: when today has
  // none left, the next one within 12 hours leads (its time says the day).
  const soon = useMemo(() => {
    if (events.length) return null;
    const limit = now.getTime() + 12 * 3_600_000;
    return (door?.upcoming ?? []).find((event) => {
      const start = when(event.starts_at);
      return start && start.getTime() > now.getTime() && start.getTime() <= limit;
    }) ?? null;
  }, [door, events.length, now]);
  const next = events[0] ?? soon;
  const later = events.slice(1);
  const finish = useMemo(() => toFinish(meetings, now), [meetings, now]);
  const calendar = door?.calendar_configured ?? false;
  const needsLoaded = rows.needs.room !== null || Object.keys(rows.needs.errors).length > 0;
  const hasWork = rows.work.length > 0;
  // An empty desk: no calendar, no meeting, nothing waits. One line says
  // what fills Today (Betterment D4).
  const emptyDesk = Boolean(door && !failed.door && !calendar && meetings.length === 0 && !hasWork && needsLoaded);
  const phone = typeof window !== "undefined" && window.matchMedia?.("(max-width: 600px)").matches;
  const week = useMemo(() => weekCounts(now, door, rows.work), [now, door, rows.work]);

  // ONE filled primary per window (UX-CANON): the first row of Needs you,
  // else the next meeting's record verb, else the first summary to make,
  // else Connect calendar, else Record now.
  const lead = hasWork ? "needs" : next ? "next" : finish.length ? "finish" : !calendar && door && !failed.door ? "calendar" : "record";
  const recordNow = () => openSurfaceOr("record-live", "/live");

  // A press that fails says so beside its verb (MUST 3).
  const act = async (key: string, failText: string, run: () => Promise<unknown>) => {
    setBusy(key);
    setActError(null);
    try {
      const result = await run();
      if (result === false) setActError({ key, text: failText });
    } catch {
      setActError({ key, text: failText });
    } finally { setBusy(null); void load(); }
  };

  const title = (event: DayEvent) => event.title || event.event_title || "Meeting";
  const sprite = (event: DayEvent) => (event.person_relationship_id ? "person" : "meeting");

  const finishNodes = finish.map((row, index) => {
    const id = String(row.id);
    const at = when(row.started_at ?? row.created_at);
    const route = readPlannedRoute(row);
    const failed = meetingRowState(row).verb === "Retry";
    const sameDay = at && startOfDay(at) === today;
    return (
      <SpineNode key={id} kind="finish" testId="today-finish" time={at ? (sameDay ? clock(at) : SHORT_DAYS[at.getDay()]) : ""}>
        <div className="today-row">
          <div className="today-row-text">
            <Button variant="chrome" className="today-row-title" onClick={() => openSourceRef(`meeting:${id}`)}>
              {String(row.title ?? "Meeting")}
            </Button>
            <span className="today-row-meta">
              <span className="kit-pill" data-tone={failed ? "danger" : "warn"}>{failed ? "Summary failed" : "No summary yet"}</span>
            </span>
          </div>
          {/* MUST 2 (Astra r1 on #1110): where the run goes, before the
              press (the route and its fallbacks); after it, every place
              the run reached (the attempt receipt). CatalogRail's grammar. */}
          <span className="today-row-route">
            <RunAttempts receipt={executedReceipt(id, summary.runRefusal?.meetingId === id ? summary.runRefusal.refusal.receipt : undefined, readRunReceipt(row))} testId="today-attempts" />
            <RouteDisclosure route={summary.runRefusal?.meetingId === id ? summary.runRefusal.refusal.route : route} testId="today-route" />
          </span>
          {routeReady(route) ? (
            <Button dense variant={lead === "finish" && index === 0 ? "primary" : "secondary"} loading={summary.runningId === id}
              onClick={() => { setJustMade({ id, title: String(row.title ?? "Meeting") }); void summary.run(id, route); }} data-testid="today-make-summary">
              Make the summary
            </Button>
          ) : (
            <Button dense variant={lead === "finish" && index === 0 ? "primary" : "secondary"}
              onClick={() => openSurfaceOr("open-concierge", "/models", "meetings")} data-testid="today-choose-engine">
              Choose engine
            </Button>
          )}
        </div>
      </SpineNode>
    );
  });

  const nextStart = next ? when(next.starts_at) : null;
  const nextOpen = next ? calendarOpener(next) : null;
  const started = Boolean(nextStart && nextStart.getTime() <= now.getTime());
  const armed = Boolean(next && (next.armed || next.source === "scheduled_recording"));
  const armsAt = next ? when(next.armed?.arms_at ?? next.starts_at) : null;
  const nextNode = next && nextStart ? (
    <SpineNode kind="next" testId="today-next" time={startOfDay(nextStart) === today ? clock(nextStart) : <>{SHORT_DAYS[nextStart.getDay()]}<br />{clock(nextStart)}</>}>
      <article className="today-next" aria-label={`Next: ${title(next)}`}>
        <header className="today-next-bar">
          <span className="today-next-label">NEXT</span>
          <span className="today-next-in" data-testid="today-countdown">{countdown(nextStart, now)}</span>
        </header>
        <div className="today-next-body">
          <span className="today-next-sprite" aria-hidden="true">
            <img src={`${SPRITES}${sprite(next)}.png`} alt="" draggable={false} />
          </span>
          <div className="today-next-text">
            <span className="today-next-title">{title(next)}</span>
            <span className="today-row-meta">
              {next.person_label ? <><Avatar name={next.person_label} /> {next.person_label}</> : null}
              {next.project_name ? <span className="kit-pill" data-tone="info">{next.project_name}</span> : null}
              {armed ? (
                <span className="kit-pill" data-tone="danger" data-live="" data-testid="today-armed">
                  {armsAt ? `Armed for ${clock(armsAt)}` : "Armed"}
                </span>
              ) : null}
            </span>
          </div>
        </div>
        <Stepper step={currentStep(next, now)} />
        <div className="today-next-verbs">
          {nextOpen ? <Button dense onClick={nextOpen} data-testid="today-open-prep">Prep</Button> : null}
          {started || armed ? (
            <Button dense variant={lead === "next" ? "primary" : "secondary"} onClick={recordNow} data-testid="today-record">Record</Button>
          ) : next.source === "calendar_event" ? (
            <Button dense variant={lead === "next" ? "primary" : "secondary"} loading={busy === "arm"} data-testid="today-arm"
              onClick={() => void act("arm", "Not armed. Try again", () => useDesk.getState().armEventRecording(next.id))}>
              Record when it starts
            </Button>
          ) : null}
          {actError?.key === "arm" ? <span className="kit-pill" data-tone="danger" role="status" data-testid="today-arm-failed">{actError.text}</span> : null}
        </div>
      </article>
    </SpineNode>
  ) : null;

  const laterNodes = later.map((event) => {
    const start = when(event.starts_at);
    const open = calendarOpener(event);
    return (
      <SpineNode key={event.id} kind="later" testId="today-later" time={start ? clock(start) : ""}>
        <div className="today-row">
          <span className="today-row-sprite" aria-hidden="true"><img src={`${SPRITES}${sprite(event)}.png`} alt="" draggable={false} /></span>
          <div className="today-row-text">
            <span className="today-row-name">{title(event)}</span>
            <span className="today-row-meta">
              {event.person_label ? <span>{event.person_label}</span> : null}
              {event.project_name ? <span className="kit-pill" data-tone="info">{event.project_name}</span> : null}
              {event.armed ? <span className="kit-pill" data-tone="danger">Armed</span> : null}
            </span>
          </div>
          {open ? <Button dense variant="ghost" onClick={open}>Prep</Button> : null}
        </div>
      </SpineNode>
    );
  });

  const nowNode = (
    <li className="today-now" data-testid="today-now" aria-label={`Now ${clock(now)}`}>
      <span className="today-time today-now-time">{clock(now)}</span>
      <span className="today-now-bead" aria-hidden="true" />
      <span className="today-now-line" aria-hidden="true" />
    </li>
  );

  // The row as the latest read has it: the run's state and its receipt.
  const madeRow = justMade ? meetings.find((row) => String(row.id) === justMade.id) ?? null : null;
  const madeReceipt = justMade
    ? executedReceipt(justMade.id,
      summary.runRefusal?.meetingId === justMade.id ? summary.runRefusal.refusal.receipt : undefined,
      readRunReceipt(madeRow))
    : null;
  const madeState = madeRow ? meetingRowState(madeRow) : null;
  const madeDone = Boolean(madeRow && (madeRow.has_summary || madeState?.label === "SUMMARY STORED" || madeState?.label === "RAN"));
  const madeFailed = madeState?.verb === "Retry";
  const justMadeNode = justMade && (madeReceipt || madeRow) && !finish.some((row) => String(row.id) === justMade.id) ? (
    <SpineNode kind="made" testId="today-just-made" time="">
      <div className="today-row">
        <div className="today-row-text">
          <Button variant="chrome" className="today-row-title" onClick={() => openSourceRef(`meeting:${justMade.id}`)}>
            {justMade.title}
          </Button>
          <span className="today-row-meta">
            <span className="kit-pill" data-tone={madeDone ? "ok" : madeFailed ? "danger" : "info"} data-dot="" data-live={!madeDone && !madeFailed ? "" : undefined}>
              {madeDone ? "Summary made" : madeFailed ? "Summary failed" : "Making the summary"}
            </span>
          </span>
        </div>
        <span className="today-row-route">
          <RunAttempts receipt={madeReceipt} testId="today-made-attempts" />
        </span>
      </div>
    </SpineNode>
  ) : null;

  // The retry is named outside the JSX: the copy scanner reads an arrow's
  // `>` after a JSX tag as the start of text.
  const retry = () => void load();
  const doorFailedNode = failed.door ? (
    <li className="today-section"><span /><span /><ReadFailed what="the calendar" onRetry={retry} testId="today-door-failed" /></li>
  ) : null;
  const meetingsFailedNode = failed.meetings ? (
    <li className="today-section"><span /><span /><ReadFailed what="the meetings" onRetry={retry} testId="today-meetings-failed" /></li>
  ) : null;
  const emptyNode = door && !next && !failed.door && !emptyDesk ? (
    <SpineNode kind="empty" testId="today-empty" time="">
      <div className="today-row">
        <div className="today-row-text">
          <span className="today-row-name">{calendar ? "No more meetings today" : "No calendar yet"}</span>
        </div>
        {calendar ? null : (
          <Button dense variant={lead === "calendar" ? "primary" : "secondary"}
            onClick={() => openSurfaceOr("configure-settings", "/settings", "meetings")}>Connect calendar</Button>
        )}
      </div>
    </SpineNode>
  ) : null;

  const pastToday = finish.length ? (
    <li className="today-section" aria-hidden="true"><span>TO FINISH</span></li>
  ) : null;

  const ahead = events.length;
  return (
    <>
      {/* Busy until the first load ends: the day's rows land after it and
          move what is drawn (the desk sweep's still fence, under load). */}
      <div className="desk-pullout-body desk-surface-body intelligence-pullout today" aria-busy={loaded ? undefined : true}>
        <div className="today-head">
          <h2 className="today-day" data-testid="today-day">{`${DAY_NAMES[now.getDay()]} ${now.getDate()} ${MONTH_NAMES[now.getMonth()]}`}</h2>
          <span className="today-strip">
            {ahead ? <span><b>{ahead}</b> {ahead === 1 ? "meeting ahead" : "meetings ahead"}</span> : null}
            {finish.length ? <span><b>{finish.length}</b> to finish</span> : null}
          </span>
          <span className="today-head-sp" />
          <Button dense variant={lead === "record" ? "primary" : "secondary"} onClick={recordNow} data-testid="today-record-now">Record now</Button>
        </div>
        <div className="today-grid">
          <TodayNeeds work={rows.work} count={rows.needs.count} now={now} limit={phone ? NEEDS_TOP_PHONE : NEEDS_TOP}
            primary={lead === "needs"} projects={rows.multipleProjects} loaded={needsLoaded} emptyDesk={emptyDesk}
            failed={rows.needs.room === null && Object.keys(rows.needs.errors).length > 0} calendarLead={lead === "calendar"}
            next={next && nextStart ? `${title(next)} at ${clock(nextStart)}` : null} />
          <ol className="today-spine" aria-label="Today">
            {nowNode}
            {nextNode}
            {laterNodes}
            {doorFailedNode}
            {emptyNode}
            {justMadeNode}
            {meetingsFailedNode}
            {pastToday}
            {finishNodes}
          </ol>
        </div>
        <SinceYesterday brief={brief} failed={failed.brief} now={now} openRequest={sinceRequest} onRetry={retry} />
        <ThisWeek days={week} />
      </div>
      <SurfaceFooter receipt={summary.receipt ? <span className="surface-footer-receipt-line" role="status">{summary.receipt.text}</span> : <NeedsDroppedReceipt />} />
    </>
  );
}
