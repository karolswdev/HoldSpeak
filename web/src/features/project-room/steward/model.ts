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

export type StepState = "pending" | "running" | "completed" | "skipped" | "failed" | "interrupted";

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
  unattendedEnabled: boolean;
  createdAt: string | null;
  updatedAt: string | null;
};

/* ── Watch wire shape (subset for steward posture) ── */

export type StewardWatch = {
  id: string;
  name: string;
  connectorId: string;
  state: string;
  evaluationCadenceMinutes: number;
  circuitState: string;
  circuitFailureStreak: number;
  circuitOpenedAt: string | null;
};

/* ── Decoders ── */

function decodeSummary(raw: unknown): RunSummary {
  if (!raw || typeof raw !== "object") return {};
  const s = raw as Record<string, unknown>;
  // Spread the rest so unknown wire fields (phase_results, etc.) survive
  // for downstream consumers like coverageSummary.
  return {
    ...s,
    outcome: s.outcome != null ? String(s.outcome) : undefined,
    reason: s.reason != null ? String(s.reason) : undefined,
    phasesCompleted: Array.isArray(s.phases_completed)
      ? (s.phases_completed as unknown[]).map(String)
      : undefined,
    interruptedPhase: s.interrupted_phase != null
      ? String(s.interrupted_phase)
      : undefined,
    effectsApplied: decodeEffectsApplied(s),
  };
}

/** The applied-effects count lives in phase_results on the wire
 * (verify.actions_taken, else act.actions_taken); a top-level
 * effects_applied wins if a future wire version adds one. */
function decodeEffectsApplied(s: Record<string, unknown>): number | undefined {
  if (s.effects_applied != null) return Number(s.effects_applied);
  const pr = s.phase_results as Record<string, unknown> | undefined;
  for (const phase of ["verify", "act"]) {
    const body = pr?.[phase] as Record<string, unknown> | undefined;
    if (body && body.actions_taken != null) return Number(body.actions_taken);
  }
  return undefined;
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
    unattendedEnabled: Boolean(raw.unattended_enabled),
    createdAt: raw.created_at != null ? String(raw.created_at) : null,
    updatedAt: raw.updated_at != null ? String(raw.updated_at) : null,
  };
}

export function decodeWatch(raw: Record<string, unknown>): StewardWatch {
  return {
    id: String(raw.id ?? ""),
    name: String(raw.name ?? ""),
    connectorId: String(raw.connector_id ?? ""),
    state: String(raw.state ?? ""),
    evaluationCadenceMinutes: Number(raw.evaluation_cadence_minutes ?? 60),
    circuitState: String(raw.circuit_state ?? "closed"),
    circuitFailureStreak: Number(raw.circuit_failure_streak ?? 0),
    circuitOpenedAt: raw.circuit_opened_at != null
      ? String(raw.circuit_opened_at)
      : null,
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
  interrupted: "Interrupted",
};

export function stepStateLabel(state: string): string {
  return STEP_STATE_LABELS[state] ?? state.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

export function stepStateTone(state: string): string | undefined {
  if (state === "completed") return "ok";
  if (state === "failed" || state === "interrupted") return "danger";
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

/** Human substance for a run row secondary line.
 *  The primary line already carries the state token, so we never repeat it.
 *  Renders the effect count and/or the reason -- the two things that earn
 *  a secondary line's place. Returns null when there is nothing to say. */
export function runRowSubstance(run: StewardRun): string | null {
  const parts: string[] = [];
  if (run.summary.effectsApplied != null) {
    const n = run.summary.effectsApplied;
    parts.push(`${n} effect${n === 1 ? "" : "s"}`);
  }
  const reason = summaryReasonLabel(run.summary.reason);
  if (reason) parts.push(reason);
  return parts.length > 0 ? parts.join(", ") : null;
}

/* ── Honest pluralization ── */

/** "1 step" / "3 steps" -- honest grammar, no "1 STEPS". */
export function pluralize(n: number, singular: string, plural?: string): string {
  return `${n} ${n === 1 ? singular : (plural ?? singular + "s")}`;
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

/* ── Coverage: partial/degraded observe phase ── */

export type SourceCoverage = { source: string; state: string };

/** Extract per-source coverage from a run's summary.
 *  Wire shape: summary.phase_results.observe.coverage (object keyed by source name). */
export function runCoverage(run: StewardRun): SourceCoverage[] {
  const pr = run.summary as Record<string, unknown>;
  const phaseResults = pr.phase_results as Record<string, unknown> | undefined;
  if (!phaseResults) return [];
  const observe = phaseResults.observe as Record<string, unknown> | undefined;
  if (!observe) return [];
  const coverage = observe.coverage as Record<string, unknown> | undefined;
  if (!coverage || typeof coverage !== "object") return [];
  return Object.entries(coverage).map(([source, val]) => ({
    source,
    state: (val as Record<string, unknown>)?.state != null
      ? String((val as Record<string, unknown>).state)
      : "unknown",
  }));
}

/** Whether a step's observed state is partial (degraded). */
export function stepIsPartial(step: StewardStep): boolean {
  if (!step.observed || typeof step.observed !== "object") return false;
  return (step.observed as Record<string, unknown>).partial === true;
}

/** Coverage summary: "N of M sources answered" or null when clean. */
export function coverageSummary(run: StewardRun): string | null {
  const sources = runCoverage(run);
  if (sources.length === 0) return null;
  const ok = sources.filter((s) => s.state === "ok").length;
  if (ok === sources.length) return null;
  return `${ok} of ${sources.length} source${sources.length === 1 ? "" : "s"} answered`;
}

/* ── HS-164-05: provenance -- unattended vs manual ── */

/** The conductor's exact principal identity (from workbench_conductor.py:617). */
const CONDUCTOR_IDENTITY = "local-steward-conductor";

/** Whether a run was started by the unattended conductor (not a human click). */
export function isUnattendedRun(run: StewardRun): boolean {
  return run.requestedBy === `principal:${CONDUCTOR_IDENTITY}`;
}

/** Human provenance label: "Scheduled" for conductor runs, "Manual" for human. */
export function provenanceLabel(run: StewardRun): string {
  return isUnattendedRun(run) ? "Scheduled" : "Manual";
}

/** Tone for the provenance chip. */
export function provenanceTone(run: StewardRun): string | undefined {
  return isUnattendedRun(run) ? "info" : undefined;
}

/* ── HS-164-05: grant text assembly ── */

/** The eligible effect kinds as a human list (for the grant sentence).
 *  Uses the ACTIVE-VOICE labels that say what the steward MAY DO. */
const EFFECT_GRANT_LABELS: Record<string, string> = {
  refresh_sources: "refresh sources",
  create_proposals: "create proposals",
  apply_proposal_effects: "apply proposal effects",
  draft_update: "draft updates",
  create_door_item: "create door items",
};

function effectGrantLabel(kind: string): string {
  return EFFECT_GRANT_LABELS[kind] ?? kind.replace(/_/g, " ");
}

/** Assemble the grant text from real policy + watch state.
 *  The approval IS the label. Never a static sentence. */
export function assembleGrantText(
  policy: StewardPolicy,
  watches: StewardWatch[],
): string {
  if (!policy.unattendedEnabled) return "Unattended operation is off.";

  const parts: string[] = [];

  // Cadence: pick the smallest cadence from active watches, or default
  // The wire's evaluable states are "active" and "tested" (the
  // graduated family) -- "graduated" is prose, never a state value.
  const activeWatches = watches.filter((w) => w.state === "active" || w.state === "tested");
  const cadences = activeWatches.map((w) => w.evaluationCadenceMinutes).filter((c) => c > 0);
  const cadence = cadences.length > 0 ? Math.min(...cadences) : 60;
  parts.push(`every ${cadence} minutes`);

  // Effects
  const eligibleLabels = policy.eligibleEffectKinds.map(effectGrantLabel);
  if (eligibleLabels.length > 0) {
    parts.push(`the steward may ${eligibleLabels.join(", ")}`);
  } else {
    parts.push("no effects are eligible");
  }

  // Bounds
  parts.push(`at most ${policy.maxActionsPerRun} actions per run`);

  return `While enabled: ${parts.join(", ")}.`;
}

/* ── HS-164-05: circuit state labels ── */

const CIRCUIT_STATE_LABELS: Record<string, string> = {
  closed: "Healthy",
  open: "Circuit open",
  half_open: "Probing",
};

export function circuitStateLabel(state: string): string {
  return CIRCUIT_STATE_LABELS[state] ?? state.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

export function circuitStateTone(state: string): string | undefined {
  if (state === "closed") return "ok";
  if (state === "open") return "danger";
  if (state === "half_open") return "warn";
  return undefined;
}
