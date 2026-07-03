// HS-78-02: the speak-to-fill mic — hold to talk, release to fill.
//
// Every desk text input carries one (the standing voice-first rule, now on
// the web): press and hold, speak, release; the transcript lands in the
// field through onText with NO confirm step. Capture + transcription live
// in the shared helper (the hub's own local Whisper; nothing egresses).
import { useRef, useState } from "react";
// @ts-ignore — plain ESM shared helper (the one browser-mic call site).
import {
  cancelCapture,
  speakToFillSupported,
  startCapture,
  stopAndTranscribe,
} from "../../scripts/speak-to-fill.js";

export function MicButton({
  onText,
  label = "Hold to talk",
}: {
  onText: (text: string) => void;
  label?: string;
}) {
  const [state, setState] = useState<"idle" | "listening" | "busy" | "failed">("idle");
  const holding = useRef(false);

  if (!speakToFillSupported()) return null;

  const start = async () => {
    holding.current = true;
    try {
      await startCapture();
      if (!holding.current) {
        await cancelCapture();
        return;
      }
      setState("listening");
    } catch {
      setState("failed");
      setTimeout(() => setState("idle"), 1600);
    }
  };

  const stop = async () => {
    holding.current = false;
    if (state !== "listening") return;
    setState("busy");
    try {
      const text = await stopAndTranscribe();
      if (text) onText(text);
      setState("idle");
    } catch {
      setState("failed");
      setTimeout(() => setState("idle"), 1600);
    }
  };

  return (
    <button
      type="button"
      className={`desk-mic is-${state}`}
      title={state === "failed" ? "Mic unavailable" : label}
      aria-label={label}
      onPointerDown={(e) => {
        e.preventDefault();
        e.stopPropagation();
        void start();
      }}
      onPointerUp={(e) => {
        e.stopPropagation();
        void stop();
      }}
      onPointerLeave={() => {
        if (holding.current) void stop();
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <span aria-hidden="true">{state === "busy" ? "…" : "🎙"}</span>
    </button>
  );
}
