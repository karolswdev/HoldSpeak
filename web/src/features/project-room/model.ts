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

/** One decoded aggregate change (wire: change_kind/summary_json/created_at). */
export type RoomChangeRow = {
  id: string;
  kind: string;
  label: string;
  occurredAt: string | null;
};

const CHANGE_KIND_LABELS: Record<string, string> = {
  "project.created": "Created",
  "project.updated": "Updated",
  "project.archived": "Archived",
  "project.restored": "Restored",
  "project.resource.linked": "Resource linked",
  "project.resource.unlinked": "Resource unlinked",
};

function humanizeValue(v: unknown): string {
  return String(v).replace(/[._]/g, " ").replace(/^./, (c) => c.toUpperCase());
}

function changeLabel(kind: string, summary: Record<string, unknown>): string {
  // Action-shaped summaries (item mutations): the VALUES are the story.
  if (typeof summary.action === "string" && summary.action) {
    const action = humanizeValue(summary.action);
    const itemType = typeof summary.item_type === "string" && summary.item_type
      ? ` · ${String(summary.item_type)}` : "";
    return `${action}${itemType}`;
  }
  const base = CHANGE_KIND_LABELS[kind]
    ?? (kind.split(".").pop() ?? "Change").replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
  // Field-patch summaries: the changed field NAMES are the story.
  const fields = Object.keys(summary);
  if (fields.length === 0) return base;
  return `${base} · ${fields.slice(0, 3).join(", ")}${fields.length > 3 ? "…" : ""}`;
}

export function decodeChangeRow(raw: Record<string, unknown>): RoomChangeRow {
  const kind = String(raw.change_kind ?? "");
  let summary: Record<string, unknown> = {};
  const rawSummary = raw.summary_json;
  if (typeof rawSummary === "string" && rawSummary) {
    try { summary = JSON.parse(rawSummary) as Record<string, unknown>; } catch { summary = {}; }
  } else if (rawSummary && typeof rawSummary === "object") {
    summary = rawSummary as Record<string, unknown>;
  }
  return {
    id: String(raw.id ?? ""),
    kind,
    label: changeLabel(kind, summary),
    occurredAt: raw.created_at ? String(raw.created_at) : null,
  };
}

/** Changes section data shape (when ok). */
export type RoomChangesData = {
  recent: RoomChangeRow[];
};

/** Review section data shape (when ok) — HS-160-06. */
export type RoomReviewData = {
  pendingCount: number;
  openReviewId: string | null;
  lastAcceptedAt: string | null;
};

/* ── HS-169-04: the four questions ── */

/** A "needs you" row: something the owner must act on. */
export type RoomNeedsYouItem = {
  source: string;
  title: string;
  why: string;
  since: string;
  url: string | null;
  verb: "open" | "decide";
  severity: "danger" | "warning" | "info";
};

/** Needs-you section data shape (when ok). */
export type RoomNeedsYouData = {
  items: RoomNeedsYouItem[];
  count: number;
};

/** A source row: per-Watch status. */
export type RoomSourceItem = {
  watchId: string;
  provider: string;
  scope: string;
  tokens: string[];
  checkedAt: string | null;
  nextCheckAt: string | null;
  host: string;
  state: "live" | "paused" | "cant_check";
  plainReason: string | null;
  suggested: boolean;
};

/** Sources section data shape (when ok). */
export type RoomSourcesData = {
  items: RoomSourceItem[];
  count: number;
  nextCheckAt: string | null;
};

/** Health derivation. */
export type RoomHealthData = {
  assessment: "at_risk" | "on_track";
  reason: string | null;
  inputs: {
    overdue: number;
    ciFailing: boolean;
    reviewWaitingDays: number | null;
    targetPassed: boolean;
  };
};

/** A since-read entry. */
export type RoomSinceReadEntry = {
  phrase: string;
  at: string;
  url: string | null;
};

/** A since-read group. */
export type RoomSinceReadGroup = {
  source: string;
  summary: string;
  entries: RoomSinceReadEntry[];
};

/** Since-read section data shape. */
export type RoomSinceReadData = {
  readAt: string | null;
  groups: RoomSinceReadGroup[];
};

/** A decision row. */
export type RoomDecisionItem = {
  id: string;
  text: string;
  at: string;
  url: string | null;
};

/** A commitment row. */
export type RoomCommitmentItem = {
  id: string;
  text: string;
  dueAt: string | null;
  owner: string | null;
};

/** Target section data. */
export type RoomTargetData = {
  targetAt: string | null;
  daysLeft: number | null;
  passed: boolean;
};

/** The full room snapshot (typed, WEB-ARC-004). */
export type RoomSnapshot = {
  projectId: string;
  revision: number;
  observedAt: string;
  nextCheckAt: string | null;
  project: RoomProjectOrientation;
  items: RoomSection<RoomItemsData>;
  meetings: RoomSection<RoomMeetingsData>;
  resources: RoomSection<RoomResourcesData>;
  changes: RoomSection<RoomChangesData>;
  review: RoomSection<RoomReviewData>;
  // HS-169-04: the four questions
  needsYou: RoomSection<RoomNeedsYouData>;
  sources: RoomSection<RoomSourcesData>;
  health: RoomSection<RoomHealthData>;
  sinceRead: RoomSection<RoomSinceReadData>;
  decisions: RoomSection<{ items: RoomDecisionItem[] }>;
  commitments: RoomSection<{ items: RoomCommitmentItem[] }>;
  target: RoomSection<RoomTargetData>;
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
    nextCheckAt: raw.nextCheckAt != null ? String(raw.nextCheckAt) : null,
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
      recent: Array.isArray(s.recent)
        ? (s.recent as Record<string, unknown>[]).map(decodeChangeRow)
        : [],
    })),
    review: decodeSection<RoomReviewData>(raw.review, (s) => ({
      pendingCount: Number(s.pending_count ?? 0),
      openReviewId: s.open_review_id != null ? String(s.open_review_id) : null,
      lastAcceptedAt: s.last_accepted_at != null ? String(s.last_accepted_at) : null,
    })),
    // HS-169-04: the four questions
    needsYou: decodeSection<RoomNeedsYouData>(raw.needsYou, (s) => ({
      items: Array.isArray(s.items)
        ? (s.items as Record<string, unknown>[]).map((r) => ({
            source: String(r.source ?? ""),
            title: String(r.title ?? ""),
            why: String(r.why ?? ""),
            since: String(r.since ?? ""),
            url: r.url != null ? String(r.url) : null,
            verb: (r.verb === "decide" ? "decide" : "open") as "open" | "decide",
            severity: (["danger", "warning", "info"].includes(String(r.severity ?? ""))
              ? String(r.severity) : "info") as "danger" | "warning" | "info",
          }))
        : [],
      count: Number(s.count ?? 0),
    })),
    sources: decodeSection<RoomSourcesData>(raw.sources, (s) => ({
      items: Array.isArray(s.items)
        ? (s.items as Record<string, unknown>[]).map((r) => ({
            watchId: String(r.watchId ?? ""),
            provider: String(r.provider ?? ""),
            scope: String(r.scope ?? ""),
            tokens: Array.isArray(r.tokens) ? (r.tokens as unknown[]).map(String) : [],
            checkedAt: r.checkedAt != null ? String(r.checkedAt) : null,
            nextCheckAt: r.nextCheckAt != null ? String(r.nextCheckAt) : null,
            host: String(r.host ?? ""),
            state: (["live", "paused", "cant_check"].includes(String(r.state ?? ""))
              ? String(r.state) : "live") as "live" | "paused" | "cant_check",
            plainReason: r.plainReason != null ? String(r.plainReason) : null,
            suggested: Boolean(r.suggested),
          }))
        : [],
      count: Number(s.count ?? 0),
      nextCheckAt: s.nextCheckAt != null ? String(s.nextCheckAt) : null,
    })),
    health: decodeSection<RoomHealthData>(raw.health, (s) => ({
      assessment: (s.assessment === "at_risk" ? "at_risk" : "on_track") as "at_risk" | "on_track",
      reason: s.reason != null ? String(s.reason) : null,
      inputs: {
        overdue: Number((s.inputs as Record<string, unknown> | undefined)?.overdue ?? 0),
        ciFailing: Boolean((s.inputs as Record<string, unknown> | undefined)?.ciFailing),
        reviewWaitingDays: (s.inputs as Record<string, unknown> | undefined)?.reviewWaitingDays != null
          ? Number((s.inputs as Record<string, unknown>).reviewWaitingDays) : null,
        targetPassed: Boolean((s.inputs as Record<string, unknown> | undefined)?.targetPassed),
      },
    })),
    sinceRead: decodeSection<RoomSinceReadData>(raw.sinceRead, (s) => ({
      readAt: s.readAt != null ? String(s.readAt) : null,
      groups: Array.isArray(s.groups)
        ? (s.groups as Record<string, unknown>[]).map((g) => ({
            source: String(g.source ?? ""),
            summary: String(g.summary ?? ""),
            entries: Array.isArray(g.entries)
              ? (g.entries as Record<string, unknown>[]).map((e) => ({
                  phrase: String(e.phrase ?? ""),
                  at: String(e.at ?? ""),
                  url: e.url != null ? String(e.url) : null,
                }))
              : [],
          }))
        : [],
    })),
    decisions: decodeSection<{ items: RoomDecisionItem[] }>(raw.decisions, (s) => ({
      items: Array.isArray(s.items)
        ? (s.items as Record<string, unknown>[]).map((r) => ({
            id: String(r.id ?? ""),
            text: String(r.text ?? ""),
            at: String(r.at ?? ""),
            url: r.url != null ? String(r.url) : null,
          }))
        : [],
    })),
    commitments: decodeSection<{ items: RoomCommitmentItem[] }>(raw.commitments, (s) => ({
      items: Array.isArray(s.items)
        ? (s.items as Record<string, unknown>[]).map((r) => ({
            id: String(r.id ?? ""),
            text: String(r.text ?? ""),
            dueAt: r.dueAt != null ? String(r.dueAt) : null,
            owner: r.owner != null ? String(r.owner) : null,
          }))
        : [],
    })),
    target: decodeSection<RoomTargetData>(raw.target, (s) => ({
      targetAt: s.targetAt != null ? String(s.targetAt) : null,
      daysLeft: s.daysLeft != null ? Number(s.daysLeft) : null,
      passed: Boolean(s.passed),
    })),
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
