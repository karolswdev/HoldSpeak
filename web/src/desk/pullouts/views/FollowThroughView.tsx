import { useCallback, useEffect, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { refreshIntelligenceAttention } from "../../intelligenceAttention";
import { openSurfaceOr } from "../../shell";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
} from "../../surface/Surface";
import { StringGadget } from "../../surface/gadgets";

type FollowThroughVerb = "done" | "dismiss" | "snooze" | "delegate" | "reopen";
type Lane = "now" | "waiting" | "unassigned" | "overdue";

type Provenance = {
  meeting_id: string | null;
  segment_text: string | null;
  segment_speaker: string | null;
  segment_start: number | null;
  available: boolean;
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
  provenance: Provenance | null;
};

type FollowThroughBoard = Record<Lane, FollowThroughCard[]>;

const LANES: ReadonlyArray<{ id: Lane; label: string }> = [
  { id: "now", label: "Now" },
  { id: "waiting", label: "Waiting" },
  { id: "unassigned", label: "Unassigned" },
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

function sourceFor(card: FollowThroughCard): { glyph: string; label: string } {
  if (card.source === "people_commitment") return { glyph: "♧", label: "people" };
  if (card.source === "decision") return { glyph: "◇", label: "decision" };
  return { glyph: "⌁", label: "meeting" };
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

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setBoard(await apiFetch<FollowThroughBoard>("/api/follow-through/board"));
    } catch (cause) {
      setError(readableError(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    if (focusCardId) setOpenCardId(focusCardId);
  }, [focusCardId]);

  const complete = async (
    cardId: string,
    verb: FollowThroughVerb,
    payload: Record<string, string> = {},
  ) => {
    setBusyCardId(cardId);
    setError("");
    try {
      await apiFetch("/api/follow-through/complete", {
        method: "POST",
        json: { card_id: cardId, verb, payload },
      });
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
    if (!card.decision_id) {
      setError("No decision recorded for this follow-through.");
      return;
    }
    void apiFetch<Array<{ id: string }>>(
      `/api/decision-records/source/meeting/${encodeURIComponent(card.decision_id)}`,
    ).then((receipts) => {
      if (receipts[0]) onOpenReceipts?.(receipts[0].id);
      else setError("No decision recorded for this follow-through.");
    }).catch((cause) => setError(readableError(cause)));
  };

  if (loading) return <SurfaceState loading />;
  if (error && !board) return <SurfaceState error={error} onRetry={() => void reload()} />;
  if (!board) return null;

  const visibleLanes = overdueOnly ? LANES.filter((lane) => lane.id === "overdue") : LANES;
  // HS-132-08 — the board's emptiness is a fact about the BOARD, never about
  // the current filter. Counting only the visible lanes let a dispatched
  // overdue filter print a clear board while real commitments stood open.
  const boardTotal = LANES.reduce((count, lane) => count + board[lane.id].length, 0);
  const visibleTotal = visibleLanes.reduce((count, lane) => count + board[lane.id].length, 0);
  if (!boardTotal) {
    return <SurfaceState empty emptyLabel="No follow-through yet" />;
  }
  if (!visibleTotal) {
    return (
      <SurfaceState
        empty
        emptyLabel="No overdue follow-through. Other lanes hold work."
        onAction={onClearFilter}
        actionLabel="Show all lanes"
      />
    );
  }

  return (
    <div className="follow-through-view">
      {error ? <SurfaceState error={error} onRetry={() => void reload()} /> : null}
      {visibleLanes.map((lane) => {
        const cards = board[lane.id];
        return (
          <SurfaceSection
            key={lane.id}
            label={lane.label}
            actions={<span className="follow-through-count">{cards.length}</span>}
            className={`follow-through-lane${lane.id === "overdue" ? " is-overdue" : ""}`}
          >
            {cards.length ? (
              <SurfaceLedger count={`${cards.length} ${lane.label.toUpperCase()}`} cols="follow-through">
                {cards.map((card) => {
                  const open = openCardId === card.id;
                  const source = sourceFor(card);
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
                          <span className="follow-through-owner" title={card.owner ?? "Unassigned"}>
                            {initials(card.owner)}
                          </span>
                          <span
                            className="follow-through-due"
                            data-overdue={overdue || undefined}
                          >
                            {dueLabel(card.due)}
                          </span>
                          <button
                            type="button"
                            className="follow-through-source"
                            title={peopleCommitment ? "Open People" : "Open governing decision"}
                            aria-label={`${peopleCommitment ? "Open People" : "Open decision"} for ${card.text}`}
                            onClick={(event) => {
                              event.stopPropagation();
                              openDecision(card);
                            }}
                          >
                            {source.glyph}
                          </button>
                        </>
                      }
                    >
                      <div className="follow-through-expanded">
                        <div className="follow-through-verbs" aria-label={`Verbs for ${card.text}`}>
                          <Button dense variant="ghost" disabled={busyCardId === card.id} onClick={() => void complete(card.id, "done")} aria-label="Mark done">✓</Button>
                          <Button dense variant="ghost" disabled={busyCardId === card.id} onClick={() => void complete(card.id, "dismiss")} aria-label="Dismiss">↷</Button>
                          {!peopleCommitment ? <Button dense variant="ghost" disabled={busyCardId === card.id} onClick={() => void complete(card.id, "snooze", { until: tomorrow() })} aria-label="Snooze until tomorrow">◷</Button> : null}
                          {!peopleCommitment ? <Button dense variant="ghost" disabled={busyCardId === card.id} onClick={() => setDelegatingCardId(delegatingCardId === card.id ? null : card.id)} aria-label="Delegate">⇢</Button> : null}
                          <Button dense variant="ghost" disabled={busyCardId === card.id} onClick={() => void complete(card.id, "reopen")} aria-label="Reopen">↺</Button>
                        </div>
                        {delegatingCardId === card.id ? (
                          <div className="follow-through-delegate">
                            <StringGadget label={`Delegate ${card.text} to`} value={delegateTo} onChange={setDelegateTo} placeholder="OWNER" />
                            <Button dense disabled={!delegateTo.trim() || busyCardId === card.id} onClick={() => void complete(card.id, "delegate", { to: delegateTo.trim() })}>Assign</Button>
                          </div>
                        ) : null}
                        {card.provenance?.available ? (
                          <blockquote className="follow-through-provenance">
                            {card.provenance.segment_speaker ? <cite>{card.provenance.segment_speaker}</cite> : null}
                            <span>{card.provenance.segment_text ?? "Source moment unavailable"}</span>
                          </blockquote>
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
