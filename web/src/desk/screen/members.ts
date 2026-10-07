/** PHILO-14 A1 — what the Projects hold, read from the hub, kept once.
 *
 *  A loose object is one no Project holds. The store's primitives carry no
 *  Project, so the screen reads each Project's resources
 *  (`GET /api/projects/{id}/resources`, kind:id refs) and its meetings
 *  (`GET /api/projects/{id}/meetings`), and the people (`GET
 *  /api/people/relationships`, once `/api/people/readiness` says ready).
 *
 *  Astra's P1 on #939: unknown stays unknown. A read that fails is kept as
 *  FAILED, never as an empty list: its Project wears NOT READ and the screen
 *  draws nothing loose whose filing that read would decide. Retry rereads
 *  exactly the failed reads.
 *
 *  One small cache (this module's store): a Project is read again only when
 *  its `updatedAt` changes or the hub says `desk_changed`; reads in flight
 *  are shared, never repeated. */
import { useCallback, useEffect, useMemo } from "react";
import { create } from "zustand";
import { apiFetch } from "../../lib/api";
import { useOnDeskChanged } from "../useDeskChangedRefresh";
import { normalizeRef, type ScreenPerson } from "./compose";

export type MemberRead = "resources" | "meetings";

interface ProjectEntry {
  /** The Project's `updatedAt` this entry was read at. */
  key: string;
  /** The refs each read gave; null = the read failed (unknown). */
  resources: string[] | null;
  meetings: string[] | null;
}

interface PeopleEntry {
  /** ready: the persons are read; locked: the store is not ready (no
   *  persons, nothing unknown); failed: a read failed (unknown). */
  state: "ready" | "locked" | "failed";
  persons: ScreenPerson[];
}

interface MembersState {
  projects: Record<string, ProjectEntry>;
  people: PeopleEntry | null;
}

export const useScreenMembersStore = create<MembersState>(() => ({ projects: {}, people: null }));

const inflight = new Map<string, Promise<void>>();

async function readRefs(projectId: string, which: MemberRead): Promise<string[] | null> {
  const id = encodeURIComponent(projectId);
  try {
    if (which === "resources") {
      const body = await apiFetch<{ resources?: Array<{ resource_ref?: string; deleted?: boolean }> } | null>(
        `/api/projects/${id}/resources`,
      );
      if (!body || !Array.isArray(body.resources)) return null;
      return body.resources
        .filter((row) => row?.resource_ref && !row.deleted)
        .map((row) => normalizeRef(String(row.resource_ref)));
    }
    const body = await apiFetch<{ meetings?: Array<{ id?: string; meeting_id?: string }> } | null>(
      `/api/projects/${id}/meetings`,
    );
    if (!body || !Array.isArray(body.meetings)) return null;
    return body.meetings
      .map((row) => row?.id ?? row?.meeting_id)
      .filter(Boolean)
      .map((mid) => `meeting:${mid}`);
  } catch {
    return null;
  }
}

/** Read `which` of a Project (both by default); a read already out is shared. */
export function loadProject(projectId: string, key: string, which: MemberRead[] = ["resources", "meetings"]): Promise<void> {
  const flight = `${projectId}|${key}|${which.join(",")}`;
  const out = inflight.get(flight);
  if (out) return out;
  const run = Promise.all(which.map((w) => readRefs(projectId, w))).then((results) => {
    useScreenMembersStore.setState((s) => {
      const prev = s.projects[projectId];
      const base: ProjectEntry = prev && prev.key === key ? prev : { key, resources: null, meetings: null };
      const next = { ...base };
      which.forEach((w, i) => {
        next[w] = results[i];
      });
      return { projects: { ...s.projects, [projectId]: next } };
    });
  }).finally(() => inflight.delete(flight));
  inflight.set(flight, run);
  return run;
}

export function loadPeople(): Promise<void> {
  const out = inflight.get("people");
  if (out) return out;
  const run = (async () => {
    let entry: PeopleEntry;
    try {
      const ready = await apiFetch<{ state?: string; readiness?: string } | null>("/api/people/readiness");
      const state = ready?.state ?? ready?.readiness;
      if (!state) entry = { state: "failed", persons: [] };
      else if (state !== "ready") entry = { state: "locked", persons: [] };
      else {
        const body = await apiFetch<{ relationships?: Array<{ id?: string; display_name?: string }> } | null>(
          "/api/people/relationships",
        );
        if (!body || !Array.isArray(body.relationships)) entry = { state: "failed", persons: [] };
        else
          entry = {
            state: "ready",
            persons: body.relationships
              .filter((r) => r?.id && r.display_name)
              .map((r) => ({ id: String(r.id), name: String(r.display_name) })),
          };
      }
    } catch {
      entry = { state: "failed", persons: [] };
    }
    useScreenMembersStore.setState({ people: entry });
  })().finally(() => inflight.delete("people"));
  inflight.set("people", run);
  return run;
}

/** Retry: exactly the reads of this Project that failed. */
export function retryProject(projectId: string): void {
  const entry = useScreenMembersStore.getState().projects[projectId];
  if (!entry) return;
  const failed = (["resources", "meetings"] as const).filter((w) => entry[w] === null);
  if (failed.length) void loadProject(projectId, entry.key, [...failed]);
}

export function retryPeople(): void {
  void loadPeople();
}

/** Test seam. */
export function resetScreenMembers(): void {
  inflight.clear();
  useScreenMembersStore.setState({ projects: {}, people: null });
}

export interface ScreenMembers {
  filed: ReadonlySet<string>;
  persons: ScreenPerson[];
  /** Every Project and People has answered (or failed) once. */
  loaded: boolean;
  /** The Projects with a failed read, and which. */
  notRead: Record<string, MemberRead[]>;
  /** A resources read failed: no object's filing is known. */
  unknownAll: boolean;
  /** A meetings read failed: no meeting's filing is known. */
  unknownMeetings: boolean;
  /** People could not be read. */
  peopleNotRead: boolean;
}

export function useScreenMembers(projects: readonly { id: string; updatedAt?: string | null }[]): ScreenMembers {
  const state = useScreenMembersStore();
  const keyed = useMemo(() => projects.map((p) => ({ id: p.id, key: String(p.updatedAt ?? "") })), [projects]);
  const signature = keyed.map((p) => `${p.id}@${p.key}`).join("|");

  useEffect(() => {
    const cached = useScreenMembersStore.getState().projects;
    for (const p of keyed) {
      if (cached[p.id]?.key !== p.key) void loadProject(p.id, p.key);
    }
    if (!useScreenMembersStore.getState().people) void loadPeople();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature]);

  const rereadAll = useCallback(() => {
    for (const p of keyed) void loadProject(p.id, p.key);
    void loadPeople();
  }, [keyed]);
  useOnDeskChanged(rereadAll);

  return useMemo(() => {
    const filed = new Set<string>();
    const notRead: Record<string, MemberRead[]> = {};
    let loaded = state.people !== null;
    let unknownAll = false;
    let unknownMeetings = false;
    for (const p of keyed) {
      const entry = state.projects[p.id];
      if (!entry || entry.key !== p.key) {
        if (!entry) loaded = false;
        // A changed Project keeps its last read while the new one is out.
      }
      if (!entry) continue;
      const failed: MemberRead[] = [];
      if (entry.resources === null) {
        failed.push("resources");
        unknownAll = true;
      } else entry.resources.forEach((r) => filed.add(r));
      if (entry.meetings === null) {
        failed.push("meetings");
        unknownMeetings = true;
      } else entry.meetings.forEach((r) => filed.add(r));
      if (failed.length) notRead[p.id] = failed;
    }
    const people = state.people;
    return {
      filed,
      persons: people?.persons ?? [],
      loaded,
      notRead,
      unknownAll,
      unknownMeetings,
      peopleNotRead: people?.state === "failed",
    };
  }, [state, keyed]);
}
