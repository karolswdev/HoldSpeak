// The Record orb (HS-73-06): the product's primary verb lives in the world.
// Bottom-center, iPad parity (the DioAmbientRecorder entry). It drives the
// HUB's recorder via /live's exact calls — never a browser microphone (no
// new plumbing, no new egress). State is honest by construction: seeded
// from /api/state and kept live by the ONE runtime bus; a meeting started
// anywhere (the /live page, the CLI, the iPad) shows here and the orb can
// only stop it — never double-start.
import { useEffect, useRef, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { useDesk } from "../store";

type OrbState = "idle" | "recording" | "busy";

export function RecordOrb() {
  const [state, setState] = useState<OrbState>("idle");
  const [external, setExternal] = useState(false);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [elapsed, setElapsed] = useState("");
  const meetingsBefore = useRef<Set<string>>(new Set());
  const { refresh, markNew } = useDesk.getState();
  const { subscribe } = useRuntimeBus();

  // Live truth: any meeting_live/runtime_activity frame flips the orb.
  useEffect(() => {
    const apply = (activity: any) => {
      if (!activity || typeof activity !== "object") return;
      const s = String(activity.state || "").toLowerCase();
      if (s === "meeting_live") {
        setState((prev) => {
          if (prev !== "recording") {
            setExternal(true); // it started somewhere else
            setStartedAt((t) => t ?? Date.now());
          }
          return "recording";
        });
      } else if (s === "idle" || s === "complete") {
        setState((prev) => (prev === "recording" ? "idle" : prev));
        setStartedAt(null);
        setExternal(false);
      }
    };
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

  const start = async () => {
    setState("busy");
    meetingsBefore.current = new Set(
      useDesk.getState().items.meeting.map((m) => String(m.id)),
    );
    try {
      // /live's exact call — the hub's recorder, never a browser mic.
      await apiFetch("/api/meeting/start", { method: "POST" });
      setExternal(false);
      setStartedAt(Date.now());
      setState("recording");
    } catch {
      setState("idle");
    }
  };

  const stop = async () => {
    setState("busy");
    try {
      await apiFetch("/api/meeting/stop", { method: "POST" });
    } catch {
      /* the state frame settles the orb either way */
    }
    setStartedAt(null);
    setExternal(false);
    setState("idle");
    // The finished meeting materializes as an object in front of you.
    await refresh();
    const after = useDesk.getState().items.meeting.map((m) => String(m.id));
    const fresh = after.find((id) => !meetingsBefore.current.has(id));
    if (fresh) markNew(fresh);
  };

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
          recording ? void stop() : state === "idle" ? void start() : undefined
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
