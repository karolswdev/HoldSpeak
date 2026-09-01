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
