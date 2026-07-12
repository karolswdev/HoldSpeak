import { useCallback, useEffect, useState } from "react";
import { Button, InlineMessage } from "../components/signal/Signal";
import { apiFetch, readableError, type JsonRecord } from "../lib/api";

type MeetingConflict = {
  id: string;
  meeting_id: string;
  local: JsonRecord;
  incoming: JsonRecord;
  detected_at?: string;
};

export type MeetingConflictResolution = {
  resolution: "keep_current" | "use_incoming";
  deleted: boolean;
  meeting: JsonRecord | null;
  remaining_conflicts: MeetingConflict[];
};

function rows(value: unknown): JsonRecord[] {
  return Array.isArray(value)
    ? value.filter(
        (row): row is JsonRecord => Boolean(row) && typeof row === "object",
      )
    : [];
}

function versionSummary(
  label: string,
  value: JsonRecord,
  fallbackTitle: string,
) {
  if (value.deleted) {
    return (
      <article className="meeting-conflict-version is-deletion">
        <h4>{label}</h4>
        <strong>Meeting deleted</strong>
        <p>This version removes the Meeting and its retained projections.</p>
      </article>
    );
  }
  const segments = rows(value.segments);
  const latest = String(segments.at(-1)?.text ?? "").trim();
  const tags = Array.isArray(value.tags)
    ? value.tags.map(String).filter(Boolean)
    : [];
  return (
    <article className="meeting-conflict-version">
      <h4>{label}</h4>
      <dl>
        <div>
          <dt>Title</dt>
          <dd>{String(value.title || fallbackTitle)}</dd>
        </div>
        <div>
          <dt>Capture</dt>
          <dd>{String(value.capture_status || "saved")}</dd>
        </div>
        <div>
          <dt>Transcript</dt>
          <dd>
            {segments.length} {segments.length === 1 ? "segment" : "segments"}
            {latest ? ` · ${latest.slice(0, 140)}` : ""}
          </dd>
        </div>
        <div>
          <dt>Tags</dt>
          <dd>{tags.length ? tags.join(", ") : "None"}</dd>
        </div>
        <div>
          <dt>Source</dt>
          <dd>{String(value.provenance || "unknown device")}</dd>
        </div>
      </dl>
    </article>
  );
}

export function MeetingConflictRecovery({
  meetingId,
  onResolved,
}: {
  meetingId: string;
  onResolved?(result: MeetingConflictResolution): void | Promise<void>;
}) {
  const [conflicts, setConflicts] = useState<MeetingConflict[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!meetingId) return;
    setLoading(true);
    setError("");
    try {
      const payload = await apiFetch<{ conflicts?: MeetingConflict[] }>(
        `/api/meetings/${encodeURIComponent(meetingId)}/sync-conflicts`,
      );
      setConflicts(Array.isArray(payload.conflicts) ? payload.conflicts : []);
    } catch (reason) {
      setError(
        `${readableError(reason)} Both Meeting versions remain retained.`,
      );
    } finally {
      setLoading(false);
    }
  }, [meetingId]);

  useEffect(() => {
    void load();
  }, [load]);

  const resolve = async (
    conflict: MeetingConflict,
    resolution: "keep_current" | "use_incoming",
  ) => {
    setBusyId(`${conflict.id}:${resolution}`);
    setError("");
    try {
      const result = await apiFetch<MeetingConflictResolution>(
        `/api/meetings/${encodeURIComponent(meetingId)}/sync-conflicts/${encodeURIComponent(conflict.id)}/resolve`,
        { method: "POST", json: { resolution } },
      );
      setConflicts(result.remaining_conflicts || []);
      await onResolved?.(result);
    } catch (reason) {
      setError(
        `${readableError(reason)} Both Meeting versions remain retained.`,
      );
    } finally {
      setBusyId("");
    }
  };

  if (loading && conflicts.length === 0) return null;
  if (!error && conflicts.length === 0) return null;

  return (
    <section
      className="meeting-conflict-recovery"
      aria-label="Meeting conflicts"
    >
      {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}
      {conflicts.map((conflict) => {
        const incomingDeletes = Boolean(conflict.incoming.deleted);
        return (
          <div className="meeting-conflict" key={conflict.id}>
            <div>
              <h3>Choose the Meeting version</h3>
              <p>
                Two edits have the same sync time. HoldSpeak kept both and made
                no silent choice. Select the version that should remain under
                this Meeting identity.
              </p>
            </div>
            <div className="meeting-conflict-versions">
              {versionSummary(
                "Current on this desktop",
                conflict.local,
                "Untitled Meeting",
              )}
              {versionSummary(
                "Incoming from synced device",
                conflict.incoming,
                "Untitled Meeting",
              )}
            </div>
            <div className="button-row">
              <Button
                dense
                loading={busyId === `${conflict.id}:keep_current`}
                disabled={Boolean(busyId)}
                onClick={() => void resolve(conflict, "keep_current")}
              >
                Keep current Meeting
              </Button>
              <Button
                dense
                variant={incomingDeletes ? "danger" : "secondary"}
                loading={busyId === `${conflict.id}:use_incoming`}
                disabled={Boolean(busyId)}
                onClick={() => void resolve(conflict, "use_incoming")}
              >
                {incomingDeletes
                  ? "Delete this Meeting from this device"
                  : "Use synced Meeting"}
              </Button>
            </div>
          </div>
        );
      })}
    </section>
  );
}
