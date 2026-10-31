import type { TerminalDescriptor } from "./types";

export type WorkspaceFace = "sessions" | "files" | "changes" | "context";

export interface WorkspaceSelection {
  projectId: string | null;
  sessionId: string | null;
  face: WorkspaceFace;
  pendingLaunch: string | null;
  pendingKind: "launch" | "queue" | null;
  pendingProjectId: string | null;
  pendingHandoffs: WorkspacePendingHandoff[];
  requestEpoch: number;
}

export interface WorkspacePendingHandoff {
  id: string;
  kind: "launch" | "queue";
  projectId: string | null;
  originRef: string | null;
  epoch: number;
}

const initial: WorkspaceSelection = {
  projectId: null,
  sessionId: null,
  face: "sessions",
  pendingLaunch: null,
  pendingKind: null,
  pendingProjectId: null,
  pendingHandoffs: [],
  requestEpoch: 0,
};
let current = initial;
const listeners = new Set<() => void>();

function publish(next: WorkspaceSelection): void {
  current = next;
  for (const listener of listeners) listener();
}

export function workspaceSelectionSnapshot(): WorkspaceSelection {
  return current;
}

export function subscribeWorkspaceSelection(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function setWorkspaceSelection(next: Partial<WorkspaceSelection>): void {
  const changesSelection = next.projectId !== undefined || next.sessionId !== undefined || next.face !== undefined;
  publish({ ...current, ...next, requestEpoch: changesSelection ? current.requestEpoch + 1 : current.requestEpoch });
}

/** Internal view update that does not represent a newer owner request. */
export function setWorkspaceSelectionQuiet(next: Partial<WorkspaceSelection>): void {
  publish({ ...current, ...next });
}

/** A form open/close is a newer owner intent even when its semantic face stays. */
export function bumpWorkspaceRequestEpoch(): number {
  const requestEpoch = current.requestEpoch + 1;
  publish({ ...current, requestEpoch });
  return requestEpoch;
}

export function selectWorkspaceSession(descriptor: TerminalDescriptor, face: WorkspaceFace = "files"): void {
  publish({
    ...current,
    // An unbound shell can still be the source the owner is about to file in
    // the explicitly selected Project. Keep that target while a bound agent
    // takes the Project from its authoritative context.
    projectId: descriptor.context.project?.id ?? current.projectId,
    sessionId: descriptor.id,
    face,
    pendingLaunch: current.pendingHandoffs[0]?.id ?? null,
    pendingKind: current.pendingHandoffs[0]?.kind ?? null,
    pendingProjectId: current.pendingHandoffs[0]?.projectId ?? null,
    requestEpoch: current.requestEpoch + 1,
  });
}

export function selectWorkspaceFace(face: WorkspaceFace): void {
  publish({ ...current, face, requestEpoch: current.requestEpoch + 1 });
}

export function queueWorkspaceLaunch(launchId: string, projectId: string | null, kind: "launch" | "queue" = "launch", epoch = current.requestEpoch, originRef: string | null = null): void {
  const pendingHandoffs = [...current.pendingHandoffs.filter((handoff) => handoff.id !== launchId), { id: launchId, kind, projectId, originRef, epoch }];
  publish({ ...current, pendingHandoffs, pendingLaunch: pendingHandoffs[0]?.id ?? null, pendingKind: pendingHandoffs[0]?.kind ?? null, pendingProjectId: pendingHandoffs[0]?.projectId ?? null });
}

export function resolveWorkspaceLaunch(launchId: string, descriptor: TerminalDescriptor): void {
  const pending = current.pendingHandoffs.find((handoff) => handoff.id === launchId);
  if (!pending) return;
  const next = current.pendingHandoffs.filter((handoff) => handoff.id !== launchId);
  const base = { ...current, pendingHandoffs: next, pendingLaunch: next[0]?.id ?? null, pendingKind: next[0]?.kind ?? null, pendingProjectId: next[0]?.projectId ?? null };
  if (current.requestEpoch === pending.epoch) {
    publish({ ...base, projectId: descriptor.context.project?.id ?? pending.projectId, sessionId: descriptor.id, face: "files", requestEpoch: current.requestEpoch + 1 });
  } else {
    publish(base);
  }
}

export function cancelWorkspaceLaunch(launchId: string): void {
  const next = current.pendingHandoffs.filter((handoff) => handoff.id !== launchId);
  publish({ ...current, pendingHandoffs: next, pendingLaunch: next[0]?.id ?? null, pendingKind: next[0]?.kind ?? null, pendingProjectId: next[0]?.projectId ?? null });
}
