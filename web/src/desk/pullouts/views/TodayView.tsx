/** PHILO-17 (owner pick 2026-10-11, concept C): the Today window is the DAY
 *  AS A TIMELINE, drawn in the desk's own material: a time spine in a paper
 *  well, the next meeting as a raised plate with a Workbench title bar and a
 *  four-step stepper, later meetings as compact rows, and a side column
 *  (Owed, To decide). Every fact is a read the hub already serves:
 *  `/api/door` (today's calendar and armed recordings), `/api/meetings`
 *  (the meetings still to finish), `/api/desk/needs-you` (the proposals to
 *  decide) and `/api/people/relationships` (what is owed both ways). */
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { openSurfaceOr } from "../../shell";
import { openSourceRef } from "../../surface/citations";
import { calendarOpener } from "../../openObject";
import { useDesk } from "../../store";
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
type DoorRead = { upcoming?: DayEvent[]; calendar_configured?: boolean };
type MeetingRow = Record<string, unknown>;
type NeedsItem = { proposalId?: string; title?: string; proposalKind?: string; meetingTitle?: string; muted?: boolean; waiting?: boolean };

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

/** PHILO-17 (Astra r1 on #1110, MUST 4): the owed totals from ONE bounded
 *  read: the roster answer with its counts (`?counts=1`). A closed People
 *  store is read as closed (no totals), never as zero. */
async function readOwed(): Promise<{ state: "ok"; owed: { you: number; them: number } } | { state: "closed" } | { state: "failed" }> {
  try {
    const ready = await apiFetch<{ state?: string; readiness?: string }>("/api/people/readiness");
    if ((ready.state ?? ready.readiness) !== "ready") return { state: "closed" };
    const list = await apiFetch<{ relationships?: Array<{ you_owe_count?: number; owes_you_count?: number }> }>(
      "/api/people/relationships?counts=1");
    const owed = (list.relationships ?? []).reduce(
      (sum, row) => ({ you: sum.you + (Number(row.you_owe_count) || 0), them: sum.them + (Number(row.owes_you_count) || 0) }),
      { you: 0, them: 0 });
    return { state: "ok", owed };
  } catch {
    return { state: "failed" };
  }
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

export function TodayView({ header }: { header: ReactNode }) {
  const [now, setNow] = useState(() => new Date());
  const [door, setDoor] = useState<DoorRead | null>(null);
  const [meetings, setMeetings] = useState<MeetingRow[]>([]);
  const [needs, setNeeds] = useState<NeedsItem[]>([]);
  const [owed, setOwed] = useState<{ you: number; them: number } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  // PHILO-17 (Astra r1 on #1110, MUST 3): a source that could not be read
  // says so (with Retry); it never reads as empty.
  const [failed, setFailed] = useState<{ door: boolean; meetings: boolean; needs: boolean; people: boolean }>(
    { door: false, meetings: false, needs: false, people: false });
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
        const [doorRead, meetingRead, needsRead, owedRead] = await Promise.all([
          apiFetch<DoorRead>("/api/door").then((v) => ({ ok: true as const, v }), () => ({ ok: false as const })),
          apiFetch<{ meetings?: MeetingRow[] }>("/api/meetings?limit=40").then((v) => ({ ok: true as const, v }), () => ({ ok: false as const })),
          apiFetch<{ items?: NeedsItem[] }>("/api/desk/needs-you").then((v) => ({ ok: true as const, v }), () => ({ ok: false as const })),
          readOwed(),
        ]);
        if (doorRead.ok) setDoor(doorRead.v);
        else setDoor((current) => current);
        if (meetingRead.ok) setMeetings(meetingRead.v.meetings ?? []);
        if (needsRead.ok) setNeeds(needsRead.v.items ?? []);
        if (owedRead.state === "ok") setOwed(owedRead.owed);
        else if (owedRead.state === "closed") setOwed(null);
        setFailed({ door: !doorRead.ok, meetings: !meetingRead.ok, needs: !needsRead.ok, people: owedRead.state === "failed" });
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
  const next = events[0] ?? null;
  const later = events.slice(1);
  const finish = useMemo(() => toFinish(meetings, now), [meetings, now]);
  const decidable = needs.filter((item) => item.proposalId && !item.muted && !item.waiting);
  const decide = decidable.find((item) => item.proposalKind === "decision") ?? decidable[0] ?? null;
  const calendar = door?.calendar_configured ?? false;

  // ONE filled primary per window (UX-CANON): the next meeting's record
  // verb, else the first summary to make, else Connect calendar, else
  // Record now.
  const lead = next ? "next" : finish.length ? "finish" : !calendar && door && !failed.door ? "calendar" : "record";
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
  const armsAt = next ? when(next.armed?.arms_at ?? next.starts_at) : null;
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
          {nextOpen ? <Button dense onClick={nextOpen} data-testid="today-open-prep">Open prep</Button> : null}
          {started || armed ? (
            <Button dense variant="primary" onClick={recordNow} data-testid="today-record">Record</Button>
          ) : next.source === "calendar_event" ? (
            <Button dense variant="primary" loading={busy === "arm"} data-testid="today-arm"
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

  const doorFailedNode = failed.door ? (
    <li className="today-section"><span /><span /><ReadFailed what="the calendar" onRetry={() => void load()} testId="today-door-failed" /></li>
  ) : null;
  const meetingsFailedNode = failed.meetings ? (
    <li className="today-section"><span /><span /><ReadFailed what="the meetings" onRetry={() => void load()} testId="today-meetings-failed" /></li>
  ) : null;
  const emptyNode = door && !next && !failed.door ? (
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
            {meetingsFailedNode}
            {pastToday}
            {finishNodes}
            {nowNode}
            {nextNode}
            {laterNodes}
            {doorFailedNode}
            {emptyNode}
          </ol>
          <aside className="today-side" aria-label="Owed and to decide">
            {failed.people ? <ReadFailed what="People" onRetry={() => void load()} testId="today-people-failed" /> : null}
            {failed.needs ? <ReadFailed what="what to decide" onRetry={() => void load()} testId="today-needs-failed" /> : null}
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
                {actError?.key === "decide" ? <span className="kit-pill" data-tone="danger" role="status" data-testid="today-decide-failed">{actError.text}</span> : null}
                <div className="today-plate-verbs">
                  <Button dense disabled={busy === "decide"} data-testid="today-confirm"
                    onClick={() => void act("decide", "Not confirmed. Try again", () => apiFetch(`/api/proposals/${encodeURIComponent(String(decide.proposalId))}/confirm`, { method: "POST" }))}>
                    Confirm
                  </Button>
                  <Button dense variant="ghost" disabled={busy === "decide"} data-testid="today-not-now"
                    onClick={() => void act("decide", "Not moved. Try again", () => apiFetch(`/api/proposals/${encodeURIComponent(String(decide.proposalId))}/defer`, { method: "POST", json: {} }))}>
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
