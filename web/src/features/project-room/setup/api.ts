// HS-159-05 -- typed API wrappers for the 10 project-setup routes
// (WEB-ARC-004: decode at the boundary, never pass Record<string,unknown>
// into views).  Mirrors holdspeak/web/routes/project_setup.py.

import { apiFetch } from "../../../lib/api";
import type {
  SetupSession,
  SetupProposal,
  TestResultResponse,
  FinalizeEnvelope,
  SetupAnswer,
  ProviderConnectionStatus,
  DiscoveryResponse,
  ValidateRepoResponse,
  ClarifyScopeResponse,
  JiraConnection,
  JiraConnectionsResponse,
  JiraDiscoveryResponse,
  JiraSearchResult,
  JiraValidateScopeResponse,
  JiraClarifyScopeResponse,
} from "./model";
import {
  decodeSession,
  decodeProposal,
  decodeTestResultResponse,
  decodeFinalizeEnvelope,
  decodeAnswer,
  decodeProviderConnectionStatus,
  decodeDiscoveryResponse,
  decodeValidateRepoResponse,
  decodeClarifyScopeResponse,
  decodeJiraConnection,
  decodeJiraConnectionsResponse,
  decodeJiraDiscoveryResponse,
  decodeJiraSearchResult,
  decodeJiraValidateScopeResponse,
  decodeJiraClarifyScopeResponse,
} from "./model";

const BASE = "/api/project-setups";

function enc(id: string): string {
  return encodeURIComponent(id);
}

/* ── Session lifecycle ── */

/** POST /api/project-setups -- start a durable setup session. */
export async function startSetup(): Promise<SetupSession> {
  const raw = await apiFetch<Record<string, unknown>>(BASE, {
    method: "POST",
  });
  return decodeSession(raw);
}

/** GET /api/project-setups/{session_id} -- resume read (rehydration). */
export async function getSetup(sessionId: string): Promise<SetupSession> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${BASE}/${enc(sessionId)}`,
  );
  return decodeSession(raw);
}

/* ── Answers ── */

/** POST /api/project-setups/{session_id}/answers -- record an answer. */
export async function submitAnswer(
  sessionId: string,
  questionId: string,
  text: string,
): Promise<SetupAnswer> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${BASE}/${enc(sessionId)}/answers`,
    {
      method: "POST",
      json: {
        question_id: questionId,
        payload: { text },
      },
    },
  );
  return decodeAnswer(raw);
}

/* ── Suggestions ── */

/** POST /api/project-setups/{session_id}/suggest -- generate proposals. */
export async function suggest(
  sessionId: string,
): Promise<SetupProposal[]> {
  const raw = await apiFetch<{ proposals: Record<string, unknown>[] }>(
    `${BASE}/${enc(sessionId)}/suggest`,
    { method: "POST" },
  );
  return (raw.proposals || []).map(decodeProposal);
}

/* ── Proposal operations ── */

/** POST .../proposals/{id}/select */
export async function selectProposal(
  sessionId: string,
  proposalId: string,
): Promise<SetupProposal> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${BASE}/${enc(sessionId)}/proposals/${enc(proposalId)}/select`,
    { method: "POST" },
  );
  return decodeProposal(raw);
}

/** POST .../proposals/{id}/deselect */
export async function deselectProposal(
  sessionId: string,
  proposalId: string,
): Promise<SetupProposal> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${BASE}/${enc(sessionId)}/proposals/${enc(proposalId)}/deselect`,
    { method: "POST" },
  );
  return decodeProposal(raw);
}

/** POST .../proposals/{id}/clarify */
export async function clarifyProposal(
  sessionId: string,
  proposalId: string,
  patch: Record<string, unknown>,
): Promise<SetupProposal> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${BASE}/${enc(sessionId)}/proposals/${enc(proposalId)}/clarify`,
    { method: "POST", json: { patch } },
  );
  return decodeProposal(raw);
}

/** POST .../proposals/{id}/test */
export async function testProposal(
  sessionId: string,
  proposalId: string,
): Promise<TestResultResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${BASE}/${enc(sessionId)}/proposals/${enc(proposalId)}/test`,
    { method: "POST" },
  );
  return decodeTestResultResponse(raw);
}

/* ── Finalize / abandon ── */

/** POST /api/project-setups/{session_id}/finalize */
export async function finalize(
  sessionId: string,
  commandId?: string,
): Promise<FinalizeEnvelope> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${BASE}/${enc(sessionId)}/finalize`,
    {
      method: "POST",
      json: commandId ? { command_id: commandId } : {},
    },
  );
  return decodeFinalizeEnvelope(raw);
}

/** POST /api/project-setups/{session_id}/abandon */
export async function abandon(sessionId: string): Promise<void> {
  await apiFetch<Record<string, unknown>>(
    `${BASE}/${enc(sessionId)}/abandon`,
    { method: "POST" },
  );
}

/* ── Provider routes (HS-161-05) ── */

const PROVIDERS = "/api/providers";

/** GET /api/providers/github/connection -- check connection status. */
export async function getGitHubConnection(): Promise<ProviderConnectionStatus> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${PROVIDERS}/github/connection`,
  );
  return decodeProviderConnectionStatus(raw);
}

/** POST /api/providers/github/connection/recheck -- re-probe connection. */
export async function recheckGitHubConnection(): Promise<ProviderConnectionStatus> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${PROVIDERS}/github/connection/recheck`,
    { method: "POST" },
  );
  return decodeProviderConnectionStatus(raw);
}

/** GET /api/providers/github/discover -- discover repositories. */
export async function discoverGitHub(
  query?: string,
  cursor?: string,
): Promise<DiscoveryResponse> {
  const params = new URLSearchParams();
  if (query) params.set("query", query);
  if (cursor) params.set("cursor", cursor);
  const qs = params.toString();
  const raw = await apiFetch<Record<string, unknown>>(
    `${PROVIDERS}/github/discover${qs ? `?${qs}` : ""}`,
  );
  return decodeDiscoveryResponse(raw);
}

/** POST /api/providers/github/validate-repo -- validate a typed repo. */
export async function validateGitHubRepo(
  ownerRepo: string,
): Promise<ValidateRepoResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${PROVIDERS}/github/validate-repo`,
    { method: "POST", json: { owner_repo: ownerRepo } },
  );
  return decodeValidateRepoResponse(raw);
}

/** POST /api/project-setups/{sid}/proposals/{pid}/clarify-scope -- scope a proposal. */
export async function clarifyScope(
  sessionId: string,
  proposalId: string,
  repo?: string,
): Promise<ClarifyScopeResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${BASE}/${enc(sessionId)}/proposals/${enc(proposalId)}/clarify-scope`,
    { method: "POST", json: repo ? { repo } : {} },
  );
  return decodeClarifyScopeResponse(raw);
}

/* ── Jira provider routes (HS-166-04) ── */

/** GET /api/providers/jira/connections -- list all connections + known accounts. */
export async function getJiraConnections(): Promise<JiraConnectionsResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${PROVIDERS}/jira/connections`,
  );
  return decodeJiraConnectionsResponse(raw);
}

/** POST /api/providers/jira/connections -- add a connection. */
export async function addJiraConnection(
  site: string,
  email: string,
): Promise<JiraConnection> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${PROVIDERS}/jira/connections`,
    { method: "POST", json: { site, email } },
  );
  return decodeJiraConnection(raw);
}

/** POST /api/providers/jira/connections/{ref}/recheck -- recheck one connection. */
export async function recheckJiraConnection(
  ref: string,
): Promise<JiraConnection> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${PROVIDERS}/jira/connections/${encodeURIComponent(ref)}/recheck`,
    { method: "POST" },
  );
  return decodeJiraConnection(raw);
}

/** GET /api/providers/jira/discover -- bounded Jira discovery. */
export async function discoverJira(
  connectionRef: string,
  kind: "projects" | "issue_types" | "statuses",
  opts?: { query?: string; projectKey?: string; cursor?: number; limit?: number },
): Promise<JiraDiscoveryResponse> {
  const params = new URLSearchParams();
  params.set("connection_ref", connectionRef);
  params.set("kind", kind);
  if (opts?.query) params.set("query", opts.query);
  if (opts?.projectKey) params.set("project_key", opts.projectKey);
  if (opts?.cursor != null) params.set("cursor", String(opts.cursor));
  if (opts?.limit != null) params.set("limit", String(opts.limit));
  const raw = await apiFetch<Record<string, unknown>>(
    `${PROVIDERS}/jira/discover?${params.toString()}`,
  );
  return decodeJiraDiscoveryResponse(raw);
}

/** POST /api/providers/jira/search -- JQL search. */
export async function searchJira(
  connectionRef: string,
  jql: string,
  limit?: number,
  enrich?: boolean,
): Promise<JiraSearchResult> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${PROVIDERS}/jira/search`,
    {
      method: "POST",
      json: {
        connection_ref: connectionRef,
        jql,
        limit: limit ?? 50,
        enrich: enrich ?? false,
      },
    },
  );
  return decodeJiraSearchResult(raw);
}

/** POST /api/providers/jira/validate-scope -- typed project validation. */
export async function validateJiraScope(
  connectionRef: string,
  projectKey: string,
): Promise<JiraValidateScopeResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${PROVIDERS}/jira/validate-scope`,
    {
      method: "POST",
      json: { connection_ref: connectionRef, project_key: projectKey },
    },
  );
  return decodeJiraValidateScopeResponse(raw);
}

/** POST /api/project-setups/{sid}/proposals/{pid}/clarify-jira-scope -- scope a Jira proposal. */
export async function clarifyJiraScope(
  sessionId: string,
  proposalId: string,
  connectionRef: string,
  projects: string[],
  issueTypes?: string[],
): Promise<JiraClarifyScopeResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    `${BASE}/${enc(sessionId)}/proposals/${enc(proposalId)}/clarify-jira-scope`,
    {
      method: "POST",
      json: {
        connection_ref: connectionRef,
        projects,
        issue_types: issueTypes ?? [],
      },
    },
  );
  return decodeJiraClarifyScopeResponse(raw);
}
