import { apiFetch, newDeliveryId } from "../../lib/api";

export type AssignmentScope =
  | { kind: "global" }
  | { kind: "group"; group_id: string }
  | { kind: "capability"; capability_id: string }
  | { kind: "subject"; subject_kind: string; subject_id: string; capability_id: string };

export type AssignmentEntry = {
  ordinal: number;
  profile_id: string;
  profile_revision: number;
  label: string;
  boundary: string;
  readiness: string;
};

export type AssignmentProjection = {
  id: string;
  revision: number;
  scope: AssignmentScope;
  entries: AssignmentEntry[];
  retry_policy_id: string | null;
  issues: AssignmentIssue[];
};

export type AssignmentIssue = {
  code: string;
  severity: "blocking" | "repair";
  profile_id?: string;
  capability_id?: string;
};

export type AssignmentEffective = {
  status: "assigned" | "no_assignment" | "no_compatible_assignment";
  inherited_from: "global" | "group" | "capability" | "subject" | "invocation" | null;
  assignment: AssignmentProjection | null;
  repair: string | null;
};

export type AssignmentSummaryRow = {
  id: string;
  label: string;
  editor_capability_id: string | null;
  inherited_from: "global" | "group" | null;
  assignment: AssignmentProjection | null;
  status: string;
  repair: string | null;
};

export type AssignmentSummary = {
  schema: "InferenceAssignmentSummary@1";
  rows: AssignmentSummaryRow[];
  task_overrides: Array<{
    id: string;
    label: string;
    group: { id: string; label: string };
    has_override: boolean;
    effective: AssignmentEffective;
    issues: AssignmentIssue[];
  }>;
  issue_count: number;
};

export type AssignmentCandidate = {
  profile_id: string;
  profile_revision: number;
  label: string;
  boundary: string;
  readiness: string;
  status: "compatible" | "savable_with_repair";
  issues: AssignmentIssue[];
};

export type AssignmentEditorProjection = {
  schema: "AssignmentEditorProjection@1";
  scope: AssignmentScope;
  selected_capability: {
    id: string;
    revision: number;
    label: string;
    group: { id: string; label: string };
    allowed_boundaries: string[];
    fallback_dispositions: string[];
  };
  draft_base_revision: number;
  configured_assignment: AssignmentProjection | null;
  effective: AssignmentEffective;
  candidates: AssignmentCandidate[];
  retry_policy: { permitted_ids: string[]; default_id: string };
};

export function getAssignmentSummary(signal?: AbortSignal): Promise<AssignmentSummary> {
  return apiFetch<AssignmentSummary>("/api/inference/assignments", { signal });
}

export function getAssignmentEditor(scope: AssignmentScope, capabilityId: string): Promise<AssignmentEditorProjection> {
  return apiFetch<AssignmentEditorProjection>("/api/inference/assignments/editor", {
    method: "POST", json: { scope, capability_id: capabilityId },
  });
}

export function saveAssignment(
  scope: AssignmentScope,
  expectedRevision: number,
  entries: Pick<AssignmentCandidate, "profile_id" | "profile_revision">[],
  retryPolicyId: string | null,
): Promise<unknown> {
  return apiFetch("/api/inference/assignments/set", {
    method: "POST",
    json: {
      command_id: newDeliveryId(), scope, expected_revision: expectedRevision,
      entries, retry_policy_id: retryPolicyId,
    },
  });
}

export function previewAssignmentDefault(scope: AssignmentScope, capabilityId: string): Promise<{ effective: AssignmentEffective }> {
  return apiFetch("/api/inference/assignments/preview-use-default", {
    method: "POST", json: { scope, capability_id: capabilityId },
  });
}

export function clearAssignmentDefault(
  scope: AssignmentScope, capabilityId: string, expectedRevision: number,
): Promise<unknown> {
  return apiFetch("/api/inference/assignments/clear", {
    method: "POST",
    json: {
      command_id: newDeliveryId(), scope, capability_id: capabilityId,
      expected_revision: expectedRevision,
    },
  });
}
