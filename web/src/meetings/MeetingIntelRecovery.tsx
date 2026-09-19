// HS-111-03 — intel recovery is a one-row attention slab (audit §3.5):
// a GadgetGroup, one row of tokens (state · kept · not done) with the
// RETRY/SKIP verbs on the row. The warn reads as the token's color
// only; the transcript well stays the spine.
// HS-201-06 — every word on the row is a plain one (tenet 4).
import { useCallback, useEffect, useState } from "react";
import { Button } from "../components/signal/Signal";
import { SurfaceState } from "../desk/surface/Surface";
import { GadgetGroup, GadgetRow } from "../desk/surface/gadgets";
import { apiFetch, readableError } from "../lib/api";
import { countToken } from "../desk/surface/count";

type RecoveryFact = {
  label: string;
  detail: string;
};

export type MeetingIntelRecoveryState = {
  meeting_id: string;
  visible: boolean;
  state: string;
  headline: string;
  completed: RecoveryFact[];
  remaining: RecoveryFact;
  job: {
    status: string;
    attempts: number;
    requested_at: string;
    updated_at: string;
  } | null;
  actions: {
    retry: boolean;
    skip: boolean;
  };
};

type RecoveryResponse = {
  success: boolean;
  recovery: MeetingIntelRecoveryState;
};

/** The wire speaks sentences ("3 saved segments"); the slab speaks
 * tokens. Facts that carry no count stay off the line.
 *
 * HS-201-06 (Constitution tenet 4, ASD-STE100): the words are whole and
 * common — `KEPT 3 SEGMENTS · 2 ARTIFACTS`, never the clipped `RETAINED
 * 3 SEG / 2 ART` (audit row 2). A count of zero says nothing at all
 * (UX-CANON A8: no counters of zero), so `RETAINED 0 SEG` is gone. */
function keptToken(completed: RecoveryFact[]): string {
  const tokens: string[] = [];
  for (const fact of completed) {
    const match = /(\d+)\s+saved\s+(segment|artifact)/i.exec(fact.detail);
    if (!match) continue;
    const token = countToken(
      Number(match[1]),
      match[2].toLowerCase() === "segment" ? "SEGMENT" : "ARTIFACT",
    );
    if (token) tokens.push(token);
  }
  return tokens.join(" · ");
}

/** HS-201-06: the hub names the remaining work in its own vocabulary
 * ("routed meeting intelligence"). The face says it in plain words: a
 * summary is a summary, and "routed artifacts" is dropped — the user
 * never asked for a route (audit rows 3 and 4). */
function remainingWords(label: string): string {
  return label
    .replace(/,?\s*and\s+routed\s+artifacts/i, "")
    .replace(/routed\s+meeting\s+intelligence/i, "artifacts")
    .replace(/remaining\s+meeting\s+intelligence/i, "the rest of the summary")
    .replace(/intelligence/gi, "summary")
    .trim()
    .toUpperCase();
}

/** HS-201-06 (audit row 5): the hub's refusal is one sentence and the
 * face adds a second. Without a full stop between them they read as one
 * run-on line. End the first sentence before the second begins. */
function twoSentences(first: string, second: string): string {
  const head = first.trim();
  const closed = /[.!?]$/.test(head) ? head : `${head}.`;
  return `${closed} ${second}`;
}

export function MeetingIntelRecovery({
  meetingId,
  onChanged,
}: {
  meetingId: string;
  onChanged?(recovery: MeetingIntelRecoveryState): void | Promise<void>;
}) {
  const [recovery, setRecovery] = useState<MeetingIntelRecoveryState | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<"retry" | "skip" | "">("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!meetingId) return;
    setLoading(true);
    setError("");
    try {
      setRecovery(
        await apiFetch<MeetingIntelRecoveryState>(
          `/api/meetings/${encodeURIComponent(meetingId)}/intel-recovery`,
        ),
      );
    } catch (reason) {
      setError(
        twoSentences(
          readableError(reason),
          "The Meeting and completed work remain saved.",
        ),
      );
    } finally {
      setLoading(false);
    }
  }, [meetingId]);

  useEffect(() => {
    void load();
  }, [load]);

  const choose = async (action: "retry" | "skip") => {
    setBusy(action);
    setError("");
    try {
      const result = await apiFetch<RecoveryResponse>(
        `/api/meetings/${encodeURIComponent(meetingId)}/intel-recovery/${action}`,
        { method: "POST" },
      );
      setRecovery(result.recovery);
      await onChanged?.(result.recovery);
    } catch (reason) {
      setError(
        twoSentences(
          readableError(reason),
          "The Meeting and completed work remain saved.",
        ),
      );
    } finally {
      setBusy("");
    }
  };

  if (loading && recovery === null) return null;
  if (!error && !recovery?.visible) return null;
  // HS-172: QUEUED and RUNNING states are shown in the header chip now;
  // the legacy panel (prose REMAINING + clipped text) is suppressed.
  const st = recovery?.state?.toLowerCase() ?? "";
  if (st === "queued" || st === "running" || st === "pending") return null;

  const kept = recovery ? keptToken(recovery.completed) : "";
  const running = recovery?.state === "running";
  return (
    <section
      className="meeting-intel-recovery"
      aria-label="Meeting intelligence recovery"
    >
      {error ? <SurfaceState error={error} onRetry={() => void load()} /> : null}
      {/* HS-201-06: the group is the meeting SUMMARY. "Intelligence" is
          the wire's word for it, and a summary is what the user asked
          for (Constitution tenet 4, audit row 4). */}
      {recovery?.visible ? (
        <GadgetGroup label="Summary">
          <GadgetRow
            label={
              <span
                className="surface-token"
                data-tone={running ? undefined : "warn"}
              >
                {recovery.state.toUpperCase()}
              </span>
            }
            fact={kept ? `KEPT ${kept}` : undefined}
          >
            <span className="gadget-fact" title={recovery.remaining.detail}>
              {`NOT DONE: ${remainingWords(recovery.remaining.label)}`}
            </span>
            {recovery.actions.retry ? (
              <Button
                dense
                loading={busy === "retry"}
                disabled={Boolean(busy)}
                onClick={() => void choose("retry")}
              >
                Retry
              </Button>
            ) : null}
            {recovery.actions.skip ? (
              <Button
                dense
                variant="ghost"
                loading={busy === "skip"}
                disabled={Boolean(busy)}
                onClick={() => void choose("skip")}
              >
                Skip
              </Button>
            ) : null}
          </GadgetRow>
        </GadgetGroup>
      ) : null}
    </section>
  );
}
