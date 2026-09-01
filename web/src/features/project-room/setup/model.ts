// HS-159-05 -- setup domain types and decoders (WEB-ARC-004).
// Decode from the REAL wire shapes mined from integration tests
// (tests/integration/test_project_setup_routes.py) and the service
// (holdspeak/services/project_setup_service.py).

/* ── Stage machine (SRS SS5) ── */

export const STAGES = ["outcome", "signals", "proposals", "review"] as const;
export type SetupStage = (typeof STAGES)[number];

export const SESSION_STATES = ["active", "completed", "abandoned", "expired"] as const;
export type SessionState = (typeof SESSION_STATES)[number];

/* ── Question IDs (SRS SS4.1) ── */

export const Q_OUTCOME = "outcome" as const;
export const Q_SIGNALS = "signals" as const;

export const QUESTION_TEXT: Record<string, string> = {
  [Q_OUTCOME]: "What outcome are you trying to create or protect?",
  [Q_SIGNALS]: "What would you want HoldSpeak to notice without being asked?",
};

/* ── Cadence presets (SRS SS4.1) ── */

export type CadencePresetKey = "active_work" | "normal" | "daily" | "weekdays";

export const CADENCE_PRESETS: Record<CadencePresetKey, { label: string; minutes: number; weekdaysOnly?: boolean }> = {
  active_work: { label: "Active work", minutes: 15 },
  normal: { label: "Normal", minutes: 35 },
  daily: { label: "Daily", minutes: 1440 },
  weekdays: { label: "Weekdays", minutes: 1440, weekdaysOnly: true },
};

/* ── Action choices (SRS SS4, V0) ── */

export type ActionKind =
  | "project.observe"
  | "project.propose"
  | "project.steward.run_once"
  | "project.update.draft"
  | "door.add_item"
  | "workbench.add_item";

export const ACTION_LABELS: Record<string, string> = {
  "project.observe": "Put it in Project attention",
  "project.propose": "Propose an action",
  "project.steward.run_once": "Run the Project Steward",
  "project.update.draft": "Draft the next update",
  "door.add_item": "Create follow-through",
  "workbench.add_item": "Add to Workbench",
};

/* ── Watch spec sub-types ── */

export type WatchSubject = {
  kind: string;
  scope?: Record<string, unknown>;
};

export type WatchTrigger = {
  kind: string;
  everyMinutes?: number;
  weekdaysOnly?: boolean;
};

export type WatchConditionClause = {
  field: string;
  comparison: string;
  value?: unknown;
};

export type WatchCondition = {
  schema: string;
  operator: string;
  clauses: WatchConditionClause[];
};

export type WatchAction = {
  schema: string;
  kind: string;
};

export type WatchRule = {
  condition: WatchCondition;
  actions: WatchAction[];
};

export type WatchSpec = {
  schema: string;
  name: string;
  intent: string;
  provider: { id: string; transport: string };
  subject: WatchSubject;
  trigger: WatchTrigger;
  rules: WatchRule[];
  action: WatchAction;
  mode: string;
};

/* ── Answer ── */

export type AnswerPayload = {
  original: string;
  normalized: string;
};

export type SetupAnswer = {
  id: string;
  sessionId: string;
  questionId: string;
  answerSchema: string;
  answer: AnswerPayload;
  revision: number;
  createdAt: string;
};

/* ── Proposal rationale ── */

export type ProposalRationale = {
  fact: string;
  detail: string;
  subjectCount: number;
};

/* ── Test result ── */

export type TestResult = {
  entityCount: number;
  representativeEntities: Record<string, unknown>[];
  observedAt: string;
  error: { type: string; message: string } | null;
  message: string;
};

/* ── Watch states for the live brief (INT-011) ── */

export type WatchBriefState =
  | "mentioned"
  | "proposed"
  | "tested"
  | "disabled"
  | "active";

/* ── Proposal ── */

export type SetupProposal = {
  id: string;
  sessionId: string;
  providerId: string;
  specSchema: string;
  spec: WatchSpec;
  rationale: ProposalRationale;
  state: string;
  testState: string | null;
  testResult: TestResult | null;
  createdAt: string;
  updatedAt: string;
};

/* ── Session ── */

export type SetupSession = {
  id: string;
  state: SessionState;
  stage: SetupStage;
  draftSchema: string;
  expiresAt: string;
  projectId: string | null;
  createdAt: string;
  updatedAt: string;
  answers: Record<string, SetupAnswer>;
  proposals: SetupProposal[];
};

/* ── Finalize envelope ── */

export type FinalizeEnvelope = {
  projectId: string;
  resultKind: string;
  projectRevision: number;
  changedRefs: string[];
  refusedProposals: { id: string; testState: string }[];
};

/* ── Test result response ── */

export type TestResultResponse = {
  proposalId: string;
  testState: string;
  result: TestResult;
};

/* ================================================================== */
/* Decoders -- defensive: handle both string and parsed JSON fields   */
/* ================================================================== */

function parseJsonField(raw: unknown): Record<string, unknown> {
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw) as Record<string, unknown>;
    } catch {
      return {};
    }
  }
  if (raw && typeof raw === "object") return raw as Record<string, unknown>;
  return {};
}

export function decodeAnswer(raw: Record<string, unknown>): SetupAnswer {
  // The backend repo parses answer_json -> answer via _payload
  const answerData = parseJsonField(raw.answer ?? raw.answer_json);
  return {
    id: String(raw.id ?? ""),
    sessionId: String(raw.session_id ?? ""),
    questionId: String(raw.question_id ?? ""),
    answerSchema: String(raw.answer_schema ?? ""),
    answer: {
      original: String(answerData.original ?? ""),
      normalized: String(answerData.normalized ?? ""),
    },
    revision: Number(raw.revision ?? 0),
    createdAt: String(raw.created_at ?? ""),
  };
}

export function decodeWatchSpec(raw: Record<string, unknown>): WatchSpec {
  const provider = (raw.provider ?? {}) as Record<string, unknown>;
  const subject = (raw.subject ?? {}) as Record<string, unknown>;
  const trigger = (raw.trigger ?? {}) as Record<string, unknown>;
  const actionRaw = (raw.action ?? {}) as Record<string, unknown>;
  const rulesRaw = Array.isArray(raw.rules) ? raw.rules : [];

  return {
    schema: String(raw.schema ?? ""),
    name: String(raw.name ?? ""),
    intent: String(raw.intent ?? ""),
    provider: {
      id: String(provider.id ?? ""),
      transport: String(provider.transport ?? ""),
    },
    subject: {
      kind: String(subject.kind ?? ""),
      scope: subject.scope as Record<string, unknown> | undefined,
    },
    trigger: {
      kind: String(trigger.kind ?? ""),
      everyMinutes: trigger.every_minutes != null ? Number(trigger.every_minutes) : undefined,
      weekdaysOnly: trigger.weekdays_only != null ? Boolean(trigger.weekdays_only) : undefined,
    },
    rules: rulesRaw.map((r: Record<string, unknown>) => {
      const cond = (r.condition ?? {}) as Record<string, unknown>;
      return {
        condition: {
          schema: String(cond.schema ?? ""),
          operator: String(cond.operator ?? ""),
          clauses: Array.isArray(cond.clauses)
            ? cond.clauses.map((cl: Record<string, unknown>) => ({
                field: String(cl.field ?? ""),
                comparison: String(cl.comparison ?? ""),
                value: cl.value,
              }))
            : [],
        },
        actions: Array.isArray(r.actions)
          ? r.actions.map((a: Record<string, unknown>) => ({
              schema: String(a.schema ?? ""),
              kind: String(a.kind ?? ""),
            }))
          : [],
      };
    }),
    action: {
      schema: String(actionRaw.schema ?? ""),
      kind: String(actionRaw.kind ?? ""),
    },
    mode: String(raw.mode ?? "yolo"),
  };
}

export function decodeRationale(raw: Record<string, unknown>): ProposalRationale {
  return {
    fact: String(raw.fact ?? ""),
    detail: String(raw.detail ?? ""),
    subjectCount: Number(raw.subject_count ?? 0),
  };
}

export function decodeTestResult(raw: Record<string, unknown>): TestResult {
  const errorRaw = raw.error;
  return {
    entityCount: Number(raw.entity_count ?? 0),
    representativeEntities: Array.isArray(raw.representative_entities)
      ? raw.representative_entities
      : [],
    observedAt: String(raw.observed_at ?? ""),
    error:
      errorRaw && typeof errorRaw === "object"
        ? {
            type: String((errorRaw as Record<string, unknown>).type ?? ""),
            message: String((errorRaw as Record<string, unknown>).message ?? ""),
          }
        : null,
    message: String(raw.message ?? ""),
  };
}

export function decodeProposal(raw: Record<string, unknown>): SetupProposal {
  const specData = parseJsonField(raw.spec ?? raw.spec_json);
  const rationaleData = parseJsonField(raw.rationale ?? raw.rationale_json);
  const testResultRaw = raw.test_result ?? raw.test_result_json;
  const testResultData =
    testResultRaw != null ? parseJsonField(testResultRaw) : null;

  return {
    id: String(raw.id ?? ""),
    sessionId: String(raw.session_id ?? ""),
    providerId: String(raw.provider_id ?? ""),
    specSchema: String(raw.spec_schema ?? ""),
    spec: decodeWatchSpec(specData),
    rationale: decodeRationale(rationaleData),
    state: String(raw.state ?? "proposed"),
    testState: raw.test_state != null ? String(raw.test_state) : null,
    testResult: testResultData != null ? decodeTestResult(testResultData) : null,
    createdAt: String(raw.created_at ?? ""),
    updatedAt: String(raw.updated_at ?? ""),
  };
}

export function decodeSession(raw: Record<string, unknown>): SetupSession {
  // Answers: keyed by question_id
  const answersRaw = (raw.answers ?? {}) as Record<string, Record<string, unknown>>;
  const answers: Record<string, SetupAnswer> = {};
  for (const [qid, aRaw] of Object.entries(answersRaw)) {
    if (aRaw && typeof aRaw === "object") {
      answers[qid] = decodeAnswer(aRaw);
    }
  }

  // Proposals: array
  const proposalsRaw = Array.isArray(raw.proposals) ? raw.proposals : [];
  const proposals = proposalsRaw.map((p: Record<string, unknown>) =>
    decodeProposal(p),
  );

  const stage = String(raw.stage ?? "outcome");

  return {
    id: String(raw.id ?? ""),
    state: String(raw.state ?? "active") as SessionState,
    stage: STAGES.includes(stage as SetupStage) ? (stage as SetupStage) : "outcome",
    draftSchema: String(raw.draft_schema ?? ""),
    expiresAt: String(raw.expires_at ?? ""),
    projectId: raw.project_id != null ? String(raw.project_id) : null,
    createdAt: String(raw.created_at ?? ""),
    updatedAt: String(raw.updated_at ?? ""),
    answers,
    proposals,
  };
}

export function decodeTestResultResponse(
  raw: Record<string, unknown>,
): TestResultResponse {
  const resultRaw = parseJsonField(raw.result);
  return {
    proposalId: String(raw.proposal_id ?? ""),
    testState: String(raw.test_state ?? ""),
    result: decodeTestResult(resultRaw),
  };
}

export function decodeFinalizeEnvelope(
  raw: Record<string, unknown>,
): FinalizeEnvelope {
  const refused = Array.isArray(raw.refused_proposals)
    ? raw.refused_proposals.map((r: Record<string, unknown>) => ({
        id: String(r.id ?? ""),
        testState: String(r.test_state ?? ""),
      }))
    : [];
  return {
    projectId: String(raw.project_id ?? raw.id ?? ""),
    resultKind: String(raw.result_kind ?? ""),
    projectRevision: Number(raw.project_revision ?? 0),
    changedRefs: Array.isArray(raw.changed_refs)
      ? raw.changed_refs.map(String)
      : [],
    refusedProposals: refused,
  };
}

/* ── Project name inference (mirrors server: outcome_text[:80] or "New Project") ── */

/** Derive the project name the server will use at finalize.
 *  The finalize API does NOT accept a name override; this is read-only. */
export function inferProjectName(outcomeText: string): string {
  return outcomeText.substring(0, 80).trim() || "New Project";
}

/* ── Derived helpers ── */

/** Compute the brief state for a proposal (INT-011 five-state vocabulary). */
export function proposalBriefState(p: SetupProposal): WatchBriefState {
  if (p.state === "selected" && p.testState === "passed") return "tested";
  if (p.state === "selected") return "proposed";
  if (p.state === "proposed") return "proposed";
  // deselected or failed proposals
  return "disabled";
}

/** Human-readable cadence from a trigger. */
export function cadenceLabel(trigger: WatchTrigger): string {
  if (!trigger.everyMinutes) return "Manual";
  if (trigger.weekdaysOnly && trigger.everyMinutes === 1440) return "Weekdays";
  if (trigger.everyMinutes === 1440) return "Daily";
  if (trigger.everyMinutes <= 15) return "Every 15 min";
  if (trigger.everyMinutes <= 35) return "Every 35 min";
  return `Every ${trigger.everyMinutes} min`;
}

/** Human-readable condition summary from a spec's rules (raw form). */
export function conditionSummary(spec: WatchSpec): string {
  const clauses = spec.rules.flatMap((r) => r.condition.clauses);
  if (clauses.length === 0) return "Any change";
  return clauses
    .map((c) => {
      const val = c.value != null ? ` ${String(c.value)}` : "";
      return `${c.field} ${c.comparison}${val}`;
    })
    .join(", ");
}

/* ── Plain-words condition renderer (HS-159-05 defect 2) ────────── */

/** Subject-kind nouns for sentence construction. */
const SUBJECT_NOUNS: Record<string, string> = {
  meetings: "meeting",
  decisions: "decision",
  action_items: "action item",
  action_item: "action item",
  resources: "resource",
  changes: "change",
  notes: "note",
  threads: "thread",
  people: "person",
  recipes: "recipe",
  workflows: "workflow",
  pull_requests: "PR",
  pull_request: "PR",
};

/** Comparison verbs for the closed WatchCondition@1 vocabulary. */
const COMPARISON_VERBS: Record<string, (field: string, value: string | null, noun: string) => string> = {
  changed: (field, _v, _noun) => `When ${field} changes`,
  changed_to: (field, value, _noun) => `When ${field} becomes ${value ?? "unknown"}`,
  equals: (field, value, _noun) => `When ${field} is ${value ?? "unknown"}`,
  not_equals: (field, value, _noun) => `When ${field} is not ${value ?? "unknown"}`,
  older_than: (field, value, _noun) => `When ${field} is older than ${value ?? "unknown"}`,
  newer_than: (field, value, _noun) => `When ${field} is newer than ${value ?? "unknown"}`,
  greater_than: (field, value, _noun) => `When ${field} exceeds ${value ?? "unknown"}`,
  less_than: (field, value, _noun) => `When ${field} is below ${value ?? "unknown"}`,
  contains: (field, value, _noun) => `When ${field} contains ${value ?? "unknown"}`,
  not_contains: (field, value, _noun) => `When ${field} does not contain ${value ?? "unknown"}`,
  exists: (field, _v, _noun) => `When ${field} exists`,
  not_exists: (field, _v, _noun) => `When ${field} does not exist`,
};

/* ── Closed PR phrase table (HS-161-05 final copy pass) ─────────── */

/** Owner-grade phrases for the closed set of PR condition combinations.
 *  Keyed on "field:comparison" or "field:comparison:value".
 *  Consulted BEFORE the generic verb path for pull_request subjects. */
const PR_PHRASE_TABLE: Record<string, string | ((value: string) => string)> = {
  "review_requested:changed": "When a review is requested",
  "review_decision:changed": "When the review decision changes",
  "review_decision:equals:approved": "When the review decision is approved",
  "checks:changed_to:failure": "When CI checks fail",
  "checks:changed_to:success": "When CI checks recover",
  "checks:changed": "When CI checks change",
  "head_sha:changed": "When the head commit changes",
  "state:changed": "When the PR state changes",
  "merged:changed_to:true": "When a PR merges",
  "updated_at:older_than": (value: string) => {
    // Parse duration: "7d" -> "7 days", "14d" -> "14 days"
    const match = value.match(/^(\d+)d$/);
    if (match) {
      const n = Number(match[1]);
      return `When a PR goes quiet for ${n} ${n === 1 ? "day" : "days"}`;
    }
    return `When a PR goes quiet for ${value}`;
  },
};

/** Look up a PR clause in the closed phrase table.
 *  Returns the exact phrase or null (fall through to generic). */
function prPhrase(clause: WatchConditionClause): string | null {
  const valueStr = clause.value != null ? String(clause.value).toLowerCase() : null;

  // Try field:comparison:value first (most specific)
  if (valueStr != null) {
    const keyWithValue = `${clause.field}:${clause.comparison}:${valueStr}`;
    const exact = PR_PHRASE_TABLE[keyWithValue];
    if (typeof exact === "string") return exact;
  }

  // Try field:comparison (may be a function needing the value)
  const keyBase = `${clause.field}:${clause.comparison}`;
  const entry = PR_PHRASE_TABLE[keyBase];
  if (typeof entry === "string") return entry;
  if (typeof entry === "function" && valueStr != null) return entry(valueStr);

  return null;
}

/** Plain-words condition from a single clause (defect 2).
 *  HS-161-05: PR subjects consult the closed phrase table first. */
function clausePlainWords(clause: WatchConditionClause, subjectKind: string): string {
  // PR subjects: closed phrase table first (owner-grade copy)
  if (subjectKind === "pull_requests" || subjectKind === "pull_request") {
    const phrase = prPhrase(clause);
    if (phrase) return phrase;
  }

  // Generic path (non-PR subjects, or PR combinations not in the table)
  const fieldName = subjectKind === "pull_requests" || subjectKind === "pull_request"
    ? prFieldLabel(clause.field)
    : clause.field;
  const valueStr = clause.value != null ? String(clause.value) : null;
  const verb = COMPARISON_VERBS[clause.comparison];
  if (verb) return verb(fieldName, valueStr, SUBJECT_NOUNS[subjectKind] ?? subjectKind);
  const valPart = valueStr ? ` ${valueStr}` : "";
  return `When ${(SUBJECT_NOUNS[subjectKind] ?? subjectKind)} ${fieldName} ${clause.comparison}${valPart}`;
}

/** Plain-words conditions for a full spec (HS-159-05 defect 2).
 *  Maps the closed WatchCondition@1 vocabulary to sentences.
 *  Machine values stay in data- attributes on the rendered elements. */
export function conditionPlainWords(spec: WatchSpec): string {
  const clauses = spec.rules.flatMap((r) => r.condition.clauses);
  if (clauses.length === 0) return "On any change";
  // Deduplicate identical plain-words clauses
  const seen = new Set<string>();
  const unique: string[] = [];
  for (const c of clauses) {
    const text = clausePlainWords(c, spec.subject.kind);
    if (!seen.has(text)) {
      seen.add(text);
      unique.push(text);
    }
  }
  return unique.join("; ");
}

/** Plain-words description of the query/scope (repo, state, base branch).
 *  Distinct from conditionPlainWords which describes transition clauses.
 *  HS-161-05 defect 2: Query != Conditions. */
export function queryPlainWords(spec: WatchSpec): string {
  const parts: string[] = [];
  const scope = spec.subject.scope as Record<string, unknown> | undefined;

  // Repository
  if (scope?.repository) {
    parts.push(String(scope.repository));
  } else if (scope?.repositories) {
    const repos = scope.repositories as string[];
    if (repos.length > 0) parts.push(repos.join(", "));
  }

  // Query filters (state, base branch)
  const query = (scope?.query ?? {}) as Record<string, unknown>;
  if (query.state) parts.push(`${String(query.state)} PRs`);
  if (query.base) parts.push(`base: ${String(query.base)}`);

  // Subject kind
  const noun = SUBJECT_NOUNS[spec.subject.kind] ?? spec.subject.kind;
  if (parts.length === 0) return `All ${noun}s`;
  return parts.join(", ");
}

/* ── Mode/posture labels (HS-159-05 defect 3) ────────────────────── */

/** Human-readable posture labels for watch mode values. */
export const MODE_LABELS: Record<string, string> = {
  yolo: "YOLO",
  safe: "Secure",
  neutral: "Normal",
};

/** Human-readable mode label, with fallback. */
export function modeLabel(mode: string): string {
  return MODE_LABELS[mode] ?? mode;
}

/* ── Stage progress (HS-159-05 defect 6) ────────────────────────── */

/** Total number of setup stages visible to the user. */
export const STAGE_COUNT = 4;

/** Stage labels and ordinals for the step indicator. */
export const STAGE_META: Record<string, { index: number; label: string }> = {
  outcome: { index: 1, label: "Outcome" },
  signals: { index: 2, label: "Signals" },
  proposals: { index: 3, label: "Suggestions" },
  review: { index: 4, label: "Review" },
};

/* ── Provider connection vocabulary (HS-161-05) ─────────────────── */

/** The seven provider-state tokens. Wire values from GET /api/providers/github/connection. */
export const PROVIDER_STATES = [
  "checking",
  "connected",
  "connection_required",
  "capability_missing",
  "partial",
  "unavailable",
  "owner_action_required",
] as const;
export type ProviderState = (typeof PROVIDER_STATES)[number];

/** Provider connection status from the wire (mined from test_provider_routes.py). */
export type ProviderConnectionStatus = {
  state: ProviderState;
  errorCode: string | null;
  errorDetail: string | null;
  display: {
    account: string | null;
    recoveryHint: string | null;
  };
};

/** One discovered repository item from GET /api/providers/github/discover. */
export type DiscoveryItem = {
  id: string;
  name: string;
  owner: string;
  visibility: string;
};

/** Discovery response from the wire. */
export type DiscoveryResponse = {
  state: string;
  items: DiscoveryItem[];
  cursor: string | null;
  errorCode: string | null;
};

/** Validate-repo response from POST /api/providers/github/validate-repo. */
export type ValidateRepoResponse = {
  valid: boolean;
  message: string | null;
};

/** Clarify-scope response from POST /api/project-setups/{sid}/proposals/{pid}/clarify-scope. */
export type ClarifyScopeResponse = {
  scopeState: string;
  repositories: string[];
};

/* ── Provider state display vocabulary ────────────────────────────── */

/** Human card copy for each provider state token. */
export const PROVIDER_STATE_COPY: Record<ProviderState, { headline: string; detail: string }> = {
  checking: {
    headline: "Checking connection",
    detail: "Verifying GitHub access...",
  },
  connected: {
    headline: "Connected",
    detail: "GitHub is ready. Choose a repository to watch.",
  },
  connection_required: {
    headline: "Connection required",
    detail: "GitHub needs to be connected before it can be used.",
  },
  capability_missing: {
    headline: "Capability missing",
    detail: "The GitHub CLI is not installed or not found.",
  },
  partial: {
    headline: "Partially connected",
    detail: "GitHub is reachable but some permissions are missing.",
  },
  unavailable: {
    headline: "Unavailable",
    detail: "GitHub cannot be reached at this time.",
  },
  owner_action_required: {
    headline: "Authentication required",
    detail: "GitHub needs you to authenticate before HoldSpeak can connect.",
  },
};

/** The ONE next action for each provider state. */
export const PROVIDER_STATE_ACTION: Record<ProviderState, { label: string; kind: "recheck" | "discover" | "authenticate" | "install" | "wait" | "retry" }> = {
  checking: { label: "Checking...", kind: "wait" },
  connected: { label: "Choose repository", kind: "discover" },
  connection_required: { label: "Connect GitHub", kind: "authenticate" },
  capability_missing: { label: "Install GitHub CLI", kind: "install" },
  partial: { label: "Recheck connection", kind: "recheck" },
  unavailable: { label: "Retry", kind: "retry" },
  owner_action_required: { label: "Recheck", kind: "recheck" },
};

/* ── Provider decoders ────────────────────────────────────────────── */

export function decodeProviderConnectionStatus(raw: Record<string, unknown>): ProviderConnectionStatus {
  const display = (raw.display ?? {}) as Record<string, unknown>;
  return {
    state: (PROVIDER_STATES.includes(raw.state as ProviderState) ? raw.state : "unavailable") as ProviderState,
    errorCode: raw.error_code != null ? String(raw.error_code) : null,
    errorDetail: raw.error_detail != null ? String(raw.error_detail) : null,
    display: {
      account: display.account != null ? String(display.account) : null,
      recoveryHint: display.recovery_hint != null ? String(display.recovery_hint) : null,
    },
  };
}

export function decodeDiscoveryItem(raw: Record<string, unknown>): DiscoveryItem {
  const owner = raw.owner as Record<string, unknown> | undefined;
  return {
    id: String(raw.id ?? ""),
    name: String(raw.name ?? ""),
    owner: owner?.login != null ? String(owner.login) : String(raw.owner ?? ""),
    visibility: String(raw.visibility ?? ""),
  };
}

export function decodeDiscoveryResponse(raw: Record<string, unknown>): DiscoveryResponse {
  const items = Array.isArray(raw.items)
    ? raw.items.map((i: Record<string, unknown>) => decodeDiscoveryItem(i))
    : [];
  return {
    state: String(raw.state ?? ""),
    items,
    cursor: raw.cursor != null ? String(raw.cursor) : null,
    errorCode: raw.error_code != null ? String(raw.error_code) : null,
  };
}

export function decodeValidateRepoResponse(raw: Record<string, unknown>): ValidateRepoResponse {
  return {
    valid: Boolean(raw.valid),
    message: raw.message != null ? String(raw.message) : null,
  };
}

export function decodeClarifyScopeResponse(raw: Record<string, unknown>): ClarifyScopeResponse {
  return {
    scopeState: String(raw.scope_state ?? ""),
    repositories: Array.isArray(raw.repositories)
      ? raw.repositories.map(String)
      : [],
  };
}

/* ── PR condition plain-words vocabulary (HS-161-05) ────────────── */

/** Field-specific plain-words renderers for PR condition fields.
 *  Extends the base COMPARISON_VERBS with PR-domain knowledge. */
const PR_FIELD_LABELS: Record<string, string> = {
  review_requested: "review requested",
  review_decision: "review decision",
  checks: "CI checks",
  head_sha: "commit SHA",
  state: "PR state",
  merged: "merged",
  updated_at: "last updated",
  title: "title",
  draft: "draft status",
  labels: "labels",
  number: "PR number",
};

/** Resolve a PR field name to its plain-words label. */
export function prFieldLabel(field: string): string {
  return PR_FIELD_LABELS[field] ?? field.replace(/_/g, " ");
}
