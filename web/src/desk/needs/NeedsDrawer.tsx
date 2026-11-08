/** Needs you, the desk of today (the bold language, 2026-11-08; canvas NB
 *  "Needs you: the desk of today", the first phone in "The three on the
 *  phone"). Owner, on the face before it: "way too cluttered… 'more'
 *  doesn't even look like a button".
 *
 *  Top to bottom: the mast (NeedsMast.tsx: the lamp, the day and what must
 *  be fixed, the counts in mono, Mine · People and Later, the spine); the
 *  one thing that waits most, raised (FirstPlate.tsx); the ledger by weight
 *  (Ledger.tsx: Must fix, Should fix, To do, Noted); the status bar. At the
 *  phone width it is one column: the plate first, then the ledger.
 *
 *  The rows are the one row (NeedRow.tsx, Today draws it too); their verbs
 *  and the wells they open are NeedVerbs.tsx. The data is the hub's one
 *  answer (`useNeedsYou`, #788): the status bar speaks the same number as
 *  the Dock badge and the bell, and the rows are the members.
 */
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { useAgentFlights } from "../agentFlights";
import { reportWriteFailure } from "../hooks/useWriteReceipt";
import { refreshNeedsYou, useNeedsYou } from "../needsYou";
import { PeopleReadFailed } from "../people/PeopleReadFailed";
import { openSurfaceOr } from "../shell";
import { useDesk } from "../store";
import { ScrollHint, StatusBar, SurfaceSection, SurfaceState, type StatusBarItem } from "../surface";
import { NeedsList } from "../surface/objects";
import { wireDate } from "../surface/format";
import { groupGaps, readCoverage } from "../coverage";
import { armingFace, coverageGroupFace, dayWord, needFace, needFaces, needsHead, nextWord, type NeedFace } from "./needsFace";
import { useArmingOutcome } from "./arming";
import { Disclosure } from "../surface/patterns/Disclosure";
import { Token } from "../surface/Token";
import { ItemReader, ItemReaderContext, readsInPlace } from "./ItemReader";
import { INTELLIGENCE_NAVIGATE, takeFollowThrough, type IntelligenceNavigation } from "../intelligenceNavigation";
import { faceOpener, hhmm, useDropped, useSourceReceipt } from "./NeedVerbs";
import { NeedRow, useRowMarks } from "./NeedRow";
import { inScope, NeedsMast, weightsOf, type NeedsScope } from "./NeedsMast";
import { FirstPlate, pickFirst } from "./FirstPlate";
import { Ledger, ledgerGroups } from "./Ledger";
import "./needs.css";

// The row, its verbs and the mast live in their own files; these names
// stay importable from here.
export {
  faceOpener, needsRowSprite, openAgentAnswer, offerUndo, useDropped, nudgeText, useSourceReceipt, recheckSource, hasRowMenu,
} from "./NeedVerbs";
export { NeedRow, quietState, glyphWord, useRowMarks } from "./NeedRow";
export { inScope, type NeedsScope } from "./NeedsMast";
export { dayWord };

interface DoorRead {
  upcoming?: Array<{ title?: string; starts_at?: string; source?: string }>;
  calendar_configured?: boolean;
}

/** `Checked just now`, `Checked 4 min ago`, `Checked 09:14`. */
export function checkedWord(at: string | null | undefined, now: Date = new Date()): string | null {
  const d = at ? new Date(at) : null;
  if (!d || Number.isNaN(d.getTime())) return null;
  const minutes = Math.floor((now.getTime() - d.getTime()) / 60000);
  if (minutes < 1) return "Checked just now";
  if (minutes < 60) return `Checked ${minutes} min ago`;
  return `Checked ${hhmm(d)}`;
}

/** The rows for a later day (Later shows them): his own rows the count
 *  leaves out because they wait for a day to come (a due date after today,
 *  a Later he said). A proposal to confirm and a source stay on today. */
export function isLater(face: Pick<NeedFace, "uncounted" | "source" | "direction" | "due" | "verbs">, now: Date = new Date()): boolean {
  if (!face.uncounted || face.source || face.direction === "theirs") return false;
  if (face.verbs.kind === "program" && face.verbs.later) return true;
  const due = face.due ? wireDate(face.due) : null;
  if (!due) return false;
  const day = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  return day(due) > day(now);
}

/** The drawer is drawn after this long even when a read is still out (the
 *  Room's cap, roomReads.ts ROOM_READS_CAP_MS). */
const NEEDS_READS_CAP_MS = 8000;

/** The one list's rows, as both of its faces draw them (the Needs-you
 *  window and Today's top, Betterment daily D4): the recording that arms,
 *  the hub's members (with the asks folded into them), the rows the count
 *  leaves out, and the sources that could not be read. One read, one rank. */
export function useNeedFaces() {
  const needs = useNeedsYou();
  const flights = useAgentFlights((s) => s.flights);
  const sessions = useAgentFlights((s) => s.sessions);
  const arming = useDesk((s) => s.scheduledArming);
  const [, tick] = useState(0);

  // The countdown ticks while a recording arms.
  const live = Boolean(arming && !arming.outcome);
  useEffect(() => {
    if (!live) return;
    const t = window.setInterval(() => tick((n) => n + 1), 250);
    return () => window.clearInterval(t);
  }, [live]);

  const now = new Date();
  // The rows name their Project when two or more Projects need him (the
  // Chair's rule, HS-200-15: one Project on every row says nothing).
  const multipleProjects = (needs.room?.projects?.length ?? 0) > 1;
  const ctx = { flights, sessions, now, multipleProjects };
  const coverage = readCoverage(
    needs.room?.coverage, needs.room?.complete ?? undefined, Boolean(needs.errors.room),
  );
  // PHILO-15-09 (B11): the calendar is an offer, never a row: the head's
  // number is the number of rows below it. The offer is in the strip.
  // PHILO-15 B60: a source held by quiet hours is drawn after the gaps and
  // is not counted.
  // PHILO-17 (needsyou): the sources of one cause are ONE row (the hub
  // counts the cause once); each source stays in the row's detail.
  const sources = [...groupGaps(coverage.gaps), ...groupGaps(coverage.quiet)].map((rows) => coverageGroupFace(rows, now));
  const outcome = useArmingOutcome();
  const liveArming = arming && !arming.outcome ? arming : null;
  // PHILO-15-09 (B11): the hub counts a recording that arms; the desk draws
  // it with the live countdown when the bus has it, else from the hub's row.
  // A countdown the bus has ended (cancelled, refused) is not drawn again.
  const hubArming = (needs.arming ?? []).filter((row) => row.scheduleId !== arming?.scheduleId);
  const armed = [
    ...(liveArming
      ? [armingFace(
        liveArming, (liveArming.fireAt - now.getTime()) / 1000,
        outcome.refusal?.scheduleId === liveArming.scheduleId ? outcome.refusal.reason : null,
      )]
      : []),
    ...hubArming.map((row) => ({
      ...armingFace(
        { scheduleId: row.scheduleId, title: row.title, calendarEventId: row.calendarEventId },
        0,
        null,
        row.didNotRecord,
      ),
      ...(row.didNotRecord ? {} : {
        fact: "Arms now",
        lamp: { label: "ARMS", tone: "ask" as const },
      }),
    })),
  ];
  // The bus and the hub disagree on a countdown (one started, or ended):
  // read the one number again.
  const hubLists = (id: string) => (needs.arming ?? []).some((row) => row.scheduleId === id);
  const armingStale = liveArming
    ? !hubLists(liveArming.scheduleId)
    : Boolean(arming?.outcome && hubLists(arming.scheduleId));
  useEffect(() => {
    if (armingStale) void refreshNeedsYou(false);
  }, [armingStale]);
  // Board A-5: one list, no group heads. A recording that arms, then the
  // agents (one object, one row), then the rest in the hub's rank order.
  // PHILO-17 (needsyou, walker BLOCKS): the work leads; the sources that
  // could not be read (plumbing) come last.
  // The asks the hub folded into an item are listed, not members: they ride
  // in so their item's row carries them (one object, one row, one count).
  const foldedAsks = needs.unmutedItems
    .filter((item) => item.foldedInto && !item.waiting)
    .map((item) => ({ ref: String(item.ref ?? item.id ?? ""), kind: "attention" as const, item }));
  // Betterment D1: a row the one count rule leaves out (a promise not kept
  // yet, what a person owes, his own work due on a later day) is listed
  // after the counted rows, marked not counted. Betterment D2: what a person
  // owes is in the one list too (They owe me), never a list of its own.
  const listedOnly = needs.unmutedItems
    .filter((item) => (item.counted === false || item.waiting) && !item.foldedInto)
    .map((item) => ({ ref: String(item.ref ?? item.id ?? ""), kind: "attention" as const, item }));
  const work = [
    ...armed,
    ...needFaces([...needs.members, ...foldedAsks], ctx),
    ...needFaces(listedOnly, ctx).map((face) => ({ ...face, uncounted: true })),
  ];
  const faces = [...work, ...sources];
  return { needs, now, ctx, coverage, multipleProjects, outcome, work, faces };
}

/** Betterment D3: the Undo receipt of the last Drop (8 s), in the foot of
 *  every face that draws the rows (the Needs-you window, Today). */
export function NeedsDroppedReceipt() {
  const dropped = useDropped((st) => st.dropped);
  if (!dropped) return null;
  return (
    <Token className="surface-footer-receipt-line needs-dropped" role="status" data-testid="needs-dropped">
      {`Dropped · ${dropped.name}`}
      <Button dense variant="secondary" aria-label={`Undo: ${dropped.name}`} data-testid="needs-undo"
        onClick={() => {
          useDropped.getState().set(null);
          void dropped.undo().then(() => refreshNeedsYou(false)).catch((error) =>
            reportWriteFailure("Undo", error, () => void dropped.undo()));
        }}>Undo</Button>
    </Token>
  );
}

export function NeedsDrawer() {
  const { needs, now, coverage, multipleProjects, outcome, faces, ctx } = useNeedFaces();
  const [door, setDoor] = useState<DoorRead | null>(null);
  const [scope, setScope] = useState<NeedsScope>("mine");
  const [showLater, setShowLater] = useState(false);
  const [showMuted, setShowMuted] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  // The item reader (2026-11-08): the action item read in place, by a press
  // on its row, its menu's Open, or an `action_item:<id>` ref (the
  // follow-through request: its event when this window is mounted, the
  // pending id when it mounts after).
  const [readerId, setReaderId] = useState<string | null>(() => takeFollowThrough());
  useEffect(() => {
    const onNavigate = (event: Event) => {
      const nav = (event as CustomEvent<IntelligenceNavigation>).detail;
      if (nav?.view !== "follow-through" || !nav.followThroughId) return;
      takeFollowThrough();
      setReaderId(nav.followThroughId);
    };
    window.addEventListener(INTELLIGENCE_NAVIGATE, onNavigate);
    return () => window.removeEventListener(INTELLIGENCE_NAVIGATE, onNavigate);
  }, []);

  // The Door read: the next event and whether a calendar is connected.
  const computedAt = needs.room?.computedAt ?? null;
  const [doorRead, setDoorRead] = useState(false);
  useEffect(() => {
    let alive = true;
    void apiFetch<DoorRead>("/api/door")
      .then((body) => { if (alive) setDoor(body ?? null); })
      .catch(() => undefined)
      .finally(() => { if (alive) setDoorRead(true); });
    return () => { alive = false; };
  }, [computedAt, needs.count]);
  // PHILO-17 (the desk sweep, sweepreds r2): the drawer is drawn once its
  // first reads end (the hub's answer and the Door read), or at the cap: the
  // mast and the rows never move under his eye (UX-CANON D). Once drawn it
  // stays drawn.
  const needsRead = needs.room !== null || Object.keys(needs.errors).length > 0;
  const [capped, setCapped] = useState(false);
  useEffect(() => {
    const timer = window.setTimeout(() => setCapped(true), NEEDS_READS_CAP_MS);
    return () => window.clearTimeout(timer);
  }, []);
  const [drawn, setDrawn] = useState(false);
  const ready = capped || (needsRead && doorRead);
  useLayoutEffect(() => { if (ready && !drawn) setDrawn(true); }, [ready, drawn]);
  const settling = !(drawn || ready);

  const noCalendar = Boolean(door && door.calendar_configured === false);
  // Listed, never counted: the muted (the mast's Muted · N).
  const muted = needs.mutedItems.map((item) =>
    needFace({ ref: String(item.id ?? item.ref ?? ""), kind: "attention", item }, ctx));
  // PHILO-15-09 (B11, the A5 ruling): the head is the hub's one number, the
  // number the Dock badge and the bell say.
  const head = needsHead(needs.count, needs.complete && coverage.complete);
  const scoped = faces.filter((face) => inScope(face, scope));
  // The desk of today: the rows for a later day wait behind Later (Mine).
  const later = scope === "mine" ? scoped.filter((face) => isLater(face, now)) : [];
  const shown = showMuted ? muted.filter((face) => inScope(face, scope))
    : showLater && later.length ? later
      : scoped.filter((face) => scope !== "mine" || !isLater(face, now));
  // Betterment D3: promises kept on arrival, NEW under their meeting at the
  // top. The hub is told they were seen once they are drawn; this window
  // keeps them grouped until it closes, so no row moves under his eye.
  const arrivals = useRef(new Map<string, NonNullable<NeedFace["arrival"]>>());
  for (const face of faces) if (face.arrival) arrivals.current.set(face.id, face.arrival);
  const arrivalOf = (face: NeedFace) => (showMuted ? undefined : face.arrival ?? arrivals.current.get(face.id));
  const groups: Array<{ arrival: NonNullable<NeedFace["arrival"]>; faces: NeedFace[] }> = [];
  for (const face of shown) {
    const arrival = arrivalOf(face);
    if (!arrival) continue;
    const group = groups.find((g) => g.arrival.meetingId === arrival.meetingId);
    if (group) group.faces.push({ ...face, arrival });
    else groups.push({ arrival, faces: [{ ...face, arrival }] });
  }
  const rest = shown.filter((face) => !arrivalOf(face));
  // The one thing that waits most (the plate), then the ledger by weight.
  const first = showMuted || showLater ? null : pickFirst(rest);
  // One lead verb on the face: the plate's brass Button; with no plate the
  // first row drawn (a SETUP, repair or offer verb is never filled, HS-201-01).
  const firstId = first ? first.id : showMuted ? null
    : [...groups.flatMap((g) => g.faces), ...rest].find((f) => !f.source && f.verbs.kind !== "setup")?.id ?? null;
  const groupKey = groups.map((g) => g.arrival.meetingId).sort().join("|");
  const told = useRef(new Set<string>());
  useEffect(() => {
    const fresh = groupKey.split("|").filter((id) => id && !told.current.has(id));
    if (!fresh.length) return;
    for (const id of fresh) told.current.add(id);
    void apiFetch("/api/desk/needs-you/seen", { method: "POST", json: { meeting_ids: fresh } }).catch(() => undefined);
  }, [groupKey]);
  const dropped = useDropped((st) => st.dropped);
  const all = [...faces, ...muted];
  const memberRefs = new Set(faces.filter((f) => !f.uncounted).map((f) => f.memberRef ?? f.id));
  const sourceReceipt = useSourceReceipt((st) => st.receipt);
  useRowMarks(listRef, all, memberRefs);
  // The item in the reader: its row's face. Once the list is read and the
  // item is not in it (Done, Later, or gone), the reader returns to the list.
  const readerFace = readerId
    ? all.find((f) => f.verbs.kind === "work" && f.verbs.cardId === readerId) ?? null
    : null;
  const readerGone = Boolean(readerId && !readerFace && needsRead);
  useEffect(() => { if (readerGone) setReaderId(null); }, [readerGone]);

  const upcoming = door?.upcoming?.[0];
  const next = nextWord(upcoming
    ? { label: upcoming.title, at: upcoming.starts_at }
    : (needs.room?.next as { label?: string; at?: string } | null | undefined));
  const ranked = computedAt ? new Date(computedAt) : null;
  const checked = ranked && !Number.isNaN(ranked.getTime()) ? `checked ${hhmm(ranked)}` : null;
  // The weights the mast and the status bar say: his own rows of today.
  const today = faces.filter((face) => inScope(face, "mine") && !isLater(face, now) && !face.source);
  const weights = weightsOf(today);
  const count = needsRead ? Number(needs.count ?? 0) : 0;

  // The row body is the Open (the verb Open stays for the keyboard and 393).
  const onRowPress = (event: React.MouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;
    if (target.closest("button, a, input, textarea, select, .needs-drawer-well")) return;
    const id = target.closest("li.needs-row")?.getAttribute("data-object-id");
    const face = all.find((f) => f.id === id);
    if (!face) return;
    const item = readsInPlace(face);
    if (item) setReaderId(item);
    else faceOpener(face)?.();
  };

  // W1-DOORS (atlas 2026-10-27): one truth. A next 1:1 in the status bar
  // means there is a calendar; the mast does not say "No calendar" then.
  const offer = noCalendar && !next ? (
    <span className="needs-calendar-offer" data-testid="needs-no-calendar">
      <span className="needs-calendar-word">No calendar</span>
      <Button dense variant="secondary" aria-label="Connect calendar" data-testid="needs-row-verb" data-verb="connect-calendar"
        onClick={() => openSurfaceOr("configure-settings", "/settings", "integration:calendar")}>Connect calendar</Button>
    </span>
  ) : null;
  // HS-S43 (D22/G43): People's commitments to him live in People; the People
  // scope ends with Open People, so the coverage stays one press away.
  const openPeople = (
    <Button dense variant="ghost" className="needs-people-open" data-testid="needs-people-open"
      onClick={() => openSurfaceOr("open-people", "/")}>Open People</Button>
  );
  const counted = Number(needs.count ?? 0) > 0;
  // DELIGHT slice 2: the head's number ticks (with the dock's badge) when a
  // Done lands. Before the hub's first answer there is no number yet.
  const statusItems: StatusBarItem[] = [
    { key: "head", lamp: counted ? "ask" : coverage.complete ? "ok" : "warn", text: head,
      tick: needsRead ? Number(needs.count ?? 0) : null, testId: "arrival-display" },
    weights.must > 0 ? { key: "must", text: `${weights.must} must fix`, testId: "needs-must" } : null,
    weights.should > 0 ? { key: "should", text: `${weights.should} should`, testId: "needs-should" } : null,
    next ? { key: "next", text: next, testId: "needs-next" } : null,
    outcome.receipt ? { key: "receipt", text: outcome.receipt, testId: "needs-receipt" } : null,
    !outcome.receipt && sourceReceipt
      ? { key: "source", lamp: sourceReceipt.tone === "fail" ? "fail" as const : "ok" as const, text: sourceReceipt.title ? <span title={sourceReceipt.title}>{sourceReceipt.text}</span> : sourceReceipt.text, testId: "needs-source-receipt" }
      : null,
    !outcome.receipt && !sourceReceipt && checked ? { key: "checked", text: checked, testId: "needs-checked" } : null,
  ].filter(Boolean) as StatusBarItem[];

  return (
    <div className="needs-drawer kit-face" data-testid="needs-drawer"
      data-settling={settling ? "true" : undefined} aria-busy={settling ? true : undefined}>
      {settling ? <div className="needs-drawer-settling"><SurfaceState loading /></div> : null}
      {readerFace ? <ItemReader face={readerFace} onBack={() => setReaderId(null)} /> : <ItemReaderContext.Provider value={setReaderId}>
      <NeedsMast now={now} head={head} count={count} weights={weights} total={today.length} checked={checked}
        scope={scope} setScope={(next) => { setScope(next); setShowLater(false); }}
        later={later.length} showLater={showLater} setShowLater={setShowLater}
        muted={muted.length} showMuted={showMuted} setShowMuted={setShowMuted} offer={offer} />
      {/* W5-WORDS: every source read is no row; a gap names how many and which. */}
      {!coverage.complete && coverage.expected > 0 ? (() => {
        const missing = Math.max(coverage.expected - coverage.available, coverage.gaps.length, 1);
        return <Disclosure label={`${missing} ${missing === 1 ? "source" : "sources"} not checked`} ariaLabel="Coverage">
          {coverage.gaps.length > 0 ? <ul className="needs-coverage-details">
            {coverage.gaps.map((source, index) => <li key={index}>{source.label || source.source_id}</li>)}
          </ul> : null}
        </Disclosure>;
      })() : null}
      {needs.peopleUnread ? <PeopleReadFailed testId="needs-people-read-failed" onRetry={() => void refreshNeedsYou()} /> : null}
      {/* A press on a row body opens it; each row's verbs carry the keyboard. */}
      <div ref={listRef} onClick={onRowPress} data-testid="needs-list" className="needs-drawer-list">
        <ScrollHint axis="y" scrollRef={listRef} className="needs-desk">
          {showMuted && shown.length > 0 ? (
            <SurfaceSection label="Muted" count={shown.length || null} data-testid="needs-muted" className="needs-drawer-muted">
              <NeedsList label="Muted">
                {shown.map((face) => <NeedRow key={face.id} face={face} primary={false} projects={multipleProjects} plates={false} />)}
              </NeedsList>
            </SurfaceSection>
          ) : shown.length > 0 ? (
            <>
              {first ? <FirstPlate face={first} projects={multipleProjects} /> : null}
              <Ledger groups={ledgerGroups(rest, first?.id ?? null)} firstId={firstId} projects={multipleProjects}
                arrivals={groups.map((group) => {
                  const label = `New from ${group.arrival.meetingTitle || "a meeting"}`;
                  const day = dayWord(group.arrival.startedAt);
                  return { key: group.arrival.meetingId, label: day ? `${label} · ${day}` : label, faces: group.faces };
                })} />
            </>
          ) : scope === "people" && !settling ? (
            <p className="needs-drawer-none" data-testid="needs-none">Nothing waits on people here.</p>
          ) : null}
          {scope === "people" && !settling ? <div className="needs-people-foot">{openPeople}</div> : null}
        </ScrollHint>
      </div>
      </ItemReaderContext.Provider>}
      {/* The Chair's head keeps its testids (the Chair-ready signal of the
          glass rigs): the status bar's first word IS the Chair's display. */}
      <StatusBar data-testid="arrival-headline" items={statusItems} verbs={dropped ? <NeedsDroppedReceipt /> : null} />
    </div>
  );
}
