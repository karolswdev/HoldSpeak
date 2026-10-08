/** PHILO-15 16 (B38): a Project knows its repository.
 *
 *   GET  /api/projects/{id}/repository   the registered repository, CLONED or not,
 *                                        and the repositories the Room watches
 *   POST /api/projects/{id}/repository   `project.repository.register` (owner only,
 *                                        one receipt; nothing is cloned until the
 *                                        first hand, which clones from github.com)
 */
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import { useOnDeskChanged } from "./useDeskChangedRefresh";

export interface ProjectRepository {
  project_id: string;
  repository: string | null;
  registered: boolean;
  cloned: boolean;
  registered_at?: string | null;
  cloned_at?: string | null;
  /** The GitHub repositories the Room watches (a Project with no registration
   *  registers the first one). */
  watched: string[];
  host: string;
  /** `not_read`: the registrations file exists and cannot be read (never "none"). */
  store?: "read" | "not_read";
}

export const projectRepositoryPath = (projectId: string) =>
  `/api/projects/${encodeURIComponent(projectId)}/repository`;

export function fetchProjectRepository(projectId: string): Promise<ProjectRepository> {
  return apiFetch<ProjectRepository>(projectRepositoryPath(projectId));
}

export function registerProjectRepository(projectId: string, repository: string): Promise<ProjectRepository> {
  return apiFetch<ProjectRepository>(projectRepositoryPath(projectId), { method: "POST", json: { repository } });
}

/** `owner/name · CLONED`, `owner/name · NOT CLONED`, or `owner/name · NOT REGISTERED`
 *  (a watched repository nobody registered); "" when the Project names none. */
export function repositoryWords(state: ProjectRepository | null, failed = false): string {
  // A read that failed, or a store the hub cannot read, is NOT READ (A.10).
  if (failed || state?.store === "not_read") return "NOT READ";
  if (!state) return "";
  if (state.repository) return `${state.repository} · ${state.cloned ? "CLONED" : "NOT CLONED"}`;
  const watched = state.watched?.[0];
  return watched ? `${watched} · NOT REGISTERED` : "";
}

/** The repository the drawer's Register verb names: the first watched one,
 *  when the Project registered none. */
export function registrable(state: ProjectRepository | null): string | null {
  if (!state || state.registered || state.store === "not_read") return null;
  return state.watched?.[0] ?? null;
}

/** The Project's repository, read again when the desk changes. */
export function useProjectRepository(projectId: string) {
  const [state, setState] = useState<ProjectRepository | null>(null);
  const [failed, setFailed] = useState(false);
  const [tick, setTick] = useState(0);
  useOnDeskChanged(() => setTick((n) => n + 1));
  const read = useCallback(() => {
    let live = true;
    if (!projectId) return undefined;
    fetchProjectRepository(projectId).then(
      (next) => {
        if (!live) return;
        setState(next);
        setFailed(false);
      },
      () => {
        if (live) setFailed(true);
      },
    );
    return () => {
      live = false;
    };
  }, [projectId]);
  useEffect(() => read(), [read, tick]);
  return { state, failed, reload: () => setTick((n) => n + 1) };
}
