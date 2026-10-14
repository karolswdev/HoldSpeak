import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { refreshIntelligenceAttention } from "../../intelligenceAttention";
import { useOnDeskChanged } from "../../useDeskChangedRefresh";
import { openSurfaceOr } from "../../shell";
import { openSourceRef } from "../../surface/citations";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
} from "../../surface/Surface";
import { StringGadget } from "../../surface/gadgets";
import { countToken } from "../../surface/count";

type FollowThroughVerb = "done" | "dismiss" | "snooze" | "delegate" | "reopen";
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
  decision_id?: string | null;
  /** Opaque People relationship ref supplied only by the Follow-through API. */
  target_ref?: string | null;
  /** Source object ref for action items filed from a Desk note. */
  open_ref?: string | null;
  source_ref?: string | null;
  provenance: Provenance | null;
  /** HS-150-07: person projection for mapped owner strings (route-adapter enrichment). */
  person_label?: string;
  person_relationship_id?: string;
  delegated_at?: string | null;
  created_at?: string | null;
};

type FollowThroughBoard = Record<Lane, FollowThroughCard[]>;

const LANES: ReadonlyArray<{ id: Lane; label: string }> = [
  { id: "now", label: "Now" },
  { id: "waiting", label: "Waiting" },
  // Inventory gap 11 (2026-10-03): this lane holds the items with no owner
  // AND the items not reviewed yet (those can have an owner). One true name.
  { id: "unassigned", label: "To review" },
  { id: "overdue", label: "Overdue" },
];

function initials(owner: string | null): string {
  if (!owner?.trim()) return "—";
  return owner
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function dueLabel(due: string | null): string {
  if (!due) return "—";
  const dueAt = new Date(`${due.slice(0, 10)}T00:00:00`);
  if (Number.isNaN(dueAt.getTime())) return due;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.round((dueAt.getTime() - today.getTime()) / 86_400_000);
  if (days === 0) return "today";
  if (days < 0) return `overdue ${Math.abs(days)}d`;
  return `${days}d`;
}

function isOverdue(due: string | null): boolean {
  return dueLabel(due).startsWith("overdue");
}

const GLYPH_PEOPLE = String.fromCodePoint(0x2667);
function sourceFor(card: FollowThroughCard): { glyph: string; label: string } {
  const refs = [card.open_ref, card.provenance?.source_ref, card.source_ref];
  if (refs.some((ref) => ref?.startsWith("note:"))) {
    return { glyph: "○", label: "note" };
  }
  if (refs.some((ref) => ref?.startsWith("thread:"))) {
    return { glyph: "⌁", label: "thread" };
  }
  if (card.source === "people_commitment") return { glyph: GLYPH_PEOPLE, label: "people" };
  if (card.source === "decision" || card.decision_id) return { glyph: "◇", label: "decision" };
  return { glyph: "⌁", label: "meeting" };
}

function verifiedSourceRef(card: FollowThroughCard): string | null {
  const refs = [card.open_ref, card.provenance?.source_ref, card.source_ref];
  const source = refs.find((ref) => /^(note|thread|meeting):/.test(ref ?? ""));
  if (source) return source;
  // A decision id names the decision row. It is not a meeting id, so never
  // send it through the meeting-records route.
  if (card.decision_id) return `decision:${card.decision_id}`;
  const meetingId = card.provenance?.meeting_id;
  if (!meetingId) return null;
  const segmentIndex = card.provenance?.moment?.segment_index;
  const segment = Number.isInteger(segmentIndex) ? `?view=review&segment=${segmentIndex}` : "?view=review";
  return `meeting:${meetingId}${segment}`;
}

type DoneReceipt = { cardId: string; label: string; createdAt: number };
const DONE_RECEIPT_KEY = "hs.follow-through.done-receipt";
const DONE_RECEIPT_WINDOW_MS = 8_000;

function readDoneReceipt(): DoneReceipt | null {
  if (typeof window === "undefined") return null;
  try {
    const parsed = JSON.parse(window.localStorage.getItem(DONE_RECEIPT_KEY) || "null") as Partial<DoneReceipt> | null;
    if (!parsed || typeof parsed.cardId !== "string" || typeof parsed.label !== "string" || typeof parsed.createdAt !== "number") return null;
    if (Date.now() - parsed.createdAt >= DONE_RECEIPT_WINDOW_MS) {
      window.localStorage.removeItem(DONE_RECEIPT_KEY);
      return null;
    }
    return { cardId: parsed.cardId, label: parsed.label, createdAt: parsed.createdAt };
  } catch {
    return null;
  }
}

/** HS-150-07: staleness from delegated_at ?? created_at (same logic as DoorBoardLane). */
function stalenessLabel(card: FollowThroughCard): string | null {
  const ts = card.delegated_at || card.created_at;
  if (!ts) return null;
  const then = new Date(ts).getTime();
  if (!Number.isFinite(then)) return null;
  const days = Math.max(0, Math.floor((Date.now() - then) / 86_400_000));
  return `waiting ${days}d`;
}

function tomorrow(): string {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return date.toISOString().slice(0, 10);
}

/** Execution lanes rendered directly from FollowThroughService's board read model. */
export function FollowThroughView({
  overdueOnly = false,
  focusCardId,
  onOpenReceipts,
  onClearFilter,
}: {
  overdueOnly?: boolean;
  focusCardId?: string;
  onOpenReceipts?: (receiptId: string) => void;
  onClearFilter?: () => void;
}) {
  const [board, setBoard] = useState<FollowThroughBoard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openCardId, setOpenCardId] = useState<string | null>(null);
  const [delegatingCardId, setDelegatingCardId] = useState<string | null>(null);
  const [delegateTo, setDelegateTo] = useState("");
  const [busyCardId, setBusyCardId] = useState<string | null>(null);
  const [doneReceipt, setDoneReceipt] = useState<DoneReceipt | null>(readDoneReceipt);

  const reads = useRef({ started: 0, landed: 0 });
  const reload = useCallback(async (quiet = false) => {
    if (!quiet) {
      setLoading(true);
      setError("");
    }
    const order = ++reads.current.started;
    try {
      const next = await apiFetch<FollowThroughBoard>("/api/follow-through/board");
      // A read that started earlier and answers later never replaces a newer one.
      if (order < reads.current.landed) return;
      reads.current.landed = order;
      setBoard(next);
    } catch (cause) {
      // A quiet re-read (the bus) that fails keeps the last board.
      if (!quiet) setError(readableError(cause));
    } finally {
      if (!quiet) setLoading(false);
    }
  }, []);
  // A write in another window (an action item done, a decision) moves this board.
  useOnDeskChanged(() => { void reload(true); });

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    if (focusCardId) setOpenCardId(focusCardId);
  }, [focusCardId]);

  useEffect(() => {
    if (!doneReceipt) return undefined;
    const remaining = Math.max(0, DONE_RECEIPT_WINDOW_MS - (Date.now() - doneReceipt.createdAt));
    const timer = window.setTimeout(() => {
      setDoneReceipt((current) => current?.createdAt === doneReceipt.createdAt ? null : current);
      if (readDoneReceipt()?.createdAt === doneReceipt.createdAt) window.localStorage.removeItem(DONE_RECEIPT_KEY);
    }, remaining);
    return () => window.clearTimeout(timer);
  }, [doneReceipt]);

  const complete = async (
    cardId: string,
    verb: FollowThroughVerb,
    payload: Record<string, string> = {},
    label = "",
  ) => {
    setBusyCardId(cardId);
    setError("");
    try {
      await apiFetch("/api/follow-through/complete", {
        method: "POST",
        json: { card_id: cardId, verb, payload },
      });
      if (verb === "done") {
        const receipt = { cardId, label: label || "follow-through", createdAt: Date.now() };
        window.localStorage.setItem(DONE_RECEIPT_KEY, JSON.stringify(receipt));
        setDoneReceipt(receipt);
      } else if (verb === "reopen" && doneReceipt?.cardId === cardId) {
        window.localStorage.removeItem(DONE_RECEIPT_KEY);
        setDoneReceipt(null);
      }
      setDelegatingCardId(null);
      setDelegateTo("");
      await reload();
      refreshIntelligenceAttention();
    } catch (cause) {
      setError(readableError(cause));
    } finally {
      setBusyCardId(null);
    }
  };

  const openDecision = (card: FollowThroughCard) => {
    if (card.source === "people_commitment") {
      openSurfaceOr("open-people", "/", card.target_ref ?? undefined);
      return;
    }
    const sourceRef = verifiedSourceRef(card);
    if (!sourceRef) {
      setError("No source recorded for this follow-through.");
      return;
    }
    openSourceRef(sourceRef);
  };

  const doneReceiptNode = doneReceipt ? (
    <div className="follow-through-done-receipt" role="status" data-testid="follow-through-done-receipt">
      <span>Done: {doneReceipt.label}</span>
      <Button
        dense
        variant="ghost"
        disabled={busyCardId === doneReceipt.cardId}
        onClick={() => void complete(doneReceipt.cardId, "reopen")}
      >Undo</Button>
    </div>
  ) : null;

  if (loading) return <>{doneReceiptNode}<SurfaceState loading /></>;
  if (error && !board) return <>{doneReceiptNode}<SurfaceState error={error} onRetry={() => void reload()} /></>;
  if (!board) return null;

  const visibleLanes = overdueOnly ? LANES.filter((lane) => lane.id === "overdue") : LANES;
  // HS-132-08 — the board's emptiness is a fact about the BOARD, never about
  // the current filter. Counting only the visible lanes let a dispatched
  // overdue filter print a clear board while real commitments stood open.
  const boardTotal = LANES.reduce((count, lane) => count + board[lane.id].length, 0);
  const visibleTotal = visibleLanes.reduce((count, lane) => count + board[lane.id].length, 0);
  if (!boardTotal) {
    return <>{doneReceiptNode}<SurfaceState empty emptyLabel="No follow-through yet" /></>;
  }
  if (!visibleTotal) {
    return (
      <>{doneReceiptNode}<SurfaceState
          empty
          emptyLabel="No overdue follow-through. Other lanes hold work."
          onAction={onClearFilter}
          actionLabel="Show all lanes"
        /></>
    );
  }

  return (
    <div className="follow-through-view">
      {doneReceiptNode}
      {error ? <SurfaceState error={error} onRetry={() => void reload()} /> : null}
      {visibleLanes.map((lane) => {
        const cards = board[lane.id];
        return (
          <SurfaceSection
            key={lane.id}
            label={lane.label}
            actions={cards.length > 0 ? <span className="follow-through-count">{cards.length}</span> : undefined}
            className={`follow-through-lane${lane.id === "overdue" ? " is-overdue" : ""}`}
          >
            {cards.length ? (
              <SurfaceLedger count={
                  /* A lane name is a state, not a counted noun: `3 NOW`,
                     never `3 NOWS` (inventory 2026-10-03). */
                  countToken(cards.length, lane.label.toUpperCase(), lane.label.toUpperCase()) ?? lane.label.toUpperCase()
                } cols="follow-through">
                {cards.map((card) => {
                  const open = openCardId === card.id;
                  const source = sourceFor(card);
                  const sourceAction = source.label === "note"
                    ? "Open source note"
                    : source.label === "thread"
                      ? "Open source thread"
                      : source.label === "people"
                        ? "Open People"
                        : source.label === "decision"
                          ? "Open decision"
                          : "Open meeting";
                  const overdue = isOverdue(card.due);
                  const peopleCommitment = card.source === "people_commitment";
                  return (
                    <SurfaceLedgerRow
                      key={card.id}
                      primary={card.text}
                      open={open}
                      onToggle={() => setOpenCardId(open ? null : card.id)}
                      lineLabel={`${card.text}. ${source.label} follow-through.`}
                      cells={
                        <>
                          {card.person_label ? (
                            <span className="follow-through-owner follow-through-person-chip" title={card.owner ?? "Unassigned"} data-testid="follow-through-person-chip">
                              {card.person_label}
                              {stalenessLabel(card) ? <span className="follow-through-staleness" data-testid="follow-through-staleness">{stalenessLabel(card)}</span> : null}
                            </span>
                          ) : (
                            <span className="follow-through-owner" title={card.owner ?? "Unassigned"}>
                              {initials(card.owner)}
                            </span>
                          )}
                          <span
                            className="follow-through-due"
                            data-overdue={overdue || undefined}
                          >
                            {dueLabel(card.due)}
                          </span>
                          <Button
                            dense
                            variant="ghost"
                            className="follow-through-source"
                            title={sourceAction}
                            aria-label={`${sourceAction} for ${card.text}`}
                            onClick={(event) => {
                              event.stopPropagation();
                              openDecision(card);
                            }}
                          >
                            {source.glyph}
                          </Button>
                        </>
                      }
                    >
                      <div className="follow-through-expanded">
                        <div className="follow-through-verbs" aria-label={`Verbs for ${card.text}`}>
                          {/* PHILO-15 08 (B03): every verb says its word (UX-CANON: no glyph-only controls). */}
                          <Button dense variant="ghost" disabled={busyCardId === card.id} onClick={() => void complete(card.id, "done", {}, card.text)} aria-label="Mark done">Done</Button>
                          <Button dense variant="ghost" disabled={busyCardId === card.id} onClick={() => void complete(card.id, "dismiss")} aria-label="Dismiss">Dismiss</Button>
                          {!peopleCommitment ? <Button dense variant="ghost" disabled={busyCardId === card.id} onClick={() => void complete(card.id, "snooze", { until: tomorrow() })} aria-label="Snooze until tomorrow">Snooze</Button> : null}
                          {!peopleCommitment ? <Button dense variant="ghost" disabled={busyCardId === card.id} onClick={() => setDelegatingCardId(delegatingCardId === card.id ? null : card.id)} aria-label="Delegate">Delegate</Button> : null}
                        </div>
                        {delegatingCardId === card.id ? (
                          <div className="follow-through-delegate">
                            <StringGadget label={`Delegate ${card.text} to`} value={delegateTo} onChange={setDelegateTo} placeholder="OWNER" />
                            <Button dense disabled={!delegateTo.trim() || busyCardId === card.id} onClick={() => void complete(card.id, "delegate", { to: delegateTo.trim() })}>Assign</Button>
                          </div>
                        ) : null}
                        {card.provenance?.available ? (() => {
                          const speaker = card.provenance.segment_speaker;
                          const segText = card.provenance.segment_text;
                          return (
                          <blockquote className="follow-through-provenance">
                            {speaker ? <cite>{speaker}</cite> : null}
                            <span>{segText ?? "Source moment unavailable"}</span>
                          </blockquote>
                          );
                        })() : card.provenance?.meeting_id ? (
                          // PHILO-15 08: the meeting is there, only the moment
                          // is not pinned: its transcript is one press away.
                          <div className="follow-through-provenance">
                            <Button dense variant="ghost" aria-label={`Open transcript: ${card.text}`}
                              data-testid="follow-through-open-transcript"
                              onClick={() => openSourceRef(`meeting:${card.provenance?.meeting_id}`)}>Open transcript</Button>
                          </div>
                        ) : (
                          <div className="follow-through-provenance is-unavailable">SOURCE MOMENT UNAVAILABLE</div>
                        )}
                      </div>
                    </SurfaceLedgerRow>
                  );
                })}
              </SurfaceLedger>
            ) : (
              <div className="follow-through-lane-empty">No items</div>
            )}
          </SurfaceSection>
        );
      })}
    </div>
  );
}
