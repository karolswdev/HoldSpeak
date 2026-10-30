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
import { programsTodayLine, type ProgramsSinceMorning } from "../../programs/lamp";
import { useProgramFrames } from "../../programs/api";
import { openSourceRef } from "../../surface/citations";
import { calendarOpener, openDecisionRecord, openRef } from "../../openObject";
import { useDesk } from "../../store";
import { useNeedFaces, useDropped, NeedsDroppedReceipt } from "../../needs/NeedsDrawer";
import { TodayNeeds } from "../../needs/TodayNeeds";
import type { NeedFace } from "../../needs/needsFace";
import { SinceYesterday, type MondayBrief } from "./BriefView";
import { PreparedBlock, type PreparedRead } from "./PreparedBlock";
import { MEETING_CHANGE_KINDS, NEEDS_YOU_CHANGE_KINDS, useOnDeskChanged } from "../../useDeskChangedRefresh";
import { newsWords, useAutomationNews } from "../../automationNews";
import { Avatar, DotWord, StatusBar, Steps, TickNumber, ToolGlyph, Toolbar, countWords, meetingSteps, type StatusBarItem } from "../../surface/kit";
import { openChairWindow } from "../../chair/chairWindows";
import { agentSpriteName } from "../../sprites";
import { meetingRowState } from "../../../pages/cores/history/helpers";
import { useSummaryRun } from "../../../pages/cores/history/useSummaryRun";
import { executedReceipt, readPlannedRoute, readRunReceipt, routeReady } from "../../../meetings/summaryRoute";
import { RouteDisclosure, RunAttempts, routeTitle } from "../../../meetings/RouteDisclosure";
import { StandingPagesSection, useStandingPages } from "../../standingPages";
import { useAgentFlights, useAgentFlightsLive, type AgentFlight } from "../../agentFlights";
import { conductorMembers, fleetCounts } from "../../conductor/members";
import { AGENT_NAME, type AgentId } from "../../firstrun/agentsStep";
import { openAgentLane } from "../../shell";
import "./today.css";
import { usePhoneToday } from "../../calls/phoneApi";
import { openPhoneWing } from "../../calls/phoneFocus";
import { Token } from "../../surface/Token";

/** Betterment AG9: Today's Agents line, only what is there:
 *  `2 agents need you · 1 finished`; "" with nothing. */
export function agentsLine(needYou: number, finished: number): string {
  return [
    needYou ? `${needYou} ${needYou === 1 ? "agent needs" : "agents need"} you` : "",
    finished ? `${finished} finished` : "",
  ].filter(Boolean).join(" · ");
}

/** `Claude Code finished Draft test scaffolding`. */
export function agentResultWords(flight: AgentFlight): string {
  return `${AGENT_NAME[flight.agent as AgentId] ?? flight.agent} finished ${flight.title || "its work"}`;
}

/** Icons D: the 20 px drawings that lead a row of the day. */
const GLYPHS = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/20/`;

/** A row's leading 20 px glyph: a 1:1 wears the person's disc. */
function RowGlyph({ sprite, person }: { sprite: string; person?: string }) {
  return (
    <span className="today-row-sprite" aria-hidden="true">
      {person ? <Avatar name={person} /> : <img src={`${GLYPHS}${sprite}.png`} alt="" width={20} height={20} draggable={false} />}
    </span>
  );
}

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

const SHORT_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const WEEK_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const SHORT_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
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

const LONG_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

/** DELIGHT slice 2 (2026-10-27, canvases/delight-2026-10-27.html "Today
 *  knows the hour"): the part of the day, from the clock. Night is before
 *  05:00 and from 22:00. */
export type DayPart = "morning" | "afternoon" | "evening" | "night";
export function dayPart(d: Date): DayPart {
  const h = d.getHours();
  if (h < 5 || h >= 22) return "night";
  if (h < 12) return "morning";
  if (h < 18) return "afternoon";
  return "evening";
}

/** The day line greets by the hour: `Tuesday morning`. */
export function dayGreeting(d: Date): string {
  return `${LONG_DAYS[d.getDay()]} ${dayPart(d)}`;
}

/** The day's light on Today's paper: a warm wash in the morning, none in
 *  the afternoon, a cool wash in the evening and at night (static colour,
 *  at most 6 % tint; today.css). */
export function dayLight(d: Date): "warm" | "cool" | undefined {
  const part = dayPart(d);
  if (part === "morning") return "warm";
  if (part === "afternoon") return undefined;
  return "cool";
}

/** DELIGHT slice 3: "That is the day" is said once per day, per viewer.
 *  The flag is the local date it was said on; storage that throws or is
 *  empty only means the line is said again. */
export const DAY_SAID_KEY = "holdspeak.today.daySaid";
export function dayKey(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function readDaySaid(): string | null {
  try { return window.localStorage.getItem(DAY_SAID_KEY); } catch { return null; }
}
function writeDaySaid(key: string): void {
  try { window.localStorage.setItem(DAY_SAID_KEY, key); } catch { /* a private window: said again */ }
}

/** DELIGHT slice 5 (2026-10-28, canvases/delight-2026-10-27.html "Today
 *  knows the hour", the evening): after 17:00 Today lists what got done
 *  since the morning (`GET /api/today/since-morning`: tasks ticked,
 *  decisions recorded, notes filed, sends sent, meetings held), newest
 *  first, each an object row that opens its object. It is said once per
 *  day: the first evening open shows the list; a later open the same day
 *  folds it to one line (the "That is the day" pattern, slice 3). */
export const EVENING_HOUR = 17;
export const EVENING_SAID_KEY = "holdspeak.today.eveningSaid";
export type DoneRow = { kind: string; ref: string; title: string; word: string; at: string };
type DoneRead = { since?: string; items?: DoneRow[]; programs?: ProgramsSinceMorning | null };
function readEveningSaid(): string | null {
  try { return window.localStorage.getItem(EVENING_SAID_KEY); } catch { return null; }
}
function writeEveningSaid(key: string): void {
  try { window.localStorage.setItem(EVENING_SAID_KEY, key); } catch { /* a private window: said again */ }
}
/** A done row's 20 px glyph (the kind's own D object). */
const DONE_SPRITE: Record<string, string> = {
  action: "action-item", decision: "decision", note: "note", send: "artifact", meeting: "meeting",
};
/** A done row opens its object: a decision record in the Decisions reader,
 *  every other ref through the one open grammar. */
export function openDone(ref: string): void {
  if (ref.startsWith("decision_record:")) openDecisionRecord(ref.slice("decision_record:".length));
  else openRef(ref);
}

/** Programs (PG18): `Programs: 1 running, 1 waits on you`, one object row
 *  that opens the Programs window. */
function ProgramsLine({ words }: { words: string }) {
  return (
    <Button variant="chrome" className="today-done-row today-programs" data-kind="program" data-testid="today-programs"
      onClick={() => openSurfaceOr("open-programs", "/")}>
      <img src={`${GLYPHS}program.png`} alt="" width={20} height={20} draggable={false} />
      <span className="today-done-title">{words}</span>
    </Button>
  );
}

function SinceThisMorning({ rows, failed, open, onToggle, onRetry, now, programs = "", phone = "" }: {
  rows: readonly DoneRow[]; failed: boolean; open: boolean; onToggle: () => void; onRetry: () => void; now: Date;
  /** Programs (2026-10-28): `Programs: 1 running, 1 waits on you`, or "". */
  programs?: string;
  /** Phone (2026-10-28): `Reached you 2 times: 1 answered`, or "". */
  phone?: string;
}) {
  if (failed) {
    return (
      <section className="today-fold today-done" data-testid="today-done" aria-label="Since this morning">
        <ReadFailed what="today's work" onRetry={onRetry} testId="today-done-failed" />
      </section>
    );
  }
  const shown = open && rows.length > 0;
  return (
    <section className="today-fold today-done" data-testid="today-done" aria-label="Since this morning">
      <Button variant="chrome" className="today-fold-head" aria-expanded={rows.length ? shown : undefined}
        data-testid="today-done-toggle" onClick={onToggle} disabled={!rows.length}>
        <span className="today-fold-mark" aria-hidden="true">{rows.length ? (shown ? "▾" : "▸") : ""}</span>
        <span className="today-fold-label">Since this morning</span>
        <span className="today-fold-counts" data-testid="today-done-counts">
          {rows.length ? `${rows.length} done` : "Nothing done yet"}
        </span>
      </Button>
      {programs ? <ProgramsLine words={programs} /> : null}
      {phone ? (
        <Button variant="chrome" className="today-done-row today-phone" data-kind="phone" data-testid="today-phone"
          onClick={() => openPhoneWing()}>
          <img src={`${GLYPHS}call.png`} alt="" width={20} height={20} draggable={false} />
          <span className="today-done-title">{phone}</span>
        </Button>
      ) : null}
      {shown ? (
        <ul className="today-done-list" data-testid="today-done-rows">
          {rows.map((row) => {
            const at = when(row.at);
            return (
              <li key={`${row.kind}:${row.ref}:${row.at}`}>
                <Button variant="chrome" className="today-done-row" data-kind={row.kind} data-testid="today-done-row"
                  onClick={() => openDone(row.ref)}>
                  <img src={`${GLYPHS}${DONE_SPRITE[row.kind] ?? "artifact"}.png`} alt="" width={20} height={20} draggable={false} />
                  <span className="today-done-title">{row.title}</span>
                  <span className="today-done-word">{row.word}</span>
                  <span className="today-done-time">{at ? (startOfDay(at) === startOfDay(now) ? clock(at) : SHORT_DAYS[at.getDay()]) : ""}</span>
                </Button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </section>
  );
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

function Stepper({ step }: { step: number }) {
  // W1-TRUTH: the one meeting stepper (kit meetingSteps), shared with Live.
  return <Steps label="Meeting steps" steps={meetingSteps(step)} />;
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
      <DotWord tone="fail">{`Could not read ${what}`}</DotWord>
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
                  <li key={face.id}><span className="today-week-time">Due</span>{face.personName && face.direction === "theirs" ? `${face.personName}: ${face.name}` : face.name}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function TodayMemoryPages({ now }: { now: Date }) {
  const pages = useStandingPages("desk");
  const owe = pages.filter((page) => page.slug === "what-i-owe");
  const changed = now.getDay() === 1 ? pages.filter((page) => page.slug === "what-changed-this-week") : [];
  return (
    <>
      {owe.length ? <div data-testid="today-owe"><StandingPagesSection pages={owe} presentation="questions" /></div> : null}
      {changed.length ? <div data-testid="today-changed"><StandingPagesSection pages={changed} presentation="questions" /></div> : null}
    </>
  );
}

export function TodayView({ sinceRequest = 0 }: { sinceRequest?: number }) {
  const [now, setNow] = useState(() => new Date());
  const [door, setDoor] = useState<DoorRead | null>(null);
  const [meetings, setMeetings] = useState<MeetingRow[]>([]);
  const [brief, setBrief] = useState<MondayBrief | null>(null);
  // Betterment daily D9: Morning prep's newest result (the Prepared block)
  // and the automation Prepare now runs.
  const [prepared, setPrepared] = useState<PreparedRead | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const rows = useNeedFaces();
  const dropped = useDropped((st) => st.dropped);
  // Betterment AG9: the agents: a line when one needs him or finished, and a
  // card for each finished turn he has not opened (New).
  useAgentFlightsLive();
  const agentFlights = useAgentFlights((st) => st.flights);
  const agentSessions = useAgentFlights((st) => st.sessions);
  const agentCounts = useMemo(
    () => fleetCounts(conductorMembers({ detect: null, sessions: agentSessions, flights: agentFlights, launchedAt: {} })),
    [agentSessions, agentFlights]);
  const finishedAgents = useMemo(() => agentFlights.filter((f) => f.state === "done" && f.isNew && f.launchId), [agentFlights]);
  const agentsWords = agentsLine(agentCounts.needYou, finishedAgents.length);
  // Programs (PG18): one line when any Program moved today, at any hour,
  // from the hub's `programs` block of the Since this morning read.
  const [programsBlock, setProgramsBlock] = useState<ProgramsSinceMorning | null>(null);
  const programsToday = programsTodayLine(programsBlock);
  // Phone (2026-10-28): one Since this morning line when the desk reached him.
  const phoneToday = usePhoneToday(now.getHours() >= EVENING_HOUR);
  // Betterment A6: an automation's NEW result ("<name> has a new result").
  const news = useAutomationNews();
  const [loaded, setLoaded] = useState(false);
  // MUST 1 (Astra r1 on #1111): the last summary made from here keeps its
  // receipt (every place the run reached) after its row leaves the spine.
  const [justMade, setJustMade] = useState<{ id: string; title: string } | null>(null);
  // DELIGHT slice 5: Since this morning, drawn after 17:00 only. The read
  // runs at any hour: its Programs block (PG18) feeds the Programs line.
  const evening = now.getHours() >= EVENING_HOUR;
  const eveningRef = useRef(evening);
  eveningRef.current = evening;
  const [done, setDone] = useState<{ rows: DoneRow[]; failed: boolean } | null>(null);
  const readSince = useCallback(async () => {
    const doneRead = await apiFetch<DoneRead>("/api/today/since-morning")
      .then((v) => ({ ok: true as const, v }), () => ({ ok: false as const }));
    // A failed read keeps the last Programs line (never invents none).
    if (doneRead.ok) setProgramsBlock(doneRead.v?.programs ?? null);
    if (eveningRef.current) {
      // A read that fails says so; one that answers keeps the hub's order (newest first).
      setDone((current) => doneRead.ok ? { rows: doneRead.v?.items ?? [], failed: false }
        : { rows: current?.rows ?? [], failed: !current?.rows.length });
    }
  }, []);
  useProgramFrames(() => void readSince());

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
        const [doorRead, meetingRead, briefRead, preparedRead] = await Promise.all([
          apiFetch<DoorRead>("/api/door").then((v) => ({ ok: true as const, v }), () => ({ ok: false as const })),
          apiFetch<{ meetings?: MeetingRow[] }>("/api/meetings?limit=40").then((v) => ({ ok: true as const, v }), () => ({ ok: false as const })),
          apiFetch<MondayBrief | null>("/api/brief/latest?ensure=1").then((v) => ({ ok: true as const, v }), () => ({ ok: false as const })),
          apiFetch<PreparedRead>("/api/automations/prepared").then((v) => ({ ok: true as const, v }), () => ({ ok: false as const })),
        ]);
        if (doorRead.ok) setDoor(doorRead.v);
        else setDoor((current) => current);
        if (meetingRead.ok) setMeetings(meetingRead.v.meetings ?? []);
        if (briefRead.ok) setBrief(briefRead.v ?? null);
        // A Prepared read that fails keeps the last block (never invents none).
        if (preparedRead.ok) setPrepared(preparedRead.v ?? null);
        await readSince();
        setFailed({ door: !doorRead.ok, meetings: !meetingRead.ok, brief: !briefRead.ok });
        setLoaded(true);
      } while (again.current);
    } finally {
      loading.current = false;
    }
  }, [readSince]);
  useEffect(() => { void load(); }, [load]);
  useOnDeskChanged(() => void load(), [
    ...MEETING_CHANGE_KINDS,
    ...NEEDS_YOU_CHANGE_KINDS,
    "brief", "calendar", "calendar_event", "project_update", "scheduled_recording", "workbench",
  ]);
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
  // The day the closing line was said before this window opened (read once).
  const [saidOn] = useState(readDaySaid);
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
  const emptyDesk = Boolean(door && !failed.door && !calendar && meetings.length === 0 && !hasWork && needsLoaded
    && !news.rows?.length && !prepared?.prepared && !agentsWords);
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
          <RowGlyph sprite="meeting" />
          <div className="today-row-text">
            <Button variant="chrome" className="today-row-title" onClick={() => openSourceRef(`meeting:${id}`)}>
              {String(row.title ?? "Meeting")}
            </Button>
            <span className="today-row-meta">
              <DotWord tone={failed ? "fail" : "warn"}>{failed ? "Summary failed" : "No summary yet"}</DotWord>
            </span>
          </div>
          {/* MUST 2 (Astra r1 on #1110), amended by the owner ruling of
              2026-10-25: where the run goes rides the verb's hover title;
              the row shows only a failed attempt or a route that cannot run. */}
          <span className="today-row-route">
            <RunAttempts receipt={executedReceipt(id, summary.runRefusal?.meetingId === id ? summary.runRefusal.refusal.receipt : undefined, readRunReceipt(row))} testId="today-attempts" />
            <RouteDisclosure route={summary.runRefusal?.meetingId === id ? summary.runRefusal.refusal.route : route} testId="today-route" />
          </span>
          {routeReady(route) ? (
            <Button dense variant={lead === "finish" && index === 0 ? "primary" : "secondary"} loading={summary.runningId === id}
              title={routeTitle(route)}
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
        <div className="today-next-body">
          <RowGlyph sprite={sprite(next)} person={next.person_label} />
          <div className="today-next-text">
            <span className="today-next-title">{title(next)}</span>
            <span className="today-row-meta">
              <span className="today-next-label">Next</span>
              <span className="today-next-in" data-testid="today-countdown">{countdown(nextStart, now)}</span>
              {next.person_label ? <span>{next.person_label}</span> : null}
              {next.project_name ? <span>{next.project_name}</span> : null}
              {armed ? (
                <DotWord tone="fail" className="today-armed" data-testid="today-armed">
                  {armsAt ? `Armed for ${clock(armsAt)}` : "Armed"}
                </DotWord>
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
          {actError?.key === "arm" ? <span role="status" data-testid="today-arm-failed"><DotWord tone="fail">{actError.text}</DotWord></span> : null}
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
          <RowGlyph sprite={sprite(event)} person={event.person_label} />
          <div className="today-row-text">
            <span className="today-row-name">{title(event)}</span>
            <span className="today-row-meta">
              {event.person_label ? <span>{event.person_label}</span> : null}
              {event.project_name ? <span>{event.project_name}</span> : null}
              {event.armed ? <DotWord tone="fail">Armed</DotWord> : null}
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
        <RowGlyph sprite="meeting" />
        <div className="today-row-text">
          <Button variant="chrome" className="today-row-title" onClick={() => openSourceRef(`meeting:${justMade.id}`)}>
            {justMade.title}
          </Button>
          <span className="today-row-meta">
            <DotWord tone={madeDone ? "ok" : madeFailed ? "fail" : "info"}>
              {madeDone ? "Summary made" : madeFailed ? "Summary failed" : "Making the summary"}
            </DotWord>
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
            onClick={() => openSurfaceOr("configure-settings", "/settings", "integration:calendar")}>Connect calendar</Button>
        )}
      </div>
    </SpineNode>
  ) : null;

  // Betterment A6: each automation with a NEW result, newest first. Opening
  // its window reads the result, and the row goes (here, on the Dock, at home).
  // Betterment D9: the automation that fills Prepared shows its NEW there.
  const preparedId = prepared?.prepared?.workbench_id;
  const newsNodes = (news.rows ?? []).filter((row) => row.workbench_id !== preparedId).map((row) => {
    const at = when(row.newest_at);
    return (
      <SpineNode key={row.workbench_id} kind="result" testId="today-new-result"
        time={at ? (startOfDay(at) === today ? clock(at) : SHORT_DAYS[at.getDay()]) : ""}>
        <div className="today-row">
          <RowGlyph sprite="cartridge" />
          <div className="today-row-text">
            <Button variant="chrome" className="today-row-title"
              onClick={() => useDesk.getState().openWorkbenchWindow(row.workbench_id)}>
              {newsWords(row)}
            </Button>
          </div>
          <Button dense variant="secondary" data-testid="today-open-result"
            aria-label={`Open ${row.name}`}
            onClick={() => useDesk.getState().openWorkbenchWindow(row.workbench_id)}>
            Open
          </Button>
        </div>
      </SpineNode>
    );
  });

  const agentResultNodes = finishedAgents.map((flight) => (
    <SpineNode key={`agent:${flight.launchId}`} kind="result" testId="today-agent-result" time="">
      <div className="today-row">
        <RowGlyph sprite={agentSpriteName(flight.agent)} />
        <div className="today-row-text">
          <Button variant="chrome" className="today-row-title" onClick={() => openAgentLane(String(flight.launchId))}>
            {agentResultWords(flight)}
          </Button>
        </div>
        <Button dense variant="secondary" data-testid="today-open-agent-result"
          aria-label={`Open ${flight.title}`} onClick={() => openAgentLane(String(flight.launchId))}>
          Open
        </Button>
      </div>
    </SpineNode>
  ));

  const pastToday = finish.length ? (
    <li className="today-section" aria-hidden="true"><span>To finish</span></li>
  ) : null;

  const ahead = events.length;
  const prepareWith = prepared?.automation ?? null;
  const decide = rows.work.filter((face) => face.verbs.kind === "decide").length;
  const nextWords = next && nextStart && !started
    ? `next ${next.person_relationship_id ? "1:1" : "meeting"} ${countdown(nextStart, now)}`
    : null;
  // Window grammar: the status bar says the day in warm words with a lamp,
  // never a zero; the receipt of the last run beside them.
  // DELIGHT slice 2 (a small joy): after the day's last meeting, with a
  // meeting held today and nothing left on today's calendar, the status bar
  // says so in place of the count ahead.
  const metToday = meetings.some((row) => {
    const at = when(row.started_at ?? row.created_at);
    return at !== null && startOfDay(at) === today;
  });
  // Said once per day: a window opened again the same day shows the count.
  const dayDone = loaded && !failed.door && ahead === 0 && metToday && now.getHours() >= 12
    && saidOn !== dayKey(now);
  useEffect(() => { if (dayDone) writeDaySaid(dayKey(now)); }, [dayDone, now]);
  // The evening list is said once per day: open on the first evening read.
  const [eveningSaidOn] = useState(readEveningSaid);
  const [sinceOpen, setSinceOpen] = useState<boolean | null>(null);
  const sinceShown = sinceOpen ?? eveningSaidOn !== dayKey(now);
  const doneLoaded = done !== null && !done.failed;
  // The clock passes 17:00 with Today open: one more read fetches the list.
  useEffect(() => { if (evening && loaded && done === null) void load(); }, [evening, loaded, done, load]);
  useEffect(() => { if (evening && doneLoaded) writeEveningSaid(dayKey(now)); }, [evening, doneLoaded, now]);
  const statusItems: Array<StatusBarItem | null> = [
    dayDone
      ? { key: "day", lamp: "ok", text: "That is the day", testId: "today-status-day" }
      : { key: "ahead", lamp: "info", text: countWords(ahead, "meeting ahead", "meetings ahead"), testId: "today-status-ahead" },
    { key: "finish", lamp: "warn", text: countWords(finish.length, "to finish", "to finish"), testId: "today-status-finish" },
    { key: "decide", lamp: "ask", text: countWords(decide, "decision to make", "decisions to make"), testId: "today-status-decide" },
    nextWords ? { key: "next", text: nextWords, testId: "today-status-next" } : null,
    summary.receipt
      ? { key: "receipt", text: <Token className="surface-footer-receipt-line">{summary.receipt.text}</Token> }
      : dropped ? { key: "dropped", text: <NeedsDroppedReceipt /> } : null,
  ];
  const needsCount = rows.needs.count;
  return (
    <>
      {/* Busy until the first load ends: the day's rows land after it and
          move what is drawn (the desk sweep's still fence, under load). */}
      <div className="desk-pullout-body desk-surface-body intelligence-pullout today" aria-busy={loaded ? undefined : true}
        data-light={dayLight(now)} data-testid="today-body">
        {/* Window grammar: no headline (Today is the title bar). The verbs
            sit on the toolbar; the date is a quiet fact at its end. */}
        <Toolbar
          label="Today"
          className="today-toolbar"
          data-testid="today-toolbar"
          trailingStays
          trailing={(
            /* DELIGHT slice 2: the day line greets by the hour, then the date. */
            <span className="today-date" data-testid="today-day" title={`${SHORT_DAYS[now.getDay()]} ${now.getDate()} ${SHORT_MONTHS[now.getMonth()]}`}>
              <span className="today-greeting" data-testid="today-greeting">{dayGreeting(now)}</span>
              <span className="today-date-day">{` · ${now.getDate()} ${SHORT_MONTHS[now.getMonth()]}`}</span>
            </span>
          )}
        >
          <Button dense variant={lead === "record" ? "primary" : "secondary"} onClick={recordNow} data-testid="today-record-now">
            <ToolGlyph kind="record" />
            Record now
          </Button>
          {prepareWith ? (
            <Button dense variant="secondary" loading={busy === "prepare"} data-testid="today-prepare-now"
              onClick={() => void act("prepare", "Not prepared. Try again", () =>
                apiFetch(`/api/workbenches/${encodeURIComponent(prepareWith.id)}/run`, { method: "POST", json: {} }))}>
              {busy === "prepare" ? null : <ToolGlyph kind="run" />}
              Prepare now
            </Button>
          ) : null}
          <Button dense variant="secondary" data-testid="today-refresh" onClick={retry}>
            <ToolGlyph kind="retry" />
            Refresh
          </Button>
          <Button dense variant="secondary" className="today-needs-toggle" data-testid="today-needs-all"
            onClick={() => openChairWindow("chair:needs")}>
            <ToolGlyph kind="tasks" />
            Needs you{needsCount > 0 ? <b className="today-needs-count" data-testid="today-needs-count"><TickNumber value={needsCount} /></b> : null}
          </Button>
          {actError?.key === "prepare" ? <span role="status"><DotWord tone="fail">{actError.text}</DotWord></span> : null}
        </Toolbar>
        <div className="today-scroll">
          {evening && done ? (
            <SinceThisMorning rows={done.rows} failed={done.failed} open={sinceShown} now={now} programs={programsToday} phone={phoneToday}
              onToggle={() => setSinceOpen(!sinceShown)} onRetry={retry} />
          ) : programsToday ? (
            /* PG18: before 17:00 the fold is not drawn; the Programs line
               heads the day instead. */
            <div className="today-programs-head" data-testid="today-programs-head"><ProgramsLine words={programsToday} /></div>
          ) : null}
          <PreparedBlock read={prepared} events={door?.upcoming ?? []} />
          <div className="today-grid">
            <TodayNeeds work={rows.work} count={rows.needs.count} now={now} limit={phone ? NEEDS_TOP_PHONE : NEEDS_TOP}
              primary={lead === "needs"} projects={rows.multipleProjects} loaded={needsLoaded} emptyDesk={emptyDesk}
              failed={rows.needs.room === null && Object.keys(rows.needs.errors).length > 0} calendarLead={lead === "calendar"}
              next={next && nextStart ? `${title(next)} at ${clock(nextStart)}` : null}
              peopleUnread={Boolean(rows.needs.peopleUnread)} />
            <section className="today-day-section" aria-label="The day">
              <h3 className="today-section-cap">The day</h3>
              <ol className="today-spine" aria-label="Today">
                {nowNode}
                {nextNode}
                {laterNodes}
                {doorFailedNode}
                {emptyNode}
                {justMadeNode}
                {agentResultNodes}
                {newsNodes}
                {meetingsFailedNode}
                {pastToday}
                {finishNodes}
              </ol>
            </section>
          </div>
          <TodayMemoryPages now={now} />
          <SinceYesterday brief={brief} failed={failed.brief} now={now} openRequest={sinceRequest} onRetry={retry} />
          <ThisWeek days={week} />
        </div>
      </div>
      <StatusBar
        className="today-status"
        data-testid="today-status"
        items={statusItems}
        verbs={agentsWords ? (
          <Button dense variant="secondary" className="today-agents" data-testid="today-agents"
            onClick={() => openSurfaceOr("open-conductor", "/conductor")}>
            {agentsWords}
          </Button>
        ) : undefined}
      />
    </>
  );
}
