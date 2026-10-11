/** PHILO-17 (owner 2026-10-10, "A meeting opens in one window") — the
 * meeting's one window, `pullout:meeting:<id>`.
 *
 * While the meeting records, the window is the live room (LiveCore); when
 * it stops, the SAME window shows the saved meeting (MeetingRecord, the
 * whole record the Meetings window's detail pane used to hold). No second
 * window opens. The old card body is parked (`_parked/MeetingPullout.tsx`). */
import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useDesk } from "../store";
import { SurfaceState } from "../surface";
import type { PulloutContentProps } from "./types";

const LiveCore = lazy(() =>
  import("../../pages/cores/LiveCore").then((m) => ({ default: m.LiveCore })),
);
const MeetingRecord = lazy(() =>
  import("../../pages/cores/history/MeetingRecord").then((m) => ({ default: m.MeetingRecord })),
);

/** True while THIS meeting records: the desk started it (the store's live
 * meeting), or the hub says it is the live one when the window opens.
 *
 * PHILO-17 (Astra r1): a Stop is final for this window. Once recording goes
 * idle after this meeting was live here (the window's own Stop, the orb, the
 * hub), the window latches to the record; and a hub reply asked before that
 * idle (a slow first `/api/state`) is dropped, never read as live again. */
export function useRecordingHere(meetingId: string): [boolean, () => void] {
  const deskLive = useDesk((s) => s.liveMeetingId === meetingId && s.recording !== "idle");
  const recording = useDesk((s) => s.recording);
  const [hubLive, setHubLive] = useState(false);
  const [stopped, setStopped] = useState(false);
  const epoch = useRef(0);
  const wasLive = useRef(false);
  const live = !stopped && (deskLive || hubLive);
  if (live) wasLive.current = true;
  useEffect(() => {
    const asked = epoch.current;
    let mounted = true;
    void apiFetch<Record<string, unknown>>("/api/state")
      .then((state) => {
        if (!mounted || asked !== epoch.current) return;
        const active = state?.meeting_active === true || state?.active === true || state?.status === "recording";
        const id = String(state?.meeting_id ?? state?.id ?? "");
        if (active && id === meetingId) setHubLive(true);
      })
      .catch(() => null);
    return () => {
      mounted = false;
    };
  }, [meetingId]);
  // A stop anywhere (the orb, the hub, this window) ends the live room here.
  const previous = useRef(recording);
  useEffect(() => {
    const was = previous.current;
    previous.current = recording;
    if (recording !== "idle" || was === "idle") return;
    epoch.current += 1;
    setHubLive(false);
    if (wasLive.current) setStopped(true);
  }, [recording]);
  return [live, () => setStopped(true)];
}

export function MeetingWindow({ object: o, onClose }: PulloutContentProps) {
  const [recordingHere, markStopped] = useRecordingHere(o.id);
  return (
    <Suspense fallback={<SurfaceState loading />}>
      {recordingHere ? (
        <LiveCore meetingId={o.id} onStopped={markStopped} />
      ) : (
        <MeetingRecord key={o.id} meetingId={o.id} onClose={onClose} />
      )}
    </Suspense>
  );
}
