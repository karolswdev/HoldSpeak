/** Needs you: one selection list, a reader for the selected need, and the
 * actions acknowledged in this window. The hub owns membership and rank. */
import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import { useAgentFlights } from "../agentFlights";
import { reportWriteFailure } from "../hooks/useWriteReceipt";
import { refreshNeedsYou, useNeedsYou } from "../needsYou";
import { openProjectRoom, openSurfaceOr } from "../shell";
import { useDesk } from "../store";
import { ListView, ListPane, SegmentedTabs, InspectorFacts, InspectorQuestion, StatusBar, SurfaceState, type ListVerb, type ObjectListRow, type StatusBarItem } from "../surface";
import { wireDate } from "../surface/format";
import { groupGaps, readCoverage } from "../coverage";
import { armingFace, coverageGroupFace, dayWord, needFace, needFaces, needsHead, whenWord, type NeedFace } from "./needsFace";
import { useArmingOutcome } from "./arming";
import { Token } from "../surface/Token";
import { ItemReader, readsInPlace } from "./ItemReader";
import { INTELLIGENCE_NAVIGATE, takeFollowThrough, type IntelligenceNavigation } from "../intelligenceNavigation";
import { faceOpener, hhmm, offerUndo, useDropped, type Well } from "./NeedVerbs";

import { laterAnswers, dismissAnswer, needFailure, type NeedAnswer } from "./needActions";
import { selectedNeed, needName, type SelectedNeed, type AnsweredNeed } from "./selection";
import { followThrough } from "./needsApi";
import { guideOwnsView, useGuideView } from "../walk/viewState";
import { useWindowId } from "../components/window/windowIdContext";
import { useWindowBack } from "../surface/back";
import { useCompactViewport } from "../useCompactViewport";
import { openHand } from "../agentHand";
import { runAsProgram } from "../programs/RunAsProgram";
import { briefable, copyPageLink, revokePage, sendToTelegram } from "../reach";

// The row, its verbs and the mast live in their own files; these names
// stay importable from here.
export {
  faceOpener, needsRowSprite, openAgentAnswer, offerUndo, useDropped, nudgeText, useSourceReceipt, recheckSource, hasRowMenu,
} from "./NeedVerbs";
export { NeedRow, quietState, glyphWord, useRowMarks } from "./NeedRow";
export type NeedsScope = "mine" | "people";
export function inScope(face: Pick<NeedFace, "direction">, scope: NeedsScope): boolean {
  return scope === "people" ? face.direction === "theirs" : face.direction !== "theirs";
}
export { dayWord };
const answeredId = (need: AnsweredNeed) => `${need.face.id}:${need.at}`;

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
  const {needs, now, faces, ctx, coverage, outcome} = useNeedFaces();
  const [capped, setCapped] = useState(false);
  useEffect(() => {const timer = window.setTimeout(() => setCapped(true), 8000); return () => window.clearTimeout(timer);}, []);
  const [tab, setTab] = useState("waiting");
  const [scope, setScope] = useState<NeedsScope>("mine");
  const [show, setShow] = useState("waiting");
  const [selected, setSelected] = useState<string | null>(null);
  const [answered, setAnswered] = useState<AnsweredNeed[]>([]);
  const [hidden, setHidden] = useState<Set<string>>(() => new Set());
  const [requested, setRequested] = useState<string | null>(() => takeFollowThrough());
  const dropped = useDropped(state => state.dropped);
  const [receipt, setReceipt] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const pending = useRef(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [edit, setEdit] = useState<Well | null>(null);
  const [armed, setArmed] = useState<{need: SelectedNeed; answer: NeedAnswer} | null>(null);
  const muted = needs.mutedItems.map(item => needFace({ref: String(item.id ?? item.ref ?? ""), kind: "attention", item}, ctx));
  const items = [...needs.unmutedItems, ...needs.mutedItems];
  const records = [...faces, ...muted].map(face => selectedNeed(face, items, now, ctx.sessions));
  const shown = records.filter(need => inScope(need.face, scope) && !hidden.has(need.revision)
    && (show === "muted" ? muted.some(face => face.id === need.face.id)
      : !muted.some(face => face.id === need.face.id) && (show === "later" ? need.face.uncounted && !need.face.source
        : (scope === "people" || !need.face.uncounted) && !isLater(need.face, now))));
  const waiting = shown.find(need => need.face.id === selected) ?? null;
  const windowId = useWindowId();
  const seenMeetings = useRef(new Set<string>());
  useEffect(() => {
    const id = waiting?.face.arrival?.meetingId;
    if (!id || seenMeetings.current.has(id) || guideOwnsView(windowId ?? "chair:needs")) return;
    seenMeetings.current.add(id);
    void apiFetch("/api/desk/needs-you/seen", {method: "POST", json: {meeting_ids: [id]}}).catch(() => undefined);
  }, [waiting?.face.arrival?.meetingId]);
  const history = answered.find(need => answeredId(need) === selected) ?? null;
  const current = tab === "waiting" ? waiting : history;
  const live = useRef({records, selected: waiting, tab});
  live.current = {records, selected: waiting, tab};
  const mounted = useRef(true);
  useEffect(() => {mounted.current = true; return () => {mounted.current = false;};}, []);

  const select = (id: string | null) => {setSelected(id); setEdit(null); setArmed(null);};
  const changeTab = (next: string) => {setTab(next); select(null);};
  // Removing a row moves to the following row, then the preceding one. A late
  // response only moves the selection if it still names the captured revision.
  const previous = useRef(shown);
  useEffect(() => {
    if (tab === "waiting" && selected && !waiting) {
      const at = previous.current.findIndex(need => need.face.id === selected);
      select(shown[Math.min(Math.max(0, at), shown.length - 1)]?.face.id ?? null);
    }
    previous.current = shown;
  }, [shown.map(need => need.revision).join("|"), selected, tab]);
  useEffect(() => {setArmed(null); setEdit(null);}, [waiting?.revision]);
  const back = () => select(null);
  useGuideView(() => ({tab, scope, show, selected, edit, armed}), saved => {
    setTab(saved.tab); setScope(saved.scope); setShow(saved.show); setSelected(saved.selected);
    requestAnimationFrame(() => {if (mounted.current) {setEdit(saved.edit); setArmed(saved.armed);}});
  }, () => {setTab("waiting"); setScope("mine"); setShow("waiting"); select(null);}, 1, windowId ?? "chair:needs");
  const compact = useCompactViewport();
  useWindowBack(compact && current ? {onBack: back, testId: "needs-reader-back", label: "Back"} : null, [compact, current?.revision]);
  const follow = (id: string) => {
    const need = records.find(row => readsInPlace(row.face) === id);
    if (need) {setTab("waiting"); setShow(need.face.uncounted && need.face.direction !== "theirs" ? "later" : "waiting"); setScope(need.face.direction === "theirs" ? "people" : "mine"); select(need.face.id);}
  };
  useEffect(() => {
    const navigate = (event: Event) => {
      const nav = (event as CustomEvent<IntelligenceNavigation>).detail;
      if (nav?.view === "follow-through" && nav.followThroughId) {takeFollowThrough(); setRequested(nav.followThroughId);}
    };
    window.addEventListener(INTELLIGENCE_NAVIGATE, navigate);
    return () => window.removeEventListener(INTELLIGENCE_NAVIGATE, navigate);
  }, []);
  const recordKey = records.map(need => need.revision).join("|");
  useEffect(() => {
    if (requested && records.some(need => readsInPlace(need.face) === requested)) {follow(requested); setRequested(null);}
    setHidden(old => {
      const remaining = [...old].filter(revision => records.some(need => need.revision === revision));
      return remaining.length === old.size ? old : new Set(remaining);
    });
  }, [requested, recordKey]);
  const isCurrent = (need: SelectedNeed) => mounted.current && live.current.records.some(row => row.revision === need.revision)
    && live.current.selected?.revision === need.revision && live.current.tab === "waiting";
  const run = async (need: SelectedNeed, action: NeedAnswer) => {
    if (pending.current || !isCurrent(need)) return;
    pending.current = true; setBusy(need.revision); setFailure(null);
    try {
      await action.run();
      // Completion belongs to the captured need, including when the owner
      // selected another row while the request was in flight.
      if (!mounted.current) return;
      setReceipt(`${action.label} · ${needName(need)}`);
      if (!action.keeps) {
        setHidden(old => new Set([...old, need.revision]));
        setAnswered(old => [{...need, answer: action.label, at: new Date().toISOString()}, ...old.filter(row => row.revision !== need.revision)]);
      }
      if (action.id === "dismiss") {
        const v = need.face.verbs;
        const restore = v.kind === "work" ? () => followThrough(v.cardId, "reopen")
          : "proposalId" in v ? () => apiFetch(`/api/proposals/${encodeURIComponent(v.proposalId)}/restore`, {method: "POST"}) : null;
        if (restore) offerUndo(needName(need), async () => {
          await restore();
          if (mounted.current) {
            setHidden(old => new Set([...old].filter(revision => revision !== need.revision)));
            setReceipt(`Restored · ${needName(need)}`);
          }
        });
      }
      if (isCurrent(need)) {setArmed(null); setEdit(null);}
      void refreshNeedsYou(false);
      if (need.face.verbs.kind === "answer") void useAgentFlights.getState().load();
    } catch (error) {
      const target = isCurrent(need) ? "" : ` · ${needName(need)}`;
      if (mounted.current) setFailure(`${action.label} failed${target} · ${needFailure(error)} · Work kept · Check the need, then try again`);
    } finally {
      pending.current = false;
      void refreshNeedsYou(false);
      if (mounted.current) setBusy(null);
    }
  };
  const answer = (need: SelectedNeed, action: NeedAnswer) => {
    if (!isCurrent(need) || pending.current) return;
    if (action.destructive) setArmed({need, answer: action});
    else void run(need, action);
  };
  const open = (need: SelectedNeed) => {
    if (readsInPlace(need.face)) {select(need.face.id); return;}
    faceOpener(need.face)?.();
  };
  const forRow = (row: ObjectListRow | null) => shown.find(need => need.face.id === row?.id);
  const available = (row: ObjectListRow | null) => Boolean(forRow(row)) && !busy;
  const selectedLater = waiting ? laterAnswers(waiting.face) : [];
  const dismiss = waiting ? dismissAnswer(waiting.face) : null;
  const extras: ListVerb[] = [];
  const v = waiting?.face.verbs;
  if (v?.kind === "work") extras.push(
    {id: "date", label: "Set a date", enabled: available, run: () => setEdit("date")},
    {id: "program", label: "Run as a program", enabled: available, run: () => waiting && answer(waiting, {id: "program", label: "Made a program", keeps: true, run: () => runAsProgram({kind: "action", id: v.cardId})})},
    {id: "hand", label: "Hand to an agent session", enabled: available, run: () => openHand({kind: "action", id: v.cardId, title: waiting!.face.name})},
  );
  if (v?.kind === "work" && v.direction === "theirs") extras.unshift({id: "nudge", label: "Nudge", enabled: available, run: () => setEdit("nudge")});
  if ((v?.kind === "confirm" || v?.kind === "decide") && v.meetingId && !v.projectId) extras.push({id: "project", label: "Add to Project", enabled: available, run: () => setEdit("project")});
  if (v?.kind === "program" && v.ref && briefable(v.itemKind)) extras.push(...(v.page
    ? [{id: "revoke", label: "Revoke the page", enabled: available, run: () => waiting && answer(waiting, {id: "revoke", label: "Revoke the page", destructive: true, keeps: true, run: () => revokePage(String(v.page?.package_id))})}]
    : [{id: "page", label: "Copy page link", enabled: available, run: () => waiting && answer(waiting, {id: "page", label: "Copied page link", keeps: true, run: () => copyPageLink(String(v.ref))})},
       {id: "telegram", label: "Send to Telegram", enabled: available, run: () => waiting && answer(waiting, {id: "telegram", label: "Send to Telegram", destructive: true, keeps: true, run: () => sendToTelegram(String(v.ref))})}]));
  if (waiting?.face.project) extras.push({id: "project-room", label: `Open the Project: ${waiting.face.project.name}`, enabled: available, run: () => openProjectRoom(waiting.face.project!.id)});
  extras.push(
    ...(show !== "waiting" ? [{id: "show-waiting", label: "Show waiting items", run: () => {setShow("waiting"); select(null);}}] : []),
    ...(show !== "later" && records.some(need => need.face.uncounted && !need.face.source && need.face.direction !== "theirs") ? [{id: "show-later", label: "Show later items", run: () => {setShow("later"); select(null);}}] : []),
    ...(show !== "muted" && muted.length ? [{id: "show-muted", label: "Show muted items", run: () => {setShow("muted"); select(null);}}] : []),
    {id: "people", label: "Open People", run: () => openSurfaceOr("open-people", "/")},
    {id: "calendar", label: "Calendars…", run: () => openSurfaceOr("configure-settings", "/settings", "integration:calendar")},
    {id: "refresh", label: "Read again", run: () => void refreshNeedsYou()},
  );
  const verbs: ListVerb[] = [
    {id: "answer", label: "Answer…", enabled: available, run: row => {const need = forRow(row); if (need) {select(need.face.id); requestAnimationFrame(() => rootRef.current?.querySelector<HTMLInputElement>('[data-testid="needs-answer-form"] input')?.focus());}}},
    {id: "open", label: "Open source", key: "Enter", enabled: row => {const need = forRow(row); return Boolean(need && (readsInPlace(need.face) || faceOpener(need.face)));}, run: row => {const need = forRow(row); if (need) open(need);}},
    {id: "later", label: "Later", enabled: row => Boolean(forRow(row) && laterAnswers(forRow(row)!.face).length) && !busy,
      items: selectedLater.length ? selectedLater.map(action => ({id: action.id, label: action.label, enabled: available, run: row => {const need = forRow(row); if (need) answer(need, {...action, label: "Later"});}})) : undefined, run: () => undefined},
    {id: "dismiss", label: dismiss?.label ?? "Dismiss", enabled: row => Boolean(forRow(row) && dismissAnswer(forRow(row)!.face)) && !busy,
      run: row => {const need = forRow(row), action = need && dismissAnswer(need.face); if (need && action) answer(need, action);}},
    {id: "more", label: "More", items: extras, run: () => undefined},
  ];
  const lastReceipt = receipt || outcome.receipt;
  const status: StatusBarItem[] = [
    ...(needs.count > 0 ? [{key: "head", text: <>{needsHead(needs.count, needs.complete)}{lastReceipt ? <span data-testid="needs-receipt"> · {lastReceipt}</span> : null}</>, lamp: "ask" as const, testId: "arrival-display", priority: 100}] : []),
    ...(!needs.complete || !coverage.complete ? [{key: "coverage", text: "Some sources were not read", lamp: "fail" as const, priority: 100}] : []),
    ...(needs.peopleUnread ? [{key: "people", text: "People could not be read", lamp: "fail" as const, priority: 100}] : []),
    ...(failure ? [{key: "failure", text: failure, lamp: "fail" as const, testId: "needs-failure", priority: 200}] : []),
    ...(!needs.count && lastReceipt ? [{key: "receipt", text: lastReceipt, testId: "needs-receipt", priority: 90}] : []),
  ];
  const armedNow = armed && armed.need.revision === waiting?.revision ? armed : null;
  const question = armedNow ? <InspectorQuestion targetId={armedNow.need.revision} question={`${armedNow.answer.label}?`}
    leading={armedNow.need.face.verbs.kind === "send" ? <span data-testid="send-destination-word">{armedNow.need.face.verbs.destinationName} · {armedNow.need.face.verbs.send.channel === "file" ? "Folder" : armedNow.need.face.verbs.send.channel}</span> : undefined}
    consequence={needName(armedNow.need)} cancel={() => setArmed(null)} testId="needs-question"
    verb={{label: armedNow.answer.label, busy: Boolean(busy), disabled: Boolean(busy), testId: "needs-confirm-answer", run: () => void run(armedNow.need, armedNow.answer)}} /> : null;
  const read = needs.room !== null || Object.keys(needs.errors).length > 0;
  const empty = !needs.complete || !coverage.complete ? <SurfaceState error="Some needs were not read." onRetry={() => void refreshNeedsYou()} /> : <SurfaceState empty emptyLabel={show === "muted" ? "No muted items." : show === "later" ? "Nothing for later." : scope === "people" ? "Nothing waits on people here." : "Nothing needs you."} />;
  return <div ref={rootRef} className="surface-tab-panel kit-face" style={{container: "surface / inline-size", minHeight: 440}} data-testid="needs-drawer" aria-busy={!read || undefined}>
    <SegmentedTabs label="Needs you" value={tab} onChange={changeTab} tabs={[{id: "waiting", label: "Waiting"}, {id: "answered", label: "Answered"}]}>
      {tab === "waiting" ? <ListPane label="Need reader" listTestId="needs-list" previewTestId="needs-preview" list={<>
        <ListView label="Needs you" ordered rows={shown.map(need => ({id: need.face.id, kind: need.face.kind, name: needName(need), cells: {from: need.from}, when: need.when}))}
          columns={[{key: "name", word: "Need", priority: 100, track: "minmax(0, 3fr)"}, {key: "from", word: "From", priority: 40, track: "minmax(0, 1fr)"}, {key: "when", word: "When", priority: 20, track: "112px"}]}
          selectedId={selected} onSelect={select} onClearSelection={() => select(null)} verbs={verbs} defaultVerb="open"
          toolbar={{testId: "needs-toolbar", scopes: [{id: "whose", kind: "cycle", label: "Whose", value: scope, onChange: next => {setScope(next as NeedsScope); select(null);}, options: [{value: "mine", label: "Mine"}, {value: "people", label: "People"}]}]}}
          rowProps={row => {
            const face = shown.find(need => need.face.id === row.id)!.face;
            return {...(face.source ? {"data-testid": "needs-source-row"} : {"data-testid": "needs-row"}), "data-counted": !face.uncounted && !face.source ? "true" : "false", "data-direction": face.direction};
          }} />
        {!read ? capped ? <SurfaceState error="Needs not read." onRetry={() => void refreshNeedsYou()} /> : <SurfaceState loading /> : null}
      </>}>
        {question || (waiting ? <ItemReader key={waiting.revision + String(edit)} need={waiting} answer={answer} busy={Boolean(busy)} edit={edit} onBack={back} draft={drafts[waiting.revision + String(edit)] ?? ""} onDraftChange={value => setDrafts(old => ({...old, [waiting.revision + String(edit)]: value}))} /> : !read ? null : shown.length ? <p>Select a need.</p> : empty)}
      </ListPane> : <ListPane label="Answered need" list={<ListView label="Answered" ordered rows={answered.map(need => ({id: answeredId(need), kind: need.face.kind, name: needName(need), cells: {answer: need.answer}, when: whenWord(new Date(need.at))}))}
        columns={[{key: "name", word: "Need", priority: 100, track: "minmax(0, 3fr)"}, {key: "answer", word: "Answer", priority: 40}, {key: "when", word: "When", priority: 20}]}
        selectedId={selected} onSelect={select} toolbar={{}} verbs={[{id: "open", label: "Open source", key: "Enter", enabled: row => Boolean(answered.find(need => answeredId(need) === row?.id && faceOpener(need.face))), run: row => {const need = answered.find(need => answeredId(need) === row?.id); if (need) faceOpener(need.face)?.();}}]} defaultVerb="open" />}>
          {history ? <InspectorFacts name={needName(history)} rows={[{label: "Answer", value: history.answer}, {label: "When", value: whenWord(new Date(history.at))}, {label: "From", value: history.from}]} /> : <SurfaceState empty emptyLabel={answered.length ? "Select an answer." : "No answers in this window yet."} />}
        </ListPane>}
    </SegmentedTabs>
    <StatusBar data-testid="arrival-headline" items={status} verbs={dropped ? <NeedsDroppedReceipt /> : undefined} />
  </div>;
}
