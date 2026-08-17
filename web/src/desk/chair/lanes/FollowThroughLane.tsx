// HS-135-08 -- the Follow-Through lane: NOW/OVERDUE first, then
// WAITING to the maxItems bound. Each item with owner/age and its
// complete/dismiss verb reusing the existing Follow-Through service
// actions. Header-click opens Intelligence on the Follow-Through wing.
// The newCommitmentVerb prop exists on the lane header -- typed, default
// null, renders NOTHING when null (Article VI: hidden = absent).

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { refreshIntelligenceAttention } from "../../intelligenceAttention";
import { openIntelligence } from "../../intelligenceNavigation";
import {
  SurfaceRows,
  SurfaceRow,
  SurfaceSection,
  SurfaceState,
} from "../../surface/Surface";
import { DEFAULT_MAX_ITEMS, type LaneProps } from "../laneContract";

// ---------------------------------------------------------------------------
// types -- reused from FollowThroughView (no new endpoints)
// ---------------------------------------------------------------------------

type Lane = "now" | "waiting" | "unassigned" | "overdue";

type FollowThroughCard = {
  id: string;
  text: string;
  owner: string | null;
  due: string | null;
  source: string;
};

type FollowThroughBoard = Record<Lane, FollowThroughCard[]>;

// ---------------------------------------------------------------------------
// helpers -- reused from FollowThroughView
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// the lane
// ---------------------------------------------------------------------------

export interface FollowThroughLaneProps extends LaneProps {
  /** Forward-compatible slot: when Wave 2 lands manual commitment
   *  creation, the header shows it with zero Chair work.  null/hidden
   *  today -- hidden means ABSENT, not disabled (Article VI). */
  newCommitmentVerb?: ReactNode | null;
}

export function FollowThroughLane({
  maxItems = DEFAULT_MAX_ITEMS,
  onOpenInWindow,
  newCommitmentVerb = null,
}: FollowThroughLaneProps) {
  const [board, setBoard] = useState<FollowThroughBoard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyCardId, setBusyCardId] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setBoard(
        await apiFetch<FollowThroughBoard>("/api/follow-through/board"),
      );
    } catch (cause) {
      setError(readableError(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const doVerb = async (cardId: string, verb: "done" | "dismiss") => {
    setBusyCardId(cardId);
    setError("");
    try {
      await apiFetch("/api/follow-through/complete", {
        method: "POST",
        json: { card_id: cardId, verb, payload: {} },
      });
      await reload();
      refreshIntelligenceAttention();
    } catch (cause) {
      setError(readableError(cause));
    } finally {
      setBusyCardId(null);
    }
  };

  if (loading) return <SurfaceState loading />;
  if (error && !board) {
    return <SurfaceState error={error} onRetry={() => void reload()} />;
  }
  if (!board) return null;

  // Order: OVERDUE first, then NOW, then WAITING (urgency gradient).
  const ordered: FollowThroughCard[] = [
    ...board.overdue,
    ...board.now,
    ...board.waiting,
  ];

  if (ordered.length === 0) {
    return <SurfaceState empty emptyLabel="No follow-through yet" />;
  }

  const visible = ordered.slice(0, maxItems);
  const overflow = ordered.length - visible.length;

  const openFollowThrough = () => {
    openIntelligence({ view: "follow-through" });
  };

  return (
    <>
      {/* The forward-compatible slot: absent when null (Article VI). */}
      {newCommitmentVerb != null ? newCommitmentVerb : null}
      <SurfaceSection
        label="FOLLOW-THROUGH"
        actions={
          <button
            type="button"
            className="chair-lane-header-verb"
            onClick={openFollowThrough}
            aria-label="Open FOLLOW-THROUGH"
          >
            {String(ordered.length).padStart(2, "0")}
          </button>
        }
      >
        <SurfaceRows>
          {visible.map((card) => (
            <SurfaceRow
              key={card.id}
              title={card.text}
              detail={`${initials(card.owner)} · ${dueLabel(card.due)}`}
              onOpen={() => onOpenInWindow(card.id)}
              verbs={
                <>
                  <Button
                    dense
                    variant="ghost"
                    disabled={busyCardId === card.id}
                    onClick={() => void doVerb(card.id, "done")}
                    aria-label={`Complete ${card.text}`}
                  >
                    ✓
                  </Button>
                  <Button
                    dense
                    variant="ghost"
                    disabled={busyCardId === card.id}
                    onClick={() => void doVerb(card.id, "dismiss")}
                    aria-label={`Dismiss ${card.text}`}
                  >
                    ↷
                  </Button>
                </>
              }
            />
          ))}
        </SurfaceRows>
        {overflow > 0 ? (
          <button
            type="button"
            className="chair-lane-footer"
            onClick={openFollowThrough}
          >
            {overflow} more -- Open Intelligence
          </button>
        ) : null}
      </SurfaceSection>
    </>
  );
}
