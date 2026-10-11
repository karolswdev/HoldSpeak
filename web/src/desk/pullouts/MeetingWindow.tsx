/** PHILO-17 (owner 2026-10-10, "A meeting opens in one window") — the
 * meeting's one window, `pullout:meeting:<id>`.
 *
 * While the meeting records, the window is the live room (LiveCore); when
 * it stops, the SAME window shows the saved meeting (MeetingRecord, the
 * whole record the Meetings window's detail pane used to hold). No second
 * window opens. The old card body is parked (`_parked/MeetingPullout.tsx`). */
import { lazy, Suspense, useEffect, useState } from "react";
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
 * meeting), or the hub says it is the live one when the window opens. */
function useRecordingHere(meetingId: string): [boolean, () => void] {
  const deskLive = useDesk((s) => s.liveMeetingId === meetingId && s.recording !== "idle");
  const recording = useDesk((s) => s.recording);
  const [hubLive, setHubLive] = useState(false);
  const [stopped, setStopped] = useState(false);
  useEffect(() => {
    let live = true;
    void apiFetch<Record<string, unknown>>("/api/state")
      .then((state) => {
        const active = Boolean(state?.active ?? state?.meeting_active ?? state?.status === "recording");
        const id = String(state?.id ?? state?.meeting_id ?? "");
        if (live && active && id === meetingId) setHubLive(true);
      })
      .catch(() => null);
    return () => {
      live = false;
    };
  }, [meetingId]);
  // A stop anywhere (the orb, the hub) ends the live room here.
  useEffect(() => {
    if (recording === "idle") setHubLive(false);
  }, [recording]);
  return [!stopped && (deskLive || hubLive), () => setStopped(true)];
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
