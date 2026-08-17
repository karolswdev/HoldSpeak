// HS-135-09 -- the Meetings lane: recent meetings to the curated
// maxItems bound with truthful badges (date, segment count, intel/action
// state).  A LIVE meeting (recording active, no endedAt) pins first
// showing its live state from the existing store frames.  Header-click
// opens the Meetings surface window; item-click opens that meeting's
// detail (single-instance).  Sparse law: NO filter chrome on the lane.
//
// HS-136-03 -- scheduled recordings surface here with a SCHEDULED badge
// and their next-fire time. Sorted after live, before archived.

import { useEffect } from "react";
import { useDesk } from "../../store";
import type { ScheduledRecording } from "../../store";
import { ChairLane } from "../Lane";
import type { LaneItem } from "../Lane";
import { DEFAULT_MAX_ITEMS, type LaneProps } from "../laneContract";
import type { Meeting } from "../../../lib/primitives";

// ---------------------------------------------------------------------------
// constants
// ---------------------------------------------------------------------------

/** The surface key the Meetings window registers under (SurfaceWindows.tsx). */
const SURFACE_ID = "review-meetings";

const MONTHS = [
  "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
];

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

/** MMM DD -- the lane's date cell (reuses the HistoryCore ledger format). */
function ledgerDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return `${MONTHS[d.getMonth()]} ${String(d.getDate()).padStart(2, "0")}`;
}

/** Truthful intel/action badge for a finished meeting.  Maps the wire's
 *  intelStatus string to the same vocabulary the HistoryCore catalog uses
 *  (stateToken in history/helpers.ts), compressed to a lane-width token. */
export function intelBadge(status: string | null | undefined): string {
  if (!status) return "SAVED";
  const s = String(status).toLowerCase();
  const map: Record<string, string> = {
    complete: "SAVED",
    running: "RUNNING",
    queued: "QUEUED",
    pending: "QUEUED",
    error: "FAILED",
    failed: "FAILED",
    partial: "PARTIAL",
    skipped: "SKIPPED",
    disabled: "OFF",
  };
  return map[s] ?? "SAVED";
}

/** Build the detail string: date, segment count, action-item count. */
function meetingDetail(m: Meeting): string {
  const parts: string[] = [];
  const date = ledgerDate(m.startedAt);
  if (date) parts.push(date);
  const segs = m.segmentCount ?? m.segments?.length ?? 0;
  if (segs > 0) parts.push(`${segs} seg`);
  const actions = m.actionItemCount ?? 0;
  if (actions > 0) parts.push(`${actions} action`);
  return parts.join(" · ");
}

/** True when this meeting is the live recording (no endedAt while the
 *  desk's recording state is active). */
function isLiveMeeting(m: Meeting, isRecording: boolean): boolean {
  return isRecording && !m.endedAt;
}

// ---------------------------------------------------------------------------
// schedule helpers (HS-136-03)
// ---------------------------------------------------------------------------

/** Format a next-fire ISO timestamp as a short lane-width label. */
export function nextFireLabel(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const now = new Date();
  const diffMs = d.getTime() - now.getTime();
  // Show relative for < 24h, absolute otherwise.
  if (diffMs > 0 && diffMs < 86_400_000) {
    const h = Math.floor(diffMs / 3_600_000);
    const m = Math.floor((diffMs % 3_600_000) / 60_000);
    if (h > 0) return `in ${h}h ${m}m`;
    return `in ${m}m`;
  }
  return `${MONTHS[d.getMonth()]} ${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

/** Build a LaneItem from a scheduled recording. */
function scheduleToLaneItem(s: ScheduledRecording): LaneItem {
  const detail = nextFireLabel(s.next_fire_at);
  return {
    id: `schedule:${s.id}`,
    title: s.title || "Scheduled recording",
    detail: detail ? `Next: ${detail}` : s.one_shot ? "One-shot" : "Recurring",
    meta: "SCHEDULED",
    glyph: "⏱",
  };
}

// ---------------------------------------------------------------------------
// the lane
// ---------------------------------------------------------------------------

export function MeetingsLane({
  maxItems = DEFAULT_MAX_ITEMS,
  onOpenInWindow,
}: LaneProps) {
  const meetings = useDesk((s) => s.items.meeting);
  const recording = useDesk((s) => s.recording);
  const scheduledRecordings = useDesk((s) => s.scheduledRecordings);
  const isRecording = recording === "recording";

  // Load scheduled recordings on mount.
  useEffect(() => {
    void useDesk.getState().loadSchedules();
  }, []);

  // Nothing: the Chair's 300ms fallback owns the all-blank case.
  const enabledSchedules = scheduledRecordings.filter((s) => s.enabled);
  if (meetings.length === 0 && enabledSchedules.length === 0) return null;

  // Sort: live meeting (no endedAt while recording) pins first,
  // then by startedAt descending (most recent first).
  const sorted = [...meetings].sort((a, b) => {
    const aLive = isLiveMeeting(a, isRecording);
    const bLive = isLiveMeeting(b, isRecording);
    if (aLive && !bLive) return -1;
    if (!aLive && bLive) return 1;
    return new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime();
  });

  // Build items: live meetings first, then scheduled, then archived.
  const liveItems: LaneItem[] = [];
  const archivedItems: LaneItem[] = [];
  for (const m of sorted) {
    const live = isLiveMeeting(m, isRecording);
    const item: LaneItem = {
      id: m.id,
      title: m.title || "Untitled meeting",
      detail: meetingDetail(m),
      meta: live ? "REC" : intelBadge(m.intelStatus),
      glyph: live ? "●" : "▣",
    };
    if (live) liveItems.push(item);
    else archivedItems.push(item);
  }

  const scheduleItems = enabledSchedules.map(scheduleToLaneItem);
  const items = [...liveItems, ...scheduleItems, ...archivedItems];

  return (
    <ChairLane
      title="MEETINGS"
      maxItems={maxItems}
      items={items}
      onOpenInWindow={onOpenInWindow}
      surfaceId={SURFACE_ID}
      footerVerb="Open Meetings"
    />
  );
}
