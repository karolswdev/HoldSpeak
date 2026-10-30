/* Recordings (RECORDINGS-DESIGN-2026-10-28 §2): the dock tile and the
 * menu-bar lamp.
 *
 * The tile sits after the meeting Record key: a flat D screen with a red dot.
 * A press records this view (the browser's picker); a second press stops.
 * While it records the tile wears the Record key's red ring, and its hover
 * label says `Stop screen recording` and the time. The right button opens
 * the Recordings window.
 *
 * The lamp (beside the mic lamp) says `Recording 3:12` and carries Stop, on
 * every view: a recording another view runs says `Recording on another view`. */
import "./recordings.css";
import { useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { LampGadget } from "../surface/gadgets";
import { stateWords } from "../surface/words";
import { useDesk } from "../store";
import { frontWindowId } from "../components/window/windowRegistry";
import { SYSTEM_48 } from "../systemSprites";
import { useCompactViewport } from "../useCompactViewport";
import { canCapture, isLive, liveStartedAt, toggleCapture, stopCapture, useCapture, type CaptureState } from "./capture";
import { lengthWords, useRecordingFrames } from "./api";

/** The project of the window in front, so the recording's Note is filed there. */
export function frontProjectId(): string {
  if (frontWindowId() !== "surface-project-memory") return "";
  const scope = useDesk.getState().windowsById["surface-project-memory"]?.scope;
  return scope?.startsWith("project:") ? scope.slice("project:".length) : "";
}

/** The press of the tile, the lamp's Stop and ⌃⇧R. */
export function pressScreenRecord(): void {
  toggleCapture({ projectId: frontProjectId() });
}

/** The elapsed time of the live recording, each second. */
export function useLiveClock(capture: CaptureState): string | null {
  const started = liveStartedAt(capture);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!started) return;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [started]);
  return started ? lengthWords((now - started) / 1000) : null;
}

function openRecordings(): void {
  void import("../shell").then((m) => m.openSurfaceOr("open-recordings", "/", undefined, { origin: "dock" }));
}

/** The dock tile. On a phone (no screen capture) it shows only while a
 *  recording runs, as its Stop. */
export function ScreenRecordTile({ compact = false }: { compact?: boolean }) {
  const capture = useCapture();
  const clock = useLiveClock(capture);
  const live = isLive(capture);
  if (!live && (compact || !canCapture())) return null;
  const busy = capture.phase === "asking" || capture.phase === "stopping";
  const name = live ? "Stop screen recording" : "Record screen";
  const where = capture.remote ? "on another view" : "";
  return (
    <Button
      variant="chrome"
      data-app="screen-record"
      data-testid="desk-dock-screen-record"
      data-recording={live ? "" : undefined}
      className={`desk-dock-launch desk-dock-app desk-dock-screen-record${live ? " is-run" : ""}`}
      aria-label={`${name}${where ? `, ${where}` : ""}${clock ? `, ${clock}` : ""}`}
      aria-pressed={live}
      disabled={busy}
      onClick={pressScreenRecord}
      onContextMenu={(event) => {
        event.preventDefault();
        openRecordings();
      }}
    >
      <img src={SYSTEM_48.dockScreenRecord} alt="" width={48} height={48} className="desk-dock-sprite" draggable={false} />
      <span className="desk-dock-label" aria-hidden="true">
        {name}
        {live && clock ? (
          <span className="desk-dock-state" data-tone="rec" data-testid="desk-dock-screen-record-clock">{clock}</span>
        ) : (
          <span className="desk-dock-state">⌃⇧R</span>
        )}
      </span>
    </Button>
  );
}

/** The menu-bar lamp; it also keeps this view in step with the others. */
export function ScreenRecordLamp() {
  useRecordingFrames();
  const capture = useCapture();
  const clock = useLiveClock(capture);
  const compact = useCompactViewport();
  if (!isLive(capture)) return null;
  // At 393 the bar has no room for the long words: the lamp and Stop say it.
  // Sentence case through stateWords; recordings.css lifts the lamp's caps.
  const words = stateWords(compact ? "Recording" : capture.remote ? "Recording on another view" : `Recording${clock ? ` ${clock}` : ""}`);
  return (
    <span className="desk-mic-lamp desk-screen-lamp" role="status" data-testid="desk-screen-lamp">
      <LampGadget label={words} on tone="fail" />
      <Button
        dense
        variant="ghost"
        data-testid="desk-screen-lamp-stop"
        disabled={capture.phase === "stopping"}
        onClick={stopCapture}
      >
        Stop
      </Button>
    </span>
  );
}
