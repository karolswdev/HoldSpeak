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
  /** PHILO-15 08 (B13): proposals still to review; 0 withholds the verb. */
  proposalTotal: number;
  /** PHILO-15 B56 (Astra r1): the hub could not count them on the last read. */
  countUnread?: boolean;
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
      (typeof data.title === "string" && data.title.trim()) || "Meeting with no title",
    openTotal: Number(data.open_total ?? 0) || 0,
    decidedTotal: Number(data.decided_total ?? 0) || 0,
    proposalTotal: Number(data.proposal_total ?? 0) || 0,
  };
  publish(signal);
  return signal;
}

export function dismissAftercare(): void {
  if (aftercare !== null) publish(null);
}

type AftercareRead = {
  open_items?: { total?: unknown } | null;
  decisions?: unknown[] | null;
  proposal_total?: unknown;
};

/**
 * PHILO-15 B56: the card's counts are the hub's, read again (a "2 to review"
 * card stayed half an hour after both proposals were confirmed). A card that
 * came with proposals to review leaves when that count reaches zero; an
 * unread answer keeps the card as it is.
 */
export async function refreshAftercare(): Promise<void> {
  const current = aftercare;
  if (!current) return;
  let read: AftercareRead | null = null;
  try {
    read = await apiFetch<AftercareRead>(`/api/meetings/${encodeURIComponent(current.meetingId)}/aftercare`);
  } catch {
    return;
  }
  if (aftercare !== current || !read) return;
  // An unknown count never dismisses (Astra r1 P2): `Number(null)` is 0, so
  // a null, missing or non-number total is "not read", and the card stays.
  const raw = read.proposal_total;
  const proposals = typeof raw === "number" ? raw : typeof raw === "string" && raw.trim() ? Number(raw) : Number.NaN;
  if (!Number.isFinite(proposals)) {
    if (!current.countUnread) publish({ ...current, countUnread: true });
    return;
  }
  if (current.proposalTotal > 0 && proposals <= 0) {
    publish(null);
    return;
  }
  const next: AftercareSignal = {
    ...current,
    countUnread: false,
    proposalTotal: Math.max(0, proposals),
    openTotal: Number(read.open_items?.total ?? current.openTotal) || 0,
    decidedTotal: Array.isArray(read.decisions) ? read.decisions.length : current.decidedTotal,
  };
  if (
    next.proposalTotal !== current.proposalTotal ||
    next.openTotal !== current.openTotal ||
    next.decidedTotal !== current.decidedTotal ||
    Boolean(current.countUnread)
  ) publish(next);
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

/* PHILO-14 A1c (Astra r1, #954): where the card is rendered, published by
 * AmbientLayer from its own render state (never read back from the DOM).
 * The Chair grows Capture only while Capture's slot holds the card. */
export type AftercareHost = "capture" | "window" | "floor" | "fixed" | null;

let aftercareHost: AftercareHost = null;
const aftercareHostListeners = new Set<() => void>();

export function publishAftercareHost(next: AftercareHost): void {
  if (aftercareHost === next) return;
  aftercareHost = next;
  for (const listener of aftercareHostListeners) listener();
}

function aftercareHostSnapshot(): AftercareHost {
  return aftercareHost;
}

function subscribeAftercareHost(listener: () => void): () => void {
  aftercareHostListeners.add(listener);
  return () => aftercareHostListeners.delete(listener);
}

export function useAftercareHost(): AftercareHost {
  return useSyncExternalStore(
    subscribeAftercareHost,
    aftercareHostSnapshot,
    aftercareHostSnapshot,
  );
}
