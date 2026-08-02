// HS-111-03 — sync conflicts are twin receipt slips (audit §3.5):
// CURRENT / INCOMING side by side, each a mono fact stack on an opaque
// two-tone inset, the choosing verbs on the slips. The group label
// carries the whole truth: SYNC CONFLICT · BOTH RETAINED. Wire calls
// unchanged.
import { useCallback, useEffect, useState } from "react";
import { Button } from "../components/signal/Signal";
import { SurfaceState } from "../desk/surface/Surface";
import { GadgetGroup } from "../desk/surface/gadgets";
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

function VersionSlip({
  label,
  value,
  fallbackTitle,
  verb,
}: {
  label: string;
  value: JsonRecord;
  fallbackTitle: string;
  verb: React.ReactNode;
}) {
  if (value.deleted) {
    return (
      <article className="meeting-conflict-slip">
        <div className="meeting-conflict-slip-head">
          <span className="surface-token">{label}</span>
          <span className="surface-token" data-tone="danger">
            TOMBSTONE
          </span>
        </div>
        <dl className="meeting-conflict-slip-facts">
          <div>
            <dt>Meeting</dt>
            <dd>Deleted, with its retained projections</dd>
          </div>
        </dl>
        <div className="surface-actions">{verb}</div>
      </article>
    );
  }
  const segments = rows(value.segments);
  const latest = String(segments.at(-1)?.text ?? "").trim();
  const tags = Array.isArray(value.tags)
    ? value.tags.map(String).filter(Boolean)
    : [];
  return (
    <article className="meeting-conflict-slip">
      <div className="meeting-conflict-slip-head">
        <span className="surface-token">{label}</span>
      </div>
      <dl className="meeting-conflict-slip-facts">
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
        {tags.length ? (
          <div>
            <dt>Tags</dt>
            <dd>{tags.join(", ")}</dd>
          </div>
        ) : null}
        <div>
          <dt>Source</dt>
          <dd>{String(value.provenance || "unknown device")}</dd>
        </div>
      </dl>
      <div className="surface-actions">{verb}</div>
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
      {error ? <SurfaceState error={error} /> : null}
      {conflicts.map((conflict) => {
        const incomingDeletes = Boolean(conflict.incoming.deleted);
        return (
          <GadgetGroup key={conflict.id} label="Sync conflict · both retained">
            <div className="meeting-conflict-slips">
              <VersionSlip
                label="CURRENT"
                value={conflict.local}
                fallbackTitle="Untitled Meeting"
                verb={
                  <Button
                    dense
                    loading={busyId === `${conflict.id}:keep_current`}
                    disabled={Boolean(busyId)}
                    onClick={() => void resolve(conflict, "keep_current")}
                  >
                    Keep current
                  </Button>
                }
              />
              <VersionSlip
                label="INCOMING"
                value={conflict.incoming}
                fallbackTitle="Untitled Meeting"
                verb={
                  <Button
                    dense
                    variant={incomingDeletes ? "danger" : "secondary"}
                    loading={busyId === `${conflict.id}:use_incoming`}
                    disabled={Boolean(busyId)}
                    onClick={() => void resolve(conflict, "use_incoming")}
                  >
                    Use incoming
                  </Button>
                }
              />
            </div>
          </GadgetGroup>
        );
      })}
    </section>
  );
}
