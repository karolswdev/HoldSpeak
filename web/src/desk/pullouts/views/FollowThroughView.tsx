import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { refreshIntelligenceAttention } from "../../intelligenceAttention";
import { useOnDeskChanged } from "../../useDeskChangedRefresh";
import { openSurfaceOr } from "../../shell";
import { openSourceRef } from "../../surface/citations";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceSection, SurfaceState } from "../../surface/Surface";
import { ActionNotice, StateChip } from "../../surface";
import { GadgetGroup, GadgetRow, StringGadget } from "../../surface/gadgets";

type Lane = "now" | "waiting" | "unassigned" | "overdue";
type Provenance = {
  meeting_id: string | null;
  segment_text: string | null;
  segment_speaker: string | null;
  segment_start: number | null;
  moment?: { segment_index?: number | null } | null;
  available: boolean;
  source_ref?: string | null;
  thread_id?: string | null;
};
type FollowThroughCard = {
  id: string;
  text: string;
  owner: string | null;
  due: string | null;
  source: string;
  meeting_id?: string | null;
  decision_id?: string | null;
  target_ref?: string | null;
  open_ref?: string | null;
  source_ref?: string | null;
  provenance: Provenance | null;
  person_label?: string;
  person_relationship_id?: string;
  delegated_at?: string | null;
  created_at?: string | null;
  snoozed_until?: string | null;
  deferred_until?: string | null;
};
type FollowThroughBoard = Record<Lane, FollowThroughCard[]>;
type Draft = { owner: string; due: string; ownerDirty: boolean; dueDirty: boolean };
type DoneReceipt = { cardId: string; label: string; createdAt: number };
type WriteRequest = {
  cardId: string;
  label: string;
  verb: string;
  path: string;
  json?: Record<string, unknown>;
  result: string;
  done?: boolean;
  reopen?: boolean;
  field?: "owner" | "due";
  value?: string;
};

const LANES: ReadonlyArray<{ id: Lane; label: string }> = [
  { id: "overdue", label: "Overdue" },
  { id: "unassigned", label: "To review" },
  { id: "now", label: "Due soon" },
  { id: "waiting", label: "Later" },
];
const WRITE_LABELS: Record<string, string> = { done: "Done", dismiss: "Dismiss", snooze: "Tomorrow", delegate: "Assign", due: "Save date", reopen: "Undo", close: "Close", kill: "Stop" };
const DONE_RECEIPT_KEY = "hs.follow-through.done-receipt";
const DONE_RECEIPT_WINDOW_MS = 8_000;

function forgetDoneReceipt() {
  try { window.localStorage.removeItem(DONE_RECEIPT_KEY); } catch { /* Storage is optional. */ }
}
function readDoneReceipt(): DoneReceipt | null {
  if (typeof window === "undefined") return null;
  try {
    const parsed = JSON.parse(window.localStorage.getItem(DONE_RECEIPT_KEY) || "null") as Partial<DoneReceipt> | null;
    // People text and opaque People identities belong only to the encrypted
    // authority. Discard receipts persisted by the old face before rendering.
    if (parsed?.cardId?.startsWith("people:")) { forgetDoneReceipt(); return null; }
    if (!parsed || typeof parsed.cardId !== "string" || typeof parsed.label !== "string" || typeof parsed.createdAt !== "number") return null;
    if (Date.now() - parsed.createdAt >= DONE_RECEIPT_WINDOW_MS) { forgetDoneReceipt(); return null; }
    return { cardId: parsed.cardId, label: parsed.label, createdAt: parsed.createdAt };
  } catch { return null; }
}
function dayText(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}
function tomorrow(): string {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return dayText(date);
}
/** The due as a YYYY-MM-DD day for the date field; words give "". */
function isoDay(due: string | null | undefined): string {
  return due && /^\d{4}-\d{2}-\d{2}/.test(due) ? due.slice(0, 10) : "";
}
/** Betterment D1: the due shows once, as a date ("Tue 20 Oct"), never cut.
 *  Words that name no day show as they were said. */
function dueLabel(due: string | null): { label: string; overdue: boolean; day: string | null } {
  if (!due) return { label: "No date", overdue: false, day: null };
  const day = /^\d{4}-\d{2}-\d{2}/.test(due) ? due.slice(0, 10) : null;
  const dueAt = day ? new Date(`${day}T00:00:00`) : null;
  if (!dueAt || !Number.isFinite(dueAt.getTime())) return { label: due, overdue: false, day: null };
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const label = dueAt.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
  return { label, overdue: dueAt.getTime() < today.getTime(), day };
}
function ageLabel(card: FollowThroughCard): string | null {
  const timestamp = card.delegated_at || card.created_at;
  if (!timestamp) return null;
  const days = Math.floor((Date.now() - new Date(timestamp).getTime()) / 86_400_000);
  if (!Number.isFinite(days) || days < 1) return null;
  return `${card.delegated_at ? "Assigned" : "Added"} ${days} ${days === 1 ? "day" : "days"} ago`;
}
function sourceFor(card: FollowThroughCard): { ref: string; label: string; kind: string; people?: boolean } | null {
  if (card.source === "people_commitment") return /^people:.+/.test(card.target_ref ?? "")
    ? { ref: card.target_ref!, label: "Open People", kind: "people", people: true } : null;
  const refs = [card.open_ref, card.provenance?.source_ref, card.source_ref];
  // Betterment D1: an action item opens where it was said (its meeting), not
  // the decision record its Keep linked it to.
  const action = card.source === "action_item";
  const ref = refs.find((value) => (action ? /^(note|thread|meeting):.+/ : /^(note|thread|meeting|decision):.+/)
    .test(value ?? ""));
  if (ref) {
    const kind = ref.split(":")[0];
    return { ref, label: `Open ${kind}`, kind };
  }
  const meetingId = card.provenance?.meeting_id || card.meeting_id;
  if (card.decision_id && !(action && meetingId)) {
    return { ref: `decision:${card.decision_id}`, label: "Open decision", kind: "decision" };
  }
  if (!meetingId) return null;
  const index = card.provenance?.moment?.segment_index;
  const segment = Number.isInteger(index) ? `?view=review&segment=${index}` : "?view=review";
  return { ref: `meeting:${meetingId}${segment}`, label: "Open meeting", kind: "meeting" };
}
function draftFor(card: FollowThroughCard): Draft {
  return { owner: card.owner ?? "", due: isoDay(card.due), ownerDirty: false, dueDirty: false };
}

/** Existing board authorities, expressed as readable task rows and in-place controls. */
export function FollowThroughView({ overdueOnly = false, focusCardId, onClearFilter }: {
  overdueOnly?: boolean;
  focusCardId?: string;
  onOpenReceipts?: (receiptId: string) => void;
  onClearFilter?: () => void;
}) {
  const [board, setBoard] = useState<FollowThroughBoard | null>(null);
  const [loading, setLoading] = useState(true);
  const [readError, setReadError] = useState<{ message: string; focusId: string | null } | null>(null);
  const [boardFocusId, setBoardFocusId] = useState<string | undefined>();
  const [writeError, setWriteError] = useState<{ request: WriteRequest; message: string } | null>(null);
  const writeNoticeRef = useRef<HTMLDivElement>(null);
  const [pending, setPending] = useState<WriteRequest | null>(null);
  const pendingRef = useRef<WriteRequest | null>(null);
  const [outcome, setOutcome] = useState<{ text: string; label: string } | null>(null);
  const [openCardId, setOpenCardId] = useState<string | null>(null);
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const focusPending = useRef(focusCardId);
  const currentFocusId = useRef(focusCardId);
  currentFocusId.current = focusCardId;
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const draftsRef = useRef(drafts);
  const [doneReceipt, setDoneReceipt] = useState<DoneReceipt | null>(readDoneReceipt);
  const reads = useRef(0);
  const reload = useCallback(async (targetId: string | null = focusCardId ?? null) => {
    const order = ++reads.current;
    setLoading(true);
    try {
      const path = `/api/follow-through/board${targetId ? `?focus_id=${encodeURIComponent(targetId)}` : ""}`;
      const next = await apiFetch<FollowThroughBoard>(path);
      if (order !== reads.current) return;
      setBoard(next);
      setBoardFocusId(targetId ?? undefined);
      setReadError(null);
      // A refresh updates untouched fields, never the owner's draft. Keep
      // drafts above lane rows so moving a task to another lane loses nothing.
      const updated = { ...draftsRef.current };
      for (const lane of LANES) for (const card of next[lane.id]) {
        const prior = updated[card.id];
        if (prior) updated[card.id] = {
          ...prior,
          owner: prior.ownerDirty ? prior.owner : card.owner ?? "",
          due: prior.dueDirty ? prior.due : isoDay(card.due),
        };
      }
      draftsRef.current = updated;
      setDrafts(updated);
    } catch (cause) {
      if (order === reads.current) setReadError({ message: readableError(cause), focusId: targetId });
    } finally {
      if (order === reads.current) setLoading(false);
    }
  }, [focusCardId]);
  useOnDeskChanged(() => { void reload(); });
  useEffect(() => { void reload(); }, [reload]);
  useEffect(() => {
    if (writeError) writeNoticeRef.current?.scrollIntoView?.({ block: "nearest" });
  }, [writeError]);
  useEffect(() => {
    focusPending.current = focusCardId;
    setSelectedCardId(null);
  }, [focusCardId]);
  useEffect(() => {
    const target = focusPending.current;
    if (!target || !board || boardFocusId !== focusCardId || !LANES.some((lane) => board[lane.id].some((card) => card.id === target))) return;
    setOpenCardId(target);
    setSelectedCardId(target);
    focusPending.current = undefined;
  }, [board, boardFocusId, focusCardId]);
  useEffect(() => {
    if (!doneReceipt) return;
    const timer = window.setTimeout(() => {
      setDoneReceipt((current) => current === doneReceipt ? null : current);
      const persisted = readDoneReceipt();
      if (persisted?.cardId === doneReceipt.cardId && persisted.createdAt === doneReceipt.createdAt) forgetDoneReceipt();
    }, Math.max(0, DONE_RECEIPT_WINDOW_MS - (Date.now() - doneReceipt.createdAt)));
    return () => window.clearTimeout(timer);
  }, [doneReceipt]);

  const edit = (card: FollowThroughCard, field: "owner" | "due", value: string) => {
    const current = draftsRef.current[card.id] ?? draftFor(card);
    const next = { ...draftsRef.current, [card.id]: { ...current, [field]: value, [`${field}Dirty`]: true } };
    draftsRef.current = next;
    setDrafts(next);
  };
  const submit = async (request: WriteRequest) => {
    // The ref closes the same-event gap before React paints disabled controls.
    if (pendingRef.current) return;
    pendingRef.current = request;
    setPending(request);
    setWriteError(null);
    setOutcome(null);
    try {
      await apiFetch(request.path, { method: "POST", ...(request.json ? { json: request.json } : {}) });
      if (request.done) {
        const receipt = { cardId: request.cardId, label: request.label, createdAt: Date.now() };
        if (request.cardId.startsWith("people:")) forgetDoneReceipt();
        else {
          try { window.localStorage.setItem(DONE_RECEIPT_KEY, JSON.stringify(receipt)); } catch { /* Memory receipt remains usable. */ }
        }
        setDoneReceipt(receipt);
      } else if (request.reopen) {
        forgetDoneReceipt();
        setDoneReceipt(null);
      }
      if (request.field) {
        const current = draftsRef.current[request.cardId];
        if (current && current[request.field] === request.value) {
          const next = { ...draftsRef.current, [request.cardId]: { ...current, [`${request.field}Dirty`]: false } };
          draftsRef.current = next;
          setDrafts(next);
        }
      }
      if (!request.done) setOutcome({ text: request.result, label: request.label });
      // The write owns its original card/payload, but its follow-up read
      // belongs to the subject the owner is inspecting when it lands.
      await reload(currentFocusId.current ?? null);
      refreshIntelligenceAttention();
    } catch (cause) {
      setWriteError({ request, message: readableError(cause) });
    } finally {
      pendingRef.current = null;
      setPending(null);
    }
  };
  const action = (card: FollowThroughCard, verb: string, payload: Record<string, string> = {}) => {
    const result = verb === "delegate" ? `Assigned to ${payload.to}` : verb === "due" ? `Date saved: ${payload.due_at}`
      : verb === "snooze" ? `Until ${payload.until}` : verb === "dismiss" ? "Dismissed" : verb === "reopen" ? "Reopened" : "Done";
    void submit({ cardId: card.id, label: card.text, verb, path: "/api/follow-through/complete",
      json: { card_id: card.id, verb, payload }, result, done: verb === "done", reopen: verb === "reopen",
      ...(verb === "delegate" ? { field: "owner" as const, value: payload.to } : verb === "due" ? { field: "due" as const, value: payload.due_at } : {}),
    });
  };
  const cadence = (card: FollowThroughCard, verb: "close" | "kill" | "snooze") => {
    const until = tomorrow();
    void submit({ cardId: card.id, label: card.text, verb,
      path: `/api/cadence/loops/${encodeURIComponent(card.id)}/${verb}`,
      ...(verb === "snooze" ? { json: { until } } : {}),
      result: verb === "close" ? "Closed" : verb === "kill" ? "Stopped" : `Until ${until}`,
    });
  };
  const doneReceiptNode = doneReceipt ? (
    <div className="follow-through-done-receipt" role="status" data-testid="follow-through-done-receipt">
      <StateChip state="success" label="Done" />
      <span>{doneReceipt.label}</span>
      <Button dense variant="ghost" disabled={!!pending} onClick={() => void submit({
        cardId: doneReceipt.cardId, label: doneReceipt.label, verb: "reopen", path: "/api/follow-through/complete",
        json: { card_id: doneReceipt.cardId, verb: "reopen", payload: {} }, result: "Reopened", reopen: true,
      })}>Undo</Button>
    </div>
  ) : null;
  const shownCards = (lane: Lane) => (board?.[lane] ?? []).filter((card) => !overdueOnly || lane === "overdue" || card.id === focusCardId);
  const visibleLanes = LANES.filter((lane) => shownCards(lane.id).length > 0);
  const boardTotal = board ? LANES.reduce((count, lane) => count + board[lane.id].length, 0) : 0;
  const focusMissing = !!focusCardId && !!board && boardFocusId === focusCardId && !loading && !readError
    && !LANES.some((lane) => board[lane.id].some((card) => card.id === focusCardId));

  return (
    <div className="follow-through-view">
      {doneReceiptNode}
      {pending ? <ActionNotice><StateChip state="working" label={`${WRITE_LABELS[pending.verb]} pending`} /><span>{pending.label}</span></ActionNotice> : null}
      {outcome ? <ActionNotice tone="ok"><StateChip state="success" label={outcome.text} wrap /><span>{outcome.label}</span></ActionNotice> : null}
      {writeError ? (
        <div ref={writeNoticeRef}>
          <ActionNotice role="alert" tone="danger" action={{ label: "Retry", onClick: () => void submit(writeError.request) }}>
            <StateChip state="failure" label={`${WRITE_LABELS[writeError.request.verb]} failed`} />
            <span>{writeError.request.label}</span>
            <span>{writeError.message}</span>
          </ActionNotice>
        </div>
      ) : null}
      {readError ? <ActionNotice role="alert" tone="danger" action={{ label: "Retry read", onClick: () => void reload(readError.focusId) }}><StateChip state="failure" label="Read failed" /><span>{readError.message}</span></ActionNotice> : null}
      {focusMissing ? <ActionNotice role="alert" tone="danger" action={{ label: "Retry read", onClick: () => void reload(focusCardId) }}><StateChip state="unreachable" label="Task unavailable" /></ActionNotice> : null}
      {loading && !board ? <SurfaceState loading /> : !board ? null : !boardTotal ? <SurfaceState empty emptyLabel="No follow-through yet" /> : !visibleLanes.length ? (
        <SurfaceState empty emptyLabel="No overdue follow-through. Other lanes hold work." onAction={onClearFilter} actionLabel="Show all lanes" />
      ) : visibleLanes.map((lane) => (
        <SurfaceSection key={lane.id} label={lane.label} count={shownCards(lane.id).length} className="follow-through-lane">
          <SurfaceLedger cols="follow-through">
            {shownCards(lane.id).map((card) => {
              const source = sourceFor(card);
              const due = dueLabel(card.due);
              const draft = drafts[card.id] ?? draftFor(card);
              const people = card.source === "people_commitment";
              const loop = card.source === "decision" || card.source === "cadence_loop";
              const open = openCardId === card.id;
              const age = ageLabel(card);
              return (
                <SurfaceLedgerRow key={card.id} wrap open={open} selected={selectedCardId === card.id}
                  onToggle={() => setOpenCardId(open ? null : card.id)}
                  lineLabel={`${card.text}. ${source?.kind ?? "source unavailable"} follow-through.`}
                  primary={<span className="follow-through-identity"><strong>{card.text}</strong>
                    <span className="follow-through-owner" data-testid={card.person_label ? "follow-through-person-chip" : undefined}>{card.person_label || card.owner || "No owner"}</span>
                    {age ? <span className="follow-through-staleness" data-testid="follow-through-staleness">{age}</span> : null}
                  </span>}
                  cells={<span className="follow-through-facts">{due.day
                    ? <time dateTime={due.day}><StateChip state={due.overdue ? "warning" : "idle"} label={due.label} wrap /></time>
                    : <StateChip state="idle" label={due.label} wrap />}
                    {card.snoozed_until ? <StateChip state="idle" label={`Snoozed until ${card.snoozed_until.slice(0, 10)}`} wrap /> : null}
                    {card.deferred_until ? <StateChip state="idle" label={`Deferred until ${card.deferred_until.slice(0, 10)}`} wrap /> : null}
                    {!source ? <span>Source unavailable</span> : null}
                  </span>}
                  trailing={<>
                    {source ? <Button dense variant="ghost" aria-label={`${source.label} for ${card.text}`} onClick={() => {
                      if (source.people) openSurfaceOr("open-people", "/", source.ref);
                      else openSourceRef(source.ref);
                    }}>{source.label}</Button> : null}
                    <Button dense disabled={!!pending} aria-label={loop ? "Close loop" : "Mark done"}
                      onClick={() => loop ? cadence(card, "close") : action(card, "done")}>{loop ? "Close" : "Done"}</Button>
                    <Button dense variant="ghost" aria-label={`Details for ${card.text}`} aria-expanded={open}
                      onClick={() => setOpenCardId(open ? null : card.id)}>Details</Button>
                  </>}
                >
                  <div className="follow-through-expanded" aria-label={`Verbs for ${card.text}`}>
                    <GadgetGroup material="inset" label="Manage" actions={<>
                      {!people ? <Button dense disabled={!!pending} onClick={() => loop ? cadence(card, "snooze") : action(card, "snooze", { until: tomorrow() })}>Tomorrow</Button> : null}
                      <Button dense variant="ghost" disabled={!!pending} onClick={() => loop ? cadence(card, "kill") : action(card, "dismiss")}>{loop ? "Stop" : "Dismiss"}</Button>
                      <Button dense variant="ghost" onClick={() => setOpenCardId(null)}>Cancel</Button>
                    </>}>
                      {!people && !loop ? <>
                        <GadgetRow label="Owner" controlWidth="full"><StringGadget label="Owner" value={draft.owner} onChange={(value) => edit(card, "owner", value)} placeholder="Name" />
                          <Button dense disabled={!!pending || !draft.owner.trim()} onClick={() => action(card, "delegate", { to: draft.owner.trim() })}>Assign</Button>
                        </GadgetRow>
                        <GadgetRow label="Due date" controlWidth="full"><StringGadget label="Due date" inputProps={{ inputMode: "numeric" }} value={draft.due} onChange={(value) => edit(card, "due", value)} placeholder="YYYY-MM-DD" />
                          <Button dense disabled={!!pending || !draft.due} onClick={() => action(card, "due", { due_at: draft.due })}>Save date</Button>
                        </GadgetRow>
                      </> : null}
                      {card.provenance?.segment_text ? <blockquote className="follow-through-provenance">
                        {card.provenance.segment_speaker ? <cite>{card.provenance.segment_speaker}</cite> : null}
                        <span>{card.provenance.segment_text}</span>
                      </blockquote> : null}
                    </GadgetGroup>
                  </div>
                </SurfaceLedgerRow>
              );
            })}
          </SurfaceLedger>
        </SurfaceSection>
      ))}
    </div>
  );
}
