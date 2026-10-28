/** PHILO-14 A2 — the drawer's reads: the Room's data layer (its controller,
 *  its people read) plus the Project's filed refs and the agents in flight.
 *  No new hub route; no second copy of the Room's reads.
 *
 *  A read that fails is never an empty drawer: each failed read is named
 *  (`ROOM`, `DECISIONS`, `PEOPLE`, `RESOURCES` · NOT READ) and Retry re-runs
 *  only those. PHILO-14 A2b: a Room section the hub answered `degraded` is a
 *  failed read too (the Room's decisions name the drawer's decisions). */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useAgentFlights, useAgentFlightsLive } from "../agentFlights";
import { useDesk } from "../store";
import { PEOPLE_CHANGE_KINDS, ROOM_CHANGE_KINDS, useOnDeskChanged } from "../useDeskChangedRefresh";
import { useProjectRoomController } from "../../features/project-room/useProjectRoomController";
import { fetchRoomPeople, type RoomPersonItem } from "../../features/project-room/api";
import { drawerHead, drawerMembers, type DrawerMember, type DrawerReads } from "./members";
import { useDrawers } from "./store";

type Resource = DrawerReads["resources"][number];
export type ResourcesState = "loading" | "ok" | "failed";
export type ResourcesRead = { state: "ok"; refs: string[] } | { state: "failed" } | { state: "stale" };

/** The reads a drawer makes; the head names each one that failed. */
export type DrawerRead = "ROOM" | "DECISIONS" | "PEOPLE" | "RESOURCES";

export function useDrawerData(projectId: string) {
  const ctrl = useProjectRoomController(`project:${projectId}`, undefined);
  const revision = useDrawers((s) => s.revision);
  const [tick, setTick] = useState(0);
  useOnDeskChanged(() => setTick((n) => n + 1), ROOM_CHANGE_KINDS);
  useEffect(() => {
    if (revision || tick) void ctrl.load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [revision, tick]);
  return useDrawerMembers(projectId, ctrl);
}

/** Shared membership read. The active Room needs only this resource route;
 * it must not start the drawer's People and agent reads just to show Notes. */
export function useProjectResourceRefs(projectId: string) {
  const revision = useDrawers((s) => s.revision);
  const [resources, setResources] = useState<Resource[]>([]);
  const [resourcesState, setResourcesState] = useState<ResourcesState>("loading");
  const [firstRead, setFirstRead] = useState(false);
  const resourceRead = useRef<{ generation: number; controller: AbortController | null }>({ generation: 0, controller: null });
  const currentRead = useRef<Promise<ResourcesRead> | null>(null);
  const [tick, setTick] = useState(0);
  useOnDeskChanged(() => setTick((n) => n + 1), [...ROOM_CHANGE_KINDS, "repository", "thought"]);
  const refreshResources = useCallback((): Promise<ResourcesRead> => {
    const generation = ++resourceRead.current.generation;
    resourceRead.current.controller?.abort();
    const controller = new AbortController();
    resourceRead.current.controller = controller;
    setResourcesState("loading");
    const read = (async (): Promise<ResourcesRead> => { try {
      const body = await apiFetch<{ resources?: Resource[] }>(
        `/api/projects/${encodeURIComponent(projectId)}/resources`, { signal: controller.signal },
      );
      if (controller.signal.aborted || resourceRead.current.generation !== generation) return { state: "stale" };
      if (!Array.isArray(body?.resources)) throw new Error("Resources were not read");
      setResources(body.resources);
      setResourcesState("ok");
      return { state: "ok", refs: body.resources.filter((row) => !row.deleted && typeof row.resource_ref === "string").map((row) => row.resource_ref) };
    } catch {
      if (controller.signal.aborted || resourceRead.current.generation !== generation) return { state: "stale" };
      // Retain the last successful material; it is never proof of current membership.
      setResourcesState("failed");
      return { state: "failed" };
    } })();
    currentRead.current = read;
    return read;
  }, [projectId]);
  /** A stale result means a newer read owns the answer. Follow that exact
   * in-flight read, including later supersessions, without starting reads. */
  const followCurrentResources = useCallback(async (result: ResourcesRead): Promise<ResourcesRead> => {
    let answer = result;
    while (answer.state === "stale") {
      const current = currentRead.current;
      if (!current) return answer; // unmounted scope
      answer = await current;
      if (current === currentRead.current && answer.state === "stale") return answer;
    }
    return answer;
  }, []);
  useEffect(() => () => {
    resourceRead.current.generation += 1;
    resourceRead.current.controller?.abort();
    currentRead.current = null;
  }, []);
  useEffect(() => {
    void refreshResources().then((result) => {
      if (result.state !== "stale") setFirstRead(true);
    });
  }, [refreshResources, revision, tick]);
  const resourceRefs = useMemo(
    () => resources.filter((row) => !row.deleted && typeof row.resource_ref === "string").map((row) => row.resource_ref),
    [resources],
  );
  return { resources, resourceRefs, resourcesState, refreshResources, followCurrentResources, firstRead };
}

/** PHILO-17 U30: the drawer's objects over the Room controller its caller
 * holds; raw resource refs remain available even when cache-derived members
 * omit a filed Note. */
export function useDrawerMembers(projectId: string, ctrl: ReturnType<typeof useProjectRoomController>) {
  useAgentFlightsLive();
  const flights = useAgentFlights((s) => s.flights);
  const sessions = useAgentFlights((s) => s.sessions);
  const flightsSettled = useAgentFlights((s) => s.settled);
  const items = useDesk((s) => s.items);
  const revision = useDrawers((s) => s.revision);
  const [people, setPeople] = useState<RoomPersonItem[]>([]);
  const [peopleFailed, setPeopleFailed] = useState(false);
  const [tick, setTick] = useState(0);
  useOnDeskChanged(() => setTick((n) => n + 1), PEOPLE_CHANGE_KINDS);
  const { resources, resourceRefs, resourcesState, refreshResources, firstRead: resourcesFirstRead } = useProjectResourceRefs(projectId);

  const readPeople = useCallback(() => {
    return fetchRoomPeople(projectId).then(
      (rows) => {
        setPeople(rows);
        setPeopleFailed(false);
      },
      () => setPeopleFailed(true), // the last read stays on the glass
    );
  }, [projectId]);
  const [peopleFirstRead, setPeopleFirstRead] = useState(false);
  useEffect(() => {
    void readPeople().then(() => setPeopleFirstRead(true));
  }, [readPeople, revision, tick]);

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
      ...(resourcesState === "failed" ? (["RESOURCES"] as const) : []),
    ],
    [ctrl.error, decisionsFailed, peopleFailed, resourcesState],
  );
  /** Retry re-runs exactly the reads that failed (a Room section: the Room). */
  const retry = () => {
    if (ctrl.error || decisionsFailed) void ctrl.load();
    if (peopleFailed) void readPeople();
    if (resourcesState === "failed") void refreshResources();
  };
  return {
    name: ctrl.projectName,
    /** Phase 16: the Room's read (its sources), for the Room window's
     *  Sources section. */
    room: ctrl.room,
    loading: ctrl.loadStatus === "loading" && !ctrl.room,
    /** Every read the members come from has resolved once. */
    settled: peopleFirstRead && resourcesFirstRead && flightsSettled && ctrl.detailStatus === "ready",
    failed,
    retry,
    resourceRefs,
    resourcesState,
    refreshResources,
    head,
    members,
  };
}
