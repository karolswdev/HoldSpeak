/** One display protocol (2026-11-08): the compositor's listener. The hub's
 * `desk_request` frame (an agent's `desk.mark`, `desk.press`, `desk.say`,
 * `desk.scroll`) runs through the one executor (`requests.ts`, the Walk's
 * too) and its answer goes back to the hub. The mark is the Walk's halo on
 * the part; words are the Walk's caption line. Without a bus (a component
 * test with no provider) it listens to nothing. */
import { createPortal } from "react-dom";
import { Button } from "../../components/signal/Signal";
import { WorkMenu } from "../components/DeskMenu";
import { restoreWindowUndo, WindowUndoStale } from "../windowUndo";
import type { WindowUndo } from "../used";
import { useEffect, useRef, useState } from "react";
import { useBusSubscribe } from "../useDeskChangedRefresh";
import { MARK_MS, deskAppName, executeDeskRequest, postDeskResult, type DeskStage, type DeskResult } from "./requests";

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

interface UndoOffer { value: WindowUndo; label: string }

interface RequestFrame {
  request_id?: unknown;
  op?: unknown;
  args?: unknown;
}

export function DeskRequests() {
  const subscribe = useBusSubscribe();
  const [words, setWords] = useState("");
  const [shown, setShown] = useState(false);
  const [undo, setUndo] = useState<UndoOffer | null>(null);
  const latestUndo = useRef<UndoOffer | null>(null);
  const [undoError, setUndoError] = useState("");
  const [undoMenu, setUndoMenu] = useState<{x: number; y: number} | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!undo) return;
    const timer = setTimeout(() => setUndo((now) => now === undo ? null : now), 8000);
    return () => clearTimeout(timer);
  }, [undo]);
  const requests = useRef(new Map<string, Promise<DeskResult>>());
  useEffect(() => {
    if (!subscribe) return;
    let clear: ReturnType<typeof setTimeout> | undefined;
    let hide: ReturnType<typeof setTimeout> | undefined;
    const stage: DeskStage = {
      async undo(args) {
        const windows = Array.isArray(args.windows) ? args.windows as WindowUndo["windows"] : [];
        const names = await Promise.all(windows.map(async (item) => {
          const appName = await deskAppName(item.id);
          if (appName !== item.id) return appName;
          const { windowRegistry } = await import("../components/window/windowRegistry");
          const named = windowRegistry.get(item.id)?.label;
          if (named) return named;
          const { PRIMITIVES } = await import("../../lib/primitives");
          const kind = item.id.startsWith("pullout:") ? item.id.split(":")[1] : "";
          return PRIMITIVES[kind as keyof typeof PRIMITIVES]?.label ?? "Window";
        }));
        let verb = ({ open: "Open", close: "Close", raise: "Raise", send_back: "Send back",
          seat: "Seat", zoom: "Zoom", move: "Move", resize: "Resize", set_geometry: "Place",
          arrange: "Arrange", stage_shelf: "Move Stage shelf" } as Record<string, string>)[String(args.verb)] ?? "Change windows";
        if (args.verb === "seat" && windows[0]?.after?.minimized === false) verb = "Show";
        if (args.verb === "zoom" && (windows[0]?.after as { zoomed?: boolean })?.zoomed === false) verb = "Restore size";
        const offer = { value: { group: "desk", ...args, windows }, label: `${verb}${names.length > 1 ? " windows" : names.length ? ` ${names[0]}` : ""}` };
        latestUndo.current = offer;
        setUndoMenu(null);
        setUndo(offer);
        setUndoError("");
      },
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
      let result = requests.current.get(requestId);
      if (!result) {
        result = executeDeskRequest({ op: data.op, args }, stage)
          .catch((cause) => ({ done: false, reason: cause instanceof Error ? cause.message : "The desk did not do this request. Send it again." }));
        requests.current.set(requestId, result);
        // Match the hub's in-memory request retention. A replay posts the
        // same answer and never repeats a voice or a press.
        if (requests.current.size > 50) requests.current.delete(requests.current.keys().next().value!);
      }
      void result.then((answer) => postDeskResult(requestId, answer))
        .catch(() => undefined);
    });
    return () => {
      clearTimeout(clear);
      clearTimeout(hide);
      if (typeof unsubscribe === "function") unsubscribe();
    };
  }, [subscribe]);
  const runUndo = () => {
    if (!undo || busy) return;
    const entry = undo;
    setBusy(true);
    void restoreWindowUndo(entry.value).then(() => setUndo(now => now === entry ? null : now))
      .catch(cause => {
        if (latestUndo.current === entry) setUndoError(cause instanceof WindowUndoStale
          ? cause.message : "Undo could not be checked. Work kept. Try again.");
      })
      .finally(() => setBusy(false));
  };
  if (!shown && !undo) return null;
  const undoSlot = document.getElementById("desk-window-undo-slot");
  return (
    <>
      {shown ? <div className="walk-layer" data-walk="" data-testid="desk-requests">
        <div className="walk-caption-slot">
          <Caption text={words} testId="desk-request-words" />
        </div>
      </div> : null}
      {undo && undoSlot ? createPortal(<div className="desk-window-undo" role="status"
        aria-label={undoError || undo.label} title={undoError || undo.label}
        onContextMenu={event => {event.preventDefault(); setUndoMenu({x:event.clientX,y:event.clientY});}}>
        <span>{undoError || undo.label}</span>
        <Button variant="chrome" disabled={busy} data-testid="desk-window-undo"
          aria-label={`Undo: ${undo.label}`} onClick={runUndo}>Undo</Button>
        {undoMenu ? <WorkMenu label="Window receipt" x={undoMenu.x} y={undoMenu.y}
          entries={[
            ...(undoError ? [{type: "note" as const, id: "failure", label: undoError}] : []),
            {type: "item", id: "undo", label: `Undo: ${undo.label}`, ghost: busy ? "Undo is running" : undefined, onSelect: runUndo},
          ]} onClose={() => setUndoMenu(null)} /> : null}
      </div>, undoSlot) : null}
    </>
  );
}
