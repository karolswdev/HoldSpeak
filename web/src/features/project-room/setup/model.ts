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

/** Human-readable condition summary from a spec's rules. */
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
