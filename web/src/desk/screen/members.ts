/** PHILO-14 A1 — what the Projects hold, read from the hub.
 *
 *  A loose object is one no Project holds. The store's primitives carry no
 *  Project, so the screen reads each Project's resources
 *  (`GET /api/projects/{id}/resources`, kind:id refs) and its meetings
 *  (`GET /api/projects/{id}/meetings`), and the people (`GET
 *  /api/people/relationships`, once `/api/people/readiness` says ready): a
 *  person no Project names is loose. A
 *  read that fails holds nothing back: its Project files nothing. */
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { normalizeRef, type ScreenPerson } from "./compose";

export interface ScreenMembers {
  filed: ReadonlySet<string>;
  persons: ScreenPerson[];
  loaded: boolean;
}

const EMPTY: ScreenMembers = { filed: new Set(), persons: [], loaded: false };

async function projectRefs(projectId: string): Promise<string[]> {
  const id = encodeURIComponent(projectId);
  const [resources, meetings] = await Promise.all([
    apiFetch<{ resources?: Array<{ resource_ref?: string; deleted?: boolean }> } | null>(`/api/projects/${id}/resources`)
      .catch(() => null),
    apiFetch<{ meetings?: Array<{ id?: string; meeting_id?: string }> } | null>(`/api/projects/${id}/meetings`)
      .catch(() => null),
  ]);
  const refs: string[] = [];
  for (const row of Array.isArray(resources?.resources) ? resources!.resources : []) {
    if (row?.resource_ref && !row.deleted) refs.push(normalizeRef(String(row.resource_ref)));
  }
  for (const row of Array.isArray(meetings?.meetings) ? meetings!.meetings : []) {
    const mid = row?.id ?? row?.meeting_id;
    if (mid) refs.push(`meeting:${mid}`);
  }
  return refs;
}

async function readPersons(): Promise<ScreenPerson[]> {
  // The Dock's order (Dock.tsx readPeopleProjection): a People store that is
  // not ready is never asked for its relationships.
  const ready = await apiFetch<{ state?: string; readiness?: string } | null>("/api/people/readiness").catch(() => null);
  if ((ready?.state ?? ready?.readiness) !== "ready") return [];
  const body = await apiFetch<{ relationships?: Array<{ id?: string; display_name?: string }> } | null>(
    "/api/people/relationships",
  ).catch(() => null);
  const rows = Array.isArray(body?.relationships) ? body!.relationships : [];
  return rows
    .filter((r) => r?.id && r.display_name)
    .map((r) => ({ id: String(r.id), name: String(r.display_name) }));
}

/** Read again when the Projects change or the desk changes (`updatedAt`). */
export function useScreenMembers(projectIds: readonly string[], updatedAt: number | null): ScreenMembers {
  const [members, setMembers] = useState<ScreenMembers>(EMPTY);
  const key = projectIds.join("|");
  useEffect(() => {
    let live = true;
    void Promise.all([Promise.all(projectIds.map(projectRefs)), readPersons()]).then(([refs, persons]) => {
      if (!live) return;
      setMembers({ filed: new Set(refs.flat()), persons, loaded: true });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, updatedAt]);
  return members;
}
