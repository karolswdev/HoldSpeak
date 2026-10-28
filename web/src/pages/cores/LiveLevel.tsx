/* Live slice 3 (2026-10-28; canvas betterment/canvases/live-direction-2026-10-27.html,
 * direction A): what the hub hears, drawn as the canvas's level bars.
 *
 * Two hub facts, both new to this window:
 * - Before: POST /api/meeting/mic-check (holdspeak/meeting_session/mic_check.py)
 *   — one short sample from the meeting microphone, the macOS grant read
 *   first. The ready sheet's Microphone row shows the level and a word.
 * - During: the `audio_level` frame (source `meeting_mic` / `meeting_system`,
 *   ~15 Hz) and the new `transcript_pass` frame (the engine writes / listens;
 *   how far the saved transcript reaches). The transcript's foot says it.
 *
 * The bars are the kit LedMeter (five segments, the canvas's rising heights in
 * the meeting's kind hue); no transform, the heights are fixed. */
import { useEffect, useRef, useState } from "react";
import { LedMeter } from "../../desk/surface/gadgets";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { transcriptMark } from "./LiveTranscript";

/** The hub's answer to POST /api/meeting/mic-check. */
export type MicCheck = {
  state: "hearing" | "quiet" | "not_allowed" | "not_asked" | "unknown" | "in_use" | "off" | "failed" | string;
  level: number | null;
  permission?: string;
  settings_url?: string;
  device?: string;
  error?: string;
};

/** The `transcript_pass` frame. */
export type TranscriptPass = {
  meeting_id?: string;
  state: "writing" | "listening" | string;
  saved_through?: number;
  saved_at?: string | null;
  every?: number;
};

export function LevelBars({ level, label }: { level: number; label: string }) {
  return (
    <span className="live-level" data-testid="live-level">
      <LedMeter label={label} labelHidden value={level} segments={5} />
    </span>
  );
}

/** A level under this is the room, not a voice (the hub's HEARING_LEVEL). */
const VOICE = 0.1;
/** A source unheard this long is silent. */
const HOLD_MS = 450;

/** The live meeting's level, per source, from the `audio_level` frame. */
function useMeetingLevel(enabled: boolean) {
  const { subscribe } = useRuntimeBus();
  const heard = useRef<Record<string, { level: number; at: number }>>({});
  const [now, setNow] = useState<{ level: number; source: string }>({ level: 0, source: "" });
  useEffect(() => {
    if (!enabled) return;
    let timer = 0;
    const settle = () => {
      const at = Date.now();
      let best = { level: 0, source: "" };
      for (const [source, read] of Object.entries(heard.current)) {
        if (at - read.at > HOLD_MS) continue;
        if (read.level > best.level) best = { level: read.level, source };
      }
      setNow((prev) => (Math.abs(prev.level - best.level) < 0.02 && prev.source === best.source ? prev : best));
      if (best.level > 0) timer = window.setTimeout(settle, HOLD_MS);
    };
    const off = subscribe("audio_level", (frame) => {
      const data = frame.data as { level?: number; source?: string } | number | undefined;
      const level = typeof data === "number" ? data : Number(data?.level ?? 0);
      const source = typeof data === "object" && data ? String(data.source ?? "") : "";
      // Dictation's level is not the meeting's.
      if (!source.startsWith("meeting")) return;
      heard.current[source] = { level: Number.isFinite(level) ? level : 0, at: Date.now() };
      window.clearTimeout(timer);
      settle();
    });
    return () => {
      off();
      window.clearTimeout(timer);
    };
  }, [enabled, subscribe]);
  return now;
}

/** The transcript's foot while it records: the level, Listening or Writing,
 *  who the hub hears, and how far the saved transcript reaches. */
export function LiveListening({
  pass,
  savedThrough,
  micLabel,
  remoteLabel,
  quiet,
  idleWord = "Listening",
}: {
  pass: TranscriptPass | null;
  /** Seconds the saved transcript reaches (the frame, else /api/state). */
  savedThrough: number;
  micLabel: string;
  remoteLabel: string;
  /** Speech not set up: the hub writes nothing, so no Writing word. */
  quiet?: boolean;
  /** The word while no pass writes ("Listening for speech" before the
   *  first line). */
  idleWord?: string;
}) {
  const level = useMeetingLevel(true);
  const writing = !quiet && pass?.state === "writing";
  const who =
    level.level >= VOICE
      ? level.source === "meeting_system"
        ? remoteLabel
        : level.source === "meeting_mic"
          ? micLabel
          : ""
      : "";
  const saved = savedThrough > 0 ? transcriptMark({ start_time: savedThrough }) : "";
  return (
    <span className="live-doc-listen" data-testid="live-listening" data-state={writing ? "writing" : "listening"}>
      <LevelBars level={level.level} label="Meeting level" />
      <span className="live-doc-listen-word">{writing ? "Writing" : idleWord}</span>
      {who ? <span className="live-doc-listen-who" data-testid="live-listening-who">{who}</span> : null}
      {saved ? (
        <span className="live-doc-listen-saved" data-testid="live-saved-through">
          Saved up to {saved}
        </span>
      ) : null}
    </span>
  );
}
