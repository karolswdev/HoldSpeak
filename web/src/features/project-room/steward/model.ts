// HS-163-05 -- the Steward posture types: decode the wire shapes from
// holdspeak/web/routes/steward.py (_serialize_run/_serialize_step/_serialize_policy).
// Human labels for every machine token -- no raw ids on glass, no enum
// strings where words belong.

/* ── Run wire shape ── */

export type RunState =
  | "queued"
  | "running"
  | "stopping"
  | "completed"
  | "interrupted"
  | "failed";

export type StewardRun = {
  id: string;
  projectId: string;
  policyId: string | null;
  state: RunState;
  phase: string;
  requestedBy: string;
  watermark: string;
  summary: RunSummary;
  createdAt: string | null;
  updatedAt: string | null;
  startedAt: string | null;
  completedAt: string | null;
  stopRequestedAt: string | null;
};

export type RunSummary = {
  outcome?: string;
  reason?: string;
  phasesCompleted?: string[];
  interruptedPhase?: string;
  effectsApplied?: number;
  [key: string]: unknown;
};

/* ── Step wire shape ── */

export type StepState = "pending" | "running" | "completed" | "skipped" | "failed";

export type StewardStep = {
  id: string;
  phase: string;
  seq: number;
  state: StepState;
  effectKind: string;
  idempotencyKey: string;
  expected: Record<string, unknown>;
  observed: Record<string, unknown>;
  receipt: StepReceipt;
  error: StepError | null;
};

export type StepReceipt = {
  action?: string;
  result?: string;
  ref?: string;
  refs?: string[];
  [key: string]: unknown;
};

export type StepError = {
  code?: string;
  message?: string;
  [key: string]: unknown;
};

/* ── Policy wire shape ── */

export type StewardPolicy = {
  id: string;
  projectId: string;
  eligibleEffectKinds: string[];
  yoloFlags: Record<string, unknown>;
  maxRetries: number;
  maxActionsPerRun: number;
  cooldownSeconds: number;
  bounds: Record<string, unknown>;
  enabled: boolean;
  createdAt: string | null;
  updatedAt: string | null;
};

/* ── Decoders ── */

function decodeSummary(raw: unknown): RunSummary {
  if (!raw || typeof raw !== "object") return {};
  const s = raw as Record<string, unknown>;
  return {
    outcome: s.outcome != null ? String(s.outcome) : undefined,
    reason: s.reason != null ? String(s.reason) : undefined,
    phasesCompleted: Array.isArray(s.phases_completed)
      ? (s.phases_completed as unknown[]).map(String)
      : undefined,
    interruptedPhase: s.interrupted_phase != null
      ? String(s.interrupted_phase)
      : undefined,
    effectsApplied: s.effects_applied != null
      ? Number(s.effects_applied)
      : undefined,
  };
}

export function decodeRun(raw: Record<string, unknown>): StewardRun {
  return {
    id: String(raw.id ?? ""),
    projectId: String(raw.project_id ?? ""),
    policyId: raw.policy_id != null ? String(raw.policy_id) : null,
    state: String(raw.state ?? "queued") as RunState,
    phase: String(raw.phase ?? ""),
    requestedBy: String(raw.requested_by ?? ""),
    watermark: String(raw.watermark ?? ""),
    summary: decodeSummary(raw.summary),
    createdAt: raw.created_at != null ? String(raw.created_at) : null,
    updatedAt: raw.updated_at != null ? String(raw.updated_at) : null,
    startedAt: raw.started_at != null ? String(raw.started_at) : null,
    completedAt: raw.completed_at != null ? String(raw.completed_at) : null,
    stopRequestedAt: raw.stop_requested_at != null
      ? String(raw.stop_requested_at)
      : null,
  };
}

export function decodeStep(raw: Record<string, unknown>): StewardStep {
  const receipt = (raw.receipt && typeof raw.receipt === "object"
    ? raw.receipt
    : {}) as StepReceipt;
  const error = (raw.error && typeof raw.error === "object"
    ? raw.error
    : null) as StepError | null;
  return {
    id: String(raw.id ?? ""),
    phase: String(raw.phase ?? ""),
    seq: Number(raw.seq ?? 0),
    state: String(raw.state ?? "pending") as StepState,
    effectKind: String(raw.effect_kind ?? ""),
    idempotencyKey: String(raw.idempotency_key ?? ""),
    expected: (raw.expected && typeof raw.expected === "object"
      ? raw.expected
      : {}) as Record<string, unknown>,
    observed: (raw.observed && typeof raw.observed === "object"
      ? raw.observed
      : {}) as Record<string, unknown>,
    receipt,
    error,
  };
}

export function decodePolicy(raw: Record<string, unknown>): StewardPolicy {
  return {
    id: String(raw.id ?? ""),
    projectId: String(raw.project_id ?? ""),
    eligibleEffectKinds: Array.isArray(raw.eligible_effect_kinds)
      ? (raw.eligible_effect_kinds as unknown[]).map(String)
      : [],
    yoloFlags: (raw.yolo_flags && typeof raw.yolo_flags === "object"
      ? raw.yolo_flags
      : {}) as Record<string, unknown>,
    maxRetries: Number(raw.max_retries ?? 3),
    maxActionsPerRun: Number(raw.max_actions_per_run ?? 10),
    cooldownSeconds: Number(raw.cooldown_seconds ?? 0),
    bounds: (raw.bounds && typeof raw.bounds === "object"
      ? raw.bounds
      : {}) as Record<string, unknown>,
    enabled: Boolean(raw.enabled),
    createdAt: raw.created_at != null ? String(raw.created_at) : null,
    updatedAt: raw.updated_at != null ? String(raw.updated_at) : null,
  };
}

/* ── Human labels: effect kinds ── */

const EFFECT_KIND_LABELS: Record<string, string> = {
  refresh_sources: "Refreshed sources",
  create_proposals: "Created proposals",
  apply_proposal_effects: "Applied proposal effects",
  draft_update: "Drafted update",
  create_door_item: "Door item created",
};

/** Effect kind as words a Senior Architect reads on a Tuesday. */
export function effectKindLabel(kind: string): string {
  // Phase-prefixed steps from the integration test fixtures
  if (kind.startsWith("phase:")) {
    const phase = kind.slice("phase:".length);
    return phaseLabel(phase);
  }
  return EFFECT_KIND_LABELS[kind] ?? kind.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

/** Whether this effect kind touches a model (needs egress badge). */
export function isModelTouchingKind(kind: string): boolean {
  return kind === "create_proposals" || kind === "draft_update";
}

/* ── Human labels: phases ── */

const PHASE_LABELS: Record<string, string> = {
  observe: "Observe",
  compare: "Compare",
  propose: "Propose",
  act: "Act",
  verify: "Verify",
  record: "Record",
};

/** Six-phase label. */
export function phaseLabel(phase: string): string {
  return PHASE_LABELS[phase] ?? phase.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

/* ── Human labels: run states ── */

const RUN_STATE_LABELS: Record<string, string> = {
  queued: "Queued",
  running: "Running",
  stopping: "Stopping",
  completed: "Completed",
  interrupted: "Interrupted",
  failed: "Failed",
};

export function runStateLabel(state: string): string {
  return RUN_STATE_LABELS[state] ?? state.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

export function runStateTone(state: string): string | undefined {
  if (state === "completed") return "ok";
  if (state === "failed" || state === "interrupted") return "danger";
  if (state === "stopping") return "warn";
  return undefined;
}

/* ── Human labels: step states ── */

const STEP_STATE_LABELS: Record<string, string> = {
  pending: "Pending",
  running: "Running",
  completed: "Completed",
  skipped: "Skipped",
  failed: "Failed",
};

export function stepStateLabel(state: string): string {
  return STEP_STATE_LABELS[state] ?? state.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

export function stepStateTone(state: string): string | undefined {
  if (state === "completed") return "ok";
  if (state === "failed") return "danger";
  if (state === "skipped") return "warn";
  return undefined;
}

/* ── Human labels: summary reasons ── */

const SUMMARY_REASON_LABELS: Record<string, string> = {
  stop_requested: "Stopped by you",
  max_actions_per_run_exceeded: "Action limit reached",
  max_retries_exceeded: "Retry limit reached",
  no_eligible_effects: "No eligible effects configured",
  all_effects_skipped: "All effects were skipped",
  policy_disabled: "Policy is disabled",
};

/** Translate a machine reason to a sentence fragment. */
export function summaryReasonLabel(reason: string | undefined): string | null {
  if (!reason) return null;
  return SUMMARY_REASON_LABELS[reason] ?? reason.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

/* ── Run summary for list rows ── */

/** Human summary for a run row: "Today 09:14, completed, 2 effects". */
export function runRowSummary(run: StewardRun): string {
  const parts: string[] = [];
  parts.push(runStateLabel(run.state));
  if (run.summary.effectsApplied != null) {
    const n = run.summary.effectsApplied;
    parts.push(`${n} effect${n === 1 ? "" : "s"}`);
  }
  const reason = summaryReasonLabel(run.summary.reason);
  if (reason) parts.push(reason);
  return parts.join(", ");
}

/* ── Terminal state check ── */

/** Whether a run state is terminal (polling should stop). */
export function isTerminal(state: string): boolean {
  return state === "completed" || state === "interrupted" || state === "failed";
}

/** Whether a run is active (button should be disabled). */
export function isActive(state: string): boolean {
  return state === "queued" || state === "running" || state === "stopping";
}

/* ── Receipt subject refs ── */

/** Extract openable source refs from a step's receipt.
 *  Receipts carry refs as `ref` (single) or `refs` (array). */
export function receiptRefs(step: StewardStep): string[] {
  const refs: string[] = [];
  if (step.receipt.ref && typeof step.receipt.ref === "string") {
    refs.push(step.receipt.ref);
  }
  if (Array.isArray(step.receipt.refs)) {
    for (const r of step.receipt.refs) {
      if (typeof r === "string" && !refs.includes(r)) refs.push(r);
    }
  }
  return refs;
}

/* ── The five canonical effect kinds (mirrors backend EFFECT_KINDS) ── */

export const EFFECT_KINDS: readonly string[] = [
  "refresh_sources",
  "create_proposals",
  "apply_proposal_effects",
  "draft_update",
  "create_door_item",
];
