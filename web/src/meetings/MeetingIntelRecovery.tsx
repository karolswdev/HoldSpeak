import { useCallback, useEffect, useState } from "react";
import { Button, InlineMessage } from "../components/signal/Signal";
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

  return (
    <section
      className="meeting-intel-recovery"
      aria-label="Meeting intelligence recovery"
    >
      {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}
      {recovery?.visible ? (
        <div className="meeting-intel-recovery-card">
          <div>
            <h3>{recovery.headline}</h3>
            <p>Completed work remains available on this Meeting.</p>
          </div>
          <dl className="meeting-intel-recovery-facts">
            {recovery.completed.map((fact) => (
              <div key={fact.label}>
                <dt>{fact.label}</dt>
                <dd>{fact.detail}</dd>
              </div>
            ))}
          </dl>
          <div className="meeting-intel-remaining">
            <h4>Remaining</h4>
            <strong>{recovery.remaining.label}</strong>
            <p>{recovery.remaining.detail}</p>
          </div>
          {recovery.actions.retry || recovery.actions.skip ? (
            <div className="button-row">
              {recovery.actions.retry ? (
                <Button
                  dense
                  loading={busy === "retry"}
                  disabled={Boolean(busy)}
                  onClick={() => void choose("retry")}
                >
                  Retry remaining
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
                  Skip remaining
                </Button>
              ) : null}
            </div>
          ) : recovery.state === "running" ? (
            <p className="quiet">Wait for the running attempt to finish.</p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
