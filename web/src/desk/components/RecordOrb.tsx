// The Record orb (HS-73-06): the product's primary verb lives in the world.
// Bottom-center, iPad parity (the DioAmbientRecorder entry). It drives the
// HUB's recorder via /live's exact calls — never a browser microphone (no
// new plumbing, no new egress). State is honest by construction: seeded
// from /api/state and kept live by the ONE runtime bus; a meeting started
// anywhere (the /live page, the CLI, the iPad) shows here and the orb can
// only stop it — never double-start.
import "./record-orb.css";
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { useDesk } from "../store";
import { SYSTEM } from "../systemSprites";
import { Button } from "../../components/signal/Signal";

export function RecordOrb() {
  const state = useDesk((s) => s.recording);
  const external = useDesk((s) => s.recordingExternal);
  const startedAt = useDesk((s) => s.recordingStartedAt);
  const [elapsed, setElapsed] = useState("");
  const { subscribe } = useRuntimeBus();

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

  useEffect(() => {
    if (state !== "recording" || startedAt == null) {
      setElapsed("");
      return;
    }
    const t = window.setInterval(() => {
      const s = Math.floor((Date.now() - startedAt) / 1000);
      setElapsed(`${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`);
    }, 1000);
    return () => window.clearInterval(t);
  }, [state, startedAt]);

  const recording = state === "recording";
  return (
    <div className="desk-orb-wrap">
      {recording && external && (
        <span className="desk-orb-note">live elsewhere</span>
      )}
      {recording && elapsed && (
        <span className="desk-orb-elapsed">{elapsed}</span>
      )}
      <Button
        variant="chrome"
        className={`desk-orb is-${state}`}
        onClick={() => {
          if (recording) {
            void useDesk.getState().stopRecording();
            return;
          }
          if (state !== "idle") return;
          // PHILO-17: the start opens the new meeting's own window (the
          // live room; on Stop the same window shows the saved meeting).
          void useDesk.getState().startRecording();
        }}
        aria-label={recording ? "Stop recording" : "Record a meeting"}
        title={recording ? "Stop recording" : "Record a meeting"}
        disabled={state === "busy"}
      >
        {/* HS-111-09 — the record key is the 40px system sprite
            (80 device px at DPR 2, exact 2x): Signal Workbench material,
            not the macOS gloss gradient it replaces. */}
        <img
          src={SYSTEM.recordOrb}
          alt=""
          width={40}
          height={40}
          className="desk-orb-face desk-chrome-sprite"
          draggable={false}
        />
      </Button>
    </div>
  );
}
