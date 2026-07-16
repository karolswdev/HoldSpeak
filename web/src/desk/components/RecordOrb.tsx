// The Record orb (HS-73-06): the product's primary verb lives in the world.
// Bottom-center, iPad parity (the DioAmbientRecorder entry). It drives the
// HUB's recorder via /live's exact calls — never a browser microphone (no
// new plumbing, no new egress). State is honest by construction: seeded
// from /api/state and kept live by the ONE runtime bus; a meeting started
// anywhere (the /live page, the CLI, the iPad) shows here and the orb can
// only stop it — never double-start.
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { useDesk } from "../store";

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
    void apiFetch<any>("/api/state")
      .then((snapshot) =>
        apply(snapshot?.activity || snapshot?.runtime?.activity),
      )
      .catch(() => null);
    return unsub;
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
      <button
        type="button"
        className={`desk-orb is-${state}`}
        onClick={() =>
          recording
            ? void useDesk.getState().stopRecording()
            : state === "idle"
              ? void useDesk.getState().startRecording()
              : undefined
        }
        aria-label={recording ? "Stop recording" : "Record a meeting"}
        title={recording ? "Stop recording" : "Record a meeting"}
        disabled={state === "busy"}
      >
        <span className="desk-orb-core" aria-hidden="true" />
      </button>
    </div>
  );
}
