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

/* ── Room snapshot types (WEB-ARC-004 discriminated section states) ── */

/** Section state vocabulary (CONTRACTS-P0 SS6.2). */
export type SectionStateOk = "ok";
export type SectionStateDegraded = "degraded";
export type SectionStateAbsent = "absent";
export type SectionState = SectionStateOk | SectionStateDegraded | SectionStateAbsent;

/** An ok section carries its data alongside state:"ok". */
export type OkSection<T> = T & { state: SectionStateOk };

/** A degraded section: the sub-read failed (NFR-003). */
export type DegradedSection = { state: SectionStateDegraded; error_code: string };

/** An absent section: domain not yet built (Art VI, NFR-006). */
export type AbsentSection = { state: SectionStateAbsent; reason: string };

/** Discriminated union for any section in the room snapshot. */
export type RoomSection<T> = OkSection<T> | DegradedSection | AbsentSection;

/** The project orientation block from /room. */
export type RoomProjectOrientation = {
  id: string;
  name: string;
  description: string | null;
  isArchived: boolean;
  meetingCount: number;
  createdAt: string;
  updatedAt: string;
  // SS5.1 room fields (nullable)
  purpose: string | null;
  outcomeText: string | null;
  ownerRef: string | null;
  lifecycle: string | null;
  posture: string | null;
  postureReason: string | null;
  startAt: string | null;
  targetAt: string | null;
  revision: number;
};

/** Focus item from the items section. */
export type RoomFocusItem = {
  id: string;
  projectId: string;
  itemType: string;
  title: string;
  severity: string | null;
  dueAt: string | null;
  sortKey: number | null;
  createdAt: string;
};

/** Items section data shape (when ok). */
export type RoomItemsData = {
  focus: RoomFocusItem[];
  totalsByType: Record<string, number>;
  total: number;
};

/** Meetings section data shape (when ok). */
export type RoomMeetingsData = {
  count: number;
  latest: Record<string, unknown> | null;
};

/** Resources section data shape (when ok). */
export type RoomResourcesData = {
  count: number;
  latest: Record<string, unknown> | null;
};

/** Changes section data shape (when ok). */
export type RoomChangesData = {
  recent: Record<string, unknown>[];
};

/** The full room snapshot (typed, WEB-ARC-004). */
export type RoomSnapshot = {
  projectId: string;
  revision: number;
  observedAt: string;
  project: RoomProjectOrientation;
  items: RoomSection<RoomItemsData>;
  meetings: RoomSection<RoomMeetingsData>;
  resources: RoomSection<RoomResourcesData>;
  changes: RoomSection<RoomChangesData>;
  review: RoomSection<Record<string, never>>;
  sources: RoomSection<Record<string, never>>;
  updates: RoomSection<Record<string, never>>;
  steward: RoomSection<Record<string, never>>;
};

/* ── Room snapshot decoder ── */

function decodeOrientation(raw: Record<string, unknown>): RoomProjectOrientation {
  return {
    id: String(raw.id ?? ""),
    name: String(raw.name ?? ""),
    description: raw.description != null ? String(raw.description) : null,
    isArchived: Boolean(raw.is_archived),
    meetingCount: Number(raw.meeting_count ?? 0),
    createdAt: String(raw.created_at ?? ""),
    updatedAt: String(raw.updated_at ?? ""),
    purpose: raw.purpose != null ? String(raw.purpose) : null,
    outcomeText: raw.outcome_text != null ? String(raw.outcome_text) : null,
    ownerRef: raw.owner_ref != null ? String(raw.owner_ref) : null,
    lifecycle: raw.lifecycle != null ? String(raw.lifecycle) : null,
    posture: raw.posture != null ? String(raw.posture) : null,
    postureReason: raw.posture_reason != null ? String(raw.posture_reason) : null,
    startAt: raw.start_at != null ? String(raw.start_at) : null,
    targetAt: raw.target_at != null ? String(raw.target_at) : null,
    revision: Number(raw.revision ?? 0),
  };
}

function decodeFocusItem(raw: Record<string, unknown>): RoomFocusItem {
  return {
    id: String(raw.id ?? ""),
    projectId: String(raw.project_id ?? ""),
    itemType: String(raw.item_type ?? ""),
    title: String(raw.title ?? ""),
    severity: raw.severity != null ? String(raw.severity) : null,
    dueAt: raw.due_at != null ? String(raw.due_at) : null,
    sortKey: raw.sort_key != null ? Number(raw.sort_key) : null,
    createdAt: String(raw.created_at ?? ""),
  };
}

function decodeSection<T>(
  raw: unknown,
  decodeData: (section: Record<string, unknown>) => T,
): RoomSection<T> {
  if (!raw || typeof raw !== "object") {
    return { state: "absent", reason: "missing" };
  }
  const section = raw as Record<string, unknown>;
  const state = String(section.state ?? "absent");
  if (state === "absent") {
    return { state: "absent", reason: String(section.reason ?? "unknown") };
  }
  if (state === "degraded") {
    return { state: "degraded", error_code: String(section.error_code ?? "unknown") };
  }
  return { state: "ok", ...decodeData(section) };
}

/** Decode a raw /room JSON response into a typed RoomSnapshot (WEB-ARC-004). */
export function decodeRoomSnapshot(raw: Record<string, unknown>): RoomSnapshot {
  const project = (raw.project ?? {}) as Record<string, unknown>;
  return {
    projectId: String(raw.project_id ?? ""),
    revision: Number(raw.revision ?? 0),
    observedAt: String(raw.observed_at ?? ""),
    project: decodeOrientation(project),
    items: decodeSection<RoomItemsData>(raw.items, (s) => ({
      focus: Array.isArray(s.focus) ? s.focus.map((r: unknown) => decodeFocusItem(r as Record<string, unknown>)) : [],
      totalsByType: (s.totals_by_type && typeof s.totals_by_type === "object")
        ? Object.fromEntries(
            Object.entries(s.totals_by_type as Record<string, unknown>).map(
              ([k, v]) => [k, Number(v ?? 0)],
            ),
          )
        : {},
      total: Number(s.total ?? 0),
    })),
    meetings: decodeSection<RoomMeetingsData>(raw.meetings, (s) => ({
      count: Number(s.count ?? 0),
      latest: (s.latest && typeof s.latest === "object") ? s.latest as Record<string, unknown> : null,
    })),
    resources: decodeSection<RoomResourcesData>(raw.resources, (s) => ({
      count: Number(s.count ?? 0),
      latest: (s.latest && typeof s.latest === "object") ? s.latest as Record<string, unknown> : null,
    })),
    changes: decodeSection<RoomChangesData>(raw.changes, (s) => ({
      recent: Array.isArray(s.recent) ? s.recent as Record<string, unknown>[] : [],
    })),
    review: decodeSection<Record<string, never>>(raw.review, () => ({} as Record<string, never>)),
    sources: decodeSection<Record<string, never>>(raw.sources, () => ({} as Record<string, never>)),
    updates: decodeSection<Record<string, never>>(raw.updates, () => ({} as Record<string, never>)),
    steward: decodeSection<Record<string, never>>(raw.steward, () => ({} as Record<string, never>)),
  };
}

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
