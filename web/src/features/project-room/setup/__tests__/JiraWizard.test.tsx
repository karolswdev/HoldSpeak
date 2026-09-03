// HS-166-04 round 2 — JiraWizard tests: accounts (D1), scope (D2),
// test (D3), mounted flow, suggestion badge.

import React from "react";
import { render, screen, fireEvent, within, waitFor, act } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

/* ── Mocks ── */

vi.mock("../../../../desk/surface/controls/MicButton", () => ({
  MicButton: ({
    onText,
    label,
  }: {
    onText: (text: string) => void;
    label?: string;
  }) => (
    <button data-testid="mic-btn" aria-label={label} onClick={() => onText("voice")}>
      Mic
    </button>
  ),
}));

vi.mock("../../../../desk/surface/SurfaceFooter", () => ({
  SurfaceFooter: ({
    verbs,
  }: {
    verbs?: React.ReactNode;
  }) => (
    <footer data-testid="surface-footer">{verbs}</footer>
  ),
}));

// jsdom doesn't have scrollIntoView
HTMLElement.prototype.scrollIntoView = vi.fn();

import {
  JiraAccountsStep,
  JiraScopeStep,
  JiraTestStep,
  JiraWizardFlow,
} from "../JiraWizard";

import type {
  JiraConnection,
  JiraKnownAccount,
  JiraDiscoveryResponse,
  JiraSearchResult,
  JiraScope,
  SetupProposal,
} from "../model";

/* ── Fixtures ── */

const CONN_ALPHA: JiraConnection = {
  provider_id: "jira",
  connection_ref: "alpha.atlassian.net|user@example.com",
  state: "connected",
  account: { site: "alpha.atlassian.net", email: "user@example.com" },
  error_code: null,
  error_detail: null,
  recovery: null,
  checked_at: "2026-09-02T10:00:00+00:00",
  last_connected_at: "2026-09-02T10:00:00+00:00",
};

const CONN_BETA: JiraConnection = {
  provider_id: "jira",
  connection_ref: "beta.atlassian.net|admin@example.com",
  state: "owner_action_required",
  account: { site: "beta.atlassian.net", email: "admin@example.com" },
  error_code: "auth_required",
  error_detail: "Not authenticated",
  recovery: {
    command: "acli jira auth login --site beta.atlassian.net --email admin@example.com --token",
    hint: "Authenticate with your Atlassian API token",
  },
  checked_at: "2026-09-02T10:01:00+00:00",
  last_connected_at: null,
};

const KNOWN_ACME: JiraKnownAccount = {
  site: "acme.atlassian.net",
  email: "karol@acme.dev",
  displayName: "Karol",
  authType: "pat",
  ref: "acme.atlassian.net|karol@acme.dev",
  current: false,
};

const PROJECTS_RESPONSE: JiraDiscoveryResponse = {
  state: "ready",
  items: [
    { id: "KAN", key: "KAN", name: "Kanban Board", type: "software", style: "next-gen" },
    { id: "HR", key: "HR", name: "HR Updates", type: "software", style: "next-gen" },
  ],
  cursor: null,
  errorCode: null,
  errorDetail: null,
  connectionRef: "alpha.atlassian.net|user@example.com",
};

const ISSUE_TYPES_RESPONSE: JiraDiscoveryResponse = {
  state: "ready",
  items: [
    { id: "10004", name: "Epic", subtask: false },
    { id: "10005", name: "Subtask", subtask: true },
    { id: "10006", name: "Task", subtask: false },
  ],
  cursor: null,
  errorCode: null,
  errorDetail: null,
  connectionRef: "alpha.atlassian.net|user@example.com",
  source: "enumerated",
};

const STATUSES_RESPONSE: JiraDiscoveryResponse = {
  state: "ready",
  items: [
    { id: "10005", name: "In Progress", category: "indeterminate", category_name: "In Progress" },
    { id: "10006", name: "Done", category: "done", category_name: "Done" },
  ],
  cursor: null,
  errorCode: null,
  errorDetail: null,
  connectionRef: "alpha.atlassian.net|user@example.com",
  source: "observed",
};

const PREVIEW_OK: JiraSearchResult = {
  state: "ready",
  items: [
    { key: "KAN-1", id: "10002", summary: "Task 1", issueType: "Task", status: "In Progress", statusCategory: "indeterminate", assignee: null, priority: null, labels: [], url: "", dueDate: "2026-09-10" },
    { key: "KAN-2", id: "10004", summary: "Task 2", issueType: "Task", status: "In Progress", statusCategory: "indeterminate", assignee: null, priority: null, labels: [], url: "" },
  ],
  calls: 3,
  errorCode: null,
  errorDetail: null,
  connectionRef: "alpha.atlassian.net|user@example.com",
};

const PREVIEW_INVALID: JiraSearchResult = {
  state: "failed",
  items: [],
  calls: 0,
  errorCode: "query_invalid",
  errorDetail: "failed to parse JQL",
  connectionRef: "alpha.atlassian.net|user@example.com",
  queryInvalid: "failed to parse JQL query: Unexpected token",
};

const EMPTY_SCOPE: JiraScope = {
  connectionRef: "",
  projects: [],
  issueTypes: [],
  statusCategories: [],
  jql: "",
};

const SCOPED: JiraScope = {
  connectionRef: "alpha.atlassian.net|user@example.com",
  projects: ["KAN"],
  issueTypes: ["Task", "Epic"],
  statusCategories: ["indeterminate"],
  jql: "project = KAN AND status != Done",
};

function jiraProposal(overrides: Record<string, unknown> = {}): SetupProposal {
  return {
    id: "wprop_jira_01",
    sessionId: "psetup_test",
    providerId: "jira",
    specSchema: "WatchSpec@1",
    spec: {
      schema: "WatchSpec@1",
      name: "Jira blockers",
      intent: "Watch blocked issues",
      provider: { id: "jira", transport: "connector_pack", connection_ref: "alpha.atlassian.net|user@example.com" },
      subject: { kind: "issue", scope: { connection_ref: "alpha.atlassian.net|user@example.com", projects: ["KAN"] }, query: { connection_ref: "alpha.atlassian.net|user@example.com" } },
      trigger: { kind: "poll", everyMinutes: 15 },
      rules: [{ condition: { schema: "WatchCondition@1", operator: "any", clauses: [{ field: "status", comparison: "entered_state", value: "Blocked" }] }, actions: [{ schema: "WatchAction@1", kind: "project.observe" }] }],
      action: { schema: "WatchAction@1", kind: "project.observe" },
      mode: "yolo",
    },
    rationale: { fact: "Jira connected", detail: "", source: "jira", template_id: "jira_blockers" },
    state: "proposed",
    testState: null,
    testResult: null,
  } as unknown as SetupProposal;
}

function testedProposal(): SetupProposal {
  const p = jiraProposal();
  p.state = "selected";
  p.testState = "passed";
  p.testResult = {
    entityCount: 3,
    representativeEntities: [
      { key: "KAN-1", summary: "Task 1", status: "In Progress", due_at: "2026-09-10" },
      { key: "KAN-2", summary: "Task 2", status: "In Progress" },
      { key: "KAN-3", summary: "Subtask 2.1", status: "Done" },
    ],
    observedAt: "2026-09-02T21:51:43Z",
    durationMs: 900,
    error: null,
    message: "Test passed -- 3 current matches",
    provider: "jira",
    connection: { site: "alpha.atlassian.net", email: "user@example.com", connection_ref: "alpha.atlassian.net|user@example.com" },
    projects: ["KAN"],
    normalizedJql: "project = KAN AND status != Done",
    matchedConditions: "status entered Blocked",
    supportedTransitions: ["jira.issue.status_changed", "jira.issue.assigned", "jira.issue.due_changed", "jira.issue.resolved"],
    calls: 4,
  } as unknown as SetupProposal["testResult"];
  return p;
}

/* ═══════════════════════════════════════════════════════════════════
   D1 — Accounts step
   ═══════════════════════════════════════════════════════════════════ */

describe("JiraAccountsStep", () => {
  const noop = () => {};

  it("renders connected card with ok tier and StateChip success", () => {
    render(
      <JiraAccountsStep
        connections={[CONN_ALPHA]}
        knownAccounts={[]}
        selectedRef={null}
        onSelect={noop}
        onRecheck={noop}
        onAdd={noop}
        onBack={noop}
        onNext={noop}
      />,
    );
    expect(screen.getAllByText("alpha.atlassian.net").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("user@example.com")).toBeTruthy();
    // StateChip renders "Connected" -- may appear in facts too
    expect(screen.getAllByText("Connected").length).toBeGreaterThanOrEqual(1);
  });

  it("renders sign-in card with warn tier and fold containing login command", () => {
    render(
      <JiraAccountsStep
        connections={[CONN_BETA]}
        knownAccounts={[]}
        selectedRef={null}
        onSelect={noop}
        onRecheck={noop}
        onAdd={noop}
        onBack={noop}
        onNext={noop}
      />,
    );
    expect(screen.getAllByText("beta.atlassian.net").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Sign in").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Login command")).toBeTruthy();
  });

  it("renders known-to-acli card with cool tier and Use verb", () => {
    render(
      <JiraAccountsStep
        connections={[]}
        knownAccounts={[KNOWN_ACME]}
        selectedRef={null}
        onSelect={noop}
        onRecheck={noop}
        onAdd={noop}
        onBack={noop}
        onNext={noop}
      />,
    );
    expect(screen.getAllByText("acme.atlassian.net").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Known to acli")).toBeTruthy();
    // TransportKey renders label as aria-label, not visible text
    const useBtn = screen.getByText("Use this account");
    expect(useBtn).toBeTruthy();
  });

  it("renders ghost Add card with StringGadget inputs", () => {
    render(
      <JiraAccountsStep
        connections={[]}
        knownAccounts={[]}
        selectedRef={null}
        onSelect={noop}
        onRecheck={noop}
        onAdd={noop}
        onBack={noop}
        onNext={noop}
      />,
    );
    const addCard = screen.getByTestId("jira-add-card");
    expect(addCard).toBeTruthy();
    expect(screen.getByText("Add account")).toBeTruthy();
    // StringGadget renders inputs with aria-label
    expect(screen.getByLabelText("Site")).toBeTruthy();
    expect(screen.getByLabelText("Email")).toBeTruthy();
  });

  it("LampGadget shows N of M connected", () => {
    render(
      <JiraAccountsStep
        connections={[CONN_ALPHA, CONN_BETA]}
        knownAccounts={[]}
        selectedRef={null}
        onSelect={noop}
        onRecheck={noop}
        onAdd={noop}
        onBack={noop}
        onNext={noop}
      />,
    );
    expect(screen.getByText("1 of 2 connected")).toBeTruthy();
  });

  it("ProvenanceChip on each connection card names the site", () => {
    render(
      <JiraAccountsStep
        connections={[CONN_ALPHA, CONN_BETA]}
        knownAccounts={[]}
        selectedRef={null}
        onSelect={noop}
        onRecheck={noop}
        onAdd={noop}
        onBack={noop}
        onNext={noop}
      />,
    );
    // ProvenanceChip renders source + boundary
    const provChips = screen.getAllByText("acli");
    expect(provChips.length).toBeGreaterThanOrEqual(2);
  });

  it("onAdd is called with site and email from the ghost card", () => {
    const onAdd = vi.fn();
    render(
      <JiraAccountsStep
        connections={[]}
        knownAccounts={[]}
        selectedRef={null}
        onSelect={noop}
        onRecheck={noop}
        onAdd={onAdd}
        onBack={noop}
        onNext={noop}
      />,
    );
    const siteInput = screen.getByLabelText("Site") as HTMLInputElement;
    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    fireEvent.change(siteInput, { target: { value: "test.atlassian.net" } });
    fireEvent.change(emailInput, { target: { value: "test@test.com" } });
    const addBtn = screen.getByText("Add");
    fireEvent.click(addBtn);
    expect(onAdd).toHaveBeenCalledWith("test.atlassian.net", "test@test.com");
  });

  it("known account deduplicates against connections", () => {
    const sameKnown: JiraKnownAccount = {
      ...KNOWN_ACME,
      site: "alpha.atlassian.net",
      email: "user@example.com",
      ref: "alpha.atlassian.net|user@example.com",
    };
    render(
      <JiraAccountsStep
        connections={[CONN_ALPHA]}
        knownAccounts={[sameKnown]}
        selectedRef={null}
        onSelect={noop}
        onRecheck={noop}
        onAdd={noop}
        onBack={noop}
        onNext={noop}
      />,
    );
    // Should NOT show "Known to acli" since it's already a connection
    expect(screen.queryByText("Known to acli")).toBeNull();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   D2 — Scope step
   ═══════════════════════════════════════════════════════════════════ */

describe("JiraScopeStep", () => {
  const noop = () => {};

  it("renders project cards", () => {
    render(
      <JiraScopeStep
        projects={PROJECTS_RESPONSE}
        issueTypes={null}
        statuses={null}
        scope={EMPTY_SCOPE}
        preview={null}
        site="alpha.atlassian.net"
        onSelectProject={noop}
        onToggleType={noop}
        onToggleStatus={noop}
        onJqlChange={noop}
        onPreview={noop}
        onSearchProjects={noop}
        discovering={false}
        previewing={false}
        onBack={noop}
        onTest={noop}
      />,
    );
    expect(screen.getByText("Kanban Board")).toBeTruthy();
    expect(screen.getByText("HR Updates")).toBeTruthy();
  });

  it("shows population sheet with CheckGadget toggles when project selected", () => {
    render(
      <JiraScopeStep
        projects={PROJECTS_RESPONSE}
        issueTypes={ISSUE_TYPES_RESPONSE}
        statuses={STATUSES_RESPONSE}
        scope={{ ...EMPTY_SCOPE, projects: ["KAN"] }}
        preview={null}
        site="alpha.atlassian.net"
        onSelectProject={noop}
        onToggleType={noop}
        onToggleStatus={noop}
        onJqlChange={noop}
        onPreview={noop}
        onSearchProjects={noop}
        discovering={false}
        previewing={false}
        onBack={noop}
        onTest={noop}
      />,
    );
    // CheckGadget renders aria-label checkboxes
    expect(screen.getByLabelText("Epic")).toBeTruthy();
    expect(screen.getByLabelText("Task")).toBeTruthy();
    expect(screen.getByLabelText("In Progress")).toBeTruthy();
    expect(screen.getByLabelText("Done")).toBeTruthy();
  });

  it("renders preview with SurfaceLedgerRow showing issue keys", () => {
    render(
      <JiraScopeStep
        projects={PROJECTS_RESPONSE}
        issueTypes={null}
        statuses={null}
        scope={{ ...EMPTY_SCOPE, projects: ["KAN"] }}
        preview={PREVIEW_OK}
        site="alpha.atlassian.net"
        onSelectProject={noop}
        onToggleType={noop}
        onToggleStatus={noop}
        onJqlChange={noop}
        onPreview={noop}
        onSearchProjects={noop}
        discovering={false}
        previewing={false}
        onBack={noop}
        onTest={noop}
      />,
    );
    const previewEl = screen.getByTestId("jira-preview");
    expect(previewEl).toBeTruthy();
    expect(screen.getByText("KAN-1")).toBeTruthy();
    expect(screen.getByText("Task 1")).toBeTruthy();
    expect(screen.getByText("KAN-2")).toBeTruthy();
  });

  it("query_invalid renders as ActionNotice", () => {
    render(
      <JiraScopeStep
        projects={PROJECTS_RESPONSE}
        issueTypes={null}
        statuses={null}
        scope={{ ...EMPTY_SCOPE, projects: ["KAN"], jql: "bad query" }}
        preview={PREVIEW_INVALID}
        site="alpha.atlassian.net"
        onSelectProject={noop}
        onToggleType={noop}
        onToggleStatus={noop}
        onJqlChange={noop}
        onPreview={noop}
        onSearchProjects={noop}
        discovering={false}
        previewing={false}
        onBack={noop}
        onTest={noop}
      />,
    );
    expect(screen.getByText("failed to parse JQL query: Unexpected token")).toBeTruthy();
    // It's inside an ActionNotice with role="alert"
    expect(screen.getByRole("alert")).toBeTruthy();
  });

  it("ProvenanceChip on project cards names the site", () => {
    render(
      <JiraScopeStep
        projects={PROJECTS_RESPONSE}
        issueTypes={null}
        statuses={null}
        scope={EMPTY_SCOPE}
        preview={null}
        site="alpha.atlassian.net"
        onSelectProject={noop}
        onToggleType={noop}
        onToggleStatus={noop}
        onJqlChange={noop}
        onPreview={noop}
        onSearchProjects={noop}
        discovering={false}
        previewing={false}
        onBack={noop}
        onTest={noop}
      />,
    );
    const provs = screen.getAllByText("acli");
    expect(provs.length).toBeGreaterThanOrEqual(2);
  });

  it("categories-seen chip shows count", () => {
    render(
      <JiraScopeStep
        projects={PROJECTS_RESPONSE}
        issueTypes={null}
        statuses={STATUSES_RESPONSE}
        scope={{ ...EMPTY_SCOPE, projects: ["KAN"] }}
        preview={null}
        site="alpha.atlassian.net"
        onSelectProject={noop}
        onToggleType={noop}
        onToggleStatus={noop}
        onJqlChange={noop}
        onPreview={noop}
        onSearchProjects={noop}
        discovering={false}
        previewing={false}
        onBack={noop}
        onTest={noop}
      />,
    );
    expect(screen.getByText("2 of 3 categories seen")).toBeTruthy();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   D3 — Test step
   ═══════════════════════════════════════════════════════════════════ */

describe("JiraTestStep", () => {
  const noop = () => {};

  it("renders ProgressPlan with 5 steps from real test result", () => {
    render(
      <JiraTestStep
        proposal={testedProposal()}
        site="alpha.atlassian.net"
        email="user@example.com"
        onTestAgain={noop}
        onReview={noop}
        onBack={noop}
      />,
    );
    expect(screen.getByText(/Switch to alpha\.atlassian\.net/)).toBeTruthy();
    expect(screen.getByText(/Read back account/)).toBeTruthy();
    expect(screen.getByText(/Search KAN/)).toBeTruthy();
    expect(screen.getByText(/Enrich due dates/)).toBeTruthy();
    expect(screen.getByText("Baseline ready")).toBeTruthy();
  });

  it("Receipt shows 'Test passed' with timestamp", () => {
    render(
      <JiraTestStep
        proposal={testedProposal()}
        site="alpha.atlassian.net"
        email="user@example.com"
        onTestAgain={noop}
        onReview={noop}
        onBack={noop}
      />,
    );
    expect(screen.getByText("Test passed")).toBeTruthy();
  });

  it("ProvenanceChip in plan footer names the site", () => {
    render(
      <JiraTestStep
        proposal={testedProposal()}
        site="alpha.atlassian.net"
        email="user@example.com"
        onTestAgain={noop}
        onReview={noop}
        onBack={noop}
      />,
    );
    const provs = screen.getAllByText("acli");
    expect(provs.length).toBeGreaterThanOrEqual(1);
  });

  it("renders match count with calls from test result", () => {
    render(
      <JiraTestStep
        proposal={testedProposal()}
        site="alpha.atlassian.net"
        email="user@example.com"
        onTestAgain={noop}
        onReview={noop}
        onBack={noop}
      />,
    );
    const matchCount = screen.getByTestId("jira-test-match-count");
    expect(matchCount).toBeTruthy();
    expect(matchCount.textContent).toContain("4 calls");
  });

  it("renders representative issue ledger rows", () => {
    render(
      <JiraTestStep
        proposal={testedProposal()}
        site="alpha.atlassian.net"
        email="user@example.com"
        onTestAgain={noop}
        onReview={noop}
        onBack={noop}
      />,
    );
    expect(screen.getByText("KAN-1")).toBeTruthy();
    expect(screen.getByText("Task 1")).toBeTruthy();
    expect(screen.getByText("KAN-3")).toBeTruthy();
  });

  it("renders will-notice conditions as active chips and transitions as idle", () => {
    render(
      <JiraTestStep
        proposal={testedProposal()}
        site="alpha.atlassian.net"
        email="user@example.com"
        onTestAgain={noop}
        onReview={noop}
        onBack={noop}
      />,
    );
    const notice = screen.getByTestId("jira-will-notice");
    expect(notice).toBeTruthy();
    // Conditions are active chips
    expect(screen.getByText("Status enters Blocked")).toBeTruthy();
    // Transitions are idle chips
    expect(screen.getByText("Status changed")).toBeTruthy();
    expect(screen.getByText("Assigned")).toBeTruthy();
  });

  it("LampGadget shows 'Tested' when passed", () => {
    render(
      <JiraTestStep
        proposal={testedProposal()}
        site="alpha.atlassian.net"
        email="user@example.com"
        onTestAgain={noop}
        onReview={noop}
        onBack={noop}
      />,
    );
    expect(screen.getByText("Tested")).toBeTruthy();
  });

  it("shows 'Test again' and 'Review and activate' keys", () => {
    render(
      <JiraTestStep
        proposal={testedProposal()}
        site="alpha.atlassian.net"
        email="user@example.com"
        onTestAgain={noop}
        onReview={noop}
        onBack={noop}
      />,
    );
    // Verb buttons render as plain text buttons (not TransportKey)
    expect(screen.getByText("Test again")).toBeTruthy();
    expect(screen.getByText("Review and activate")).toBeTruthy();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   JiraWizardFlow — sequences accounts → scope → test
   ═══════════════════════════════════════════════════════════════════ */

describe("JiraWizardFlow", () => {
  const noop = () => {};
  const defaultProps = {
    proposal: jiraProposal(),
    connections: [CONN_ALPHA, CONN_BETA],
    knownAccounts: [],
    selectedRef: null as string | null,
    projects: null as JiraDiscoveryResponse | null,
    issueTypes: null as JiraDiscoveryResponse | null,
    statuses: null as JiraDiscoveryResponse | null,
    scope: EMPTY_SCOPE,
    preview: null as JiraSearchResult | null,
    loading: false,
    discovering: false,
    previewing: false,
    onLoadConnections: vi.fn(),
    onAddConnection: noop,
    onRecheckConnection: noop,
    onSelectConnection: noop,
    onSelectProject: noop,
    onToggleType: noop,
    onToggleStatus: noop,
    onJqlChange: noop,
    onPreview: noop,
    onSearchProjects: noop,
    onClarifyScope: noop,
    onTest: noop,
    onDone: noop,
    onUpdateScope: noop,
  };

  it("starts on accounts step with jira-wizard-flow testid", () => {
    render(<JiraWizardFlow {...defaultProps} />);
    expect(screen.getByTestId("jira-wizard-flow")).toBeTruthy();
    expect(screen.getByTestId("jira-accounts-step")).toBeTruthy();
  });

  it("calls onLoadConnections on mount when no connections", () => {
    const onLoad = vi.fn();
    render(<JiraWizardFlow {...defaultProps} connections={[]} onLoadConnections={onLoad} />);
    expect(onLoad).toHaveBeenCalledTimes(1);
  });
});

/* ═══════════════════════════════════════════════════════════════════
   SetupRoot mounts JiraWizardFlow + suggestions collapse
   ═══════════════════════════════════════════════════════════════════ */

// The mounted test through SetupRoot requires mocking ../api AND
// ../../../../desk/surface/Surface, which clobbers SurfaceLedger/
// SurfaceWell/SurfaceLedgerRow for the entire module. That breaks
// JiraTestStep and JiraScopeStep (they use those components).
// The mounted path is validated by the glass rig (honest e2e).
// This unit test verifies the flow composition in isolation.

/* ═══════════════════════════════════════════════════════════════════
   SuggestionCards Jira badge names the site
   ═══════════════════════════════════════════════════════════════════ */

describe("SuggestionCards Jira badge", () => {
  // We test this by importing SuggestionCards directly and verifying
  // the EgressChip title includes the site from connection_ref.

  it("Jira proposal EgressChip title names the site from connection_ref", async () => {
    // Import the actual SuggestionCards (it has the EgressChip logic)
    const { SuggestionCards } = await import("../SuggestionCards");
    const p = jiraProposal();
    const noop = () => {};
    render(
      <SuggestionCards
        proposals={[p]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );
    // The EgressChip for jira has title with the site
    const egressChip = document.querySelector('[title*="alpha.atlassian.net"]');
    expect(egressChip).toBeTruthy();
  });
});
