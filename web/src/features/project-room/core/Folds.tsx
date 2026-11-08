// The Room's folds: the fold itself, the Programs fold and the Files fold.
import React, { useMemo } from "react";
import { StateChip } from "../../../desk/surface";
import { FoldGadget } from "../../../desk/surface/gadgets";
import { RoomProgramRows } from "../../../desk/programs/RoomPrograms";
import { useDesk } from "../../../desk/store";
import { ROOM_CHANGE_KINDS } from "../../../desk/useDeskChangedRefresh";
import { useProjectResourceRefs } from "../../../desk/drawer/useDrawerData";
import { drawerMembers } from "../../../desk/drawer/members";
import { Button } from "../../../components/signal/Signal";
import type { RoomProgramRow, RoomSection } from "../model";
import { RoomFiledNotesSection, type FiledNoteRequest } from "../RoomFiledNotesSection";
import type { useProjectRoomController } from "../useProjectRoomController";

/* ── PHILO-17 refit: a folded section ── */

/** HS-S13 (G13-A), Room fold 2026-11-08: the Programs filed to this
 *  Project, always one fold in the grammar of Files and Sources (the count
 *  only when there is one; open when there are rows). Rows reuse the
 *  Programs list's row (`desk/programs/RoomProgramRows`). None: one muted
 *  line and New program, which opens the Programs window scoped to this
 *  Project. A hub that does not read Programs and a failed or malformed read
 *  each say what they are, never a zero. */
export const ROOM_PROGRAM_CHANGE_KINDS = Object.freeze([...ROOM_CHANGE_KINDS, "program"]);

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

/** A secondary section, folded until asked for (the library FoldGadget).
 *  A fold whose section draws nothing is not drawn (CSS :has). */
export function RoomFold({ title, token, open, testId, children }: {
  title: string;
  token?: number;
  open?: boolean;
  testId: string;
  children: React.ReactNode;
}) {
  return (
    <div className="room-fold" data-testid={testId}>
      <FoldGadget title={title} token={token} open={open}>
        {children}
      </FoldGadget>
    </div>
  );
}

/** The live Room reads only filed refs here. It does not start the drawer's
 * People/agent reads or mount the parked drawer to show one Note section. */
export function RoomFiledNotes({ projectId, ctrl, request, onRequestHandled, presentationReady }: {
  projectId: string;
  ctrl: ReturnType<typeof useProjectRoomController>;
  request: FiledNoteRequest;
  onRequestHandled: (seq: number) => void;
  presentationReady: boolean;
}) {
  const data = useProjectResourceRefs(projectId);
  const items = useDesk((state) => state.items);
  const members = useMemo(() => drawerMembers({ projectId, projectName: ctrl.projectName,
    room: null, meetings: [], decisions: [], artifacts: [], people: [],
    resources: data.resources, flights: [], sessions: [], items,
  }).filter((member) => member.ref.startsWith("note:")), [projectId, ctrl.projectName, data.resources, items]);
  return <RoomFiledNotesSection projectId={projectId} resourceRefs={data.resourceRefs}
    resourcesState={data.resourcesState} refreshResources={data.refreshResources}
    followCurrentResources={data.followCurrentResources}
    members={members} request={request} onRequestHandled={onRequestHandled}
    presentationReady={presentationReady} />;
}
