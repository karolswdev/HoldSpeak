// PARKED 2026-11-11: The person views compose kit lists, facts, forms and questions.
/* The person ledger and its one composer; acknowledged writes keep newer drafts. */
import { CycleGadget, PadGadget, SurfaceLedger, SurfaceLedgerRow, SurfaceRow, SurfaceRows, SurfaceSection, SurfaceState, Spine, countToken, StatusBar } from "../../desk/surface";
import { PersonPrograms, personProgramsOf } from "../../desk/programs/PersonPrograms";
import { wireDate } from "../../desk/surface/format";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError } from "../../lib/api";
import * as hub from "../../desk/people/api";
import { failureTitle } from "../../desk/surface/plainFailure";
import { openSourceRef } from "../../desk/surface/citations";
import { refOpener } from "../../desk/openObject";
import { composePeoplePrep, type PeoplePrepData, type PrepCalendarEvent } from "../../desk/people/prepData";
import { keptDraft, useDeskDraft } from "../../desk/deskMemory";
import { useDesk } from "../../desk/store";
import { useDeskWriteReceipt } from "../../desk/hooks/useWriteReceipt";
import { nudgeText } from "../../desk/needs/NeedsDrawer";
import { NoteSendWells } from "../../desk/documentSendsLazy";
import "./people.css";
import { wireWords } from "../../desk/surface/words";
import { Readiness, Session, Commitment, OneOnOneBrief, RelationshipDetail, stateOf, isStoreOutage, isProtectedFailure, OweAttempt, CREATE_NO_EFFECT, ACCEPT_NO_EFFECT, failureCode, isAuthOrKeyFailure, checkSavedRequest, oneOnOneWhen, shortWhen, prsSummaryLabel, capTokens, shortDay, lowerDay, PrepNext, untilWords, isOverdue, dayLabel, kindWord } from "./peopleModel";
import { CommitmentInspector } from "./PeopleLinks";
type NowConcern = "prs" | "assignments" | "commitments" | null;
/** PHILO-17 REFIT: one row of a plate: the words, one pill, one verb. */
function PlateRow({ title, onTitle, meta, verb, testId }: { title: string; onTitle?: () => void; meta?: ReactNode; verb?: ReactNode; testId?: string }) {
  return <li className="people-plate-row" data-testid={testId}>
    <span className="people-plate-text">
      {onTitle ? <Button variant="chrome" className="people-plate-title" onClick={onTitle}>{title}</Button> : <span className="people-plate-title">{title}</span>}
      {meta ? <span className="people-plate-meta">{meta}</span> : null}
    </span>
    {verb}
  </li>;
}

/** HS-172-05: the rows behind a Prep concern (PRs, assignments, overdue). */
function ConcernDetail({ concern, brief }: { concern: Exclude<NowConcern, null>; brief: OneOnOneBrief }) {
  const ws = brief.watch_summary;
  if (concern === "prs" && ws?.prs_waiting?.length) return <div data-testid="now-prs-detail" className="people-concern">
    <SurfaceLedger count={`PRS WAITING ${ws.prs_waiting.length}`} cols="room">
      {ws.prs_waiting.map((pr) => <SurfaceLedgerRow key={`pr-${pr.pr_number}`} wrap expands={false}
        primary={<span className="surface-primary">{`#${pr.pr_number} · ${pr.title}`}</span>}
        cells={<span className="people-now-caption"><span className={pr.days_waiting >= 3 ? "people-now-caption-warning" : ""}>{pr.days_waiting} {pr.days_waiting === 1 ? "day" : "days"}</span>{pr.repo ? <> · <span>{pr.repo}</span></> : null}</span>}
        trailing={pr.url ? <Button dense variant="ghost" onClick={() => window.open(pr.url, "_blank", "noopener")}>Open PR</Button> : undefined} />)}
    </SurfaceLedger>
  </div>;
  if (concern === "assignments" && ws?.open_assignments?.length) return <div data-testid="now-assignments-detail" className="people-concern">
    <SurfaceLedger count={`ASSIGNMENTS OPEN ${ws.open_assignments.length}`} cols="room">
      {ws.open_assignments.map((a) => <SurfaceLedgerRow key={a.key} wrap expands={false}
        primary={<span className="surface-primary">{`${a.key} · ${a.summary}`}</span>}
        cells={<span className="people-now-caption"><span>{wireWords(a.status)}</span>{a.overdue ? <> · <span className="people-now-caption-warning">Overdue</span></> : null}</span>}
        trailing={a.url ? <Button dense variant="ghost" onClick={() => window.open(a.url, "_blank", "noopener")}>Open issue</Button> : undefined} />)}
    </SurfaceLedger>
  </div>;
  return null;
}

/** PHILO-17 REFIT — Prep, the lead: the next 1:1 as the focus plate (when,
 *  what to raise, add to the agenda), then two plates: what he owes and
 *  what is owed to him, each with its add row. Every fact is the person's
 *  record or the hub's 1:1 brief (`/brief`, read-only). */
/** Betterment D7: Nudge on a row she owes. It drafts the short message
 *  Needs you drafts (`nudgeText`), keeps it as a note and opens its Send
 *  well here; he presses Send (the egress rule). */
function PrepNudge({ task, person, due }: { task: string; person: string; due: string | null }) {
  const [note, setNote] = useState<{ id: string; title: string } | null>(null);
  const [failed, setFailed] = useState(false);
  const started = useRef(false);
  const text = nudgeText(task, person, due);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const title = `Nudge: ${task}`;
    void (async () => {
      try {
        const made = await hub.keepNudge(title, text);
        const id = String(made.note?.id ?? "");
        if (!id) { setFailed(true); return; }
        setNote({ id, title });
      } catch { setFailed(true); }
    })();
  }, [task, text]);
  return <div className="people-nudge" role="region" aria-label={`Nudge: ${task}`} data-testid="prep-nudge">
    <p className="people-nudge-text" data-testid="prep-nudge-text">{text}</p>
    {failed ? <SurfaceState error="The message was not prepared. Nothing was sent. Press Nudge to try again." />
      : note ? <NoteSendWells id={note.id} title={note.title} /> : <SurfaceState loading />}
  </div>;
}

/** HS-S33: what happened to the I owe Add, with the words he submitted
 *  (the field may already hold newer words). */
function OweReceipt({ attempt, onCheck, onAccept, onStartAnother }: { attempt: OweAttempt; onCheck(): void; onAccept(): void; onStartAnother(): void }) {
  const words = <span className="people-plate-title" data-testid="people-owe-submitted">{attempt.phase === "saved" ? attempt.saved.body : attempt.body}</span>;
  if (attempt.phase === "saved") {
    return <div className="people-row people-add-line" role="status" data-testid="people-owe-receipt" data-phase="saved">
      <span className="people-state" data-tone="ok">{attempt.saved.state === "open" ? "Saved" : `Saved · ${attempt.saved.state}`}</span>{words}
    </div>;
  }
  if (attempt.phase === "creation_uncertain") {
    return <div className="people-row people-add-line" role="status" data-testid="people-owe-receipt" data-phase={attempt.phase}>
      <span className="people-failure-label">The promise may be saved · Look in the list before you add it again</span>{words}
      <Button dense variant="ghost" onClick={onStartAnother} data-testid="people-owe-start-another">Start another promise</Button>
    </div>;
  }
  const checking = attempt.phase === "checking";
  const note = attempt.phase === "acceptance_uncertain" ? attempt.note : "Request saved · Not yet a promise";
  const acceptable = attempt.phase === "acceptance_uncertain" && attempt.acceptable;
  return <div className="people-row people-add-line" role="status" data-testid="people-owe-receipt" data-phase={attempt.phase}>
    <span className="people-failure-label">{note}</span>{words}
    <Button dense variant="secondary" disabled={!acceptable} onClick={onAccept} data-testid="people-owe-accept-saved">Accept saved request</Button>
    <Button dense variant="ghost" loading={checking} disabled={checking} onClick={onCheck} data-testid="people-owe-check">Check saved request</Button>
  </div>;
}

export function PeopleLedger({ relationship, onRefresh, onProtectedFailure, onNext, composerRequest }: { relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown, mayHaveSaved?: boolean): void; onNext?(next: PrepNext): void;
  composerRequest?: number }) {
  const [brief, setBrief] = useState<OneOnOneBrief | null>(null);
  const [failure, setFailure] = useState("");
  const [prepTitle, setPrepTitle] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [concern, setConcern] = useState<NowConcern>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const recordingState = useDesk((state) => state.recording);
  const { failure: recordingFailure, receipt: recordingReceipt } = useDeskWriteReceipt();
  const [selectedCommitment, setSelectedCommitment] = useState<{ commitment: Commitment } | null>(null);
  const commitmentOrigin = useRef<HTMLElement | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [preparedAt] = useState(() => new Date().toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false }));
  // The person's record is re-read after each write; the brief follows it.
  // A failed brief read is a state: it stays on screen until Try again (a
  // new `attempt`); a quiet re-read of the record never erases it
  // (peoplePrepB4: "a failed brief read is a named failure with Try again").
  const failedAt = useRef<{ attempt: number; id: string } | null>(null);
  useEffect(() => {
    if (failedAt.current?.attempt === attempt && failedAt.current.id === relationship.id) return;
    failedAt.current = null;
    let live = true;
    void hub.readBrief<OneOnOneBrief>(relationship.id)
      .then((result) => { if (live) { setBrief(result.brief ?? ({ open_commitments: [], agenda_items: [] } as unknown as OneOnOneBrief)); setFailure(""); } })
      .catch((cause) => {
        if (!live) return;
        if (isProtectedFailure(cause) && !isStoreOutage(cause)) { onProtectedFailure(cause); return; }
        failedAt.current = { attempt, id: relationship.id };
        setFailure("Could not load the prep · Nothing changed · Try again"); setPrepTitle(failureTitle(cause));
      });
    return () => { live = false; };
  }, [relationship, attempt]); // eslint-disable-line react-hooks/exhaustive-deps
  // The countdown ticks; the words change in a fixed box.
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 30_000);
    return () => window.clearInterval(timer);
  }, []);
  const [agendaDraft, setAgendaDraft, forgetAgenda] = useDeskDraft(`people/1on1/${relationship.id}`);
  const [oweDraft, setOweDraftRaw, forgetOwe] = useDeskDraft(`people/request/${relationship.id}`);
  // HS-S33: the I owe attempt. The ref is the synchronous guard (a second
  // Enter cannot start a second request); the state draws it.
  const oweRef = useRef<OweAttempt | null>(null);
  const [owe, setOweState] = useState<OweAttempt | null>(null);
  const setOwe = (next: OweAttempt | null) => { oweRef.current = next; setOweState(next); };
  const oweSeq = useRef(0);
  const oweEdits = useRef(0);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; oweRef.current = null; }; }, []);
  const setOweDraft = (value: string) => { oweEdits.current += 1; setOweDraftRaw(value); };
  const [owedDraft, setOwedDraft, forgetOwed] = useDeskDraft(`people/owed/${relationship.id}`);
  const [noteDraft, setNoteDraft, forgetNote] = useDeskDraft(`people/context/${relationship.id}/body`);
  const [visibility, setVisibility, forgetVisibility] = useDeskDraft(`people/context/${relationship.id}/visibility`);
  const [savedKind, setComposeKind] = useDeskDraft(`people/compose/${relationship.id}`);
  const composeKind = savedKind || "agenda";
  const composeRef = useRef<HTMLDivElement>(null);
  const agendaRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!composerRequest) return;
    setComposeKind("note");
    composeRef.current?.scrollIntoView?.({ block: "nearest" });
    composeRef.current?.querySelector("textarea")?.focus();
  }, [composerRequest, Boolean(brief || failure)]);
  // Betterment D7: Nudge on her row prepares a message; he presses Send.
  const [nudging, setNudging] = useState<{ id: string; task: string; due: string | null } | null>(null);
  const toggleNudge = (row: { id: string; task: string; due: string | null }) => setNudging((current) => (current?.id === row.id ? null : row));

  useEffect(() => {
    const event = brief ? composePeoplePrep(brief).nextOneOnOne ?? null : null;
    const last = brief?.last_time?.one_on_one ? brief.last_time.started_at : null;
    onNext?.({ at: relationship.next_one_on_one ?? event?.starts_at ?? null, eventId: event?.id ?? null, last });
  }, [brief, relationship.next_one_on_one, onNext]);
  // The folds keep one place in the tree (a Fragment's second child), so a
  // well open in a fold survives the prep's first read.
  if (!brief && !failure) return <SurfaceState loading />;

  const inspectCommitment = (commitment: Commitment) => {
    commitmentOrigin.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setSelectedCommitment({ commitment });
  };
  const closeCommitment = () => {
    setSelectedCommitment(null);
    commitmentOrigin.current?.focus();
  };
  const run = async (key: string, work: () => Promise<unknown>, after?: () => void) => {
    setBusy(key);
    try { await work(); after?.(); onRefresh(); } catch (cause) { onProtectedFailure(cause); } finally { setBusy(null); }
  };
  const addAgenda = (onSaved?: () => void) => {
    const submitted = agendaDraft;
    const body = submitted.trim(); if (!body || busy === "agenda") return;
    void run("agenda", async () => {
      const session = relationship.sessions?.[0] ?? (await hub.createOneOnOne<Session>(relationship.id)).one_on_one;
      await hub.addAgendaItem(session.id, body);
    }, () => { if ((keptDraft(`people/1on1/${relationship.id}`) ?? "") === submitted) { forgetAgenda(); onSaved?.(); } });
  };
  // What he owes: the hub's own path (a request he accepts becomes his
  // commitment). HS-S33: two writes, one held request id.
  const live = (seq: number) => mounted.current && oweRef.current?.seq === seq;
  const finishOwe = (attempt: Extract<OweAttempt, { requestId: string }>, mark: { edits: number; drafts: unknown } | null, onSaved?: () => void) => {
    void (async () => {
      const { seq, relationshipId, body, requestId } = attempt;
      setOwe({ phase: "accepting", seq, relationshipId, body, requestId });
      let made: { commitment?: { id?: unknown; request_id?: unknown; body?: unknown; state?: unknown } };
      try {
        made = await hub.acceptRequest(requestId);
      } catch (cause) {
        if (!live(seq)) return;
        await settleFailure(seq, cause, () => setOwe({ phase: "acceptance_uncertain", seq, relationshipId, body, requestId, acceptable: !ACCEPT_NO_EFFECT.has(failureCode(cause)),
          note: ACCEPT_NO_EFFECT.has(failureCode(cause)) ? "Request saved · Accept was refused" : "Request saved · Not yet a promise" }));
        return;
      }
      if (!live(seq)) return;
      const commitment = made?.commitment;
      if (!commitment || typeof commitment.id !== "string" || !commitment.id || commitment.request_id !== requestId) {
        setOwe({ phase: "acceptance_uncertain", seq, relationshipId, body, requestId, acceptable: true, note: "Request saved · Not yet a promise" });
        return;
      }
      setOwe({ phase: "saved", seq, relationshipId, body, requestId, saved: { body: String(commitment.body ?? body), state: String(commitment.state ?? "open") } });
      // Clear only the exact unchanged draft of this attempt: same text, no
      // edit here, no draft write anywhere since the press.
      const key = `people/request/${relationshipId}`;
      if (mark && mark.edits === oweEdits.current && mark.drafts === useDesk.getState().drafts && (keptDraft(key) ?? "").trim() === body) {
        forgetOwe(); setOwe(null); onSaved?.();
      }
      onRefresh();
    })();
  };
  /** A failed write of this attempt: a key or owner failure clears the
   *  private view; a store 503 asks readiness which one it was. */
  const settleFailure = async (seq: number, cause: unknown, keep: () => void) => {
    let clear = isAuthOrKeyFailure(cause);
    if (!clear && cause instanceof ApiError && cause.status === 503) {
      try {
        const ready = await hub.readReadiness<Readiness>();
        clear = stateOf(ready) !== "ready";
      } catch { clear = true; }
      if (!live(seq)) return;
    }
    if (clear) { setOwe(null); onProtectedFailure(cause, true); return; }
    keep();
  };
  const addOwe = (onSaved?: () => void) => {
    const submitted = oweDraft;
    const body = submitted.trim(); if (!body) return;
    const current = oweRef.current;
    if (current && current.phase !== "saved") return;
    const seq = ++oweSeq.current;
    const relationshipId = relationship.id;
    const mark = { edits: oweEdits.current, drafts: useDesk.getState().drafts };
    setOwe({ phase: "creating", seq, relationshipId, body });
    void (async () => {
      let made: { request?: { id?: unknown; relationship_id?: unknown } };
      try {
        made = await hub.createRequest(relationship.id, body);
      } catch (cause) {
        if (!live(seq)) return;
        if (cause instanceof ApiError && CREATE_NO_EFFECT.has(failureCode(cause)) && !isAuthOrKeyFailure(cause)) {
          setOwe(null); onProtectedFailure(cause); return;
        }
        await settleFailure(seq, cause, () => setOwe({ phase: "creation_uncertain", seq, relationshipId, body }));
        return;
      }
      if (!live(seq)) return;
      const request = made?.request;
      if (!request || typeof request.id !== "string" || !request.id || (request.relationship_id !== undefined && request.relationship_id !== relationshipId)) {
        setOwe({ phase: "creation_uncertain", seq, relationshipId, body });
        return;
      }
      finishOwe({ phase: "accepting", seq, relationshipId, body, requestId: request.id }, mark, onSaved);
    })();
  };
  /** Check saved request: one read of the person; it never writes. */
  const checkOwe = () => {
    const current = oweRef.current;
    if (!current || current.phase !== "acceptance_uncertain") return;
    const { seq, relationshipId, body, requestId } = current;
    setOwe({ phase: "checking", seq, relationshipId, body, requestId });
    void hub.readPerson(relationshipId)
      .then((read) => {
        if (!live(seq)) return;
        const found = checkSavedRequest(read, relationshipId, requestId, body);
        if (found.kind === "saved") { setOwe({ phase: "saved", seq, relationshipId, body, requestId, saved: found.saved }); onRefresh(); return; }
        setOwe({ phase: "acceptance_uncertain", seq, relationshipId, body, requestId,
          acceptable: found.kind === "acceptable", note: found.kind === "acceptable" ? "Request saved · Not yet a promise" : found.note });
      })
      .catch((cause) => {
        if (!live(seq)) return;
        void settleFailure(seq, cause, () => setOwe({ phase: "acceptance_uncertain", seq, relationshipId, body, requestId, acceptable: true, note: "Could not read the saved request · Check again" }));
      });
  };
  /** Accept saved request: the same id again (the store returns the one
   *  commitment if it was already accepted). */
  const acceptSavedOwe = () => {
    const current = oweRef.current;
    if (!current || current.phase !== "acceptance_uncertain" || !current.acceptable) return;
    finishOwe(current, null);
  };
  const addOwed = (onSaved?: () => void) => {
    const submitted = owedDraft;
    const body = submitted.trim(); if (!body || busy === "owed") return;
    void run("owed", () => hub.createOwed(relationship.id, body),
      () => { if ((keptDraft(`people/owed/${relationship.id}`) ?? "") === submitted) { forgetOwed(); onSaved?.(); } });
  };
  const addNote = () => {
    const submitted = noteDraft;
    const selectedVisibility = visibility === "shared_intent" ? "shared_intent" : "leader_private";
    if (!submitted.trim() || busy) return;
    void run("note", () => hub.createNote(relationship.id, { topic: "", body: submitted.trim(), visibility: selectedVisibility }),
      () => { if ((keptDraft(`people/context/${relationship.id}/body`) ?? "") === submitted
        && (keptDraft(`people/context/${relationship.id}/visibility`) ?? "") === visibility) { forgetNote(); forgetVisibility(); } });
  };
  const done = (id: string) => void run(`done:${id}`, () => hub.commitmentDone(id));
  const completeAction = (id: string) => void run(`action-done:${id}`, () => hub.completeAction(id));
  const removeAgenda = (id: string) => void run(`remove:${id}`, () => hub.removeAgendaItem(id));
  // HS-S33: Asked of you for the held request goes through the attempt.
  const heldRequest = owe && "requestId" in owe && owe.phase !== "saved" ? owe.requestId : null;
  const accept = (id: string) => {
    if (id === heldRequest) { acceptSavedOwe(); return; }
    void run(`accept:${id}`, () => hub.acceptRequest(id));
  };

  const prep = brief ? composePeoplePrep(brief) : null;
  const nextEvent = prep?.nextOneOnOne ?? null;
  const nextAt = relationship.next_one_on_one ?? nextEvent?.starts_at ?? null;
  const suggestions = !nextAt && prep ? prep.calendarLinkSuggestions : [];
  const nextTitle = nextEvent?.title || (relationship.calendar_links ?? [])[0]?.label || "1:1";
  const until = nextAt ? untilWords(nextAt, now) : "";

  const ws = brief?.watch_summary;
  const prCount = ws?.prs_waiting?.length ?? 0;
  const assignCount = ws?.open_assignments?.length ?? 0;
  const youOweRows = (relationship.commitments ?? []).filter((item) => (item.state ?? "open") === "open");
  // The brief's open commitments name what is overdue (the 1:1 brief's read).
  const overdue = (brief?.open_commitments ?? []).filter((item) => isOverdue(item.due));
  const lm = brief?.last_meeting;
  const displayName = brief?.display_name ?? relationship.display_name;
  const toggle = (next: Exclude<NowConcern, null>) => setConcern((current) => (current === next ? null : next));
  const concernRows: ReactNode[] = [];
  if (brief && prCount) concernRows.push(<li key="prs" className="people-work-row" data-testid="prep-prs-row">
    <span className="people-pill" data-tone={ws?.oldest_waiting_days && ws.oldest_waiting_days >= 3 ? "warn" : "info"} data-testid="prep-prs-label">{prsSummaryLabel(prCount, displayName)}</span>
    <span className="people-raise-tokens">
      {ws?.oldest_waiting_days ? <span className="people-prep-token" data-warning={ws.oldest_waiting_days >= 3 || undefined} data-testid="prep-prs-days">{ws.oldest_waiting_days}+ DAYS</span> : null}
      <span className="people-prep-token" data-testid="prep-prs-numbers">{capTokens((ws?.prs_waiting ?? []).map((pr) => `#${pr.pr_number}`))}</span>
    </span>
    <Button dense variant="ghost" onClick={() => toggle("prs")} aria-expanded={concern === "prs"} data-testid="prep-prs-open">{concern === "prs" ? "Hide" : "Show"}</Button>
  </li>);
  if (brief && assignCount) concernRows.push(<li key="assign" className="people-work-row" data-testid="prep-assignments-row">
    <span className="people-pill" data-tone={(ws?.open_assignments ?? []).some((a) => a.overdue) ? "warn" : "info"} data-testid="prep-assignments-label">{assignCount} {assignCount === 1 ? "ASSIGNMENT" : "ASSIGNMENTS"} OPEN</span>
    <span className="people-raise-tokens">
      <span className="people-prep-token" data-testid="prep-assignments-keys">{capTokens((ws?.open_assignments ?? []).map((a) => a.key).filter(Boolean))}</span>
      {(ws?.open_assignments ?? []).some((a) => a.overdue) ? <span className="people-prep-token" data-warning="true" data-testid="prep-assignments-overdue">OVERDUE</span> : null}
    </span>
    <Button dense variant="ghost" onClick={() => toggle("assignments")} aria-expanded={concern === "assignments"} data-testid="prep-assignments-open">{concern === "assignments" ? "Hide" : "Show"}</Button>
  </li>);
  if (overdue.length) concernRows.push(<li key="overdue" className="people-work-row" data-testid="prep-commitments-row">
    <span className="people-pill" data-tone="danger" data-testid="prep-commitments-label">{countToken(overdue.length, "COMMITMENT")} OVERDUE</span>
    <span className="people-raise-tokens"><span className="people-prep-token">{overdue[0].body.length > 30 ? overdue[0].body.slice(0, 30) : overdue[0].body}</span></span>
  </li>);
  const agenda = prep?.agenda ?? [];
  const asked = (relationship.requests ?? []).filter((item) => item.state === "requested");
  const owedRows = (relationship.owed_to_you ?? []).filter((item) => (item.state ?? "open") === "open");
  const actions = prep?.openMeetingActions ?? [];
  const myActions = (brief?.i_owe_meeting_actions ?? []).filter((a) => !["done", "dismissed", "completed"].includes(String(a.status ?? "")));
  const firstName = (displayName || "").trim().split(/\s+/)[0] || "They";
  // LAST TIME: the newest meeting of the linked 1:1 series (the brief's
  // linked_meetings, newest first), its decisions and open actions.
  // Betterment D7: the hub's Last time (the last 1:1 with her, else the
  // last meeting she was in) leads; the linked series is the fallback.
  const lastTime = brief?.last_time ?? null;
  const last = brief?.linked_meetings?.[0] ?? null;
  const lastId = lastTime?.meeting_id ?? last?.meeting_id ?? lm?.meeting_id ?? null;
  const lastTitle = lastTime ? (lastTime.one_on_one ? "1:1" : lastTime.title || "Meeting") : last?.title || lm?.title || "Meeting";
  const lastLines: Array<{ key: string; kind: "decision" | "action"; text: string; meta?: string | null }> = lastTime ? [
    ...lastTime.decisions.map((d) => ({ key: `d-${d.id}`, kind: "decision" as const, text: d.decision_text })),
    ...lastTime.points.map((a) => ({ key: `a-${a.id}`, kind: "action" as const, text: a.task, meta: [a.owner, a.status === "done" ? "Done" : null].filter(Boolean).join(" · ") || null })),
  ] : last ? [
    ...last.decisions.map((d) => ({ key: `d-${d.id}`, kind: "decision" as const, text: d.decision_text })),
    ...last.open_action_items.map((a) => ({ key: `a-${a.id}`, kind: "action" as const, text: a.task, meta: [a.owner, a.due ? `By ${shortDay(a.due)}` : null].filter(Boolean).join(" · ") || null })),
  ] : [];
  const showLast = Boolean(lastId && (lastTime || lastLines.length || (lm && lm.item_count > 0)));
  const lastStarted = lastTime?.started_at ?? last?.started_at ?? null;
  const lastFacts = lastTime ? [
    lastTime.points.length ? (lastTime.points.length === 1 ? "1 point" : `${lastTime.points.length} points`) : null,
    lastTime.decisions.length ? (lastTime.decisions.length === 1 ? "1 decision" : `${lastTime.decisions.length} decisions`) : null,
  ].filter(Boolean).join(" · ") : "";
  // ON THE DESK: what the plaintext desk holds on this person's projects
  // (the brief's memory excerpts; its search words are the person's names).
  const excerpts = (brief?.memory?.excerpts ?? []).filter((e) => (e.title || e.text).trim());

  // The ledger's rows, one model for both ways.
  type LedgerRow = { key: string; side: "they" | "you"; tone: "brass" | "steel" | "coral" | "moss"; text: string; due: string | null;
    meta?: ReactNode; verb?: ReactNode; inspect?: Commitment; open?: () => void; testId?: string };
  const toneOf = (side: "they" | "you", due?: string | null): LedgerRow["tone"] => (isOverdue(due) ? "coral" : side === "they" ? "brass" : "steel");
  const fromMeeting = (title?: string | null, kind?: string | null) => title ? `from ${title}` : kind === "thought" ? "from Note" : kind === "meeting" ? "from Meeting" : "";
  const nudgeVerb = (id: string, task: string, due: string | null) => <Button dense variant="ghost" aria-expanded={nudging?.id === id} onClick={() => toggleNudge({ id, task, due })}>Nudge</Button>;
  const doneVerb = (key: string, press: () => void) => <Button dense variant="ghost" loading={busy === key} onClick={press}>Done</Button>;
  const doneRows = [...(relationship.owed_to_you ?? []).map((row) => ({ row, side: "they" as const })), ...(relationship.commitments ?? []).map((row) => ({ row, side: "you" as const }))]
    .filter(({ row }) => row.state === "done").slice(-3);
  const ledgerOpen: LedgerRow[] = [
    ...asked.map((item) => ({ key: `q:${item.id}`, side: "you" as const, tone: "steel" as const, text: item.body, due: null, testId: "people-asked",
      meta: "Asked of you",
      verb: <Button dense variant="ghost" loading={busy === `accept:${item.id}` || (item.id === heldRequest && owe?.phase === "accepting")} disabled={item.id === heldRequest && (owe?.phase !== "acceptance_uncertain" || !owe.acceptable)} onClick={() => accept(item.id)}>Accept</Button> })),
    ...owedRows.map((item) => ({ key: `o:${item.id}`, side: "they" as const, tone: toneOf("they", item.due), text: item.body, due: item.due ?? null,
      meta: `${firstName} owes you`, inspect: item,
      verb: isOverdue(item.due) ? nudgeVerb(item.id, item.body, item.due ?? null) : doneVerb(`done:${item.id}`, () => done(item.id)) })),
    ...actions.map((action) => ({ key: `a:${action.id}`, side: "they" as const, tone: toneOf("they", action.due), text: action.task, due: action.due ?? null,
      meta: [`${firstName} owes you`, fromMeeting(action.meeting_title, action.source_type)].filter(Boolean).join(" · "),
      open: refOpener(action.source_ref || (action.meeting_id ? `meeting:${action.meeting_id}` : null)) ?? undefined,
      verb: isOverdue(action.due) ? nudgeVerb(action.id, action.task, action.due) : doneVerb(`action-done:${action.id}`, () => completeAction(action.id)) })),
    ...youOweRows.map((item) => ({ key: `c:${item.id}`, side: "you" as const, tone: toneOf("you", item.due), text: item.body, due: item.due ?? null,
      meta: ["You owe", item.execution_links?.length ? "On an automation" : ""].filter(Boolean).join(" · "), inspect: item, verb: doneVerb(`done:${item.id}`, () => done(item.id)) })),
    ...myActions.map((action) => ({ key: `m:${action.id}`, side: "you" as const, tone: toneOf("you", action.due), text: action.task, due: action.due ?? null, testId: "prep-i-owe-action",
      meta: ["You owe", fromMeeting(action.meeting_title)].filter(Boolean).join(" · "),
      open: refOpener(action.meeting_id ? `meeting:${action.meeting_id}` : null) ?? undefined, verb: doneVerb(`action-done:${action.id}`, () => completeAction(action.id)) })),
  ];
  const dayOf = (row: LedgerRow) => (row.due ? wireDate(row.due)?.getTime() ?? Infinity : Infinity);
  const ledger: LedgerRow[] = [
    ...ledgerOpen.filter((row) => row.tone === "coral").sort((a, b) => dayOf(a) - dayOf(b)),
    ...ledgerOpen.filter((row) => row.tone !== "coral").sort((a, b) => dayOf(a) - dayOf(b)),
    ...doneRows.map(({ row, side }) => ({ key: `d:${row.id}`, side, tone: "moss" as const, text: row.body, due: null, meta: "Done", inspect: row,
      verb: <Button dense variant="ghost" onClick={() => inspectCommitment(row)}>Open inspector</Button> })),
  ];
  const theyCount = owedRows.length + actions.length;
  const youCount = youOweRows.length + myActions.length;
  const ledgerFacts = [theyCount ? `${theyCount} owed to you` : "", youCount ? `${youCount} you owe` : ""].filter(Boolean).join(" · ");
  const eventId = nextEvent?.id ?? null;
  const record = eventId && recordingState !== "recording" ? (
    <Button dense variant="primary" loading={recordingState === "busy"} disabled={recordingState !== "idle"}
      onClick={() => void useDesk.getState().startRecording({ calendarEventId: eventId })} data-testid="prep-record-meeting">Record 1:1</Button>
  ) : null;

  // The ledger by weight: the plate, what is owed both ways, the agenda,
  // the Programs, the last 1:1, the open work, the desk; then the folds.
  return <><div data-testid="people-prep-lens" className="people-prep">
    {failure ? <span className="people-failure" role="alert" data-testid="people-next-failure">
      <span className="people-failure-label" title={prepTitle || undefined}>{failure}</span>
      <Button dense variant="ghost" onClick={() => setAttempt((n) => n + 1)}>Try again</Button>
    </span> : null}
    {nextAt ? <section className="people-now" data-tone="steel" aria-label="Next 1:1" data-testid="people-plate">
      <span className="people-now-eyebrow">Next 1:1</span>
      <h3 className="people-now-title">{nextTitle}</h3>
      <span className="people-now-facts" data-testid="people-next-1on1">{[oneOnOneWhen(nextAt), until].filter(Boolean).join(" · ")}</span>
      <div className="people-now-verbs"><Button variant="primary" onClick={() => {
        agendaRef.current?.scrollIntoView?.({ block: "start", behavior: "smooth" });
        agendaRef.current?.focus();
      }}>Open prep</Button></div>
    </section> : null}

    {/* The commitments: ONE ledger by weight. Each row is a promise, its
        spine in the meaning colour (brass owed to you, steel you owe,
        coral overdue, moss done), the words, the day in mono and its one
        verb: Nudge on theirs past its day, else Done; Accept on a request;
        Open inspector on a done one. Overdue first, then by day. One Add on the head asks
        which way it goes. */}
    <section className="people-section people-commitments" aria-label="Commitments" data-testid="people-commitments">
      <header className="people-section-head">
        <h3 className="people-section-cap">Commitments</h3>
        {ledgerFacts ? <span className="people-section-fact" data-testid="people-commitments-facts">{ledgerFacts}</span> : null}
      </header>
      {ledger.length ? <SurfaceLedger cols="people" label="Commitments">
        <ul className="surface-ledger-rows" data-testid="prep-commitments">
          {ledger.map((row) => <SurfaceLedgerRow key={row.key} data-testid={row.testId} wrap
            lead={<Spine className="people-ledger-spine" tone={row.tone} />}
            lineLabel={row.inspect || row.open ? row.text : undefined}
            primary={<span className="people-ledger-words" data-side={row.side} data-tone={row.tone}>{row.text}</span>}
            meta={row.meta}
            cells={row.due ? <span className="people-ledger-due" data-overdue={row.tone === "coral" || undefined}>{`by ${shortDay(row.due)}`}</span> : undefined}
            trailing={row.verb}
            expands={Boolean(row.inspect)}
            open={Boolean(row.inspect) && selectedCommitment?.commitment.id === row.inspect?.id}
            onToggle={row.inspect ? () => (selectedCommitment?.commitment.id === row.inspect!.id ? closeCommitment() : inspectCommitment(row.inspect!)) : row.open}>
            {row.inspect && selectedCommitment?.commitment.id === row.inspect.id ? <CommitmentInspector key={row.inspect.id} commitment={row.inspect} onClose={closeCommitment} onRefresh={() => { onRefresh(); setSelectedCommitment(null); }} onProtectedFailure={onProtectedFailure} /> : null}
          </SurfaceLedgerRow>)}
        </ul>
      </SurfaceLedger> : null}
      {nudging ? <PrepNudge key={nudging.id} task={nudging.task} person={displayName} due={nudging.due} /> : null}
    </section>

    <section ref={agendaRef} tabIndex={-1} className="people-section" aria-label="Agenda" data-testid="people-next-plate">
      <header className="people-section-head">
        <h3 className="people-section-cap">Agenda</h3>
        {record}
      </header>
      {!nextAt && suggestions.length && prep ? <LinkSuggestions relationship={relationship} prep={prep} onLinked={onRefresh} onProtectedFailure={onProtectedFailure} testId="prep-link-suggestion" />
        : !nextAt && brief ? <div className="people-row people-next-none"><span className="people-row-meta">No 1:1 planned</span></div> : null}
      {prep?.projects.length ? <div className="people-row people-projects" data-testid="prep-projects">
        {prep.projects.map((project) => <Button key={project.id} variant="chrome" className="people-link" onClick={refOpener(`project:${project.id}`) ?? undefined}>{project.name}</Button>)}
      </div> : null}
      {brief && !agenda.length ? <span className="people-row-meta">No agenda items</span> : null}
      {brief ? <ol className="people-rows" data-testid="prep-to-raise">
        {agenda.map((item, index) => <li key={item.id} className="people-row people-raise-row" data-testid="prep-agenda">
          <span className="people-raise-n" aria-hidden="true">{index + 1}</span>
          <span className="people-raise-words">{item.body}</span>
          {item.rolled_from_id ? <span className="people-row-meta">Rolled</span> : null}
          <Button dense variant="ghost" className="people-raise-remove" aria-label={`Remove ${item.body}`} loading={busy === `remove:${item.id}`} onClick={() => removeAgenda(item.id)}>Remove</Button>
        </li>)}
      </ol> : null}
    </section>

    {/* Programs (2026-10-28, §9b): the Programs for this person, and the
        1:1's "To show them" and "To ask". */}
    <PersonPrograms programs={personProgramsOf(brief, relationship)} name={firstName} />

    {showLast && lastId ? <section className="people-section" aria-label="Last time" data-testid="prep-last">
      <header className="people-section-head">
        <h3 className="people-section-cap">Last time</h3>
        <span className="people-section-fact" data-testid="prep-meeting-row">
          <span className="people-plate-title" data-testid="prep-last-title">{lastStarted ? `${lastTitle} on ${dayLabel(lastStarted)}` : lastTitle}</span>
          {lastTime ? (lastFacts ? <span data-testid="prep-last-facts">{lastFacts}</span> : null) : lm && lm.item_count > 0 ? <span className="people-prep-token" data-testid="prep-meeting-items">{lm.item_count} {lm.item_count === 1 ? "ITEM" : "ITEMS"}</span> : null}
          {lm && lm.open_count > 0 ? <span className="people-prep-token" data-testid="prep-meeting-open-count">{lm.open_count} OPEN</span> : null}
          <Button dense variant="ghost" onClick={() => openSourceRef(`meeting:${lastId}`)} data-testid="prep-meeting-open">Open meeting</Button>
        </span>
      </header>
      {lastLines.length ? <ul className="people-rows">
        {lastLines.slice(0, 4).map((line) => <PlateRow key={line.key} title={line.text}
          meta={<><span className="people-state" data-tone={line.kind === "decision" ? "ok" : "info"}><span className="kit-dot" data-tone={line.kind === "decision" ? "ok" : "info"} aria-hidden="true" />{line.kind === "decision" ? "Decision" : "Action"}</span>{line.meta ? <span>{line.meta}</span> : null}</>} />)}
      </ul> : null}
      {lastLines.length > 4 ? <div className="people-row"><span className="people-row-meta">{`${lastLines.length - 4} more in the meeting`}</span></div> : null}
    </section> : null}

    {concernRows.length ? <section className="people-section" aria-label="Open work" data-testid="prep-summary-rows">
      <header className="people-section-head"><h3 className="people-section-cap">Open work</h3></header>
      <ul className="people-rows people-work-rows">{concernRows}</ul>
      {concern && brief ? <ConcernDetail concern={concern} brief={brief} /> : null}
    </section> : null}

    {excerpts.length ? <section className="people-section" aria-label="On the desk" data-testid="prep-memory">
      <header className="people-section-head"><h3 className="people-section-cap">On the desk</h3></header>
      <ul className="people-rows">
        {excerpts.slice(0, 4).map((e, index) => <PlateRow key={e.ref || `${e.kind}-${index}`} title={e.title || e.text}
          onTitle={e.ref ? () => openSourceRef(e.ref) : undefined}
          meta={<><span>{kindWord(e.kind)}</span>{e.title && e.text ? <span className="people-excerpt">{e.text}</span> : null}</>} />)}
      </ul>
    </section> : null}

    {(relationship.notes ?? []).length ? <section className="people-section people-notes" aria-label="Notes" data-testid="people-notes">
      <h3 className="people-section-cap">Notes</h3>
      <ul className="people-rows">{[...(relationship.notes ?? [])].sort((a, b) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? ""))).map((note) => <li key={note.id} className="people-note">
        {note.topic ? <strong>{note.topic}</strong> : null}<span className="people-context-note-body">{note.body}</span>
        <span className="people-row-meta">{[note.created_at ? dayLabel(note.created_at) : "", note.visibility === "leader_private" ? "Leader private" : "Shared"].filter(Boolean).join(" · ")}</span>
      </li>)}</ul>
    </section> : null}
    <div ref={composeRef} className="people-composer" data-testid="people-composer">
      <CycleGadget label="Add to this person" value={composeKind} onChange={setComposeKind} options={[
        { value: "agenda", label: "Agenda" }, { value: "note", label: "Note" },
        { value: "they", label: `${firstName} owes me` }, { value: "you", label: `I owe ${firstName}` },
      ]} />
      <PadGadget key={composeKind} micDraftScope={composeKind === "note" ? `people/context/${relationship.id}/body` : composeKind === "agenda" ? `people/1on1/${relationship.id}` : composeKind === "they" ? `people/owed/${relationship.id}` : `people/request/${relationship.id}`} label={composeKind === "note" ? "Note" : composeKind === "agenda" ? "Add to the agenda" : composeKind === "they" ? `${firstName} owes me` : `I owe ${firstName}`}
        value={composeKind === "note" ? noteDraft : composeKind === "agenda" ? agendaDraft : composeKind === "they" ? owedDraft : oweDraft}
        onChange={composeKind === "note" ? setNoteDraft : composeKind === "agenda" ? setAgendaDraft : composeKind === "they" ? setOwedDraft : setOweDraft} rows={2} autoGrow />
      <div className="people-composer-verbs">
        {composeKind === "note" ? <CycleGadget label="Visibility" value={visibility === "shared_intent" ? "shared_intent" : "leader_private"} onChange={setVisibility}
          options={[{ value: "leader_private", label: "Leader private" }, { value: "shared_intent", label: "Shared" }]} /> : null}
        <Button variant="secondary" loading={Boolean(busy) || owe?.phase === "creating" || owe?.phase === "accepting"}
          disabled={Boolean(busy) || Boolean(owe && owe.phase !== "saved") || !(composeKind === "note" ? noteDraft : composeKind === "agenda" ? agendaDraft : composeKind === "they" ? owedDraft : oweDraft).trim()}
          onClick={() => { if (composeKind === "note") addNote(); else if (composeKind === "agenda") addAgenda(); else if (composeKind === "they") addOwed(); else addOwe(); }}
          data-testid="people-composer-add">Add</Button>
      </div>
      {owe && owe.phase !== "creating" && owe.phase !== "accepting" ? <OweReceipt attempt={owe} onCheck={checkOwe} onAccept={acceptSavedOwe} onStartAnother={() => setOwe(null)} /> : null}
    </div>

  </div>
    {/* The window's status bar: the next 1:1, Encrypted, when it was prepared. */}
    <StatusBar
      data-testid="person-status"
      items={[
        nextAt ? { key: "next", lamp: until ? "ask" as const : "info" as const, text: [`1:1 ${lowerDay(oneOnOneWhen(nextAt))}`, until].filter(Boolean).join(" · ") } : null,
        { key: "lock", lamp: "ok" as const, text: <span className="people-lock" title="Encrypted · Local storage · Notes only" data-testid="person-lock">Encrypted</span> },
        { key: "receipt", text: recordingFailure ? recordingReceipt : <span className="people-prep-receipt" data-testid="prep-receipt">{`Prepared ${preparedAt}`}</span> },
      ]}
    />
  </>;
}
function LinkSuggestions({ relationship, prep, onLinked, onProtectedFailure, testId }: { relationship: RelationshipDetail; prep: PeoplePrepData; onLinked(): void; onProtectedFailure(cause: unknown): void; testId: string }) {
  const [busy, setBusy] = useState(false);
  const series = useMemo(() => {
    const seen = new Set<string>();
    return prep.calendarLinkSuggestions.filter((ev) => {
      const key = `${ev.uid}:${ev.source_id}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [prep.calendarLinkSuggestions]);
  if (!series.length) return null;
  const link = async (ev: PrepCalendarEvent) => {
    setBusy(true);
    try {
      await hub.linkSeries(relationship.id, ev.uid, ev.source_id, ev.title);
      onLinked();
    } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); }
  };
  return <div data-testid={testId}>
    <SurfaceSection label="Next 1:1">
      <SurfaceRows>{series.map((ev) => <SurfaceRow
        key={`${ev.uid}:${ev.source_id}`}
        title={ev.title}
        detail={[shortWhen(ev.starts_at), ev.source_label].filter(Boolean).join(" · ")}
        verbs={<Button dense variant="primary" loading={busy} disabled={busy} onClick={() => void link(ev)}>Link this 1:1</Button>}
      />)}</SurfaceRows>
    </SurfaceSection>
  </div>;
}
