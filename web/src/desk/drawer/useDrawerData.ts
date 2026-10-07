/** PHILO-14 A2 — the drawer's reads: the Room's data layer (its controller,
 *  its people read) plus the Project's filed refs and the agents in flight.
 *  No new hub route; no second copy of the Room's reads. */
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useAgentFlights, useAgentFlightsLive } from "../agentFlights";
import { useDesk } from "../store";
import { useOnDeskChanged } from "../useDeskChangedRefresh";
import { useProjectRoomController } from "../../features/project-room/useProjectRoomController";
import { fetchRoomPeople, type RoomPersonItem } from "../../features/project-room/api";
import { drawerHead, drawerMembers, type DrawerMember, type DrawerReads } from "./members";
import { useDrawers } from "./store";

type Resource = DrawerReads["resources"][number];

export function useDrawerData(projectId: string) {
  const ctrl = useProjectRoomController(`project:${projectId}`, undefined);
  useAgentFlightsLive();
  const flights = useAgentFlights((s) => s.flights);
  const sessions = useAgentFlights((s) => s.sessions);
  const items = useDesk((s) => s.items);
  const revision = useDrawers((s) => s.revision);
  const [people, setPeople] = useState<RoomPersonItem[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [tick, setTick] = useState(0);
  useOnDeskChanged(() => setTick((n) => n + 1));

  useEffect(() => {
    let live = true;
    // Each read stands alone: one that fails leaves the others on the glass.
    void fetchRoomPeople(projectId).then((rows) => live && setPeople(rows)).catch(() => undefined);
    void apiFetch<{ resources?: Resource[] }>(`/api/projects/${encodeURIComponent(projectId)}/resources`)
      .then((body) => live && setResources(Array.isArray(body?.resources) ? body.resources : []))
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, [projectId, revision, tick]);

  useEffect(() => {
    if (revision || tick) void ctrl.load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [revision, tick]);

  const members = useMemo<DrawerMember[]>(
    () =>
      drawerMembers({
        projectId,
        projectName: ctrl.projectName,
        room: ctrl.room,
        meetings: ctrl.meetings,
        decisions: ctrl.decisions,
        artifacts: ctrl.artifacts,
        people,
        resources,
        flights,
        sessions,
        items,
      }),
    [projectId, ctrl.projectName, ctrl.room, ctrl.meetings, ctrl.decisions, ctrl.artifacts, people, resources, flights, sessions, items],
  );
  const head = useMemo(() => drawerHead(ctrl.room), [ctrl.room]);
  return {
    name: ctrl.projectName,
    loading: ctrl.loadStatus === "loading" && !ctrl.room,
    error: ctrl.error,
    reload: () => void ctrl.load(),
    head,
    members,
  };
}
