/** PHILO-14 A2 — the drawer's reads: the Room's data layer (its controller,
 *  its people read) plus the Project's filed refs and the agents in flight.
 *  No new hub route; no second copy of the Room's reads.
 *
 *  A read that fails is never an empty drawer: each failed read is named
 *  (`ROOM`, `DECISIONS`, `PEOPLE`, `RESOURCES` · NOT READ) and Retry re-runs
 *  only those. PHILO-14 A2b: a Room section the hub answered `degraded` is a
 *  failed read too (the Room's decisions name the drawer's decisions). */
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useAgentFlights, useAgentFlightsLive } from "../agentFlights";
import { useDesk } from "../store";
import { useOnDeskChanged } from "../useDeskChangedRefresh";
import { useProjectRoomController } from "../../features/project-room/useProjectRoomController";
import { fetchRoomPeople, type RoomPersonItem } from "../../features/project-room/api";
import { drawerHead, drawerMembers, type DrawerMember, type DrawerReads } from "./members";
import { useDrawers } from "./store";

type Resource = DrawerReads["resources"][number];

/** The reads a drawer makes; the head names each one that failed. */
export type DrawerRead = "ROOM" | "DECISIONS" | "PEOPLE" | "RESOURCES";

export function useDrawerData(projectId: string) {
  const ctrl = useProjectRoomController(`project:${projectId}`, undefined);
  useAgentFlightsLive();
  const flights = useAgentFlights((s) => s.flights);
  const sessions = useAgentFlights((s) => s.sessions);
  const items = useDesk((s) => s.items);
  const revision = useDrawers((s) => s.revision);
  const [people, setPeople] = useState<RoomPersonItem[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [peopleFailed, setPeopleFailed] = useState(false);
  const [resourcesFailed, setResourcesFailed] = useState(false);
  const [tick, setTick] = useState(0);
  useOnDeskChanged(() => setTick((n) => n + 1));

  const readPeople = useCallback(() => {
    return fetchRoomPeople(projectId).then(
      (rows) => {
        setPeople(rows);
        setPeopleFailed(false);
      },
      () => setPeopleFailed(true), // the last read stays on the glass
    );
  }, [projectId]);
  const readResources = useCallback(() => {
    return apiFetch<{ resources?: Resource[] }>(`/api/projects/${encodeURIComponent(projectId)}/resources`).then(
      (body) => {
        setResources(Array.isArray(body?.resources) ? body.resources : []);
        setResourcesFailed(false);
      },
      () => setResourcesFailed(true),
    );
  }, [projectId]);

  useEffect(() => {
    void readPeople();
    void readResources();
  }, [readPeople, readResources, revision, tick]);

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
  const decisionsFailed = !ctrl.error && ctrl.room?.decisions.state === "degraded";
  const failed = useMemo<DrawerRead[]>(
    () => [
      ...(ctrl.error ? (["ROOM"] as const) : []),
      ...(decisionsFailed ? (["DECISIONS"] as const) : []),
      ...(peopleFailed ? (["PEOPLE"] as const) : []),
      ...(resourcesFailed ? (["RESOURCES"] as const) : []),
    ],
    [ctrl.error, decisionsFailed, peopleFailed, resourcesFailed],
  );
  /** Retry re-runs exactly the reads that failed (a Room section: the Room). */
  const retry = () => {
    if (ctrl.error || decisionsFailed) void ctrl.load();
    if (peopleFailed) void readPeople();
    if (resourcesFailed) void readResources();
  };
  return {
    name: ctrl.projectName,
    /** Phase 16: the Room's read (its sources), for the Room window's
     *  Sources section. */
    room: ctrl.room,
    loading: ctrl.loadStatus === "loading" && !ctrl.room,
    failed,
    retry,
    head,
    members,
  };
}
