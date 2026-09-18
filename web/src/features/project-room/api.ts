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
import type { RoomSnapshot, RoomProposalItem, RoomSuggestedSourceItem } from "./model";
import { decodeRoomSnapshot, decodeProposal, decodeSuggestedSource } from "./model";

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

/* ── room read marker (HS-169-03) ── */

export function markRoomRead(projectId: string) {
  return apiFetch<{ read_at: string }>(
    `/api/projects/${encodeURIComponent(projectId)}/room/read`,
    { method: "POST" },
  );
}

/* ── watch operations (HS-169-03) ── */

export function pauseWatch(watchId: string) {
  return apiFetch<Record<string, unknown>>(
    `/api/watches/${encodeURIComponent(watchId)}/pause`,
    { method: "POST" },
  );
}

export function resumeWatch(watchId: string) {
  return apiFetch<Record<string, unknown>>(
    `/api/watches/${encodeURIComponent(watchId)}/resume`,
    { method: "POST" },
  );
}

export function retireWatch(watchId: string) {
  return apiFetch<Record<string, unknown>>(
    `/api/watches/${encodeURIComponent(watchId)}/retire`,
    { method: "POST" },
  );
}

/* ── memory search ── */

export function searchProjectMemory(query: string, projectId?: string) {
  const params = new URLSearchParams({ query });
  if (projectId) params.set("project_id", projectId);
  return apiFetch<MemorySearchResponse>(`/api/memory/search?${params}`);
}

/* ── HS-172-03: proposals ── */

export async function fetchProjectProposals(
  projectId: string,
  state?: string,
): Promise<RoomProposalItem[]> {
  const qs = state ? `?state=${encodeURIComponent(state)}` : "";
  const raw = await apiFetch<{ proposals: Record<string, unknown>[] }>(
    `/api/projects/${encodeURIComponent(projectId)}/proposals${qs}`,
  );
  return (raw.proposals || []).map(decodeProposal);
}

export async function confirmProposal(
  proposalId: string,
  body?: { text?: string; owner?: string; due?: string },
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(
    `/api/proposals/${encodeURIComponent(proposalId)}/confirm`,
    { method: "POST", json: body || {} },
  );
}

export async function dismissProposal(
  proposalId: string,
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(
    `/api/proposals/${encodeURIComponent(proposalId)}/dismiss`,
    { method: "POST" },
  );
}

/* ── HS-172-06: suggested sources ── */

export async function fetchSuggestedSources(
  projectId: string,
): Promise<RoomSuggestedSourceItem[]> {
  const raw = await apiFetch<{ suggestions: Record<string, unknown>[] }>(
    `/api/projects/${encodeURIComponent(projectId)}/suggested-sources`,
  );
  return (raw.suggestions || []).map(decodeSuggestedSource);
}

export async function addSuggestedSource(
  projectId: string,
  ref: string,
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(
    `/api/projects/${encodeURIComponent(projectId)}/suggested-sources/${encodeURIComponent(ref)}/add`,
    { method: "POST" },
  );
}

export async function dismissSuggestedSource(
  projectId: string,
  ref: string,
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(
    `/api/projects/${encodeURIComponent(projectId)}/suggested-sources/${encodeURIComponent(ref)}/dismiss`,
    { method: "POST" },
  );
}

/* ── HS-173-04: Nudge API ── */

/** HS-173-04: a proposed nudge from the wire. */
export type NudgeItem = {
  step_id: string;
  state: string;
  pr_number: number;
  pr_title: string;
  pr_url: string;
  reviewer_login: string;
  days: number;
  comment_text: string;
  host: string;
  created_at: string;
};

export async function fetchNudges(
  projectId: string,
  state?: string,
): Promise<NudgeItem[]> {
  const qs = state ? `?state=${encodeURIComponent(state)}` : "";
  const raw = await apiFetch<{ nudges: NudgeItem[] }>(
    `/api/projects/${encodeURIComponent(projectId)}/nudges${qs}`,
  );
  return raw.nudges || [];
}

export async function sendNudge(
  stepId: string,
  text: string,
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(
    `/api/nudges/${encodeURIComponent(stepId)}/send`,
    { method: "POST", json: { text } },
  );
}

export async function dismissNudge(
  stepId: string,
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(
    `/api/nudges/${encodeURIComponent(stepId)}/dismiss`,
    { method: "POST" },
  );
}

/* ── HS-172-07: Room people ── */

export type RoomPersonItem = {
  relationship_id: string;
  display_name: string;
  prs_waiting?: number;
  assignments_open?: number;
  assignments_overdue?: number;
};

export async function fetchRoomPeople(
  projectId: string,
): Promise<RoomPersonItem[]> {
  const raw = await apiFetch<{ people: RoomPersonItem[] }>(
    `/api/projects/${encodeURIComponent(projectId)}/people`,
  );
  return raw.people || [];
}

/* ── HS-200-14: Room people preparation ── */

/** The ledger's own state: only `ready` resolves anybody. */
export type RoomPeopleLedgerState = "ready" | "locked" | "unconfigured" | "unavailable";

/** A commitment's source: story 12's record points at its meeting and,
 *  when the sentence was anchored, the transcript segment. */
export type RoomPersonCommitmentSource = {
  kind: "meeting";
  meeting_id: string;
  label: string;
  segment_index?: number;
  span_start?: number;
  span_end?: number;
};

export type RoomPersonCommitment = {
  id: string;
  text: string;
  due_at: string | null;
  owner: string;
  source: RoomPersonCommitmentSource;
};

/** An observable fact with the Watch it came from. Never inferred. */
export type RoomPersonFact = {
  kind: "prs_waiting" | "assignments_open" | "assignments_overdue";
  count: number;
  source: { kind: "watch"; watch_id: string; connector_id: string; label: string };
};

/** A Watch that names this person but whose facts are OMITTED because it
 *  is paused, retired or disabled -- drawn with its state, never silently. */
export type RoomOmittedSource = {
  kind: "watch"; watch_id: string; connector_id: string; label: string;
  state: "paused" | "retired" | "disabled" | string;
};

/** A linked person: 172-07's row plus what the Project holds on them. */
export type RoomLinkedPerson = RoomPersonItem & {
  link: "linked";
  commitments: RoomPersonCommitment[];
  facts: RoomPersonFact[];
  omitted_sources?: RoomOmittedSource[];
};

export type RoomPersonCandidate = { relationship_id: string; display_name: string };

/** An owner the Project names that no ONE ledger entry answers for. */
export type RoomUnresolvedOwner = {
  owner: string;
  /** `locked` / `unconfigured` / `unavailable` mirror the ledger's own state. */
  link: "ambiguous" | "not_linked" | "locked" | "unconfigured" | "unavailable";
  candidates: RoomPersonCandidate[];
  commitments: RoomPersonCommitment[];
};

export type RoomPeoplePreparation = {
  state: RoomPeopleLedgerState;
  expected: number;
  resolved: number;
  gaps: { ambiguous: number; not_linked: number; unreadable: number };
  people: RoomLinkedPerson[];
  unresolved: RoomUnresolvedOwner[];
};

export async function fetchRoomPeoplePreparation(
  projectId: string,
): Promise<RoomPeoplePreparation> {
  const raw = await apiFetch<Partial<RoomPeoplePreparation>>(
    `/api/projects/${encodeURIComponent(projectId)}/people`,
  );
  return {
    state: raw.state ?? "unavailable",
    expected: raw.expected ?? 0,
    resolved: raw.resolved ?? 0,
    gaps: raw.gaps ?? { ambiguous: 0, not_linked: 0, unreadable: 0 },
    people: raw.people ?? [],
    unresolved: raw.unresolved ?? [],
  };
}

/** `Resolve` / `Link`: the existing owner-alias link, in place. The
 *  alias is the owner string the record already carries; the ledger
 *  keeps it unique (invariant P2) and names the holder on a clash. */
export async function linkOwnerAlias(
  relationshipId: string,
  alias: string,
): Promise<void> {
  await apiFetch(
    `/api/people/relationships/${encodeURIComponent(relationshipId)}/owner-aliases`,
    { method: "POST", json: { alias } },
  );
}
