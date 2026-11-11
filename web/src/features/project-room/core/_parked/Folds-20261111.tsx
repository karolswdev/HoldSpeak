// @ts-nocheck
// Parked 2026-11-11: Files is a view; the Room has no folds.
// The Room's folds: the fold itself and the Files fold (the Programs fold is
// parked: _parked/roomProgramsFold.tsx).
import React, { useMemo } from "react";
import { FoldGadget } from "../../../desk/surface/gadgets";
import { useDesk } from "../../../desk/store";
import { ROOM_CHANGE_KINDS } from "../../../desk/useDeskChangedRefresh";
import { useProjectResourceRefs } from "../../../desk/drawer/useDrawerData";
import { drawerMembers } from "../../../desk/drawer/members";
import { RoomFiledNotesSection, type FiledNoteRequest } from "../RoomFiledNotesSection";
import type { useProjectRoomController } from "../useProjectRoomController";

/* ── PHILO-17 refit: a folded section ── */

/** A desk change of these kinds re-reads the Room (Programs too). */
export const ROOM_PROGRAM_CHANGE_KINDS = Object.freeze([...ROOM_CHANGE_KINDS, "program"]);

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
