import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

export type IntelligenceAttention = {
  briefReady: boolean;
  overdue: number;
  review: number;
};

const EMPTY: IntelligenceAttention = { briefReady: false, overdue: 0, review: 0 };
export const INTELLIGENCE_ATTENTION_REFRESH = "holdspeak:intelligence-attention-refresh";

export function refreshIntelligenceAttention(): void {
  window.dispatchEvent(new Event(INTELLIGENCE_ATTENTION_REFRESH));
}

/** One read-only projection for every Intelligence attention face. */
export function useIntelligenceAttention() {
  const [attention, setAttention] = useState<IntelligenceAttention>(EMPTY);
  const refresh = useCallback(() => {
    void Promise.all([
      apiFetch<{ is_empty?: boolean } | null>("/api/brief/latest"),
      apiFetch<{ overdue?: unknown[] }>("/api/follow-through/board"),
      apiFetch<unknown[]>("/api/receipts/review"),
    ]).then(([brief, board, review]) => {
      setAttention({
        briefReady: Boolean(brief && !brief.is_empty),
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
