import { Link } from "react-router-dom";
import { workroomHref } from "../../workrooms/context";
import { DeskCreateMenu } from "./DeskCreateMenu";

export function DeskStartActions({ compact = false }: { compact?: boolean }) {
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
      <Link
        className="desk-chip desk-start-action"
        to={workroomHref("/live", { action: "record-meeting" })}
      >
        <span className="desk-start-record" aria-hidden="true" /> Record
      </Link>
      <DeskCreateMenu />
    </div>
  );
}
