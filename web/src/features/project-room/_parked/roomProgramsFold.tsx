// PARKED 2026-11-08 (R1 "the brief"): the Room's Programs fold. On Now the
// Programs are one row of What is open (core/Open.tsx), and a press opens
// the Programs window scoped to the Project. Not compiled (tsconfig excludes
// _parked); its imports are as they were in core/Folds.tsx.
import React from "react";
import { StateChip } from "../../../desk/surface";
import { RoomProgramRows } from "../../../desk/programs/RoomPrograms";
import { useDesk } from "../../../desk/store";
import { Button } from "../../../components/signal/Signal";
import type { RoomProgramRow, RoomSection } from "../model";
import { RoomFold } from "../core/Folds";

/** HS-S13 (G13-A), Room fold 2026-11-08: the Programs filed to this
 *  Project, always one fold in the grammar of Files and Sources (the count
 *  only when there is one; open when there are rows). Rows reuse the
 *  Programs list's row (`desk/programs/RoomProgramRows`). None: one muted
 *  line and New program, which opens the Programs window scoped to this
 *  Project. A hub that does not read Programs and a failed or malformed read
 *  each say what they are, never a zero. */

export function RoomProgramsSection({ section, projectId, onRefresh }: {
  section: RoomSection<{ programs: RoomProgramRow[] }> | undefined;
  projectId: string;
  onRefresh: () => void;
}) {
  const rows = section?.state === "ok" ? section.programs : [];
  const failed = section?.state === "degraded";
  let body: React.ReactNode;
  if (rows.length) {
    body = <RoomProgramRows programs={rows} />;
  } else if (section?.state === "ok") {
    body = (
      <div className="room-programs-none">
        <span className="room-empty-line" data-testid="room-programs-empty">No Programs yet</span>
        <Button dense variant="secondary" data-testid="room-programs-new"
          onClick={() => useDesk.getState().openSurfaceWindow("open-programs", `project:${projectId}`)}>
          New program
        </Button>
      </div>
    );
  } else {
    body = (
      <div className="room-programs-none">
        <span data-testid="room-programs-unavailable" data-reason={failed ? section.error_code : "absent"}>
          <StateChip state="unreachable" label={failed ? "PROGRAMS NOT READ" : "NOT READ BY THIS HUB"} />
        </span>
        {failed ? <Button dense variant="secondary" onClick={onRefresh} data-testid="room-programs-refresh">Refresh</Button> : null}
      </div>
    );
  }
  return (
    <RoomFold title="Programs" token={rows.length || undefined} open={rows.length > 0 || failed || undefined}
      testId="room-fold-programs">
      <div className="room-programs">{body}</div>
    </RoomFold>
  );
}

