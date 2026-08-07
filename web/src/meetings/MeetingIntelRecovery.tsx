// HS-111-03 — intel recovery is a one-row attention slab (audit §3.5):
// a GadgetGroup labeled INTEL, one row of tokens (state · retained ·
// remaining) with the RETRY/SKIP verbs on the row. The warn reads as
// the token's color only; the transcript well stays the spine.
import { useCallback, useEffect, useState } from "react";
import { Button } from "../components/signal/Signal";
import { SurfaceState } from "../desk/surface/Surface";
import { GadgetGroup, GadgetRow } from "../desk/surface/gadgets";
import { apiFetch, readableError } from "../lib/api";

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
 * tokens ("3 SEG"). Facts that carry no count stay off the line. */
function retainedToken(completed: RecoveryFact[]): string {
  const tokens: string[] = [];
  for (const fact of completed) {
    const match = /(\d+)\s+saved\s+(segment|artifact)/i.exec(fact.detail);
    if (match) tokens.push(`${match[1]} ${match[2] === "segment" ? "SEG" : "ART"}`);
  }
  return tokens.join(" / ");
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
        `${readableError(reason)} The Meeting and completed work remain saved.`,
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
        `${readableError(reason)} The Meeting and completed work remain saved.`,
      );
    } finally {
      setBusy("");
    }
  };

  if (loading && recovery === null) return null;
  if (!error && !recovery?.visible) return null;

  const retained = recovery ? retainedToken(recovery.completed) : "";
  const running = recovery?.state === "running";
  return (
    <section
      className="meeting-intel-recovery"
      aria-label="Meeting intelligence recovery"
    >
      {error ? <SurfaceState error={error} onRetry={() => void load()} /> : null}
      {/* "Intelligence", never "intel" — the HS-100-05 vocabulary
          guard bans the abbreviation in rendered copy. */}
      {recovery?.visible ? (
        <GadgetGroup label="Intelligence">
          <GadgetRow
            label={
              <span
                className="surface-token"
                data-tone={running ? undefined : "warn"}
              >
                {recovery.state.toUpperCase()}
              </span>
            }
            fact={retained ? `RETAINED ${retained}` : undefined}
          >
            <span className="gadget-fact" title={recovery.remaining.detail}>
              {`REMAINING: ${recovery.remaining.label.toUpperCase()}`}
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
