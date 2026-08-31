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
} from "./model";
import {
  decodeSession,
  decodeProposal,
  decodeTestResultResponse,
  decodeFinalizeEnvelope,
  decodeAnswer,
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
