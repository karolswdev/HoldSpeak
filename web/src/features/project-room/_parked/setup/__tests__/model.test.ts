// PARKED (HS-170-02): retired by Phase 169; kept for reference, not built or scanned.
// HS-159-05 -- decode suites against REAL wire fixtures mined from
// tests/integration/test_project_setup_routes.py and the service
// holdspeak/services/project_setup_service.py.

import { describe, expect, it } from "vitest";
import {
  decodeSession,
  decodeProposal,
  decodeAnswer,
  decodeTestResult,
  decodeFinalizeEnvelope,
  decodeTestResultResponse,
  decodeWatchSpec,
  proposalBriefState,
  cadenceLabel,
  conditionSummary,
  STAGES,
  Q_OUTCOME,
  Q_SIGNALS,
} from "../model";

/* ── Wire fixtures (from integration test shapes) ── */

/** Fixture: start_setup response (the session row from the repo). */
const WIRE_SESSION_START = {
  id: "psetup_abc123def456",
  state: "active",
  stage: "outcome",
  draft_schema: "ProjectSetup@1",
  expires_at: "2026-09-01T10:00:00+00:00",
  created_at: "2026-08-31T10:00:00",
  updated_at: "2026-08-31T10:00:00",
  project_id: null,
};

/** Fixture: answer response (created answer row). */
const WIRE_ANSWER = {
  id: "pans_abc123",
  session_id: "psetup_abc123def456",
  question_id: "outcome",
  answer_schema: "SetupAnswer@1",
  answer: {
    original: "Ship the Q4 release on time",
    normalized: "Ship the Q4 release on time",
  },
  revision: 1,
  created_at: "2026-08-31T10:01:00",
};

/** Fixture: get_setup response (session + answers + proposals). */
const WIRE_SESSION_FULL = {
  ...WIRE_SESSION_START,
  stage: "proposals",
  answers: {
    outcome: WIRE_ANSWER,
    signals: {
      id: "pans_def456",
      session_id: "psetup_abc123def456",
      question_id: "signals",
      answer_schema: "SetupAnswer@1",
      answer: {
        original: "PRs going stale, blockers unresolved",
        normalized: "PRs going stale, blockers unresolved",
      },
      revision: 1,
      created_at: "2026-08-31T10:02:00",
    },
  },
  proposals: [
    {
      id: "wprop_meeting001",
      session_id: "psetup_abc123def456",
      provider_id: "native",
      spec_schema: "WatchSpec@1",
      spec: {
        schema: "WatchSpec@1",
        name: "Meeting activity",
        intent: "Watch associated meetings for new content",
        provider: { id: "native", transport: "local_domain" },
        subject: {
          kind: "meetings",
          scope: { meeting_ids: ["m-walk-1"] },
        },
        trigger: { kind: "poll", every_minutes: 35 },
        rules: [
          {
            condition: {
              schema: "WatchCondition@1",
              operator: "any",
              clauses: [{ field: "content", comparison: "changed" }],
            },
            actions: [{ schema: "WatchAction@1", kind: "project.observe" }],
          },
        ],
        action: { schema: "WatchAction@1", kind: "project.observe" },
        mode: "yolo",
      },
      rationale: {
        fact: "1 recent meetings",
        detail: "Meetings: Sprint planning",
        subject_count: 1,
      },
      state: "proposed",
      test_state: null,
      test_result: null,
      created_at: "2026-08-31T10:03:00",
      updated_at: "2026-08-31T10:03:00",
    },
  ],
};

/** Fixture: proposal after select. */
const WIRE_PROPOSAL_SELECTED = {
  ...WIRE_SESSION_FULL.proposals[0],
  state: "selected",
};

/** Fixture: test_proposal response. */
const WIRE_TEST_RESULT_RESPONSE = {
  proposal_id: "wprop_meeting001",
  test_state: "passed",
  result: {
    entity_count: 1,
    representative_entities: [
      { id: "m-walk-1", title: "Sprint planning", started_at: "2026-08-01T10:00:00" },
    ],
    observed_at: "2026-08-31T10:04:00+00:00",
    error: null,
    message: "Test passed -- 1 current matches",
  },
};

/** Fixture: finalize response envelope. */
const WIRE_FINALIZE_ENVELOPE = {
  project_id: "proj_abc123",
  id: "proj_abc123",
  result_kind: "created",
  project_revision: 1,
  changed_refs: ["project:proj_abc123", "watch:watch_xyz"],
  refused_proposals: [],
};

/* ── Decoder tests ── */

describe("decodeSession", () => {
  it("decodes a start_setup response", () => {
    const session = decodeSession(WIRE_SESSION_START);
    expect(session.id).toBe("psetup_abc123def456");
    expect(session.state).toBe("active");
    expect(session.stage).toBe("outcome");
    expect(session.draftSchema).toBe("ProjectSetup@1");
    expect(session.projectId).toBeNull();
    expect(session.answers).toEqual({});
    expect(session.proposals).toEqual([]);
  });

  it("decodes a full get_setup response with answers and proposals", () => {
    const session = decodeSession(WIRE_SESSION_FULL);
    expect(session.stage).toBe("proposals");
    expect(Object.keys(session.answers)).toEqual(["outcome", "signals"]);
    expect(session.answers.outcome.answer.normalized).toBe("Ship the Q4 release on time");
    expect(session.answers.signals.answer.normalized).toBe("PRs going stale, blockers unresolved");
    expect(session.proposals).toHaveLength(1);
    expect(session.proposals[0].id).toBe("wprop_meeting001");
    expect(session.proposals[0].spec.name).toBe("Meeting activity");
  });

  it("handles unknown stage gracefully (falls back to outcome)", () => {
    const session = decodeSession({ ...WIRE_SESSION_START, stage: "unknown_stage" });
    expect(session.stage).toBe("outcome");
  });
});

describe("decodeAnswer", () => {
  it("decodes an answer with parsed answer object", () => {
    const answer = decodeAnswer(WIRE_ANSWER);
    expect(answer.id).toBe("pans_abc123");
    expect(answer.questionId).toBe("outcome");
    expect(answer.answer.original).toBe("Ship the Q4 release on time");
    expect(answer.answer.normalized).toBe("Ship the Q4 release on time");
    expect(answer.revision).toBe(1);
  });

  it("decodes an answer with answer_json string (fallback)", () => {
    const wireWithString = {
      ...WIRE_ANSWER,
      answer: undefined,
      answer_json: JSON.stringify({
        original: "Spoken text",
        normalized: "Spoken text",
      }),
    };
    const answer = decodeAnswer(wireWithString);
    expect(answer.answer.original).toBe("Spoken text");
    expect(answer.answer.normalized).toBe("Spoken text");
  });
});

describe("decodeProposal", () => {
  it("decodes a proposal with parsed spec object", () => {
    const p = decodeProposal(WIRE_SESSION_FULL.proposals[0]);
    expect(p.id).toBe("wprop_meeting001");
    expect(p.providerId).toBe("native");
    expect(p.spec.name).toBe("Meeting activity");
    expect(p.spec.subject.kind).toBe("meetings");
    expect(p.spec.trigger.everyMinutes).toBe(35);
    expect(p.spec.action.kind).toBe("project.observe");
    expect(p.spec.rules).toHaveLength(1);
    expect(p.spec.rules[0].condition.clauses[0].field).toBe("content");
    expect(p.rationale.fact).toBe("1 recent meetings");
    expect(p.rationale.subjectCount).toBe(1);
    expect(p.state).toBe("proposed");
    expect(p.testState).toBeNull();
    expect(p.testResult).toBeNull();
  });

  it("decodes a proposal with spec_json string (fallback)", () => {
    const wireWithString = {
      ...WIRE_SESSION_FULL.proposals[0],
      spec: undefined,
      spec_json: JSON.stringify(WIRE_SESSION_FULL.proposals[0].spec),
      rationale: undefined,
      rationale_json: JSON.stringify(WIRE_SESSION_FULL.proposals[0].rationale),
    };
    const p = decodeProposal(wireWithString);
    expect(p.spec.name).toBe("Meeting activity");
    expect(p.rationale.fact).toBe("1 recent meetings");
  });

  it("decodes a selected proposal", () => {
    const p = decodeProposal(WIRE_PROPOSAL_SELECTED);
    expect(p.state).toBe("selected");
  });
});

describe("decodeWatchSpec", () => {
  it("decodes a meetings WatchSpec@1", () => {
    const spec = decodeWatchSpec(WIRE_SESSION_FULL.proposals[0].spec);
    expect(spec.schema).toBe("WatchSpec@1");
    expect(spec.name).toBe("Meeting activity");
    expect(spec.intent).toBe("Watch associated meetings for new content");
    expect(spec.provider.id).toBe("native");
    expect(spec.provider.transport).toBe("local_domain");
    expect(spec.subject.kind).toBe("meetings");
    expect(spec.trigger.kind).toBe("poll");
    expect(spec.trigger.everyMinutes).toBe(35);
    expect(spec.action.kind).toBe("project.observe");
    expect(spec.mode).toBe("yolo");
  });
});

describe("decodeTestResult", () => {
  it("decodes a passed test result", () => {
    const r = decodeTestResult(WIRE_TEST_RESULT_RESPONSE.result);
    expect(r.entityCount).toBe(1);
    expect(r.representativeEntities).toHaveLength(1);
    expect(r.representativeEntities[0]).toHaveProperty("title", "Sprint planning");
    expect(r.error).toBeNull();
    expect(r.message).toBe("Test passed -- 1 current matches");
  });

  it("decodes a zero-match passed test (ACT-002 honesty)", () => {
    const zeroMatch = {
      entity_count: 0,
      representative_entities: [],
      observed_at: "2026-08-31T10:04:00",
      error: null,
      message: "Test passed -- 0 current matches",
    };
    const r = decodeTestResult(zeroMatch);
    expect(r.entityCount).toBe(0);
    expect(r.representativeEntities).toHaveLength(0);
    expect(r.error).toBeNull();
    expect(r.message).toBe("Test passed -- 0 current matches");
  });

  it("decodes a failed test result with error", () => {
    const failed = {
      entity_count: 0,
      representative_entities: [],
      observed_at: "2026-08-31T10:04:00",
      error: { type: "ConnectionError", message: "Cannot reach service" },
      message: "Test failed: Cannot reach service",
    };
    const r = decodeTestResult(failed);
    expect(r.entityCount).toBe(0);
    expect(r.error).not.toBeNull();
    expect(r.error!.type).toBe("ConnectionError");
    expect(r.error!.message).toBe("Cannot reach service");
  });
});

describe("decodeTestResultResponse", () => {
  it("decodes the full test response", () => {
    const r = decodeTestResultResponse(WIRE_TEST_RESULT_RESPONSE);
    expect(r.proposalId).toBe("wprop_meeting001");
    expect(r.testState).toBe("passed");
    expect(r.result.entityCount).toBe(1);
  });

  it("decodes Jira enrichment fields including calls (HS-166-04 catch 1)", () => {
    const wire = {
      proposal_id: "wprop_jira01",
      test_state: "passed",
      result: {
        entity_count: 3,
        representative_entities: [
          { key: "KAN-1", summary: "Task 1", status: "In Progress" },
        ],
        observed_at: "2026-09-02T10:00:00+00:00",
        error: null,
        message: "Test passed -- 3 current matches",
        duration_ms: 912,
        provider: "jira",
        connection: { site: "alpha.atlassian.net", email: "user@example.com", connection_ref: "alpha.atlassian.net|user@example.com" },
        projects: ["KAN"],
        normalized_jql: "project in (\"KAN\") ORDER BY updated DESC",
        matched_conditions: "",
        supported_transitions: ["status", "assigned", "priority", "due", "resolved"],
        calls: 4,
      },
    };
    const r = decodeTestResultResponse(wire as Record<string, unknown>);
    expect(r.result.calls).toBe(4);
    expect(r.result.durationMs).toBe(912);
    expect(r.result.provider).toBe("jira");
    expect(r.result.connection!.site).toBe("alpha.atlassian.net");
    expect(r.result.projects).toEqual(["KAN"]);
    expect(r.result.normalizedJql).toBe("project in (\"KAN\") ORDER BY updated DESC");
    expect(r.result.supportedTransitions).toHaveLength(5);
  });
});

describe("decodeFinalizeEnvelope", () => {
  it("decodes a finalize response", () => {
    const e = decodeFinalizeEnvelope(WIRE_FINALIZE_ENVELOPE);
    expect(e.projectId).toBe("proj_abc123");
    expect(e.resultKind).toBe("created");
    expect(e.projectRevision).toBe(1);
    expect(e.changedRefs).toContain("project:proj_abc123");
    expect(e.refusedProposals).toHaveLength(0);
  });

  it("falls back to id when project_id is missing", () => {
    const wireNoProjectId = {
      ...WIRE_FINALIZE_ENVELOPE,
      project_id: undefined,
    };
    const e = decodeFinalizeEnvelope(wireNoProjectId);
    expect(e.projectId).toBe("proj_abc123");
  });
});

/* ── Derived helper tests ── */

describe("proposalBriefState", () => {
  it("returns proposed for a proposed proposal", () => {
    const p = decodeProposal(WIRE_SESSION_FULL.proposals[0]);
    expect(proposalBriefState(p)).toBe("proposed");
  });

  it("returns proposed for a selected proposal without test", () => {
    const p = decodeProposal(WIRE_PROPOSAL_SELECTED);
    expect(proposalBriefState(p)).toBe("proposed");
  });

  it("returns tested for selected+passed", () => {
    const p = decodeProposal({
      ...WIRE_PROPOSAL_SELECTED,
      test_state: "passed",
    });
    expect(proposalBriefState(p)).toBe("tested");
  });

  it("returns disabled for deselected proposal", () => {
    const p = decodeProposal({
      ...WIRE_SESSION_FULL.proposals[0],
      state: "deselected",
    });
    expect(proposalBriefState(p)).toBe("disabled");
  });
});

describe("cadenceLabel", () => {
  it("returns correct labels for presets", () => {
    expect(cadenceLabel({ kind: "poll", everyMinutes: 15 })).toBe("Every 15 min");
    expect(cadenceLabel({ kind: "poll", everyMinutes: 35 })).toBe("Every 35 min");
    expect(cadenceLabel({ kind: "poll", everyMinutes: 1440 })).toBe("Daily");
    expect(cadenceLabel({ kind: "poll", everyMinutes: 1440, weekdaysOnly: true })).toBe("Weekdays");
    expect(cadenceLabel({ kind: "manual" })).toBe("Manual");
  });
});

describe("conditionSummary", () => {
  it("summarizes rule conditions", () => {
    const spec = decodeWatchSpec(WIRE_SESSION_FULL.proposals[0].spec);
    expect(conditionSummary(spec)).toBe("content changed");
  });

  it("returns 'Any change' when no clauses", () => {
    const spec = decodeWatchSpec({
      ...WIRE_SESSION_FULL.proposals[0].spec,
      rules: [
        {
          condition: { schema: "WatchCondition@1", operator: "any", clauses: [] },
          actions: [],
        },
      ],
    });
    expect(conditionSummary(spec)).toBe("Any change");
  });
});

describe("stage constants", () => {
  it("has four stages in order", () => {
    expect(STAGES).toEqual(["outcome", "signals", "proposals", "review"]);
  });

  it("exports question IDs", () => {
    expect(Q_OUTCOME).toBe("outcome");
    expect(Q_SIGNALS).toBe("signals");
  });
});

/* ══════════════════════════════════════════════════════════════════
   Jira decoder tests (HS-166-04): wire fixtures from the REAL
   Python routes (holdspeak/web/routes/providers.py + watch_service.py)
   ══════════════════════════════════════════════════════════════════ */

import {
  decodeJiraConnection,
  decodeJiraKnownAccount,
  decodeJiraConnectionsResponse,
  decodeJiraDiscoveryItem,
  decodeJiraDiscoveryResponse,
  decodeJiraSearchItem,
  decodeJiraSearchResult,
  decodeJiraValidateScopeResponse,
  decodeJiraClarifyScopeResponse,
  providerStateCopy,
  providerStateAction,
  jiraFieldLabel,
  conditionLabel,
  actionLabel,
  plural,
  formatDueToken,
  cadenceLabel,
} from "../model";

/* Wire fixtures from jira_provider.py connection_status return shape */
const WIRE_JIRA_CONNECTION_CONNECTED = {
  state: "connected",
  provider_id: "jira",
  connection_ref: "myteam.atlassian.net|user@example.com",
  account: { site: "myteam.atlassian.net", email: "user@example.com" },
  error_code: null,
  error_detail: null,
  recovery: null,
  checked_at: "2026-09-02T10:00:00+00:00",
  last_connected_at: "2026-09-02T10:00:00+00:00",
};

const WIRE_JIRA_CONNECTION_UNAUTH = {
  state: "owner_action_required",
  provider_id: "jira",
  connection_ref: "other.atlassian.net|admin@example.com",
  account: { site: "other.atlassian.net", email: "admin@example.com" },
  error_code: "auth_required",
  error_detail: "Not authenticated; run the login command",
  recovery: {
    command: "acli jira auth login --site other.atlassian.net --email admin@example.com --token",
    hint: "Authenticate with your Atlassian API token",
  },
  checked_at: "2026-09-02T10:01:00+00:00",
  last_connected_at: null,
};

const WIRE_JIRA_KNOWN_ACCOUNT = {
  site: "myteam.atlassian.net",
  email: "user@example.com",
  display_name: "Test User",
  auth_type: "oauth",
  ref: "myteam.atlassian.net|user@example.com",
  current: true,
};

const WIRE_JIRA_CONNECTIONS_RESPONSE = {
  connections: [WIRE_JIRA_CONNECTION_CONNECTED, WIRE_JIRA_CONNECTION_UNAUTH],
  known_accounts: [WIRE_JIRA_KNOWN_ACCOUNT],
};

const WIRE_JIRA_PROJECT_ITEM = {
  id: "KAN",
  key: "KAN",
  name: "Kanban Project",
  project_id: "10001",
  type: "software",
  style: "next-gen",
  private: false,
  lead: "Test Lead",
};

const WIRE_JIRA_ISSUE_TYPE_ITEM = {
  id: "10001",
  name: "Task",
  subtask: false,
  hierarchy_level: 0,
};

const WIRE_JIRA_STATUS_ITEM = {
  id: "10002",
  name: "In Progress",
  category: "indeterminate",
  category_name: "In Progress",
};

const WIRE_JIRA_DISCOVERY_PROJECTS = {
  state: "ready",
  items: [WIRE_JIRA_PROJECT_ITEM],
  cursor: null,
  error_code: null,
  error_detail: null,
  connection_ref: "myteam.atlassian.net|user@example.com",
  query: null,
};

const WIRE_JIRA_DISCOVERY_TYPES = {
  state: "ready",
  items: [WIRE_JIRA_ISSUE_TYPE_ITEM],
  cursor: null,
  error_code: null,
  error_detail: null,
  connection_ref: "myteam.atlassian.net|user@example.com",
  source: "enumerated",
};

const WIRE_JIRA_DISCOVERY_STATUSES = {
  state: "ready",
  items: [WIRE_JIRA_STATUS_ITEM],
  cursor: null,
  error_code: null,
  error_detail: null,
  connection_ref: "myteam.atlassian.net|user@example.com",
  source: "observed",
  categories: [{ key: "done", name: "Done", source: "static" }],
};

const WIRE_JIRA_SEARCH_ITEM = {
  key: "KAN-1",
  id: "10100",
  summary: "Set up the project",
  issue_type: "Task",
  status: "To Do",
  status_category: "new",
  assignee: "Test User",
  assignee_id: "acc123",
  priority: "Medium",
  labels: ["setup"],
  url: "https://myteam.atlassian.net/browse/KAN-1",
};

const WIRE_JIRA_SEARCH_RESULT = {
  state: "ready",
  items: [WIRE_JIRA_SEARCH_ITEM],
  cursor: null,
  error_code: null,
  error_detail: null,
  connection_ref: "myteam.atlassian.net|user@example.com",
  calls: 2,
};

const WIRE_JIRA_SEARCH_INVALID = {
  state: "failed",
  items: [],
  cursor: null,
  error_code: "query_invalid",
  error_detail: "failed to parse JQL query: Unexpected token",
  connection_ref: "myteam.atlassian.net|user@example.com",
  query_invalid: "failed to parse JQL query: Unexpected token",
};

const WIRE_JIRA_VALIDATE_OK = {
  valid: true,
  project: { key: "KAN", name: "Kanban Project", type: "software", style: "next-gen" },
  issue_types: [{ id: "10001", name: "Task", subtask: false }],
  error_code: null,
  error_detail: null,
  connection_ref: "myteam.atlassian.net|user@example.com",
};

const WIRE_JIRA_VALIDATE_FAIL = {
  valid: false,
  project: null,
  issue_types: [],
  error_code: "query_invalid",
  error_detail: "Project not found",
  connection_ref: "myteam.atlassian.net|user@example.com",
};

const WIRE_JIRA_CLARIFY = {
  proposal_id: "wprop_jira01",
  scope_state: "scoped",
  error: null,
  projects: ["KAN"],
};

describe("decodeJiraConnection", () => {
  it("decodes a connected Jira connection", () => {
    const c = decodeJiraConnection(WIRE_JIRA_CONNECTION_CONNECTED);
    expect(c.state).toBe("connected");
    expect(c.connection_ref).toBe("myteam.atlassian.net|user@example.com");
    expect(c.account.site).toBe("myteam.atlassian.net");
    expect(c.account.email).toBe("user@example.com");
    expect(c.error_code).toBeNull();
    expect(c.recovery).toBeNull();
  });

  it("decodes an owner_action_required connection with recovery", () => {
    const c = decodeJiraConnection(WIRE_JIRA_CONNECTION_UNAUTH);
    expect(c.state).toBe("owner_action_required");
    expect(c.recovery).not.toBeNull();
    expect(c.recovery!.command).toContain("acli jira auth login");
    expect(c.recovery!.hint).toContain("Authenticate");
    expect(c.error_code).toBe("auth_required");
  });
});

describe("decodeJiraKnownAccount", () => {
  it("decodes a known acli account", () => {
    const ka = decodeJiraKnownAccount(WIRE_JIRA_KNOWN_ACCOUNT);
    expect(ka.site).toBe("myteam.atlassian.net");
    expect(ka.email).toBe("user@example.com");
    expect(ka.displayName).toBe("Test User");
    expect(ka.authType).toBe("oauth");
    expect(ka.current).toBe(true);
  });
});

describe("decodeJiraConnectionsResponse", () => {
  it("decodes the connections envelope", () => {
    const r = decodeJiraConnectionsResponse(WIRE_JIRA_CONNECTIONS_RESPONSE);
    expect(r.connections).toHaveLength(2);
    expect(r.knownAccounts).toHaveLength(1);
    expect(r.connections[0].state).toBe("connected");
    expect(r.connections[1].state).toBe("owner_action_required");
  });
});

describe("decodeJiraDiscoveryItem", () => {
  it("decodes a project item", () => {
    const item = decodeJiraDiscoveryItem(WIRE_JIRA_PROJECT_ITEM);
    expect(item.key).toBe("KAN");
    expect(item.name).toBe("Kanban Project");
    expect(item.type).toBe("software");
    expect(item.lead).toBe("Test Lead");
  });

  it("decodes an issue type item", () => {
    const item = decodeJiraDiscoveryItem(WIRE_JIRA_ISSUE_TYPE_ITEM);
    expect(item.name).toBe("Task");
    expect(item.subtask).toBe(false);
    expect(item.hierarchy_level).toBe(0);
  });

  it("decodes a status item", () => {
    const item = decodeJiraDiscoveryItem(WIRE_JIRA_STATUS_ITEM);
    expect(item.name).toBe("In Progress");
    expect(item.category).toBe("indeterminate");
  });
});

describe("decodeJiraDiscoveryResponse", () => {
  it("decodes a project discovery response", () => {
    const r = decodeJiraDiscoveryResponse(WIRE_JIRA_DISCOVERY_PROJECTS);
    expect(r.state).toBe("ready");
    expect(r.items).toHaveLength(1);
    expect(r.items[0].key).toBe("KAN");
    expect(r.cursor).toBeNull();
    expect(r.connectionRef).toBe("myteam.atlassian.net|user@example.com");
  });

  it("decodes a types discovery with source", () => {
    const r = decodeJiraDiscoveryResponse(WIRE_JIRA_DISCOVERY_TYPES);
    expect(r.source).toBe("enumerated");
    expect(r.items[0].name).toBe("Task");
  });

  it("decodes a statuses discovery with categories", () => {
    const r = decodeJiraDiscoveryResponse(WIRE_JIRA_DISCOVERY_STATUSES);
    expect(r.source).toBe("observed");
    expect(r.categories).toHaveLength(1);
    expect(r.categories![0].key).toBe("done");
  });
});

describe("decodeJiraSearchItem", () => {
  it("decodes a search item from real wire keys", () => {
    const item = decodeJiraSearchItem(WIRE_JIRA_SEARCH_ITEM);
    expect(item.key).toBe("KAN-1");
    expect(item.summary).toBe("Set up the project");
    expect(item.issueType).toBe("Task");
    expect(item.status).toBe("To Do");
    expect(item.statusCategory).toBe("new");
    expect(item.assignee).toBe("Test User");
    expect(item.priority).toBe("Medium");
    expect(item.labels).toEqual(["setup"]);
  });
});

describe("decodeJiraSearchResult", () => {
  it("decodes a successful search result", () => {
    const r = decodeJiraSearchResult(WIRE_JIRA_SEARCH_RESULT);
    expect(r.state).toBe("ready");
    expect(r.items).toHaveLength(1);
    expect(r.calls).toBe(2);
    expect(r.errorCode).toBeNull();
  });

  it("decodes a query_invalid search with error message", () => {
    const r = decodeJiraSearchResult(WIRE_JIRA_SEARCH_INVALID);
    expect(r.state).toBe("failed");
    expect(r.errorCode).toBe("query_invalid");
    expect(r.queryInvalid).toBe("failed to parse JQL query: Unexpected token");
  });
});

describe("decodeJiraValidateScopeResponse", () => {
  it("decodes a valid scope", () => {
    const r = decodeJiraValidateScopeResponse(WIRE_JIRA_VALIDATE_OK);
    expect(r.valid).toBe(true);
    expect(r.project!.key).toBe("KAN");
    expect(r.issueTypes).toHaveLength(1);
    expect(r.errorCode).toBeNull();
  });

  it("decodes an invalid scope", () => {
    const r = decodeJiraValidateScopeResponse(WIRE_JIRA_VALIDATE_FAIL);
    expect(r.valid).toBe(false);
    expect(r.project).toBeNull();
    expect(r.errorCode).toBe("query_invalid");
    expect(r.errorDetail).toBe("Project not found");
  });
});

describe("decodeJiraClarifyScopeResponse", () => {
  it("decodes a clarify-jira-scope response", () => {
    const r = decodeJiraClarifyScopeResponse(WIRE_JIRA_CLARIFY);
    expect(r.proposalId).toBe("wprop_jira01");
    expect(r.scopeState).toBe("scoped");
    expect(r.error).toBeNull();
    expect(r.projects).toEqual(["KAN"]);
  });
});

describe("providerStateCopy", () => {
  it("returns GitHub copy unchanged", () => {
    const c = providerStateCopy("github", "connected");
    expect(c.headline).toBe("Connected");
    expect(c.detail).toContain("GitHub");
  });

  it("returns Jira copy with site name", () => {
    const c = providerStateCopy("jira", "connected", "myteam.atlassian.net");
    expect(c.headline).toBe("myteam.atlassian.net is ready");
    expect(c.detail).toContain("projects");
  });

  it("returns Jira owner_action_required with site", () => {
    const c = providerStateCopy("jira", "owner_action_required", "other.atlassian.net");
    expect(c.headline).toBe("Authentication required");
    expect(c.detail).toContain("other.atlassian.net");
  });
});

describe("providerStateAction", () => {
  it("returns GitHub action unchanged", () => {
    const a = providerStateAction("github", "connected");
    expect(a.label).toBe("Choose repository");
  });

  it("returns Jira action", () => {
    const a = providerStateAction("jira", "connected");
    expect(a.label).toBe("Choose projects");
    expect(a.kind).toBe("discover");
  });
});

describe("jiraFieldLabel", () => {
  it("resolves known fields", () => {
    expect(jiraFieldLabel("status_category")).toBe("status category");
    expect(jiraFieldLabel("due_date")).toBe("due date");
  });

  it("falls back for unknown fields", () => {
    expect(jiraFieldLabel("custom_thing")).toBe("custom thing");
  });
});

describe("conditionLabel (HS-166-04 catch 2)", () => {
  it("renders entered_state as human text", () => {
    expect(conditionLabel({ field: "status", comparison: "entered_state", value: "Blocked" }))
      .toBe("Status enters Blocked");
  });

  it("renders due within", () => {
    expect(conditionLabel({ field: "due", comparison: "within", value: "7" }))
      .toBe("Due within 7 days");
  });

  it("renders overdue", () => {
    expect(conditionLabel({ field: "due", comparison: "overdue" }))
      .toBe("Overdue");
  });

  it("renders assignee changed", () => {
    expect(conditionLabel({ field: "assignee", comparison: "changed" }))
      .toBe("Assignee changed");
  });

  it("renders resolved", () => {
    expect(conditionLabel({ field: "resolution", comparison: "resolved" }))
      .toBe("Resolved");
  });

  it("renders no activity", () => {
    expect(conditionLabel({ field: "updated", comparison: "older_than", value: "14" }))
      .toBe("No activity 14 days");
  });

  it("falls back to humanized form for unknown", () => {
    expect(conditionLabel({ field: "custom_field", comparison: "equals", value: "X" }))
      .toBe("custom field equals X");
  });
});

describe("actionLabel (HS-166-04 catch 2)", () => {
  it("renders known actions as human text", () => {
    expect(actionLabel("project.observe")).toBe("Put it in Project attention");
    expect(actionLabel("project.steward.run_once")).toBe("Run the Steward");
    expect(actionLabel("door.add_item")).toBe("Add to the Door");
  });

  it("falls back for unknown actions", () => {
    expect(actionLabel("custom.do_thing")).toBe("Custom Do Thing");
  });
});

describe("plural (HS-166-04 nit 3)", () => {
  it("uses singular for 1", () => {
    expect(plural(1, "issue")).toBe("1 issue");
    expect(plural(1, "call")).toBe("1 call");
    expect(plural(1, "match", "matches")).toBe("1 match");
  });

  it("uses plural for 0 and >1", () => {
    expect(plural(0, "issue")).toBe("0 issues");
    expect(plural(3, "call")).toBe("3 calls");
    expect(plural(2, "match", "matches")).toBe("2 matches");
  });
});

describe("formatDueToken (live walk defect 1)", () => {
  it("formats date-only string without timezone shift", () => {
    // This must produce SEP 10 in ANY timezone, not SEP 9
    expect(formatDueToken("2026-09-10")).toBe("DUE SEP 10");
    expect(formatDueToken("2026-01-01")).toBe("DUE JAN 1");
    expect(formatDueToken("2026-12-31")).toBe("DUE DEC 31");
  });

  it("handles null/empty", () => {
    expect(formatDueToken(null)).toBe("");
    expect(formatDueToken("")).toBe("");
    expect(formatDueToken(undefined)).toBe("");
  });

  it("falls back for non-date strings", () => {
    expect(formatDueToken("tomorrow")).toBe("DUE tomorrow");
  });
});

describe("conditionLabel snapshot-level comparisons (live walk defect 2)", () => {
  it("maps due_within_days regardless of field", () => {
    expect(conditionLabel({ field: "due_at", comparison: "due_within_days", value: 7 }))
      .toBe("Due within 7 days");
  });

  it("maps overdue regardless of field", () => {
    expect(conditionLabel({ field: "due_at", comparison: "overdue" }))
      .toBe("Overdue");
  });

  it("maps inactive_for regardless of field", () => {
    expect(conditionLabel({ field: "updated", comparison: "inactive_for", value: 14 }))
      .toBe("No activity 14 days");
  });

  it("maps older_than regardless of field", () => {
    expect(conditionLabel({ field: "any", comparison: "older_than", value: 30 }))
      .toBe("No activity 30 days");
  });

  it("maps newer_than regardless of field", () => {
    expect(conditionLabel({ field: "any", comparison: "newer_than", value: 7 }))
      .toBe("Activity within 7 days");
  });

  it("keeps status enters Blocked", () => {
    expect(conditionLabel({ field: "status", comparison: "entered_state", value: "Blocked" }))
      .toBe("Status enters Blocked");
  });
});

describe("cadenceLabel (live walk defect 3)", () => {
  it("renders 1440 as Daily", () => {
    expect(cadenceLabel({ kind: "poll", everyMinutes: 1440 })).toBe("Daily");
  });

  it("renders 35 as Every 35 min", () => {
    expect(cadenceLabel({ kind: "poll", everyMinutes: 35 })).toBe("Every 35 min");
  });

  it("renders 15 as Every 15 min", () => {
    expect(cadenceLabel({ kind: "poll", everyMinutes: 15 })).toBe("Every 15 min");
  });

  it("renders 1440 weekdays as Weekdays", () => {
    expect(cadenceLabel({ kind: "poll", everyMinutes: 1440, weekdaysOnly: true })).toBe("Weekdays");
  });
});
