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
  /** HS-166-04: Jira enrichment fields (SS8.2 display contract). */
  provider?: string;
  connection?: { site: string; email: string; connection_ref: string };
  projects?: string[];
  normalizedJql?: string;
  matchedConditions?: string;
  supportedTransitions?: string[];
  calls?: number;
  durationMs?: number;
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
  const connRaw = raw.connection;
  const result: TestResult = {
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
  // HS-166-04: Jira enrichment fields (SS8.2 display contract)
  if (raw.provider != null) result.provider = String(raw.provider);
  if (connRaw && typeof connRaw === "object") {
    const c = connRaw as Record<string, unknown>;
    result.connection = {
      site: String(c.site ?? ""),
      email: String(c.email ?? ""),
      connection_ref: String(c.connection_ref ?? ""),
    };
  }
  if (Array.isArray(raw.projects)) result.projects = raw.projects.map(String);
  if (raw.normalized_jql != null) result.normalizedJql = String(raw.normalized_jql);
  if (raw.matched_conditions != null) result.matchedConditions = String(raw.matched_conditions);
  if (Array.isArray(raw.supported_transitions)) result.supportedTransitions = raw.supported_transitions.map(String);
  if (raw.calls != null) result.calls = Number(raw.calls);
  if (raw.duration_ms != null) result.durationMs = Number(raw.duration_ms);
  return result;
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

  // HS-166-04: Jira issue subjects use conditionLabel (human tokens)
  if (subjectKind === "issue") {
    return conditionLabel(clause);
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
  const id = String(raw.id ?? "");
  // Wire sends {id: "owner/name", name, visibility} -- no owner field.
  // Derive owner from id (split on first "/").
  const derivedOwner = id.includes("/") ? id.split("/")[0] : "";
  return {
    id,
    name: String(raw.name ?? ""),
    owner: derivedOwner,
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
  // Wire sends {valid, error_code, error_detail} -- no message field.
  // Map error_detail to message so the UI renders the adapter's real reason.
  const detail = raw.error_detail != null ? String(raw.error_detail) : null;
  return {
    valid: Boolean(raw.valid),
    message: detail || null,
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

/* ── Provider-keyed state copy (HS-166-04) ────────────────────────── */

export type ProviderStateCopy = { headline: string; detail: string };
export type ProviderStateAction = { label: string; kind: "recheck" | "discover" | "authenticate" | "install" | "wait" | "retry" };

function _jiraStateCopy(state: ProviderState, site?: string): ProviderStateCopy {
  const s = site || "Jira";
  switch (state) {
    case "checking": return { headline: `${s} checking`, detail: "Verifying Jira access..." };
    case "connected": return { headline: `${s} is ready`, detail: "Choose projects to watch." };
    case "connection_required": return { headline: "Connection required", detail: "Jira needs to be connected." };
    case "capability_missing": return { headline: "acli not installed", detail: "Install the Atlassian CLI to connect." };
    case "partial": return { headline: "Partially connected", detail: "Jira is reachable but some access is missing." };
    case "unavailable": return { headline: "Unavailable", detail: "Jira cannot be reached." };
    case "owner_action_required": return { headline: "Authentication required", detail: `${s} needs you to sign in.` };
  }
}

export function providerStateCopy(provider: "github" | "jira", state: ProviderState, site?: string): ProviderStateCopy {
  if (provider === "github") return PROVIDER_STATE_COPY[state];
  return _jiraStateCopy(state, site);
}

const JIRA_STATE_ACTION: Record<ProviderState, ProviderStateAction> = {
  checking: { label: "Checking...", kind: "wait" },
  connected: { label: "Choose projects", kind: "discover" },
  connection_required: { label: "Add account", kind: "authenticate" },
  capability_missing: { label: "Install acli", kind: "install" },
  partial: { label: "Recheck connection", kind: "recheck" },
  unavailable: { label: "Retry", kind: "retry" },
  owner_action_required: { label: "Recheck", kind: "recheck" },
};

export function providerStateAction(provider: "github" | "jira", state: ProviderState): ProviderStateAction {
  if (provider === "github") return PROVIDER_STATE_ACTION[state];
  return JIRA_STATE_ACTION[state];
}

/* ── Jira connection types (HS-166-04) ────────────────────────────── */

export type JiraConnection = {
  provider_id: string;
  connection_ref: string;
  state: ProviderState;
  account: { site: string; email: string };
  error_code: string | null;
  error_detail: string | null;
  recovery: { command: string; hint: string } | null;
  checked_at: string | null;
  last_connected_at: string | null;
};

export type JiraKnownAccount = {
  site: string;
  email: string;
  displayName: string;
  authType: string;
  ref: string;
  current: boolean;
};

export type JiraConnectionsResponse = {
  connections: JiraConnection[];
  knownAccounts: JiraKnownAccount[];
};

export type JiraDiscoveryItem = {
  id: string;
  key?: string;
  name: string;
  project_id?: string;
  type?: string;
  style?: string;
  private?: boolean;
  lead?: string | null;
  subtask?: boolean;
  hierarchy_level?: number;
  category?: string;
  category_name?: string;
};

export type JiraDiscoveryResponse = {
  state: string;
  items: JiraDiscoveryItem[];
  cursor: number | null;
  errorCode: string | null;
  errorDetail: string | null;
  connectionRef: string;
  source?: string;
  categories?: Array<{ key: string; name: string; source: string }>;
};

export type JiraSearchItem = {
  key: string;
  id: string;
  summary: string;
  issueType: string;
  status: string;
  statusCategory: string;
  assignee: string | null;
  priority: string | null;
  labels: string[];
  url: string;
  dueDate?: string | null;
  resolution?: string | null;
};

export type JiraSearchResult = {
  state: string;
  items: JiraSearchItem[];
  calls: number;
  errorCode: string | null;
  errorDetail: string | null;
  connectionRef: string;
  queryInvalid?: string;
};

export type JiraValidateScopeResponse = {
  valid: boolean;
  project: { key: string; name: string; type: string; style: string } | null;
  issueTypes: Array<{ id: string; name: string; subtask: boolean; hierarchy_level?: number }>;
  errorCode: string | null;
  errorDetail: string | null;
  connectionRef: string;
};

export type JiraClarifyScopeResponse = {
  proposalId: string;
  scopeState: string;
  error: string | null;
  projects: string[];
};

export type JiraScope = {
  connectionRef: string;
  projects: string[];
  issueTypes: string[];
  statusCategories: string[];
  jql: string;
};

/* ── Jira decoders (HS-166-04) ────────────────────────────────────── */

export function decodeJiraConnection(raw: Record<string, unknown>): JiraConnection {
  const account = (raw.account ?? {}) as Record<string, unknown>;
  const recovery = raw.recovery as Record<string, unknown> | null | undefined;
  return {
    provider_id: String(raw.provider_id ?? ""),
    connection_ref: String(raw.connection_ref ?? raw.external_connection_ref ?? ""),
    state: (PROVIDER_STATES.includes(raw.state as ProviderState) ? raw.state : "unavailable") as ProviderState,
    account: {
      site: String(account.site ?? ""),
      email: String(account.email ?? ""),
    },
    error_code: raw.error_code != null ? String(raw.error_code) : null,
    error_detail: raw.error_detail != null ? String(raw.error_detail) : null,
    recovery: recovery && typeof recovery === "object"
      ? { command: String(recovery.command ?? ""), hint: String(recovery.hint ?? "") }
      : null,
    checked_at: raw.checked_at != null ? String(raw.checked_at) : null,
    last_connected_at: raw.last_connected_at != null ? String(raw.last_connected_at) : null,
  };
}

export function decodeJiraKnownAccount(raw: Record<string, unknown>): JiraKnownAccount {
  return {
    site: String(raw.site ?? ""),
    email: String(raw.email ?? ""),
    displayName: String(raw.display_name ?? ""),
    authType: String(raw.auth_type ?? ""),
    ref: String(raw.ref ?? ""),
    current: Boolean(raw.current),
  };
}

export function decodeJiraConnectionsResponse(raw: Record<string, unknown>): JiraConnectionsResponse {
  const connections = Array.isArray(raw.connections)
    ? raw.connections.map((c: Record<string, unknown>) => decodeJiraConnection(c))
    : [];
  const knownAccounts = Array.isArray(raw.known_accounts)
    ? raw.known_accounts.map((a: Record<string, unknown>) => decodeJiraKnownAccount(a))
    : [];
  return { connections, knownAccounts };
}

export function decodeJiraDiscoveryItem(raw: Record<string, unknown>): JiraDiscoveryItem {
  const item: JiraDiscoveryItem = {
    id: String(raw.id ?? ""),
    name: String(raw.name ?? ""),
  };
  if (raw.key != null) item.key = String(raw.key);
  if (raw.project_id != null) item.project_id = String(raw.project_id);
  if (raw.type != null) item.type = String(raw.type);
  if (raw.style != null) item.style = String(raw.style);
  if (raw.private != null) item.private = Boolean(raw.private);
  if (raw.lead != null) item.lead = String(raw.lead);
  if (raw.subtask != null) item.subtask = Boolean(raw.subtask);
  if (raw.hierarchy_level != null) item.hierarchy_level = Number(raw.hierarchy_level);
  if (raw.category != null) item.category = String(raw.category);
  if (raw.category_name != null) item.category_name = String(raw.category_name);
  return item;
}

export function decodeJiraDiscoveryResponse(raw: Record<string, unknown>): JiraDiscoveryResponse {
  const items = Array.isArray(raw.items)
    ? raw.items.map((i: Record<string, unknown>) => decodeJiraDiscoveryItem(i))
    : [];
  const categories = Array.isArray(raw.categories)
    ? raw.categories.map((c: Record<string, unknown>) => ({
        key: String(c.key ?? ""),
        name: String(c.name ?? ""),
        source: String(c.source ?? ""),
      }))
    : undefined;
  return {
    state: String(raw.state ?? ""),
    items,
    cursor: raw.cursor != null ? Number(raw.cursor) : null,
    errorCode: raw.error_code != null ? String(raw.error_code) : null,
    errorDetail: raw.error_detail != null ? String(raw.error_detail) : null,
    connectionRef: String(raw.connection_ref ?? ""),
    source: raw.source != null ? String(raw.source) : undefined,
    categories,
  };
}

export function decodeJiraSearchItem(raw: Record<string, unknown>): JiraSearchItem {
  return {
    key: String(raw.key ?? ""),
    id: String(raw.id ?? ""),
    summary: String(raw.summary ?? ""),
    issueType: String(raw.issue_type ?? ""),
    status: String(raw.status ?? ""),
    statusCategory: String(raw.status_category ?? ""),
    assignee: raw.assignee != null ? String(raw.assignee) : null,
    priority: raw.priority != null ? String(raw.priority) : null,
    labels: Array.isArray(raw.labels) ? raw.labels.map(String) : [],
    url: String(raw.url ?? ""),
    dueDate: raw.due_date != null ? String(raw.due_date) : raw.duedate != null ? String(raw.duedate) : undefined,
    resolution: raw.resolution != null ? String(raw.resolution) : undefined,
  };
}

export function decodeJiraSearchResult(raw: Record<string, unknown>): JiraSearchResult {
  const items = Array.isArray(raw.items)
    ? raw.items.map((i: Record<string, unknown>) => decodeJiraSearchItem(i))
    : [];
  return {
    state: String(raw.state ?? ""),
    items,
    calls: Number(raw.calls ?? 0),
    errorCode: raw.error_code != null ? String(raw.error_code) : null,
    errorDetail: raw.error_detail != null ? String(raw.error_detail) : null,
    connectionRef: String(raw.connection_ref ?? ""),
    queryInvalid: raw.query_invalid != null ? String(raw.query_invalid) : undefined,
  };
}

export function decodeJiraValidateScopeResponse(raw: Record<string, unknown>): JiraValidateScopeResponse {
  const projectRaw = raw.project as Record<string, unknown> | null | undefined;
  const issueTypesRaw = Array.isArray(raw.issue_types) ? raw.issue_types : [];
  return {
    valid: Boolean(raw.valid),
    project: projectRaw && typeof projectRaw === "object"
      ? {
          key: String(projectRaw.key ?? ""),
          name: String(projectRaw.name ?? ""),
          type: String(projectRaw.type ?? ""),
          style: String(projectRaw.style ?? ""),
        }
      : null,
    issueTypes: issueTypesRaw.map((it: Record<string, unknown>) => ({
      id: String(it.id ?? ""),
      name: String(it.name ?? ""),
      subtask: Boolean(it.subtask),
      ...(it.hierarchy_level != null ? { hierarchy_level: Number(it.hierarchy_level) } : {}),
    })),
    errorCode: raw.error_code != null ? String(raw.error_code) : null,
    errorDetail: raw.error_detail != null ? String(raw.error_detail) : null,
    connectionRef: String(raw.connection_ref ?? ""),
  };
}

export function decodeJiraClarifyScopeResponse(raw: Record<string, unknown>): JiraClarifyScopeResponse {
  return {
    proposalId: String(raw.proposal_id ?? ""),
    scopeState: String(raw.scope_state ?? ""),
    error: raw.error != null ? String(raw.error) : null,
    projects: Array.isArray(raw.projects) ? raw.projects.map(String) : [],
  };
}

/* ── Jira condition plain-words vocabulary (HS-166-04) ────────────── */

const JIRA_FIELD_LABELS: Record<string, string> = {
  status: "status",
  status_category: "status category",
  priority: "priority",
  assignee: "assignee",
  labels: "labels",
  components: "components",
  sprint: "sprint",
  due_date: "due date",
  resolution: "resolution",
  issue_type: "issue type",
};

export function jiraFieldLabel(field: string): string {
  return JIRA_FIELD_LABELS[field] ?? field.replace(/_/g, " ");
}

/** Format a date-only string (YYYY-MM-DD) as a DUE token without timezone shift.
 *  Never use `new Date(iso)` for date-only values — that parses as UTC midnight
 *  and shifts a day in negative-UTC-offset timezones. */
const MONTH_NAMES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
export function formatDueToken(dateStr: string | null | undefined): string {
  if (!dateStr) return "";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(dateStr);
  if (match) {
    const month = parseInt(match[2], 10) - 1;
    const day = parseInt(match[3], 10);
    return `DUE ${MONTH_NAMES[month] ?? "???"} ${day}`;
  }
  // Fallback for non-date strings
  return `DUE ${dateStr}`;
}

/* ── Condition + action human labels (HS-166-04 catch 2) ────────── */

/** Human-readable condition clause label from field/comparison/value. */
export function conditionLabel(clause: { field?: string; comparison?: string; value?: unknown }): string {
  const f = String(clause.field ?? "").replace(/_/g, " ");
  const comp = String(clause.comparison ?? "");
  const v = clause.value != null ? String(clause.value) : "";

  // Known patterns
  if (f === "status" && comp === "entered_state" && v) return `Status enters ${v}`;
  if (f === "status" && comp === "changed") return "Status changed";
  if (f === "due" && comp === "within" && v) return `Due within ${v} days`;
  if (f === "due" && comp === "overdue") return "Overdue";
  if (f === "assignee" && comp === "changed") return "Assignee changed";
  if (f === "priority" && comp === "changed") return "Priority changed";
  if (f === "priority" && comp === "changed_to" && v) return `Priority changed to ${v}`;
  if (f === "resolution" && comp === "resolved") return "Resolved";
  if (comp === "older_than" && v) return `No activity ${v} days`;
  if (comp === "newer_than" && v) return `Activity within ${v} days`;

  // Snapshot-level comparisons where the field is implied by the comparison
  // (due_within_days, overdue, inactive_for — the field may be "due_at" or anything)
  if (comp === "due_within_days" && v) return `Due within ${v} days`;
  if (comp === "overdue") return "Overdue";
  if (comp === "inactive_for" && v) return `No activity ${v} days`;

  // Fallback: humanize
  const humanComp = comp.replace(/_/g, " ");
  return v ? `${f} ${humanComp} ${v}` : `${f} ${humanComp}`;
}

/** Human-readable action kind label. */
const ACTION_LABEL_MAP: Record<string, string> = {
  "project.observe": "Put it in Project attention",
  "project.propose": "Propose to the Project",
  "project.steward.run_once": "Run the Steward",
  "project.update.draft": "Draft an update",
  "door.add_item": "Add to the Door",
  "workbench.add_item": "Add to the Workbench",
};

export function actionLabel(kind: string): string {
  return ACTION_LABEL_MAP[kind] ?? kind.replace(/[._]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Human-readable transition kind label. */
const TRANSITION_LABEL_MAP: Record<string, string> = {
  "jira.issue.discovered": "Discovered",
  "jira.issue.assigned": "Assigned",
  "jira.issue.status_changed": "Status changed",
  "jira.issue.category_changed": "Category changed",
  "jira.issue.priority_changed": "Priority changed",
  "jira.issue.due_changed": "Due changed",
  "jira.issue.resolved": "Resolved",
};

/** Pluralize a word: "1 issue" vs "3 issues", "1 call" vs "0 calls". */
export function plural(n: number, singular: string, pluralForm?: string): string {
  return `${n} ${n === 1 ? singular : (pluralForm ?? singular + "s")}`;
}

export function transitionLabel(kind: string): string {
  return TRANSITION_LABEL_MAP[kind] ?? kind.replace(/^jira\.issue\./, "").replace(/[._]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
