// HS-160-06 — review posture types: decode the window/proposal/delta
// shapes from the REAL wire (integration tests are the fixture truth).
// Discriminated review states per SRS §7's machine subset.

/* ── Wire proposal shape (from _load_frozen_window) ── */

export type ProposalKind =
  | "risk_attention"
  | "review_flag"
  | "observation_attention"
  | "conflict"
  | "coverage_degraded";

export type ProposalLifecycle =
  | "open"
  | "accepted"
  | "dismissed"
  | "deferred"
  | "superseded";

export type Proposal = {
  id: string;
  proposalKind: ProposalKind;
  targetRef: string;
  title: string;
  rationale: string;
  patchJson: Record<string, unknown>;
  materiality: string;
  producerKind: string;
  lifecycle: ProposalLifecycle;
};

export function decodeProposal(raw: Record<string, unknown>): Proposal {
  let patchJson: Record<string, unknown> = {};
  const rawPatch = raw.patch_json;
  if (typeof rawPatch === "string" && rawPatch) {
    try {
      patchJson = JSON.parse(rawPatch) as Record<string, unknown>;
    } catch {
      patchJson = {};
    }
  } else if (rawPatch && typeof rawPatch === "object") {
    patchJson = rawPatch as Record<string, unknown>;
  }
  return {
    id: String(raw.id ?? ""),
    proposalKind: String(raw.proposal_kind ?? "") as ProposalKind,
    targetRef: String(raw.target_ref ?? ""),
    title: String(raw.title ?? ""),
    rationale: String(raw.rationale ?? ""),
    patchJson,
    materiality: String(raw.materiality ?? "0"),
    producerKind: String(raw.producer_kind ?? ""),
    lifecycle: String(raw.lifecycle ?? "open") as ProposalLifecycle,
  };
}

/* ── Wire frozen window shape ── */

export type ReviewWindow = {
  reviewId: string;
  projectId: string;
  status: string;
  sourceManifest: Record<string, { state: string }>;
  materialityVersion: string;
  openedAt: string;
  proposals: Proposal[];
};

export function decodeReviewWindow(raw: Record<string, unknown>): ReviewWindow {
  const proposals = Array.isArray(raw.proposals)
    ? (raw.proposals as Record<string, unknown>[]).map(decodeProposal)
    : [];
  const manifest = (raw.source_manifest ?? {}) as Record<string, Record<string, unknown>>;
  const sourceManifest: Record<string, { state: string }> = {};
  for (const [k, v] of Object.entries(manifest)) {
    sourceManifest[k] = { state: String(v?.state ?? "unknown") };
  }
  return {
    reviewId: String(raw.review_id ?? ""),
    projectId: String(raw.project_id ?? ""),
    status: String(raw.status ?? ""),
    sourceManifest,
    materialityVersion: String(raw.materiality_version ?? ""),
    openedAt: String(raw.opened_at ?? ""),
    proposals,
  };
}

/* ── Delta empty state (GET /delta with no open review) ── */

export type DeltaEmpty = {
  openReview: null;
  lastAcceptedAt: string | null;
  sourceCoverage: Record<string, string> | null;
};

export function decodeDeltaEmpty(raw: Record<string, unknown>): DeltaEmpty {
  const sourceCoverage = raw.source_coverage
    ? Object.fromEntries(
        Object.entries(raw.source_coverage as Record<string, unknown>).map(
          ([k, v]) => [k, String(v ?? "unknown")],
        ),
      )
    : null;
  return {
    openReview: null,
    lastAcceptedAt: raw.last_accepted_at != null ? String(raw.last_accepted_at) : null,
    sourceCoverage,
  };
}

/* ── Delta response: either a window or the empty state ── */

export type DeltaResponse =
  | { kind: "window"; window: ReviewWindow }
  | { kind: "empty"; empty: DeltaEmpty };

export function decodeDelta(raw: Record<string, unknown>): DeltaResponse {
  // If open_review is explicitly null, it's the empty state
  if ("open_review" in raw && raw.open_review === null) {
    return { kind: "empty", empty: decodeDeltaEmpty(raw) };
  }
  // Otherwise it's a frozen window
  return { kind: "window", window: decodeReviewWindow(raw) };
}

/* ── Decision verb types ── */

export type DecisionVerb = "accept" | "edit_accept" | "defer" | "dismiss";

export type DecideBody = {
  verb: DecisionVerb;
  patch?: Record<string, unknown>;
  deferred_until?: string;
  command_id?: string;
};

export type DecideResult = {
  verb: string;
  lifecycle: ProposalLifecycle;
  dismissalBasisHash?: string;
};

export function decodeDecideResult(raw: Record<string, unknown>): DecideResult {
  return {
    verb: String(raw.verb ?? ""),
    lifecycle: String(raw.lifecycle ?? "open") as ProposalLifecycle,
    dismissalBasisHash: raw.dismissal_basis_hash != null
      ? String(raw.dismissal_basis_hash)
      : undefined,
  };
}

/* ── Accept review envelope ── */

export type AcceptResult = {
  resultKind: string;
  reviewId: string;
  acceptedAt: string;
};

export function decodeAcceptResult(raw: Record<string, unknown>): AcceptResult {
  return {
    resultKind: String(raw.result_kind ?? ""),
    reviewId: String(raw.review_id ?? ""),
    acceptedAt: String(raw.accepted_at ?? ""),
  };
}

/* ── Room review section data (extends model.ts's RoomSection) ── */

export type RoomReviewData = {
  pendingCount: number;
  openReviewId: string | null;
  lastAcceptedAt: string | null;
};

export function decodeRoomReviewData(raw: Record<string, unknown>): RoomReviewData {
  return {
    pendingCount: Number(raw.pending_count ?? 0),
    openReviewId: raw.open_review_id != null ? String(raw.open_review_id) : null,
    lastAcceptedAt: raw.last_accepted_at != null ? String(raw.last_accepted_at) : null,
  };
}

/* ── Discriminated review states (SRS §7 machine subset) ── */

/** idle: no delta, no open review */
export type ReviewStateIdle = { phase: "idle"; lastAcceptedAt: string | null };
/** queue_ready: pending proposals exist but no review opened yet */
export type ReviewStateQueueReady = {
  phase: "queue_ready";
  pendingCount: number;
  openReviewId: string | null;
};
/** reviewing: in the review posture, proposals being worked */
export type ReviewStateReviewing = {
  phase: "reviewing";
  window: ReviewWindow;
  selectedIndex: number;
};
/** deciding: a decision verb is in flight */
export type ReviewStateDeciding = {
  phase: "deciding";
  window: ReviewWindow;
  selectedIndex: number;
  proposalId: string;
};
/** exhausted: all proposals decided, awaiting Finish */
export type ReviewStateExhausted = {
  phase: "exhausted";
  window: ReviewWindow;
  dispositions: Map<string, DispositionEntry>;
};
/** checkpointed: review accepted, summary shown */
export type ReviewStateCheckpointed = {
  phase: "checkpointed";
  acceptedAt: string;
  dispositions: Map<string, DispositionEntry>;
};

export type ReviewState =
  | ReviewStateIdle
  | ReviewStateQueueReady
  | ReviewStateReviewing
  | ReviewStateDeciding
  | ReviewStateExhausted
  | ReviewStateCheckpointed;

/* ── Disposition tracking ── */

export type DispositionEntry = {
  verb: DecisionVerb;
  proposalId: string;
  proposalKind: ProposalKind;
  title: string;
  deferredUntil?: string;
  editedPatch?: Record<string, unknown>;
};

/* ── Proposal grouping by kind ── */

export type ProposalGroup = {
  kind: ProposalKind;
  label: string;
  count: number;
  proposals: Proposal[];
};

const KIND_LABELS: Record<ProposalKind, string> = {
  risk_attention: "Risk attention",
  review_flag: "Review flags",
  observation_attention: "Observations",
  conflict: "Conflicts",
  coverage_degraded: "Degraded coverage",
};

export function kindLabel(kind: ProposalKind): string {
  return KIND_LABELS[kind] ?? kind;
}

export function groupProposalsByKind(proposals: Proposal[]): ProposalGroup[] {
  const map = new Map<ProposalKind, Proposal[]>();
  for (const p of proposals) {
    const list = map.get(p.proposalKind);
    if (list) list.push(p);
    else map.set(p.proposalKind, [p]);
  }
  return Array.from(map.entries()).map(([kind, items]) => ({
    kind,
    label: kindLabel(kind),
    count: items.length,
    proposals: items,
  }));
}

/* ── Undo stack entry ── */

export type UndoEntry = {
  proposalId: string;
  verb: DecisionVerb;
  previousLifecycle: ProposalLifecycle;
};
