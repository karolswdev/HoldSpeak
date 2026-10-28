// Betterment capture C7 "One home for recording": Coming up. The calendar's
// next meetings with Record when it starts, the armed ones with Records at
// HH:MM and Cancel, and a fire that failed with Did not record · HH:MM ·
// reason and Record now. ONE store (`comingUp`, `scheduledRecordings`): an
// arm in Today, Meetings ▸ Record or Capture shows in all of them.
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { SurfaceRow, SurfaceRows, SurfaceSection } from "../../../desk/surface/Surface";
import { useOnDeskChanged } from "../../../desk/useDeskChangedRefresh";
import { useDesk } from "../../../desk/store";
import type { ScheduledRecording, UpcomingRow } from "../../../desk/store/types";
import "./coming-up.css";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const pad = (n: number) => String(n).padStart(2, "0");
const clock = (d: Date) => `${pad(d.getHours())}:${pad(d.getMinutes())}`;
const sameDay = (a: Date, b: Date) =>
  a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

function when(value: unknown): Date | null {
  if (!value) return null;
  const d = new Date(String(value));
  return Number.isNaN(d.getTime()) ? null : d;
}

/** `21:15` today, `Mon 09:30` on another day. */
export function slotWord(d: Date, now: Date): string {
  return sameDay(d, now) ? clock(d) : `${DAYS[d.getDay()]} ${clock(d)}`;
}

/** A failed fire stays in the list while its meeting can still run. */
function stillRelevant(schedule: ScheduledRecording, now: Date): boolean {
  const at = when(schedule.did_not_record?.at);
  if (!at) return false;
  const window = Math.max(60, Number(schedule.duration_minutes) || 60) * 60_000;
  return now.getTime() - at.getTime() < window;
}

type Row =
  | { kind: "failed"; key: string; title: string; slot: Date; at: Date; reason: string; eventId: string }
  | { kind: "event"; key: string; title: string; slot: Date; row: UpcomingRow }
  | { kind: "schedule"; key: string; title: string; slot: Date; row: UpcomingRow };

/** The rows, in time order: the failed fires first, then what is next. */
export function comingUpRows(
  upcoming: readonly UpcomingRow[],
  schedules: readonly ScheduledRecording[],
  now: Date,
): Row[] {
  const failed = schedules.filter((s) => s.did_not_record && stillRelevant(s, now));
  const failedEvents = new Set(failed.map((s) => s.calendar_event_id).filter(Boolean));
  const rows: Row[] = failed.map((s) => {
    const at = when(s.did_not_record?.at) ?? now;
    const event = upcoming.find((r) => r.id === s.calendar_event_id);
    return {
      kind: "failed", key: `failed:${s.id}`, title: event?.title || s.title,
      slot: when(event?.starts_at) ?? at, at, reason: s.did_not_record?.reason ?? "", eventId: s.calendar_event_id ?? "",
    };
  });
  for (const row of upcoming) {
    const start = when(row.starts_at);
    if (!start) continue;
    const end = when(row.ends_at) ?? start;
    if (end.getTime() < now.getTime() || failedEvents.has(row.id)) continue;
    const title = row.title || "Meeting";
    rows.push(row.source === "scheduled_recording"
      ? { kind: "schedule", key: `schedule:${row.id}`, title, slot: start, row }
      : { kind: "event", key: `event:${row.id}`, title, slot: start, row });
  }
  return rows;
}

export function ComingUp({ limit, emptyLine, "data-testid": testId = "coming-up" }: {
  limit?: number;
  /** Read and empty: this one quiet line (Capture), else nothing. */
  emptyLine?: string;
  "data-testid"?: string;
}) {
  const read = useDesk((s) => s.comingUp);
  const schedules = useDesk((s) => s.scheduledRecordings);
  const [now, setNow] = useState(() => new Date());
  const [busy, setBusy] = useState<string | null>(null);
  const [refusal, setRefusal] = useState<{ key: string; text: string } | null>(null);

  const load = useCallback(() => {
    const desk = useDesk.getState();
    void desk.loadComingUp();
    void desk.loadSchedules();
  }, []);
  useEffect(() => { load(); }, [load]);
  useOnDeskChanged(load, ["calendar", "calendar_event", "meeting", "scheduled_recording"]);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 30_000);
    return () => window.clearInterval(timer);
  }, []);

  const rows = useMemo(() => {
    const all = comingUpRows(read?.rows ?? [], schedules, now);
    return typeof limit === "number" ? all.slice(0, limit) : all;
  }, [read, schedules, now, limit]);
  // Not read yet: an empty, busy section, so a window sized by its content
  // (Capture's seat, chair.css) is measured with the rows' room; read and
  // empty: nothing (no empty list, UX-CANON).
  if (read === null) return <section className="coming-up" data-testid={testId} aria-busy="true" />;
  if (!rows.length) {
    return emptyLine ? <p className="coming-up-none" data-testid={`${testId}-none`}>{emptyLine}</p> : null;
  }

  const act = async (key: string, failText: string, run: () => Promise<boolean | { ok: boolean; reason?: string }>) => {
    setBusy(key);
    setRefusal(null);
    try {
      const result = await run();
      const ok = typeof result === "boolean" ? result : result.ok;
      if (!ok) {
        const reason = typeof result === "object" && "reason" in result ? result.reason : "";
        setRefusal({ key, text: reason ? `${failText} · ${reason}` : failText });
      }
    } finally {
      setBusy(null);
    }
  };
  const record = (key: string, eventId: string) => act(key, "Did not start", async () => {
    await useDesk.getState().startRecording(eventId ? { calendarEventId: eventId } : undefined);
    return true;
  });

  return (
    <SurfaceSection label="Coming up" className="coming-up" data-testid={testId}>
      <SurfaceRows>
        {rows.map((item) => {
          let detail: string | null = null;
          let verb: ReactNode = null;
          let tone: string | undefined;
          if (item.kind === "failed") {
            detail = `Did not record · ${clock(item.at)}${item.reason ? ` · ${item.reason}` : ""}`;
            tone = "danger";
            verb = (
              <Button dense variant="primary" loading={busy === item.key} data-testid="coming-up-record-now"
                onClick={() => void record(item.key, item.eventId)}>
                Record now
              </Button>
            );
          } else {
            const row = item.row;
            const armed = item.kind === "event" ? row.armed ?? null : row;
            const armState = item.kind === "event" ? row.armed?.state : row.state;
            if (armState === "recording") {
              detail = "Recording";
              tone = "danger";
            } else if (armed) {
              const at = when(item.kind === "event" ? row.armed?.arms_at : row.starts_at) ?? item.slot;
              detail = `Records at ${clock(at)}`;
              tone = "danger";
              verb = (
                <Button dense variant="ghost" loading={busy === item.key} data-testid="coming-up-cancel"
                  aria-label={`Cancel the recording of ${item.title}`}
                  onClick={() => void act(item.key, "Not cancelled", () => {
                    const desk = useDesk.getState();
                    if (item.kind === "event") return desk.cancelArmedSchedule(row.armed!.recording_id);
                    return armState === "arming" ? desk.cancelArmedSchedule(row.id) : desk.disableSchedule(row.id);
                  })}>
                  Cancel
                </Button>
              );
            } else if (item.slot.getTime() <= now.getTime()) {
              verb = (
                <Button dense variant="secondary" loading={busy === item.key} data-testid="coming-up-record"
                  onClick={() => void record(item.key, row.id)}>
                  Record
                </Button>
              );
            } else {
              verb = (
                <Button dense variant="secondary" loading={busy === item.key} data-testid="coming-up-arm"
                  aria-label={`Record ${item.title} when it starts`}
                  onClick={() => void act(item.key, "Not armed. Try again", () => useDesk.getState().armEventRecording(row.id))}>
                  Record when it starts
                </Button>
              );
            }
          }
          const failedText = refusal?.key === item.key ? refusal.text : null;
          return (
            <SurfaceRow
              key={item.key}
              glyph={<span className="coming-up-slot" data-testid="coming-up-slot">{slotWord(item.slot, now)}</span>}
              title={<span data-testid="coming-up-title">{item.title}</span>}
              detail={detail || failedText ? (
                <span className="coming-up-detail">
                  {detail ? <span className="kit-pill" data-tone={tone} data-testid="coming-up-state">{detail}</span> : null}
                  {failedText ? <span className="kit-pill" data-tone="danger" role="status" data-testid="coming-up-refused">{failedText}</span> : null}
                </span>
              ) : undefined}
              verbs={verb ?? undefined}
            />
          );
        })}
      </SurfaceRows>
    </SurfaceSection>
  );
}
