/* First run C1 — the first take: one sentence through the real dictation
 * path (`/ws/dictation/stream`, the same session FirstWords uses), heard
 * back, kept as a note through the note producer (`POST /api/notes`).
 *
 * Play plays this browser's own capture of the take (`StreamSession.audio`,
 * the retained PCM that never leaves the device). The hub keeps no audio
 * of a dictation; when the browser has none either (past the retain cap, or
 * a retry of recovered audio), Play is withheld (UX-CANON A11). */
import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import {
  dictationFailure,
  streamFailure,
  type DictationFailure,
} from "../../lib/dictationRecovery";
import { retryPendingTranscription } from "../../lib/speakToFill";
import {
  micStreamSupported,
  startStreamSession,
  subscribeCaptureLevel,
  type StreamSession,
} from "../../lib/micStreamSession";
import {
  clearFirstValueKeepNoteId,
  firstValueKeepNoteId,
  FirstValueTracker,
  stageFirstValueNoteOpen,
} from "../firstValue";

/** The retain scope FirstWords uses: a failed take is retried from it. */
const SCOPE = "first-words";

export type TakeState = "idle" | "listening" | "writing" | "heard" | "failed";

export interface Take {
  text: string;
  seconds: number | null;
  at: string;
  audio: ArrayBuffer | null;
}

function clock(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
}

/** 16 kHz mono 16-bit: the WAV's data bytes over 32000 per second. */
function wavSeconds(wav: ArrayBuffer | null): number | null {
  if (!wav || wav.byteLength <= 44) return null;
  return (wav.byteLength - 44) / 32000;
}

export function useFirstTake({
  onHandoff,
}: {
  onHandoff: (disposition: "completed" | "dismissed") => Promise<void>;
}) {
  const [state, setState] = useState<TakeState>("idle");
  const [take, setTake] = useState<Take | null>(null);
  const [failure, setFailure] = useState<DictationFailure | null>(null);
  const [level, setLevel] = useState(0);
  const [keeping, setKeeping] = useState(false);
  const [message, setMessage] = useState("");
  const [playing, setPlaying] = useState(false);
  const session = useRef<StreamSession | null>(null);
  const streamFailed = useRef<DictationFailure | null>(null);
  const started = useRef(0);
  const starting = useRef(false);
  const tracker = useRef<FirstValueTracker | null>(null);
  if (!tracker.current) tracker.current = new FirstValueTracker();
  const player = useRef<HTMLAudioElement | null>(null);
  const playerUrl = useRef("");

  useEffect(() => {
    if (state !== "listening") return;
    return subscribeCaptureLevel((next) => setLevel(next));
  }, [state]);

  useEffect(
    () => () => {
      session.current?.cancel();
      player.current?.pause();
      if (playerUrl.current) URL.revokeObjectURL(playerUrl.current);
    },
    [],
  );

  const fail = useCallback((category: DictationFailure) => {
    setFailure(category);
    setState("failed");
    void tracker.current?.finish("failure", category).catch(() => undefined);
  }, []);

  const heard = useCallback(
    (raw: string, audio: ArrayBuffer | null) => {
      const text = raw.trim();
      if (!text) {
        fail("no_speech");
        return;
      }
      const seconds = wavSeconds(audio) ?? (started.current ? (Date.now() - started.current) / 1000 : null);
      setTake({ text, seconds, at: clock(new Date()), audio });
      setFailure(null);
      setState("heard");
      void tracker.current?.event("transcript_received");
    },
    [fail],
  );

  const begin = useCallback(async () => {
    if (starting.current) return;
    starting.current = true;
    setFailure(null);
    setMessage("");
    setTake(null);
    streamFailed.current = null;
    try {
      await tracker.current?.start("this_machine");
      const recovered = await retryPendingTranscription(SCOPE);
      if (recovered !== null) {
        heard(recovered, null);
        return;
      }
      const next = await startStreamSession(
        (event) => {
          if (event.type !== "error") return;
          const category = streamFailure(event);
          streamFailed.current = category;
          fail(category);
          const active = session.current;
          if (active) {
            session.current = null;
            active.cancel();
          }
        },
        { retainScope: SCOPE },
      );
      session.current = next;
      started.current = Date.now();
      setLevel(0);
      setState("listening");
      void tracker.current?.event("capture_started");
    } catch (error) {
      fail(dictationFailure(error));
    } finally {
      starting.current = false;
    }
  }, [fail, heard]);

  const stop = useCallback(async () => {
    const active = session.current;
    if (!active) return;
    session.current = null;
    setState("writing");
    void tracker.current?.event("capture_released");
    try {
      const text = await active.stop();
      if (streamFailed.current) return;
      heard(text, active.audio?.() ?? null);
    } catch (error) {
      fail(dictationFailure(error));
    }
  }, [fail, heard]);

  const play = useCallback(() => {
    const audio = take?.audio;
    if (!audio) return;
    if (!player.current) {
      if (playerUrl.current) URL.revokeObjectURL(playerUrl.current);
      playerUrl.current = URL.createObjectURL(new Blob([audio], { type: "audio/wav" }));
      player.current = new Audio(playerUrl.current);
      player.current.onended = () => setPlaying(false);
      player.current.onpause = () => setPlaying(false);
    }
    player.current.currentTime = 0;
    setPlaying(true);
    void player.current.play().catch(() => setPlaying(false));
  }, [take]);

  const again = useCallback(() => {
    player.current?.pause();
    player.current = null;
    void begin();
  }, [begin]);

  /** The heard sentence becomes a real note, then the normal Desk opens on it. */
  const keep = useCallback(async () => {
    if (!take || keeping) return;
    setKeeping(true);
    setMessage("");
    void tracker.current?.event("keep_selected");
    try {
      const noteId = firstValueKeepNoteId();
      const result = await apiFetch<{ note?: { id?: string } }>("/api/notes", {
        method: "POST",
        json: { id: noteId, title: "First dictation", body_markdown: take.text, tags: ["dictation"] },
      });
      stageFirstValueNoteOpen(`note:${String(result.note?.id || noteId)}`);
      await tracker.current?.finish("success").catch(() => undefined);
      await onHandoff("completed");
      clearFirstValueKeepNoteId();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setKeeping(false);
    }
  }, [take, keeping, onHandoff]);

  /** Continue later keeps a heard, unkept sentence first (custody). */
  const leave = useCallback(async () => {
    if (keeping) return;
    setKeeping(true);
    setMessage("");
    void tracker.current?.event("continue_later_selected");
    session.current?.cancel();
    session.current = null;
    try {
      if (take) {
        const noteId = firstValueKeepNoteId();
        const result = await apiFetch<{ note?: { id?: string } }>("/api/notes", {
          method: "POST",
          json: { id: noteId, title: "First dictation", body_markdown: take.text, tags: ["dictation"] },
        });
        stageFirstValueNoteOpen(`note:${String(result.note?.id || noteId)}`);
      }
      await onHandoff("dismissed");
      if (take) clearFirstValueKeepNoteId();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setKeeping(false);
    }
  }, [take, keeping, onHandoff]);

  return {
    leave,
    state,
    take,
    failure,
    level,
    keeping,
    message,
    playing,
    supported: micStreamSupported(),
    begin,
    stop,
    play,
    again,
    keep,
    canPlay: Boolean(take?.audio),
  };
}
