import { useCallback, useEffect, useState, useSyncExternalStore } from "react";
import { apiFetch } from "../lib/api";

export type IntelligenceAttention = {
  briefReady: boolean;
  overdue: number;
  review: number;
};

type BriefItemRef = { id?: string };
type BriefRead = {
  is_empty?: boolean;
  sections?: Record<string, BriefItemRef[]>;
  shelf?: Record<string, string>;
};

const EMPTY: IntelligenceAttention = { briefReady: false, overdue: 0, review: 0 };
export const INTELLIGENCE_ATTENTION_REFRESH = "holdspeak:intelligence-attention-refresh";

export function refreshIntelligenceAttention(): void {
  window.dispatchEvent(new Event(INTELLIGENCE_ATTENTION_REFRESH));
}

/**
 * HS-132-08 — a brief the owner has fully triaged is not attention.
 * Acknowledge/Defer are durable (the brief carries its shelf), so the badge
 * counts only the items still standing untouched.
 */
export function untriagedBriefItems(brief: BriefRead | null): number {
  if (!brief || brief.is_empty) return 0;
  const shelf = brief.shelf ?? {};
  return Object.values(brief.sections ?? {})
    .flat()
    .filter((item) => item?.id && !shelf[item.id]).length;
}

/** One read-only projection for every Intelligence attention face. */
export function useIntelligenceAttention() {
  const [attention, setAttention] = useState<IntelligenceAttention>(EMPTY);
  const refresh = useCallback(() => {
    void Promise.all([
      apiFetch<BriefRead | null>("/api/brief/latest"),
      apiFetch<{ overdue?: unknown[] }>("/api/follow-through/board"),
      apiFetch<unknown[]>("/api/decision-records/review"),
    ]).then(([brief, board, review]) => {
      setAttention({
        briefReady: untriagedBriefItems(brief) > 0,
        overdue: Array.isArray(board?.overdue) ? board.overdue.length : 0,
        review: Array.isArray(review) ? review.length : 0,
      });
    }).catch(() => setAttention(EMPTY));
  }, []);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    window.addEventListener(INTELLIGENCE_ATTENTION_REFRESH, refresh);
    return () => window.removeEventListener(INTELLIGENCE_ATTENTION_REFRESH, refresh);
  }, [refresh]);
  return { ...attention, refresh };
}

/* ── aftercare: the finished meeting, without the mascot (HS-132-08) ───── */

export type AftercareSignal = {
  meetingId: string;
  title: string;
  openTotal: number;
  decidedTotal: number;
};

let aftercare: AftercareSignal | null = null;
const aftercareListeners = new Set<() => void>();

function publish(next: AftercareSignal | null) {
  aftercare = next;
  for (const listener of aftercareListeners) listener();
}

/**
 * Seat the desk's live aftercare signal.
 *
 * `aftercare_ready` used to reach exactly one subscriber: the Qlippy block,
 * gated on presence + mascot (off by default), so a meeting that just ended
 * raised nothing. The signal now lands here, and the desk's in-flow surfaces
 * read it whether or not the mascot is on.
 */
export function publishAftercare(frame: unknown): AftercareSignal | null {
  if (!frame || typeof frame !== "object") return null;
  const data = frame as Record<string, unknown>;
  const meetingId = typeof data.meeting_id === "string" ? data.meeting_id : "";
  if (!meetingId) return null;
  const signal: AftercareSignal = {
    meetingId,
    title:
      (typeof data.title === "string" && data.title.trim()) || "Untitled meeting",
    openTotal: Number(data.open_total ?? 0) || 0,
    decidedTotal: Number(data.decided_total ?? 0) || 0,
  };
  publish(signal);
  return signal;
}

export function dismissAftercare(): void {
  if (aftercare !== null) publish(null);
}

function aftercareSnapshot(): AftercareSignal | null {
  return aftercare;
}

function subscribeAftercare(listener: () => void): () => void {
  aftercareListeners.add(listener);
  return () => aftercareListeners.delete(listener);
}

/** The desk's live finished-meeting signal, or null when nothing is waiting. */
export function useAftercare(): AftercareSignal | null {
  return useSyncExternalStore(
    subscribeAftercare,
    aftercareSnapshot,
    aftercareSnapshot,
  );
}
