/** One display protocol (2026-11-08): the compositor's listener. The hub's
 * `desk_request` frame (an agent's `desk.mark`, `desk.press`, `desk.say`,
 * `desk.scroll`) runs through the one executor (`requests.ts`, the Walk's
 * too) and its answer goes back to the hub. The mark is the Walk's halo on
 * the part; words are the Walk's caption line. Without a bus (a component
 * test with no provider) it listens to nothing. */
import { useEffect, useRef, useState } from "react";
import { useBusSubscribe } from "../useDeskChangedRefresh";
import { MARK_MS, executeDeskRequest, postDeskResult, type DeskStage } from "./requests";

/** The caption's fade out. */
export const CAPTION_OUT_MS = 200;

/** How long a line of words stays: at least the mark's time, about a
 * reading pace for a longer line. */
export function wordsMs(words: string): number {
  return Math.min(8000, Math.max(MARK_MS, 1200 + words.length * 40));
}

/** The guide's caption: one line at the bottom edge that fades in with its
 * words and out when they change (the Walk's, and an agent's words). */
export function Caption({ text, testId }: { text: string; testId: string }) {
  const [leaving, setLeaving] = useState("");
  const last = useRef(text);
  useEffect(() => {
    if (last.current === text) return;
    const before = last.current;
    last.current = text;
    if (!before) return;
    setLeaving(before);
    const timer = setTimeout(() => setLeaving(""), CAPTION_OUT_MS);
    return () => clearTimeout(timer);
  }, [text]);
  return (
    <>
      {leaving && leaving !== text ? (
        <p className="walk-caption" data-leaving="" aria-hidden="true">{leaving}</p>
      ) : null}
      {text ? (
        <p key={text} className="walk-caption" role="status" aria-live="polite" data-testid={testId}>
          {text}
        </p>
      ) : null}
    </>
  );
}

interface RequestFrame {
  request_id?: unknown;
  op?: unknown;
  args?: unknown;
}

export function DeskRequests() {
  const subscribe = useBusSubscribe();
  const [words, setWords] = useState("");
  const [shown, setShown] = useState(false);
  useEffect(() => {
    if (!subscribe) return;
    let clear: ReturnType<typeof setTimeout> | undefined;
    let hide: ReturnType<typeof setTimeout> | undefined;
    const stage: DeskStage = {
      say(line) {
        clearTimeout(clear);
        clearTimeout(hide);
        setShown(true);
        setWords(line);
        clear = setTimeout(() => {
          setWords("");
          hide = setTimeout(() => setShown(false), CAPTION_OUT_MS);
        }, wordsMs(line));
      },
    };
    const unsubscribe = subscribe("desk_request", (frame) => {
      const data = (frame?.data ?? {}) as RequestFrame;
      if (typeof data.request_id !== "string" || typeof data.op !== "string") return;
      const requestId = data.request_id;
      const args = data.args && typeof data.args === "object" ? (data.args as Record<string, unknown>) : {};
      void executeDeskRequest({ op: data.op, args }, stage)
        .catch((cause) => ({ done: false, reason: cause instanceof Error ? cause.message : "The desk could not do it" }))
        .then((result) => postDeskResult(requestId, result))
        .catch(() => undefined);
    });
    return () => {
      clearTimeout(clear);
      clearTimeout(hide);
      if (typeof unsubscribe === "function") unsubscribe();
    };
  }, [subscribe]);
  if (!shown) return null;
  return (
    <div className="walk-layer" data-walk="" data-testid="desk-requests">
      <div className="walk-caption-slot">
        <Caption text={words} testId="desk-request-words" />
      </div>
    </div>
  );
}
