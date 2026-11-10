// Parked 2026-11-09: Today is a Rail client; Needs you owns answers.
/** PHILO-17 (owner pick 2026-10-11, concept C), in the language of
 *  2026-11-08: Today is ONE page. In order: the mast (the part of the day,
 *  the facts in mono, Record now, Prepare now) and its spine, the one thing
 *  first (a raised plate: the next meeting, else the item that waits on him
 *  most in Needs you), the top of Needs you (the same rows as the Needs-you
 *  window), the day as a plain list, Since yesterday (the brief, made when
 *  Today opens, folded to one line of counts) and This week. Every fact is a
 *  read the hub already serves: `/api/door` (the calendar, armed
 *  recordings, the week), `/api/meetings` (the meetings still to finish),
 *  `/api/desk/needs-you` (the one list) and `/api/brief/latest?ensure=1`
 *  (the brief, made by the hub off its event loop when none is current). */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { openSurfaceOr } from "../../shell";
import { programsTodayLine, type ProgramsSinceMorning } from "../../programs/lamp";
import { useProgramFrames } from "../../programs/api";
import { openSourceRef } from "../../surface/citations";
import { calendarOpener } from "../../openObject";
import { useDesk } from "../../store";
import { useNeedFaces, useDropped, NeedsDroppedReceipt } from "../../needs/NeedsDrawer";
import { TodayNeeds } from "../../needs/TodayNeeds";
import { FirstPlate, pickFirst } from "../../needs/FirstPlate";
import { SinceYesterday, type MondayBrief } from "./BriefView";
import { PreparedBlock, type PreparedRead } from "./PreparedBlock";
import { MEETING_CHANGE_KINDS, NEEDS_YOU_CHANGE_KINDS, useOnDeskChanged } from "../../useDeskChangedRefresh";
import { newsWords, useAutomationNews } from "../../automationNews";
import { DotWord, StatusBar, countWords, type StatusBarItem } from "../../surface/kit";
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
import "./today/today-face.css";
import { usePhoneToday } from "../../calls/phoneApi";
import { Token } from "../../surface/Token";
import { clock, countdown, dayLight, SHORT_DAYS, startOfDay, toFinish, when, type DayEvent, type DoorRead, type MeetingRow } from "./today/time";
import {
  EVENING_HOUR, PhoneLine, ProgramsLine, ReadFailed, SinceLastHereBlock, SinceThisMorning, ThisWeek, readEveningSaid,
  weekCounts, writeEveningSaid, type DoneRead, type DoneRow, type SinceLastHere,
} from "./today/folds";
import { TodayMast } from "./today/TodayMast";
import { eventTitle, NextPlate } from "./today/NextPlate";
import { DayRow } from "./today/DayRow";

export { countdown, currentStep, dayGreeting, dayLight, dayPart, toFinish, type DayEvent, type DayPart } from "./today/time";
export { EVENING_HOUR, EVENING_SAID_KEY, openDone, SinceLastHereBlock, weekCounts, weekDays, weekLine, type DoneRow, type SinceLastHere, type WeekCount } from "./today/folds";

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

/** Today's rows of Needs you: three, under the plate (the language). */
const NEEDS_TOP = 3;

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
  // Phone (PH16): one line when the desk reached him in the last day, at any
  // hour (the Programs pattern, PG18); never a line of zero.
  const phoneToday = usePhoneToday(true);
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
  const [sinceLast, setSinceLast] = useState<SinceLastHere | null>(null);
  const readSince = useCallback(async () => {
    const doneRead = await apiFetch<DoneRead>("/api/today/since-morning")
      .then((v) => ({ ok: true as const, v }), () => ({ ok: false as const }));
    // A failed read keeps the last Programs line (never invents none).
    if (doneRead.ok) setProgramsBlock(doneRead.v?.programs ?? null);
    if (doneRead.ok) setSinceLast(doneRead.v?.since_last_here ?? null);
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

  const title = eventTitle;
  const sprite = (event: DayEvent) => (event.person_relationship_id ? "person" : "meeting");
  const ago = (at: Date | null) => (at ? (startOfDay(at) === today ? clock(at) : SHORT_DAYS[at.getDay()]) : "");

  const finishRows = finish.map((row, index) => {
    const id = String(row.id);
    const at = when(row.started_at ?? row.created_at);
    const route = readPlannedRoute(row);
    const rowFailed = meetingRowState(row).verb === "Retry";
    const lead1 = lead === "finish" && index === 0;
    return (
      <DayRow key={id} kind="finish" testId="today-finish" time={ago(at)} sprite="meeting"
        name={<Button variant="chrome" className="today-row-title" onClick={() => openSourceRef(`meeting:${id}`)}>{String(row.title ?? "Meeting")}</Button>}
        facts="to finish"
        state={rowFailed ? { word: "Summary failed", tone: "fail" } : { word: "No summary yet", tone: "ask" }}
        // MUST 2 (Astra r1 on #1110), amended 2026-10-25: where the run goes
        // rides the verb's hover title; the row shows only a failed attempt
        // or a route that cannot run.
        extra={(
          <>
            <RunAttempts receipt={executedReceipt(id, summary.runRefusal?.meetingId === id ? summary.runRefusal.refusal.receipt : undefined, readRunReceipt(row))} testId="today-attempts" />
            <RouteDisclosure route={summary.runRefusal?.meetingId === id ? summary.runRefusal.refusal.route : route} testId="today-route" />
          </>
        )}
        verb={routeReady(route) ? (
          <Button dense variant={lead1 ? "primary" : "secondary"} loading={summary.runningId === id} title={routeTitle(route)}
            onClick={() => { setJustMade({ id, title: String(row.title ?? "Meeting") }); void summary.run(id, route); }} data-testid="today-make-summary">
            Make the summary
          </Button>
        ) : (
          <Button dense variant={lead1 ? "primary" : "secondary"}
            onClick={() => openSurfaceOr("open-concierge", "/models", "meetings")} data-testid="today-choose-engine">
            Choose engine
          </Button>
        )} />
    );
  });

  const nextStart = next ? when(next.starts_at) : null;
  const started = Boolean(nextStart && nextStart.getTime() <= now.getTime());
  const plate = next && nextStart ? (
    <NextPlate next={next} now={now} recordLead={lead === "next"} busy={busy === "arm"}
      error={actError?.key === "arm" ? actError.text : null} onRecord={recordNow}
      onArm={() => void act("arm", "Not armed. Try again", () => useDesk.getState().armEventRecording(next.id))} />
  ) : null;
  // No meeting ahead: the plate is the one thing that waits on him most in
  // Needs you (FirstPlate's own pick and face), and the preview leaves it out.
  const firstNeed = plate ? null : pickFirst(rows.work);
  const previewWork = firstNeed ? rows.work.filter((face) => face.id !== firstNeed.id) : rows.work;

  const laterRows = later.map((event) => {
    const start = when(event.starts_at);
    const open = calendarOpener(event);
    return (
      <DayRow key={event.id} kind="later" testId="today-later" time={start ? clock(start) : ""}
        sprite={sprite(event)} person={event.person_label} name={title(event)}
        facts={[event.person_label, event.project_name].filter(Boolean).join(" · ") || undefined}
        state={event.armed ? { word: "Armed", tone: "info" } : null}
        verb={open ? <Button dense variant="secondary" onClick={open}>Prep</Button> : null} />
    );
  });

  const nowRow = (
    <li className="kit-listrow today-dayrow today-nowrow" data-testid="today-now" aria-label={`Now ${clock(now)}`}>
      <span className="today-hour">{clock(now)}</span>
      <span className="today-now-word">now</span>
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
  const justMadeRow = justMade && (madeReceipt || madeRow) && !finish.some((row) => String(row.id) === justMade.id) ? (
    <DayRow kind="made" testId="today-just-made" time="" sprite="meeting"
      name={<Button variant="chrome" className="today-row-title" onClick={() => openSourceRef(`meeting:${justMade.id}`)}>{justMade.title}</Button>}
      state={{ word: madeDone ? "Summary made" : madeFailed ? "Summary failed" : "Making the summary", tone: madeDone ? "ok" : madeFailed ? "fail" : "info" }}
      extra={<RunAttempts receipt={madeReceipt} testId="today-made-attempts" />} />
  ) : null;

  // The retry is named outside the JSX: the copy scanner reads an arrow's
  // `>` after a JSX tag as the start of text.
  const retry = () => void load();
  const emptyRow = door && !next && !failed.door && !emptyDesk ? (
    <DayRow kind="empty" testId="today-empty" time=""
      name={calendar ? "No more meetings today" : "No calendar yet"}
      verb={calendar ? null : (
        <Button dense variant={lead === "calendar" ? "primary" : "secondary"}
          onClick={() => openSurfaceOr("configure-settings", "/settings", "integration:calendar")}>Connect calendar</Button>
      )} />
  ) : null;

  // Betterment A6: each automation with a NEW result, newest first. Opening
  // its window reads the result, and the row goes (here, on the Dock, at home).
  // Betterment D9: the automation that fills Prepared shows its NEW there.
  const preparedId = prepared?.prepared?.workbench_id;
  const newsRows = (news.rows ?? []).filter((row) => row.workbench_id !== preparedId).map((row) => (
    <DayRow key={row.workbench_id} kind="result" testId="today-new-result" time={ago(when(row.newest_at))} sprite="cartridge"
      name={newsWords(row)}
      verb={(
        <Button dense variant="secondary" data-testid="today-open-result" aria-label={`Open ${row.name}`}
          onClick={() => useDesk.getState().openWorkbenchWindow(row.workbench_id)}>Open result</Button>
      )} />
  ));

  const agentResultRows = finishedAgents.map((flight) => (
    <DayRow key={`agent:${flight.launchId}`} kind="result" testId="today-agent-result" time="" sprite={agentSpriteName(flight.agent)}
      name={agentResultWords(flight)}
      verb={(
        <Button dense variant="secondary" data-testid="today-open-agent-result" aria-label={`Open ${flight.title}`}
          onClick={() => openAgentLane(String(flight.launchId))}>Open session</Button>
      )} />
  ));

  const ahead = events.length;
  const prepareWith = prepared?.automation ?? null;
  const decide = rows.work.filter((face) => face.verbs.kind === "decide").length;
  const nextWords = next && nextStart && !started
    ? `next ${next.person_relationship_id ? "1:1" : "meeting"} ${countdown(nextStart, now)}`
    : null;
  // DELIGHT slice 2 (a small joy): after the day's last meeting, with a
  // meeting held today and nothing left on today's calendar, the status bar
  // says so in place of the count ahead.
  const heldToday = meetings.filter((row) => {
    const at = when(row.started_at ?? row.created_at);
    return at !== null && startOfDay(at) === today;
  });
  const metToday = heldToday.length > 0;
  const held = heldToday.filter((row) => !finish.includes(row)).length;
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
  // The language: steel is ours, brass only what waits on him.
  const statusItems: Array<StatusBarItem | null> = [
    dayDone
      ? { key: "day", lamp: "ok", text: "That is the day", testId: "today-status-day" }
      : { key: "ahead", lamp: "info", text: countWords(ahead, "meeting ahead", "meetings ahead"), testId: "today-status-ahead" },
    { key: "finish", lamp: "ask", text: countWords(finish.length, "to finish", "to finish"), testId: "today-status-finish" },
    { key: "decide", lamp: "ask", text: countWords(decide, "decision to make", "decisions to make"), testId: "today-status-decide" },
    nextWords ? { key: "next", text: nextWords, testId: "today-status-next" } : null,
    summary.receipt
      ? { key: "receipt", text: <Token className="surface-footer-receipt-line">{summary.receipt.text}</Token> }
      : dropped ? { key: "dropped", text: <NeedsDroppedReceipt /> } : null,
  ];
  return (
    <>
      {/* Busy until the first load ends: the day's rows land after it and
          move what is drawn (the desk sweep's still fence, under load). */}
      <div className="desk-pullout-body desk-surface-body intelligence-pullout today" aria-busy={loaded ? undefined : true}
        data-light={dayLight(now)} data-testid="today-body">
        <TodayMast now={now} ahead={ahead} needsCount={rows.needs.count} nextWords={nextWords}
          held={held} waits={finish.length + decide} recordLead={lead === "record"} onRecord={recordNow}
          prepare={Boolean(prepareWith)} prepareBusy={busy === "prepare"}
          prepareError={actError?.key === "prepare" ? actError.text : null}
          onPrepare={() => prepareWith && void act("prepare", "Not prepared. Try again", () =>
            apiFetch(`/api/workbenches/${encodeURIComponent(prepareWith.id)}/run`, { method: "POST", json: {} }))} />
        <div className="today-scroll">
          {plate}
          {firstNeed ? <div className="today-first-need"><FirstPlate face={firstNeed} projects={rows.multipleProjects} /></div> : null}
          <SinceLastHereBlock read={sinceLast} />
          {evening && done ? (
            <SinceThisMorning rows={done.rows} failed={done.failed} open={sinceShown} now={now} programs={programsToday} phone={phoneToday}
              onToggle={() => setSinceOpen(!sinceShown)} onRetry={retry} />
          ) : programsToday || phoneToday ? (
            /* PG18, PH16: before 17:00 the fold is not drawn; the Programs
               and Phone lines head the day instead. */
            <div className="today-programs-head" data-testid="today-programs-head">
              {programsToday ? <ProgramsLine words={programsToday} /> : null}
              {phoneToday ? <PhoneLine words={phoneToday} /> : null}
            </div>
          ) : null}
          <PreparedBlock read={prepared} events={door?.upcoming ?? []} />
          <div className="today-grid">
            <TodayNeeds work={previewWork} count={firstNeed && !firstNeed.uncounted ? Math.max(0, rows.needs.count - 1) : rows.needs.count}
              now={now} limit={NEEDS_TOP}
              primary={lead === "needs" && !firstNeed} projects={rows.multipleProjects} loaded={needsLoaded} emptyDesk={emptyDesk}
              failed={rows.needs.room === null && Object.keys(rows.needs.errors).length > 0} calendarLead={lead === "calendar"}
              next={next && nextStart ? `${title(next)} at ${clock(nextStart)}` : null}
              peopleUnread={Boolean(rows.needs.peopleUnread)} />
            <section className="today-day-section" aria-label="The day">
              <h3 className="today-label">The day</h3>
              <ul className="kit-listrows today-daylist" aria-label="Today">
                {nowRow}
                {laterRows}
                {failed.door ? <li className="today-dayrow-failed"><ReadFailed what="the calendar" onRetry={retry} testId="today-door-failed" /></li> : null}
                {emptyRow}
                {justMadeRow}
                {agentResultRows}
                {newsRows}
                {failed.meetings ? <li className="today-dayrow-failed"><ReadFailed what="the meetings" onRetry={retry} testId="today-meetings-failed" /></li> : null}
                {finishRows}
              </ul>
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
        verbs={(
          <>
            {agentsWords ? (
              <Button dense variant="secondary" className="today-agents" data-testid="today-agents"
                onClick={() => openSurfaceOr("open-conductor", "/conductor")}>
                {agentsWords}
              </Button>
            ) : null}
            {/* The window refreshes itself on desk changes; a calendar change
                sends none, so Refresh stays, quiet, at the foot. */}
            <Button dense variant="ghost" data-testid="today-refresh" onClick={retry}>Refresh</Button>
          </>
        )}
      />
    </>
  );
}
