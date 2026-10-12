/** PHILO-17 (owner pick 2026-10-11, concept C): the Today window is the DAY
 *  AS A TIMELINE, drawn in the desk's own material: a time spine in a paper
 *  well, the next meeting as a raised plate with a Workbench title bar and a
 *  four-step stepper, later meetings as compact rows, and a side column
 *  (Owed, To decide). Every fact is a read the hub already serves:
 *  `/api/door` (today's calendar and armed recordings), `/api/meetings`
 *  (the meetings still to finish), `/api/desk/needs-you` (the proposals to
 *  decide) and `/api/people/relationships` (what is owed both ways). */
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { openSurfaceOr } from "../../shell";
import { openSourceRef } from "../../surface/citations";
import { calendarOpener } from "../../openObject";
import { useDesk } from "../../store";
import { useOnDeskChanged } from "../../useDeskChangedRefresh";
import { SurfaceFooter } from "../../surface/SurfaceFooter";
import { Avatar } from "../../surface/kit";
import { meetingRowState } from "../../../pages/cores/history/helpers";
import { useSummaryRun } from "../../../pages/cores/history/useSummaryRun";
import { readPlannedRoute, routeReady } from "../../../meetings/summaryRoute";
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
type DoorRead = { upcoming?: DayEvent[]; calendar_configured?: boolean };
type MeetingRow = Record<string, unknown>;
type NeedsItem = { proposalId?: string; title?: string; proposalKind?: string; meetingTitle?: string; muted?: boolean; waiting?: boolean };
type Relationship = { id: string };
type Owing = { state?: string };
interface RelationshipDetail {
  commitments?: Owing[];
  owed_to_you?: Owing[];
}

const DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const SHORT_DAYS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

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
    <ol className="today-stepper" aria-label="Meeting steps">
      {STEPS.map((label, index) => (
        <li
          key={label}
          className="today-step"
          data-state={index < step ? "done" : index === step ? "now" : "later"}
          aria-current={index === step ? "step" : undefined}
        >
          <span className="today-step-n" aria-hidden="true">{index < step ? "✓" : index + 1}</span>
          <span className="today-step-word">{label}</span>
        </li>
      ))}
    </ol>
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

export function TodayView({ header }: { header: ReactNode }) {
  const [now, setNow] = useState(() => new Date());
  const [door, setDoor] = useState<DoorRead | null>(null);
  const [meetings, setMeetings] = useState<MeetingRow[]>([]);
  const [needs, setNeeds] = useState<NeedsItem[]>([]);
  const [owed, setOwed] = useState<{ you: number; them: number } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [doorRead, meetingRead, needsRead] = await Promise.all([
      apiFetch<DoorRead>("/api/door").catch(() => null),
      apiFetch<{ meetings?: MeetingRow[] }>("/api/meetings?limit=40").catch(() => null),
      apiFetch<{ items?: NeedsItem[] }>("/api/desk/needs-you").catch(() => null),
    ]);
    setDoor(doorRead ?? { upcoming: [], calendar_configured: false });
    setMeetings(meetingRead?.meetings ?? []);
    setNeeds(needsRead?.items ?? []);
    try {
      const list = await apiFetch<{ relationships?: Relationship[] }>("/api/people/relationships");
      const details = await Promise.all((list.relationships ?? []).map((row) =>
        apiFetch<{ relationship: RelationshipDetail }>(`/api/people/relationships/${encodeURIComponent(row.id)}`)
          .then((read) => read.relationship).catch(() => null)));
      const open = (items?: Array<{ state?: string }>) => (items ?? []).filter((item) => (item.state ?? "open") === "open").length;
      setOwed(details.reduce((sum, d) => d ? { you: sum.you + open(d.commitments), them: sum.them + open(d.owed_to_you) } : sum, { you: 0, them: 0 }));
    } catch {
      setOwed(null);
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
  const next = events[0] ?? null;
  const later = events.slice(1);
  const finish = useMemo(() => toFinish(meetings, now), [meetings, now]);
  const decidable = needs.filter((item) => item.proposalId && !item.muted && !item.waiting);
  const decide = decidable.find((item) => item.proposalKind === "decision") ?? decidable[0] ?? null;
  const calendar = door?.calendar_configured ?? false;

  // ONE filled primary per window (UX-CANON): the next meeting's record
  // verb, else the first summary to make, else Connect calendar, else
  // Record now.
  const lead = next ? "next" : finish.length ? "finish" : !calendar && door ? "calendar" : "record";
  const recordNow = () => openSurfaceOr("record-live", "/live");

  const act = async (key: string, run: () => Promise<unknown>) => {
    setBusy(key);
    try { await run(); } finally { setBusy(null); void load(); }
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
              <span className="today-pill" data-tone={failed ? "danger" : "warn"}>{failed ? "Summary failed" : "No summary yet"}</span>
            </span>
          </div>
          {routeReady(route) ? (
            <Button dense variant={lead === "finish" && index === 0 ? "primary" : "secondary"} loading={summary.runningId === id}
              onClick={() => void summary.run(id, route)} data-testid="today-make-summary">
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
  const nextNode = next && nextStart ? (
    <SpineNode kind="next" testId="today-next" time={clock(nextStart)}>
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
              {next.project_name ? <span className="today-pill" data-tone="info">{next.project_name}</span> : null}
              {armed ? <span className="today-pill" data-tone="danger" data-live="">Armed</span> : null}
            </span>
          </div>
        </div>
        <Stepper step={currentStep(next, now)} />
        <div className="today-next-verbs">
          {nextOpen ? <Button dense onClick={nextOpen} data-testid="today-open-prep">Open prep</Button> : null}
          {started || armed ? (
            <Button dense variant="primary" onClick={recordNow} data-testid="today-record">Record</Button>
          ) : next.source === "calendar_event" ? (
            <Button dense variant="primary" loading={busy === "arm"} data-testid="today-arm"
              onClick={() => void act("arm", () => useDesk.getState().armEventRecording(next.id))}>
              Record when it starts
            </Button>
          ) : null}
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
              {event.project_name ? <span className="today-pill" data-tone="info">{event.project_name}</span> : null}
              {event.armed ? <span className="today-pill" data-tone="danger">Armed</span> : null}
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

  const emptyNode = door && !next ? (
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
      <div className="desk-pullout-body desk-surface-body intelligence-pullout today">
        {header}
        <div className="today-head">
          <h2 className="today-day" data-testid="today-day">{DAY_NAMES[now.getDay()]}</h2>
          <span className="today-strip">
            {ahead ? <span><b>{ahead}</b> {ahead === 1 ? "meeting ahead" : "meetings ahead"}</span> : null}
            {finish.length ? <span><b>{finish.length}</b> to finish</span> : null}
          </span>
          <span className="today-head-sp" />
          <Button dense variant={lead === "record" ? "primary" : "secondary"} onClick={recordNow} data-testid="today-record-now">Record now</Button>
        </div>
        <div className="today-grid">
          <ol className="today-spine" aria-label="Today">
            {pastToday}
            {finishNodes}
            {nowNode}
            {nextNode}
            {laterNodes}
            {emptyNode}
          </ol>
          <aside className="today-side" aria-label="Owed and to decide">
            {owed && (owed.you || owed.them) ? (
              <section className="today-plate" data-testid="today-owed">
                <h3 className="today-plate-cap">OWED</h3>
                <div className="today-figures">
                  {owed.you ? <span className="today-figure" data-tone="warn"><b>{owed.you}</b>you owe</span> : null}
                  {owed.them ? <span className="today-figure" data-tone="ok"><b>{owed.them}</b>owed to you</span> : null}
                </div>
                <Button dense variant="ghost" onClick={() => openSurfaceOr("open-people", "/", undefined)}>People</Button>
              </section>
            ) : null}
            {decide ? (
              <section className="today-plate" data-testid="today-decide">
                <h3 className="today-plate-cap">TO DECIDE</h3>
                <span className="today-decide-title">{decide.title}</span>
                {decide.meetingTitle ? <span className="today-row-meta">{decide.meetingTitle}</span> : null}
                <div className="today-plate-verbs">
                  <Button dense disabled={busy === "decide"} data-testid="today-confirm"
                    onClick={() => void act("decide", () => apiFetch(`/api/proposals/${encodeURIComponent(String(decide.proposalId))}/confirm`, { method: "POST" }))}>
                    Confirm
                  </Button>
                  <Button dense variant="ghost" disabled={busy === "decide"} data-testid="today-not-now"
                    onClick={() => void act("decide", () => apiFetch(`/api/proposals/${encodeURIComponent(String(decide.proposalId))}/defer`, { method: "POST", json: {} }))}>
                    Not now
                  </Button>
                </div>
              </section>
            ) : null}
          </aside>
        </div>
      </div>
      <SurfaceFooter receipt={summary.receipt ? <span className="surface-footer-receipt-line" role="status">{summary.receipt.text}</span> : undefined} />
    </>
  );
}
