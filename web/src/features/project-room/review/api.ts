// HS-160-06 — typed API wrappers for the review wire.
// Every endpoint is named, path-encoded, and carries its response type.

import { apiFetch } from "../../../lib/api";
import type { AcceptResult, DecideBody, DecideResult, DeltaResponse } from "./model";
import type { ReviewWindow } from "./model";
import { decodeAcceptResult, decodeDecideResult, decodeDelta, decodeReviewWindow } from "./model";

/** GET /api/projects/{id}/delta — open window or honest empty state. */
export async function fetchDelta(projectId: string): Promise<DeltaResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    `/api/projects/${encodeURIComponent(projectId)}/delta`,
  );
  return decodeDelta(raw);
}

/** POST /api/projects/{id}/reviews — open (or re-enter) a review. */
export async function openReview(projectId: string): Promise<ReviewWindow> {
  const raw = await apiFetch<Record<string, unknown>>(
    `/api/projects/${encodeURIComponent(projectId)}/reviews`,
    { method: "POST" },
  );
  return decodeReviewWindow(raw);
}

/** POST .../proposals/{proposalId}/decide — decide one proposal. */
export async function decideProposal(
  projectId: string,
  reviewId: string,
  proposalId: string,
  body: DecideBody,
): Promise<DecideResult> {
  const raw = await apiFetch<Record<string, unknown>>(
    `/api/projects/${encodeURIComponent(projectId)}/reviews/${encodeURIComponent(reviewId)}/proposals/${encodeURIComponent(proposalId)}/decide`,
    { method: "POST", json: body },
  );
  return decodeDecideResult(raw);
}

/** POST .../reviews/{reviewId}/accept — accept the review. */
export async function acceptReview(
  projectId: string,
  reviewId: string,
  commandId?: string,
): Promise<AcceptResult> {
  const raw = await apiFetch<Record<string, unknown>>(
    `/api/projects/${encodeURIComponent(projectId)}/reviews/${encodeURIComponent(reviewId)}/accept`,
    { method: "POST", json: { command_id: commandId } },
  );
  return decodeAcceptResult(raw);
}
