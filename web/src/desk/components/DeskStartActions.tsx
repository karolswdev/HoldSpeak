import { Link } from "react-router-dom";
import { workroomHref } from "../../workrooms/context";
import { useDesk } from "../store";
import { DeskCreateMenu } from "./DeskCreateMenu";

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
      <Link
        className="desk-chip desk-start-action"
        to={workroomHref("/dictation", { action: "dictate" })}
      >
        <span aria-hidden="true">⌁</span> Dictate
      </Link>
      <button
        type="button"
        className={
          "desk-chip desk-start-action" +
          (recording === "recording" ? " is-recording" : "")
        }
        disabled={recording === "busy"}
        aria-pressed={recording === "recording"}
        onClick={() =>
          recording === "recording"
            ? void useDesk.getState().stopRecording()
            : void useDesk.getState().startRecording()
        }
      >
        <span className="desk-start-record" aria-hidden="true" />{" "}
        {recording === "recording" ? "Stop" : "Record"}
      </button>
      <DeskCreateMenu />
    </div>
  );
}
