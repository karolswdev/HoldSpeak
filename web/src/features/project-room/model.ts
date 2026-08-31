// HS-158-05 extraction — wire types, domain decode, and pure composition
// seams. The response interfaces stay canonical in core-types (other cores
// share them); this module re-exports the Project-scoped subset and adds
// the typed decode layer WEB-ARC-004 requires.

export type {
  ProjectResponse,
  ProjectMeetingsResponse,
  ProjectDecisionsResponse,
  ProjectArtifactsResponse,
  SinceLastMeetingResponse,
  DecisionMomentResponse,
  DecisionTransitionResponse,
  DecisionPromoteResponse,
  MemorySearchResponse,
} from "../../pages/cores/core-types";

/* ── domain types ── */

export type ProjectTimelineEntry = {
  id: string;
  kind: "meeting" | "decision" | "artifact";
  title: string;
  occurredAt: string;
  row: Record<string, unknown>;
};

/* ── pure composition ── */

/** Pure composition seam pinned by the timeline tests. */
export function composeProjectTimeline(
  meetings: Record<string, unknown>[],
  decisions: Record<string, unknown>[],
  artifacts: Record<string, unknown>[],
): ProjectTimelineEntry[] {
  const promoted = artifacts.filter(
    (row) =>
      row.status === "promoted" ||
      row.promotion_state === "promoted" ||
      Boolean(row.promoted_at),
  );
  return [
    ...meetings.map((row) => ({
      id: String(row.id),
      kind: "meeting" as const,
      title: String(row.title || "Meeting"),
      occurredAt: String(row.started_at || row.created_at || ""),
      row,
    })),
    ...decisions.map((row) => ({
      id: String(row.id),
      kind: "decision" as const,
      title: String(row.text || "Decision"),
      occurredAt: String(row.decided_at || row.created_at || ""),
      row,
    })),
    ...promoted.map((row) => ({
      id: String(row.id),
      kind: "artifact" as const,
      title: String(row.title || row.artifact_type || "Artifact"),
      occurredAt: String(row.promoted_at || row.created_at || ""),
      row,
    })),
  ].sort((a, b) => b.occurredAt.localeCompare(a.occurredAt));
}

/* ── field decoders ── */

export function lifecycleLabel(row: Record<string, unknown>): string {
  const lifecycle = String(row.lifecycle || "recorded");
  if (lifecycle === "superseded") return "Superseded";
  return lifecycle[0].toUpperCase() + lifecycle.slice(1);
}

/** Decode a raw project payload into its identity fields. */
export function decodeProject(raw: Record<string, unknown>): {
  id: string;
  name: string;
} {
  return {
    id: String(raw.id ?? ""),
    name: String(raw.name ?? ""),
  };
}

/** Decode a raw meeting row into its timeline-relevant fields. */
export function decodeMeeting(raw: Record<string, unknown>): {
  id: string;
  title: string;
  startedAt: string;
} {
  return {
    id: String(raw.id ?? ""),
    title: String(raw.title || "Meeting"),
    startedAt: String(raw.started_at || raw.created_at || ""),
  };
}

/** Decode a raw decision row into its display-relevant fields. */
export function decodeDecision(raw: Record<string, unknown>): {
  id: string;
  text: string;
  lifecycle: string;
  decidedAt: string;
  rationale: string;
} {
  return {
    id: String(raw.id ?? ""),
    text: String(raw.text || "Decision"),
    lifecycle: String(raw.lifecycle || "recorded"),
    decidedAt: String(raw.decided_at || raw.created_at || ""),
    rationale: String(raw.rationale || ""),
  };
}
