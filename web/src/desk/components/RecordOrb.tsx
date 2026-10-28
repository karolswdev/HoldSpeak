// The Record orb (HS-73-06): the product's primary verb lives in the world.
// Bottom-center, iPad parity (the DioAmbientRecorder entry). It drives the
// HUB's recorder via /live's exact calls — never a browser microphone (no
// new plumbing, no new egress). State is honest by construction: seeded
// from /api/state and kept live by the ONE runtime bus; a meeting started
// anywhere (the /live page, the CLI, the iPad) shows here and the orb can
// only stop it — never double-start.
import "./record-orb.css";
import { useEffect, useRef } from "react";
import { apiFetch } from "../../lib/api";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { useDesk } from "../store";
import { SYSTEM_48 } from "../systemSprites";
import { Button } from "../../components/signal/Signal";
import { openSurfaceOr } from "../shell";
import { RecordClock, useRecordingElapsed } from "./RecordClock";

const RECORD_WING_LONG_PRESS_MS = 500;

export function RecordOrb() {
  const state = useDesk((s) => s.recording);
  const external = useDesk((s) => s.recordingExternal);
  const elapsed = useRecordingElapsed();
  const orbRef = useRef<HTMLButtonElement | null>(null);
  const longPressTimer = useRef<number | null>(null);
  const longPressed = useRef(false);
  const { subscribe } = useRuntimeBus();

  const clearLongPress = () => {
    if (longPressTimer.current !== null) {
      window.clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  };

  useEffect(() => clearLongPress, []);

  // Live truth: any meeting_live/runtime_activity frame flips the orb.
  // The reducer lives in the store so the chrome Record chip mirrors it.
  useEffect(() => {
    const apply = (activity: unknown) =>
      useDesk.getState().applyRecordingActivity(activity);
    const unsub = subscribe("runtime_activity", (frame) => apply(frame.data));
    // PHILO-17 (Astra r1): the live meeting's identity, also after a reload
    // and for a meeting started elsewhere, so the Live meeting door opens
    // that meeting's own window, never a second room beside it.
    const offStarted = subscribe("meeting_started", (frame) => {
      const id = String((frame.data as Record<string, unknown> | undefined)?.id ?? "");
      if (id) useDesk.setState({ liveMeetingId: id });
    });
    // PHILO-17 (Astra r2): the snapshot is asked at an epoch; a Start or a
    // Stop while it is in flight makes it stale, and it never moves the desk.
    const askedAt = useDesk.getState().recordingEpoch;
    void apiFetch<any>("/api/state")
      .then((snapshot) => {
        const id = String(snapshot?.meeting_id ?? "");
        useDesk.getState().applyRecordingSnapshot(
          snapshot?.activity || snapshot?.runtime?.activity,
          askedAt,
          snapshot?.meeting_active === true && id ? id : null,
        );
      })
      .catch(() => null);
    return () => {
      unsub();
      offStarted();
    };
  }, []);

  const recording = state === "recording";
  return (
    <div className="desk-orb-wrap">
      {/* The floating dock (2026-10-26): Record is one dock tile. Its name,
          the elapsed time and "live elsewhere" show on hover and focus as the
          tile's label above it (dock.css); the aria-label says the same. */}
      <span className="desk-orb-label" aria-hidden="true">
        {recording ? "Stop recording" : "Record a meeting"}
        {recording && external && (
          <span className="desk-orb-note">live elsewhere</span>
        )}
        {recording && elapsed && (
          <span className="desk-orb-elapsed">{elapsed}</span>
        )}
      </span>
      <RecordClock target={orbRef} />
      <Button
        ref={orbRef}
        variant="chrome"
        className={`desk-orb is-${state}`}
        onPointerDown={() => {
          longPressed.current = false;
          clearLongPress();
          longPressTimer.current = window.setTimeout(() => {
            longPressTimer.current = null;
            longPressed.current = true;
            openSurfaceOr("review-meetings", "/history", "record");
          }, RECORD_WING_LONG_PRESS_MS);
        }}
        onPointerUp={clearLongPress}
        onPointerCancel={clearLongPress}
        onPointerLeave={clearLongPress}
        onClick={() => {
          clearLongPress();
          if (longPressed.current) {
            longPressed.current = false;
            return;
          }
          if (recording) {
            void useDesk.getState().stopRecording();
            return;
          }
          if (state !== "idle") return;
          // PHILO-17: the start opens the new meeting's own window (the
          // live room; on Stop the same window shows the saved meeting).
          void useDesk.getState().startRecording();
        }}
        aria-label={recording
          ? `Stop recording${external ? ", live elsewhere" : ""}${elapsed ? `, ${elapsed}` : ""}`
          : "Record a meeting"}
        disabled={state === "busy"}
      >
        {/* The floating dock (2026-10-26): the record key is the 48 px D
            drawing (system/48/), the size of every dock tile. */}
        <img
          src={SYSTEM_48.recordOrb}
          alt=""
          width={48}
          height={48}
          className="desk-orb-face desk-chrome-sprite"
          draggable={false}
        />
      </Button>
    </div>
  );
}
