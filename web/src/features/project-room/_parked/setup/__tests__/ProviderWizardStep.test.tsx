// HS-161-05 -- provider wizard step tests: all seven provider-state tokens
// + their ONE next action, recheck flow, discovery + typed fallback, badge
// presence on card/test, plain-words PR conditions, SETFLOW-003 round-trip
// state preservation, never-active-before-test.
//
// Fixtures mined from tests/integration/test_provider_routes.py:
// - Connection status: TestGitHubConnection.test_connected_state (line 212),
//   TestGitHubConnection.test_connection_failure_state (line 220)
// - Recheck: TestGitHubRecheck.test_recheck_re_probes (line 233)
// - Discovery: TestGitHubDiscover.test_discover_returns_items (line 259),
//   discover_with_query_filter (line 269), discover_pagination (line 276)
// - Validate: TestGitHubValidateRepo.test_valid_repo (line 299)
// - Auth-degraded: TestAuthDegradedPath.test_unauthenticated_probe (line 380)
// - Clarify-scope: TestClarifyScope.test_clarify_scope_with_discovered_repos
//   (line 423), test_clarify_scope_with_typed_repo (line 456)

import React from "react";
import { render, screen, fireEvent, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

/* ── Mocks (hoisted before imports) ── */

vi.mock("../../../../desk/surface/controls/MicButton", () => ({
  MicButton: ({
    onText,
    label,
  }: {
    onText: (text: string) => void;
    label?: string;
  }) => (
    <button
      data-testid="mic-btn"
      aria-label={label}
      onClick={() => onText("voice input")}
    >
      Mic
    </button>
  ),
}));

vi.mock("../../../../desk/surface/SurfaceFooter", () => ({
  SurfaceFooter: ({
    egress,
    receipt,
    verbs,
  }: {
    egress?: React.ReactNode;
    receipt?: React.ReactNode;
    verbs?: React.ReactNode;
  }) => (
    <footer data-testid="surface-footer">
      {egress}
      {receipt}
      {verbs}
    </footer>
  ),
}));

import {
  DiscoveryList,
  TypedRepoInput,
  GitHubTestDisplay,
} from "../ProviderWizardStep";

import { SuggestionCards } from "../SuggestionCards";
import { ActivationReview } from "../ActivationReview";

import {
  PROVIDER_STATES,
  PROVIDER_STATE_COPY,
  PROVIDER_STATE_ACTION,
  conditionPlainWords,
  queryPlainWords,
  prFieldLabel,
  decodeProviderConnectionStatus,
  decodeDiscoveryResponse,
  decodeValidateRepoResponse,
  decodeClarifyScopeResponse,
  type ProviderConnectionStatus,
  type DiscoveryItem,
  type SetupProposal,
  type SetupAnswer,
  type WatchSpec,
} from "../model";

/* ── Wire fixtures (mined from test_provider_routes.py) ── */

/** Fixture: connected status (TestGitHubConnection.test_connected_state). */
const WIRE_CONNECTED: Record<string, unknown> = {
  state: "connected",
  error_code: null,
  error_detail: null,
  display: { account: "testuser", recovery_hint: null },
};

/** Fixture: owner_action_required status (TestAuthDegradedPath line 387). */
const WIRE_OWNER_ACTION: Record<string, unknown> = {
  state: "owner_action_required",
  error_code: "authentication_required",
  error_detail: "gh auth login",
  display: { account: null, recovery_hint: "gh auth login" },
};

/** Fixture: discover response (TestGitHubDiscover.test_discover_returns_items).
 *  Wire shape from GitHubProviderAdapter.discover(): {id, name, visibility} -- NO owner field. */
const WIRE_DISCOVER: Record<string, unknown> = {
  state: "ready",
  items: [
    { id: "acme/platform", name: "platform", visibility: "public" },
    { id: "acme/backend", name: "backend", visibility: "private" },
    { id: "acme/docs", name: "docs", visibility: "public" },
  ],
  cursor: null,
  error_code: null,
};

/** Fixture: validate-repo response (TestGitHubValidateRepo.test_valid_repo).
 *  Wire shape from GitHubProviderAdapter.validate_repo(): {valid, error_code, error_detail}. */
const WIRE_VALID_REPO: Record<string, unknown> = {
  valid: true,
  error_code: null,
  error_detail: null,
};

/** Fixture: clarify-scope response (TestClarifyScope line 453/475). */
const WIRE_CLARIFY_SCOPE: Record<string, unknown> = {
  scope_state: "scoped",
  repositories: ["acme/platform"],
};

/* ── Helpers ── */

function makeAnswer(questionId: string, text: string): SetupAnswer {
  return {
    id: `pans_${questionId}`,
    sessionId: "psetup_test",
    questionId,
    answerSchema: "SetupAnswer@1",
    answer: { original: text, normalized: text },
    revision: 1,
    createdAt: "2026-08-31T10:00:00",
  };
}

function makeGitHubProposal(overrides: Partial<SetupProposal> = {}): SetupProposal {
  return {
    id: "wprop_gh_01",
    sessionId: "psetup_test",
    providerId: "github",
    specSchema: "WatchSpec@1",
    spec: {
      schema: "WatchSpec@1",
      name: "PR health",
      intent: "Watch pull requests",
      provider: { id: "github", transport: "cli" },
      subject: { kind: "pull_requests", scope: { repository: "acme/platform" } },
      trigger: { kind: "poll", everyMinutes: 35 },
      rules: [
        {
          condition: {
            schema: "WatchCondition@1",
            operator: "any",
            clauses: [
              { field: "checks", comparison: "equals", value: "failure" },
              { field: "review_decision", comparison: "equals", value: "changes_requested" },
            ],
          },
          actions: [{ schema: "WatchAction@1", kind: "project.observe" }],
        },
      ],
      action: { schema: "WatchAction@1", kind: "project.observe" },
      mode: "yolo",
    },
    rationale: { fact: "3 active PRs", detail: "acme/platform", subjectCount: 3 },
    state: "proposed",
    testState: null,
    testResult: null,
    createdAt: "2026-08-31T10:03:00",
    updatedAt: "2026-08-31T10:03:00",
    ...overrides,
  };
}

function makeNativeProposal(): SetupProposal {
  return {
    id: "wprop_native_01",
    sessionId: "psetup_test",
    providerId: "native",
    specSchema: "WatchSpec@1",
    spec: {
      schema: "WatchSpec@1",
      name: "Meeting activity",
      intent: "Watch meetings",
      provider: { id: "native", transport: "local_domain" },
      subject: { kind: "meetings" },
      trigger: { kind: "poll", everyMinutes: 35 },
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
    rationale: { fact: "1 meeting", detail: "", subjectCount: 1 },
    state: "proposed",
    testState: null,
    testResult: null,
    createdAt: "2026-08-31T10:03:00",
    updatedAt: "2026-08-31T10:03:00",
  };
}

/* ── Provider state vocabulary (all seven tokens) ── */

describe("Provider state vocabulary", () => {
  it("defines all seven provider states", () => {
    expect(PROVIDER_STATES).toEqual([
      "checking",
      "connected",
      "connection_required",
      "capability_missing",
      "partial",
      "unavailable",
      "owner_action_required",
    ]);
  });

  it.each(PROVIDER_STATES)("state '%s' has card copy with headline and detail", (state) => {
    const copy = PROVIDER_STATE_COPY[state];
    expect(copy.headline).toBeTruthy();
    expect(copy.detail).toBeTruthy();
  });

  it.each(PROVIDER_STATES)("state '%s' has exactly ONE next action", (state) => {
    const action = PROVIDER_STATE_ACTION[state];
    expect(action.label).toBeTruthy();
    expect(action.kind).toBeTruthy();
  });
});

/* ── Provider decoder tests (wire fixtures from integration tests) ── */

describe("Provider decoders", () => {
  it("decodes connected status (test_connected_state)", () => {
    const status = decodeProviderConnectionStatus(WIRE_CONNECTED);
    expect(status.state).toBe("connected");
    expect(status.display.account).toBe("testuser");
    expect(status.errorCode).toBeNull();
  });

  it("decodes owner_action_required status (test_unauthenticated_probe)", () => {
    const status = decodeProviderConnectionStatus(WIRE_OWNER_ACTION);
    expect(status.state).toBe("owner_action_required");
    expect(status.errorCode).toBe("authentication_required");
    expect(status.errorDetail).toBe("gh auth login");
    expect(status.display.recoveryHint).toBe("gh auth login");
  });

  it("decodes discovery response -- owner derived from id (S-1)", () => {
    const disc = decodeDiscoveryResponse(WIRE_DISCOVER);
    expect(disc.state).toBe("ready");
    expect(disc.items).toHaveLength(3);
    expect(disc.items[0].id).toBe("acme/platform");
    // Wire sends no owner field; decoder derives it from id
    expect(disc.items[0].owner).toBe("acme");
    expect(disc.items[1].owner).toBe("acme");
  });

  it("decodes validate-repo valid response (test_valid_repo)", () => {
    const resp = decodeValidateRepoResponse(WIRE_VALID_REPO);
    expect(resp.valid).toBe(true);
    expect(resp.message).toBeNull();
  });

  it("decodes validate-repo invalid response -- error_detail maps to message (S-2)", () => {
    const resp = decodeValidateRepoResponse({
      valid: false,
      error_code: "scope_denied",
      error_detail: "Repository not found or not accessible",
    });
    expect(resp.valid).toBe(false);
    expect(resp.message).toBe("Repository not found or not accessible");
  });

  it("decodes clarify-scope response (test_clarify_scope_with_typed_repo)", () => {
    const resp = decodeClarifyScopeResponse(WIRE_CLARIFY_SCOPE);
    expect(resp.scopeState).toBe("scoped");
    expect(resp.repositories).toContain("acme/platform");
  });

  it("falls back unknown state to unavailable", () => {
    const status = decodeProviderConnectionStatus({ state: "bogus_state" });
    expect(status.state).toBe("unavailable");
  });
});

// HS-168-04: ConnectionStatusCard moved to web/src/pages/cores/connections/ (03 tests it)

/* ── DiscoveryList component tests ── */

describe("DiscoveryList", () => {
  const items: DiscoveryItem[] = decodeDiscoveryResponse(WIRE_DISCOVER).items;

  it("renders discovered items", () => {
    render(
      <DiscoveryList
        items={items}
        cursor={null}
        query=""
        onQueryChange={vi.fn()}
        onLoadMore={vi.fn()}
        onSelect={vi.fn()}
        loading={false}
      />
    );
    expect(screen.getByTestId("provider-discovery-list")).toBeInTheDocument();
    expect(screen.getByTestId("discovery-card-acme/platform")).toBeInTheDocument();
    expect(screen.getByTestId("discovery-card-acme/backend")).toBeInTheDocument();
  });

  it("calls onSelect when a discovery card is clicked", () => {
    const onSelect = vi.fn();
    render(
      <DiscoveryList
        items={items}
        cursor={null}
        query=""
        onQueryChange={vi.fn()}
        onLoadMore={vi.fn()}
        onSelect={onSelect}
        loading={false}
      />
    );
    fireEvent.click(screen.getByTestId("discovery-card-acme/platform"));
    expect(onSelect).toHaveBeenCalledWith("acme/platform");
  });

  it("shows loading state", () => {
    render(
      <DiscoveryList
        items={[]}
        cursor={null}
        query=""
        onQueryChange={vi.fn()}
        onLoadMore={vi.fn()}
        onSelect={vi.fn()}
        loading={true}
      />
    );
    expect(screen.getByText("Discovering repositories...")).toBeInTheDocument();
  });

  it("shows empty state with search hint", () => {
    render(
      <DiscoveryList
        items={[]}
        cursor={null}
        query="nonexistent"
        onQueryChange={vi.fn()}
        onLoadMore={vi.fn()}
        onSelect={vi.fn()}
        loading={false}
      />
    );
    expect(screen.getByText(/No repositories found/)).toBeInTheDocument();
  });

  it("shows Load more button when cursor present", () => {
    render(
      <DiscoveryList
        items={items.slice(0, 1)}
        cursor="1"
        query=""
        onQueryChange={vi.fn()}
        onLoadMore={vi.fn()}
        onSelect={vi.fn()}
        loading={false}
      />
    );
    expect(screen.getByText("Load more")).toBeInTheDocument();
  });

  // HS-168-04: discovery cards use ProvenanceChip instead of EgressChip
  it("provenance chip on each discovery card", () => {
    const { container } = render(
      <DiscoveryList
        items={items.slice(0, 1)}
        cursor={null}
        query=""
        onQueryChange={vi.fn()}
        onLoadMore={vi.fn()}
        onSelect={vi.fn()}
        loading={false}
      />
    );
    const chips = container.querySelectorAll(".surface-provenance-chip");
    expect(chips.length).toBeGreaterThanOrEqual(1);
  });
});

/* ── TypedRepoInput tests ── */

describe("TypedRepoInput", () => {
  it("renders input and button", () => {
    render(<TypedRepoInput onValidate={vi.fn()} validating={false} />);
    expect(screen.getByTestId("provider-typed-repo")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("owner/repo")).toBeInTheDocument();
  });

  it("calls onValidate on button click", () => {
    const onValidate = vi.fn();
    render(<TypedRepoInput onValidate={onValidate} validating={false} />);
    fireEvent.change(screen.getByPlaceholderText("owner/repo"), {
      target: { value: "acme/platform" },
    });
    fireEvent.click(screen.getByText("Check repo"));
    expect(onValidate).toHaveBeenCalledWith("acme/platform");
  });

  it("disables button when validating", () => {
    render(<TypedRepoInput onValidate={vi.fn()} validating={true} />);
    expect(screen.getByText("Checking...")).toBeDisabled();
  });

  it("calls onValidate on Enter key", () => {
    const onValidate = vi.fn();
    render(<TypedRepoInput onValidate={onValidate} validating={false} />);
    const input = screen.getByPlaceholderText("owner/repo");
    fireEvent.change(input, { target: { value: "acme/platform" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onValidate).toHaveBeenCalledWith("acme/platform");
  });
});

/* ── GitHubTestDisplay tests (SS 8.1) ── */
/* HS-168-04: DOM structure changed to SurfaceSection/SurfaceFacts/SurfaceLedger.
   Test selector edits to match the new rendering. */

describe("GitHubTestDisplay (HS-168-04 D3 recomposition)", () => {
  it("renders passed test with POPULATION facts and MATCHES section", () => {
    const { container } = render(
      <GitHubTestDisplay
        repo="acme/platform"
        queryPlainWordsText="acme/platform, open PRs"
        entityCount={2}
        representativeEntities={[
          { id: "42", title: "Add routing", state: "open" },
          { id: "43", title: "Fix tests", state: "open" },
        ]}
        matchedConditions="When CI checks becomes failure"
        observedAt="2026-09-01T10:00:00Z"
        error={null}
        testState="passed"
      />
    );
    expect(screen.getByTestId("provider-test-display")).toHaveAttribute("data-test-state", "passed");
    const text = container.textContent ?? "";
    expect(text).toContain("pull requests");
    expect(text).toContain("acme/platform, open PRs");
    expect(text).toContain("#42");
    expect(text).toContain("Add routing");
    expect(text).toContain("#43");
    expect(text).toContain("MATCHES");
  });

  it("renders POPULATION facts with BASE branch when provided", () => {
    const { container } = render(
      <GitHubTestDisplay
        repo="acme/platform"
        queryPlainWordsText="acme/platform, open PRs, base: main"
        entityCount={0}
        representativeEntities={[]}
        matchedConditions=""
        observedAt="2026-09-01T10:00:00Z"
        error={null}
        testState="passed"
        baseBranch="main"
      />
    );
    const text = container.textContent ?? "";
    expect(text).toContain("SUBJECT");
    expect(text).toContain("pull requests");
    expect(text).toContain("BASE");
    expect(text).toContain("main");
    expect(text).toContain("QUERY");
  });

  it("renders zero-match PASS as StateChip '0 matches' (ACT-002)", () => {
    const { container } = render(
      <GitHubTestDisplay
        repo="acme/platform"
        queryPlainWordsText="open PRs"
        entityCount={0}
        representativeEntities={[]}
        matchedConditions=""
        observedAt="2026-09-01T10:00:00Z"
        error={null}
        testState="passed"
      />
    );
    const text = container.textContent ?? "";
    expect(text).toContain("0 matches");
    expect(text).toContain("MATCHES 0");
  });

  it("renders failed test with error StateChip and message", () => {
    render(
      <GitHubTestDisplay
        repo="acme/platform"
        queryPlainWordsText=""
        entityCount={0}
        representativeEntities={[]}
        matchedConditions=""
        observedAt="2026-09-01T10:00:00Z"
        error={{ type: "PROV-009", message: "Authentication expired" }}
        testState="failed"
      />
    );
    expect(screen.getByTestId("provider-test-display")).toHaveAttribute("data-test-state", "failed");
    expect(screen.getByTestId("provider-test-error")).toBeInTheDocument();
    expect(screen.getByText("PROV-009")).toBeInTheDocument();
    expect(screen.getByText("Authentication expired")).toBeInTheDocument();
  });

  it("limits representative entities to 5 in the ledger", () => {
    const entities = Array.from({ length: 8 }, (_, i) => ({
      id: String(i + 1),
      title: `PR ${i + 1}`,
      state: "open",
    }));
    const { container } = render(
      <GitHubTestDisplay
        repo="acme/platform"
        queryPlainWordsText=""
        entityCount={8}
        representativeEntities={entities}
        matchedConditions=""
        observedAt="2026-09-01T10:00:00Z"
        error={null}
        testState="passed"
      />
    );
    const rows = container.querySelectorAll(".surface-ledger-row");
    expect(rows.length).toBeLessThanOrEqual(5);
  });
});

/* ── Plain-words PR condition vocabulary (HS-161-05) ── */

describe("PR condition plain words", () => {
  it("renders review_requested field as 'review requested'", () => {
    expect(prFieldLabel("review_requested")).toBe("review requested");
  });

  it("renders review_decision field as 'review decision'", () => {
    expect(prFieldLabel("review_decision")).toBe("review decision");
  });

  it("renders checks field as 'CI checks'", () => {
    expect(prFieldLabel("checks")).toBe("CI checks");
  });

  it("renders head_sha field as 'commit SHA'", () => {
    expect(prFieldLabel("head_sha")).toBe("commit SHA");
  });

  it("renders state field as 'PR state'", () => {
    expect(prFieldLabel("state")).toBe("PR state");
  });

  it("renders merged field as 'merged'", () => {
    expect(prFieldLabel("merged")).toBe("merged");
  });

  it("renders updated_at field as 'last updated'", () => {
    expect(prFieldLabel("updated_at")).toBe("last updated");
  });

  it("falls back unknown field to deSnaked form", () => {
    expect(prFieldLabel("some_unknown_field")).toBe("some unknown field");
  });

  it("conditionPlainWords uses PR field labels and phrase table for pull_requests subject", () => {
    const spec: WatchSpec = {
      schema: "WatchSpec@1",
      name: "PR health",
      intent: "Watch PRs",
      provider: { id: "github", transport: "cli" },
      subject: { kind: "pull_requests" },
      trigger: { kind: "poll", everyMinutes: 35 },
      rules: [
        {
          condition: {
            schema: "WatchCondition@1",
            operator: "any",
            clauses: [
              { field: "checks", comparison: "equals", value: "failure" },
              { field: "review_decision", comparison: "equals", value: "changes_requested" },
              { field: "updated_at", comparison: "older_than", value: "7d" },
            ],
          },
          actions: [{ schema: "WatchAction@1", kind: "project.observe" }],
        },
      ],
      action: { schema: "WatchAction@1", kind: "project.observe" },
      mode: "yolo",
    };
    const plainWords = conditionPlainWords(spec);
    // checks:equals:failure not in phrase table -> generic: "When CI checks is failure"
    expect(plainWords).toContain("CI checks");
    // review_decision:equals:changes_requested not in table -> generic: "When review decision is changes_requested"
    expect(plainWords).toContain("review decision");
    // updated_at:older_than:7d IS in phrase table -> "When a PR goes quiet for 7 days"
    expect(plainWords).toContain("When a PR goes quiet for 7 days");
    // Should NOT contain the raw field names
    expect(plainWords).not.toContain("review_decision");
    expect(plainWords).not.toContain("updated_at");
  });

  it("non-PR subject still uses raw field names", () => {
    const spec: WatchSpec = {
      schema: "WatchSpec@1",
      name: "Meeting activity",
      intent: "Watch meetings",
      provider: { id: "native", transport: "local_domain" },
      subject: { kind: "meetings" },
      trigger: { kind: "poll", everyMinutes: 35 },
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
    };
    const plainWords = conditionPlainWords(spec);
    expect(plainWords).toBe("When content changes");
  });
});

/* ── Five-template truth table (HS-161-05 defect 2) ── */

describe("Five-template plain-words truth table", () => {
  /** Helper: build a WatchSpec from the template's rules. */
  function templateSpec(
    name: string,
    clauses: { field: string; comparison: string; value?: unknown }[],
    scope?: Record<string, unknown>,
  ): WatchSpec {
    return {
      schema: "WatchSpec@1",
      name,
      intent: "",
      provider: { id: "github", transport: "connector_pack" },
      subject: {
        kind: "pull_request",
        scope: {
          repositories: ["acme/platform"],
          query: { state: "open", base: "main" },
          ...scope,
        },
      },
      trigger: { kind: "poll", everyMinutes: 35 },
      rules: [
        {
          condition: {
            schema: "WatchCondition@1",
            operator: "any",
            clauses,
          },
          actions: [{ schema: "WatchAction@1", kind: "project.observe" }],
        },
      ],
      action: { schema: "WatchAction@1", kind: "project.observe" },
      mode: "yolo",
    };
  }

  it("review_queue: exact owner-grade copy", () => {
    const spec = templateSpec("PR review queue", [
      { field: "review_requested", comparison: "changed" },
      { field: "review_decision", comparison: "changed" },
    ]);
    expect(conditionPlainWords(spec)).toBe(
      "When a review is requested; When the review decision changes",
    );
    expect(queryPlainWords(spec)).toBe("acme/platform, open PRs, base: main");
  });

  it("ci_health: exact owner-grade copy", () => {
    const spec = templateSpec("CI health", [
      { field: "checks", comparison: "changed_to", value: "failure" },
      { field: "checks", comparison: "changed_to", value: "success" },
    ]);
    expect(conditionPlainWords(spec)).toBe(
      "When CI checks fail; When CI checks recover",
    );
    expect(queryPlainWords(spec)).toBe("acme/platform, open PRs, base: main");
  });

  it("merge_flow: exact owner-grade copy", () => {
    const spec = templateSpec("Merge flow", [
      { field: "state", comparison: "changed" },
      { field: "merged", comparison: "changed_to", value: true },
    ]);
    expect(conditionPlainWords(spec)).toBe(
      "When the PR state changes; When a PR merges",
    );
  });

  it("delivery_drift: exact owner-grade copy", () => {
    const spec = templateSpec("Delivery drift", [
      { field: "updated_at", comparison: "older_than", value: "7d" },
    ]);
    expect(conditionPlainWords(spec)).toBe(
      "When a PR goes quiet for 7 days",
    );
  });

  it("delivery_drift: renders actual duration value (14d)", () => {
    const spec = templateSpec("Delivery drift 14d", [
      { field: "updated_at", comparison: "older_than", value: "14d" },
    ]);
    expect(conditionPlainWords(spec)).toBe(
      "When a PR goes quiet for 14 days",
    );
  });

  it("release_readiness: exact owner-grade copy", () => {
    const spec = templateSpec("Release readiness", [
      { field: "head_sha", comparison: "changed" },
      { field: "checks", comparison: "changed" },
      { field: "review_decision", comparison: "equals", value: "approved" },
    ]);
    expect(conditionPlainWords(spec)).toBe(
      "When the head commit changes; When CI checks change; When the review decision is approved",
    );
  });

  it("Query and Conditions are NEVER identical for any template", () => {
    const templates = [
      templateSpec("Review queue", [
        { field: "review_requested", comparison: "changed" },
        { field: "review_decision", comparison: "changed" },
      ]),
      templateSpec("CI health", [
        { field: "checks", comparison: "changed_to", value: "failure" },
        { field: "checks", comparison: "changed_to", value: "success" },
      ]),
      templateSpec("Merge flow", [
        { field: "state", comparison: "changed" },
        { field: "merged", comparison: "changed_to", value: true },
      ]),
      templateSpec("Delivery drift", [
        { field: "updated_at", comparison: "older_than", value: "7d" },
      ]),
      templateSpec("Release readiness", [
        { field: "head_sha", comparison: "changed" },
        { field: "checks", comparison: "changed" },
        { field: "review_decision", comparison: "equals", value: "approved" },
      ]),
    ];

    for (const spec of templates) {
      expect(queryPlainWords(spec)).not.toBe(conditionPlainWords(spec));
    }
  });

  it("deduplicates identical clause texts within one spec", () => {
    const spec = templateSpec("Dedup test", [
      { field: "checks", comparison: "changed" },
      { field: "checks", comparison: "changed" },
    ]);
    expect(conditionPlainWords(spec)).toBe("When CI checks change");
  });

  it("falls back to generic verb for PR combinations not in the table", () => {
    const spec = templateSpec("Custom", [
      { field: "labels", comparison: "contains", value: "urgent" },
    ]);
    // Not in the closed table; generic path renders with prFieldLabel
    expect(conditionPlainWords(spec)).toBe("When labels contains urgent");
  });
});

/* ── SuggestionCards egress badge tests ── */

describe("SuggestionCards provenance (HS-168-04)", () => {
  it("GitHub cards have ProvenanceChip with source 'gh'", () => {
    const proposals = [makeGitHubProposal()];
    const { container } = render(
      <SuggestionCards
        proposals={proposals}
        onSelect={vi.fn()}
        onDeselect={vi.fn()}
        onTest={vi.fn()}
        suggesting={false}
      />
    );
    const ghChips = container.querySelectorAll(".surface-provenance-source");
    const ghTexts = Array.from(ghChips).map((el) => el.textContent);
    expect(ghTexts).toContain("gh");
  });

  it("native cards have ProvenanceChip with source 'local'", () => {
    const proposals = [makeNativeProposal()];
    const { container } = render(
      <SuggestionCards
        proposals={proposals}
        onSelect={vi.fn()}
        onDeselect={vi.fn()}
        onTest={vi.fn()}
        suggesting={false}
      />
    );
    const provChips = container.querySelectorAll(".surface-provenance-source");
    const texts = Array.from(provChips).map((el) => el.textContent);
    expect(texts).toContain("local");
  });
});

/* ── ActivationReview egress badge + PR plain-words ── */

describe("ActivationReview GitHub enhancements", () => {
  it("shows egress badge on GitHub watch specs", () => {
    const ghProposal = makeGitHubProposal({
      state: "selected",
      testState: "passed",
      testResult: {
        entityCount: 1,
        representativeEntities: [{ id: "42", title: "PR 42", state: "open" }],
        observedAt: "2026-09-01T10:00:00Z",
        error: null,
        message: "Test passed -- 1 current matches",
      },
    });
    const { container } = render(
      <ActivationReview
        outcomeAnswer={makeAnswer("outcome", "Monitor PRs")}
        signalsAnswer={makeAnswer("signals", "CI failures")}
        proposals={[ghProposal]}
        onFinalize={vi.fn()}
        onBack={vi.fn()}
        finalizing={false}
      />
    );
    const badges = container.querySelectorAll(".gadget-chip-egress");
    expect(badges.length).toBeGreaterThanOrEqual(1);
  });

  it("does NOT show egress badge on native watch specs", () => {
    const nativeProposal = {
      ...makeNativeProposal(),
      state: "selected",
      testState: "passed",
      testResult: {
        entityCount: 1,
        representativeEntities: [{ id: "m1", title: "Meeting" }],
        observedAt: "2026-09-01T10:00:00Z",
        error: null,
        message: "Test passed -- 1 current matches",
      },
    };
    const { container } = render(
      <ActivationReview
        outcomeAnswer={makeAnswer("outcome", "Watch meetings")}
        signalsAnswer={makeAnswer("signals", "Content changes")}
        proposals={[nativeProposal]}
        onFinalize={vi.fn()}
        onBack={vi.fn()}
        finalizing={false}
      />
    );
    const badges = container.querySelectorAll(".gadget-chip-egress");
    expect(badges.length).toBe(0);
  });

  it("renders PR conditions with plain-words field names in review", () => {
    const ghProposal = makeGitHubProposal({
      state: "selected",
      testState: "passed",
      testResult: {
        entityCount: 2,
        representativeEntities: [],
        observedAt: "2026-09-01T10:00:00Z",
        error: null,
        message: "Test passed -- 2 current matches",
      },
    });
    render(
      <ActivationReview
        outcomeAnswer={makeAnswer("outcome", "Monitor PRs")}
        signalsAnswer={makeAnswer("signals", "CI failures")}
        proposals={[ghProposal]}
        onFinalize={vi.fn()}
        onBack={vi.fn()}
        finalizing={false}
      />
    );
    // Conditions should use plain-words (CI checks, review decision)
    const reviewEl = screen.getByTestId("setup-review");
    expect(reviewEl.textContent).toContain("CI checks");
    expect(reviewEl.textContent).toContain("review decision");
  });
});

/* ── SETFLOW-003: state preservation, never-active-before-test ── */
// HS-168-04: auth-recovery card moved to web/src/pages/cores/connections/ (03 tests it).
// State preservation + never-active-before-test still tested via SuggestionCards.

describe("SETFLOW-003 state preservation (HS-168-04)", () => {
  it("suggestion cards render with proposals present — setup state not lost", () => {
    const proposals = [makeGitHubProposal()];
    render(
      <SuggestionCards
        proposals={proposals}
        onSelect={vi.fn()}
        onDeselect={vi.fn()}
        onTest={vi.fn()}
        suggesting={false}
      />
    );
    expect(screen.getByTestId("setup-suggestion-cards")).toBeInTheDocument();
    expect(screen.getByTestId("setup-card-wprop_gh_01")).toBeInTheDocument();
  });

  it("GitHub NEVER appears active before a passing test", () => {
    const ghProposal = makeGitHubProposal({ state: "selected", testState: null });
    const { container } = render(
      <SuggestionCards
        proposals={[ghProposal]}
        onSelect={vi.fn()}
        onDeselect={vi.fn()}
        onTest={vi.fn()}
        suggesting={false}
      />
    );
    const card = container.querySelector('[data-testid="setup-card-wprop_gh_01"]');
    expect(card?.getAttribute("data-state")).not.toBe("active");
    expect(card?.getAttribute("data-state")).not.toBe("tested");
    expect(card?.getAttribute("data-state")).toBe("proposed");
  });

  it("GitHub becomes tested only after testState=passed", () => {
    const ghProposal = makeGitHubProposal({
      state: "selected",
      testState: "passed",
      testResult: {
        entityCount: 0,
        representativeEntities: [],
        observedAt: "2026-09-01T10:00:00Z",
        error: null,
        message: "Test passed -- 0 current matches",
      },
    });
    const { container } = render(
      <SuggestionCards
        proposals={[ghProposal]}
        onSelect={vi.fn()}
        onDeselect={vi.fn()}
        onTest={vi.fn()}
        suggesting={false}
      />
    );
    const card = container.querySelector('[data-testid="setup-card-wprop_gh_01"]');
    expect(card?.getAttribute("data-state")).toBe("tested");
  });
});
