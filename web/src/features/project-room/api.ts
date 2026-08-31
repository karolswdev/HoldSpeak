// HS-158-05 extraction — typed API wrappers for every apiFetch call
// ProjectMemoryCore makes today. Each wrapper names its endpoint,
// encodes path parameters, and carries the response type.

import { apiFetch } from "../../lib/api";
import type {
  ProjectResponse,
  ProjectMeetingsResponse,
  ProjectDecisionsResponse,
  ProjectArtifactsResponse,
  SinceLastMeetingResponse,
  DecisionMomentResponse,
  DecisionTransitionResponse,
  DecisionPromoteResponse,
  MemorySearchResponse,
} from "./model";
import type { RoomSnapshot } from "./model";
import { decodeRoomSnapshot } from "./model";

/* ── room projection (HS-158-05 adoption: the first render) ── */

export async function fetchProjectRoom(projectId: string): Promise<RoomSnapshot> {
  const raw = await apiFetch<Record<string, unknown>>(
    `/api/projects/${encodeURIComponent(projectId)}/room`,
  );
  return decodeRoomSnapshot(raw);
}

/* ── project data fan-out (progressive follow-ups) ── */

export function fetchProject(projectId: string) {
  return apiFetch<ProjectResponse>(
    `/api/projects/${encodeURIComponent(projectId)}`,
  );
}

export function fetchProjectMeetings(projectId: string) {
  return apiFetch<ProjectMeetingsResponse>(
    `/api/projects/${encodeURIComponent(projectId)}/meetings?limit=200`,
  );
}

export function fetchProjectDecisions(projectId: string) {
  return apiFetch<ProjectDecisionsResponse>(
    `/api/decisions?project_id=${encodeURIComponent(projectId)}&limit=500`,
  );
}

export function fetchProjectArtifacts(projectId: string) {
  return apiFetch<ProjectArtifactsResponse>(
    `/api/projects/${encodeURIComponent(projectId)}/artifacts`,
  );
}

export function fetchSinceLastMeeting(projectId: string) {
  return apiFetch<SinceLastMeetingResponse>(
    `/api/projects/${encodeURIComponent(projectId)}/since-last-meeting`,
  );
}

/* ── decision mutations ── */

export function fetchDecisionMoment(decisionId: string) {
  return apiFetch<DecisionMomentResponse>(
    `/api/decisions/${encodeURIComponent(decisionId)}/moment`,
  );
}

export function transitionDecision(
  decisionId: string,
  action: "accept" | "supersede",
  body: Record<string, unknown>,
) {
  return apiFetch<DecisionTransitionResponse>(
    `/api/decisions/${encodeURIComponent(decisionId)}/${action}`,
    { method: "POST", json: body },
  );
}

export function promoteDecision(
  decisionId: string,
  kind: string,
  withModel: boolean,
) {
  const path = withModel
    ? `/api/decisions/${encodeURIComponent(decisionId)}/promote/${kind}/draft-with-model`
    : `/api/decisions/${encodeURIComponent(decisionId)}/promote/${kind}`;
  return apiFetch<DecisionPromoteResponse>(path, {
    method: "POST",
    json: withModel ? {} : undefined,
  });
}

/* ── memory search ── */

export function searchProjectMemory(query: string, projectId: string) {
  const params = new URLSearchParams({ query, project_id: projectId });
  return apiFetch<MemorySearchResponse>(`/api/memory/search?${params}`);
}
