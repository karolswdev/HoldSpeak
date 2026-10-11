import { openSurfaceOr } from "../shell";
import { useDesk } from "../store";
import { DeskCreateMenu } from "./DeskCreateMenu";
import { Button } from "../../components/signal/Signal";

export function DeskStartActions({ compact = false }: { compact?: boolean }) {
  // One Record verb (UX remediation): the chip drives the same hub
  // recorder the orb does and mirrors its state; the /live room remains
  // reachable from the room menu for the full meeting view.
  const recording = useDesk((s) => s.recording);
  return (
    <div
      className={`desk-start-actions${compact ? " is-compact" : ""}`}
      role="group"
      aria-label="Daily starts"
    >
      <Button
        variant="chrome"
        className="desk-chip desk-start-action"
        onClick={() => openSurfaceOr("dictate", "/dictation")}
      >
        <span aria-hidden="true">⌁</span> Dictate
      </Button>
      <Button
        variant="chrome"
        className={
          "desk-chip desk-start-action" +
          (recording === "recording" ? " is-recording" : "")
        }
        disabled={recording === "busy"}
        aria-pressed={recording === "recording"}
        onClick={() => {
          if (recording === "recording") {
            void useDesk.getState().stopRecording();
            return;
          }
          // PHILO-17: the start opens the new meeting's own window (the
          // live room; on Stop the same window shows the saved meeting).
          void useDesk.getState().startRecording();
        }}
      >
        <span className="desk-start-record" aria-hidden="true" />{" "}
        {recording === "recording" ? "Stop" : "Record"}
      </Button>
      <DeskCreateMenu />
    </div>
  );
}
