// HS-161-05 -- mounted-path tests: the provider wizard renders in the REAL
// setup flow (SetupRoot -> controller -> ProviderWizardFlow). Proves the
// wizard is mounted, not just tested in isolation.
//
// Walks: select GitHub candidate -> connection check -> repo scope ->
// test -> back to cards. Also: unauthenticated path (SETFLOW-003 on
// the actual glass), and never-active-before-test at the mounted level.

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

/* ── Mock api module (all routes including provider ones) ── */

const mockStartSetup = vi.fn();
const mockGetSetup = vi.fn();
const mockSubmitAnswer = vi.fn();
const mockSuggest = vi.fn();
const mockSelectProposal = vi.fn();
const mockDeselectProposal = vi.fn();
const mockClarifyProposal = vi.fn();
const mockTestProposal = vi.fn();
const mockFinalize = vi.fn();
const mockAbandon = vi.fn();
const mockGetGitHubConnection = vi.fn();
const mockRecheckGitHubConnection = vi.fn();
const mockDiscoverGitHub = vi.fn();
const mockValidateGitHubRepo = vi.fn();
const mockClarifyScope = vi.fn();

vi.mock("../api", () => ({
  startSetup: (...args: unknown[]) => mockStartSetup(...args),
  getSetup: (...args: unknown[]) => mockGetSetup(...args),
  submitAnswer: (...args: unknown[]) => mockSubmitAnswer(...args),
  suggest: (...args: unknown[]) => mockSuggest(...args),
  selectProposal: (...args: unknown[]) => mockSelectProposal(...args),
  deselectProposal: (...args: unknown[]) => mockDeselectProposal(...args),
  clarifyProposal: (...args: unknown[]) => mockClarifyProposal(...args),
  testProposal: (...args: unknown[]) => mockTestProposal(...args),
  finalize: (...args: unknown[]) => mockFinalize(...args),
  abandon: (...args: unknown[]) => mockAbandon(...args),
  getGitHubConnection: (...args: unknown[]) => mockGetGitHubConnection(...args),
  recheckGitHubConnection: (...args: unknown[]) => mockRecheckGitHubConnection(...args),
  discoverGitHub: (...args: unknown[]) => mockDiscoverGitHub(...args),
  validateGitHubRepo: (...args: unknown[]) => mockValidateGitHubRepo(...args),
  clarifyScope: (...args: unknown[]) => mockClarifyScope(...args),
}));

/* ── Mock shell ── */
vi.mock("../../../../desk/shell", () => ({
  openSurface: vi.fn(),
}));

/* ── Mock desk store (HS-168-04: subscribe for windowsById) ── */
vi.mock("../../../../desk/store", () => ({
  useDesk: {
    getState: () => ({
      windowsById: {},
      openSurfaceWindow: vi.fn(),
    }),
    subscribe: () => () => {},
  },
}));

/* ── Mock connections API (HS-168-04: fetchConnections) ── */
vi.mock("../../../../pages/cores/connections/api", () => ({
  fetchConnections: vi.fn().mockResolvedValue({ tools: [] }),
}));

/* ── Mock SurfaceFooter ── */
vi.mock("../../../../desk/surface/SurfaceFooter", () => ({
  SurfaceFooter: ({
    verbs,
  }: {
    verbs?: React.ReactNode;
  }) => (
    <footer data-testid="surface-footer">{verbs}</footer>
  ),
}));

/* ── Mock MicButton ── */
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

/* ── Mock TitleSlotContext ── */
vi.mock("../../../../desk/surface/title", () => ({
  TitleSlotContext: React.createContext(null),
}));

/* ── Mock SurfaceColumns (renders children inline for testing) ── */
vi.mock("../../../../desk/surface/Surface", () => ({
  SurfaceColumns: ({
    main,
    side,
  }: {
    main: React.ReactNode;
    side: React.ReactNode;
  }) => (
    <div data-testid="surface-columns">
      <div data-testid="surface-main">{main}</div>
      <div data-testid="surface-side">{side}</div>
    </div>
  ),
  SurfaceSection: ({ label, children }: { label?: string; children: React.ReactNode }) => (
    <section data-testid={`surface-section-${label ?? ""}`}>{label ? <h3>{label}</h3> : null}{children}</section>
  ),
  SurfaceFacts: ({ value }: { value: unknown }) => {
    if (!value || typeof value !== "object") return null;
    return (
      <dl data-testid="surface-facts">
        {Object.entries(value as Record<string, unknown>).map(([k, v]) => (
          <React.Fragment key={k}><dt>{k}</dt><dd>{String(v)}</dd></React.Fragment>
        ))}
      </dl>
    );
  },
  SurfaceLedger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SurfaceLedgerRow: ({ primary, lead, cells, trailing, wrap, expands, children, ...rest }: Record<string, unknown>) => (
    <li className="surface-ledger-row" {...(rest["data-testid"] ? { "data-testid": rest["data-testid"] } : {})}>
      {lead != null ? <span className="surface-ledger-lead">{lead as React.ReactNode}</span> : null}
      <span className="surface-ledger-primary">{primary as React.ReactNode}</span>
      {cells != null ? <span>{cells as React.ReactNode}</span> : null}
      {trailing != null ? <span className="surface-ledger-trailing">{trailing as React.ReactNode}</span> : null}
      {children as React.ReactNode}
    </li>
  ),
}));

// jsdom doesn't have scrollIntoView
HTMLElement.prototype.scrollIntoView = vi.fn();

import { SetupCore } from "../SetupRoot";

/* ── Wire fixture helpers ── */

function githubProposal(overrides: Record<string, unknown> = {}) {
  return {
    id: "wprop_gh_01",
    sessionId: "psetup_test",
    providerId: "github",
    specSchema: "WatchSpec@1",
    spec: {
      schema: "WatchSpec@1",
      name: "PR health",
      intent: "Watch PRs",
      provider: { id: "github", transport: "cli" },
      subject: { kind: "pull_requests", scope: {} },
      trigger: { kind: "poll", everyMinutes: 35 },
      rules: [
        {
          condition: {
            schema: "WatchCondition@1",
            operator: "any",
            clauses: [
              { field: "checks", comparison: "equals", value: "failure" },
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

function makeAnswer(qid: string, text: string) {
  return {
    id: `pans_${qid}`,
    sessionId: "psetup_test",
    questionId: qid,
    answerSchema: "SetupAnswer@1",
    answer: { original: text, normalized: text },
    revision: 1,
    createdAt: "2026-08-31T10:01:00",
  };
}

function proposalsSession(proposals: Record<string, unknown>[] = [githubProposal()]) {
  return {
    id: "psetup_test",
    state: "active",
    stage: "proposals",
    draftSchema: "ProjectSetup@1",
    expiresAt: "2026-09-02T10:00:00+00:00",
    projectId: null,
    createdAt: "2026-08-31T10:00:00",
    updatedAt: "2026-08-31T10:00:00",
    answers: {
      outcome: makeAnswer("outcome", "Monitor PRs"),
      signals: makeAnswer("signals", "CI failures"),
    },
    proposals,
  };
}

/* ── Decoded responses (api module is mocked -- decoders are bypassed,
     so mock returns must be in the DECODED shape, not raw wire).
     Source shapes mined from test_provider_routes.py and decoded via
     the decoders in model.ts. ── */

const CONNECTED_STATUS = {
  state: "connected" as const,
  errorCode: null,
  errorDetail: null,
  display: { account: "testuser", recoveryHint: null },
};

const UNAUTH_STATUS = {
  state: "owner_action_required" as const,
  errorCode: "authentication_required",
  errorDetail: "gh auth login",
  display: { account: null, recoveryHint: "gh auth login" },
};

const DISCOVER_RESPONSE = {
  state: "ready",
  items: [
    { id: "acme/platform", name: "platform", owner: "acme", visibility: "public" },
    { id: "acme/backend", name: "backend", owner: "acme", visibility: "private" },
  ],
  cursor: null,
  errorCode: null,
};

const CLARIFY_SCOPED = {
  scopeState: "scoped",
  repositories: ["acme/platform"],
};

const TEST_PASSED = {
  proposalId: "wprop_gh_01",
  testState: "passed",
  result: {
    entityCount: 2,
    representativeEntities: [
      { number: 42, title: "Add routing", state: "open" },
      { number: 43, title: "Fix tests", state: "open" },
    ],
    observedAt: "2026-09-01T10:00:00Z",
    error: null,
    message: "Test passed -- 2 current matches",
  },
};

/* ── Tests ── */

// HS-168-04: auth flow moved to Connections; wizard asks scope + test only.
describe("Provider wizard mounted path (HS-168-04)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    try { sessionStorage.clear(); } catch { /* noop */ }
  });

  afterEach(() => {
    try { sessionStorage.clear(); } catch { /* noop */ }
  });

  async function renderAtProposals(proposals?: Record<string, unknown>[]) {
    sessionStorage.setItem("hs.project-setup.session-id", "psetup_test");
    mockGetSetup.mockResolvedValue(proposalsSession(proposals));

    const result = render(<SetupCore scope="" />);
    await waitFor(() => {
      expect(screen.getByTestId("setup-root")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByTestId("setup-suggestion-cards")).toBeInTheDocument();
    });
    return result;
  }

  it("selecting a GitHub proposal via card body enters the wizard (wizard mounts)", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));

    await renderAtProposals();

    await act(async () => {
      fireEvent.click(screen.getByTestId("setup-card-wprop_gh_01"));
    });

    await waitFor(() => {
      expect(screen.getByTestId("provider-wizard-flow")).toBeInTheDocument();
    });
  });

  it("selecting a GitHub proposal via Set up verb enters the wizard", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));

    await renderAtProposals();

    await act(async () => {
      fireEvent.click(screen.getByTestId("setup-card-setup-wprop_gh_01"));
    });

    await waitFor(() => {
      expect(screen.getByTestId("provider-wizard-flow")).toBeInTheDocument();
    });
  });

  it("connected state auto-discovers repos (no connection card)", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));

    await renderAtProposals();

    await act(async () => {
      fireEvent.click(screen.getByTestId("setup-card-wprop_gh_01"));
    });

    await waitFor(() => {
      expect(screen.getByTestId("provider-wizard-flow")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByTestId("provider-discovery")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByTestId("discovery-card-acme/platform")).toBeInTheDocument();
    });
  });

  it("full flow: discover -> scope -> test -> Use this Watch", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));
    mockClarifyScope.mockResolvedValue(CLARIFY_SCOPED);
    mockTestProposal.mockResolvedValue(TEST_PASSED);

    await renderAtProposals();

    await act(async () => {
      fireEvent.click(screen.getByTestId("setup-card-wprop_gh_01"));
    });

    await waitFor(() => {
      expect(screen.getByTestId("provider-wizard-flow")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByTestId("discovery-card-acme/platform")).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByTestId("discovery-card-acme/platform"));
    });

    await waitFor(() => {
      expect(mockClarifyScope).toHaveBeenCalledWith("psetup_test", "wprop_gh_01", "acme/platform");
    });

    // "Test this Watch" should be enabled (scoped)
    await waitFor(() => {
      const testBtn = screen.getByTestId("provider-test-btn");
      expect(testBtn).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByTestId("provider-test-btn"));
    });

    await waitFor(() => {
      expect(mockTestProposal).toHaveBeenCalledWith("psetup_test", "wprop_gh_01");
    });

    // After test passes, "Use this Watch" appears
    await waitFor(() => {
      expect(screen.getByTestId("provider-wizard-done")).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByTestId("provider-wizard-done"));
    });

    await waitFor(() => {
      expect(screen.queryByTestId("provider-wizard-flow")).not.toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByTestId("setup-suggestion-cards")).toBeInTheDocument();
    });
  });

  it("typed-repo fallback: Check repo validates and scopes", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));
    mockValidateGitHubRepo.mockResolvedValue({ valid: true, message: null });
    mockClarifyScope.mockResolvedValue(CLARIFY_SCOPED);

    await renderAtProposals();

    await act(async () => {
      fireEvent.click(screen.getByTestId("setup-card-wprop_gh_01"));
    });

    await waitFor(() => {
      expect(screen.getByTestId("provider-typed-repo")).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("owner/repo");
    await act(async () => {
      fireEvent.change(input, { target: { value: "acme/platform" } });
    });

    await act(async () => {
      fireEvent.click(screen.getByText("Check repo"));
    });

    await waitFor(() => {
      expect(mockValidateGitHubRepo).toHaveBeenCalledWith("acme/platform");
    });

    await waitFor(() => {
      expect(mockClarifyScope).toHaveBeenCalled();
    });
  });

  it("S-2: error_detail reaches rendered validation error", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));
    mockValidateGitHubRepo.mockResolvedValue({
      valid: false,
      message: "Repository not found or not accessible",
    });

    await renderAtProposals();

    await act(async () => {
      fireEvent.click(screen.getByTestId("setup-card-wprop_gh_01"));
    });

    await waitFor(() => {
      expect(screen.getByTestId("provider-typed-repo")).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("owner/repo");
    await act(async () => {
      fireEvent.change(input, { target: { value: "acme/nonexistent" } });
    });

    await act(async () => {
      fireEvent.click(screen.getByText("Check repo"));
    });

    await waitFor(() => {
      expect(screen.getByText("Repository not found or not accessible")).toBeInTheDocument();
    });
  });

  it("wizard owns the body: cards, tools, brief, answered rows unmount", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));
    mockDeselectProposal.mockResolvedValue(githubProposal({ state: "proposed" }));

    await renderAtProposals();

    // Verify pre-wizard: cards, tools-row, brief, answered rows present
    expect(screen.getByTestId("setup-suggestion-cards")).toBeInTheDocument();
    expect(screen.getByTestId("setup-brief")).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByTestId("setup-card-wprop_gh_01"));
    });

    await waitFor(() => {
      expect(screen.getByTestId("provider-wizard-flow")).toBeInTheDocument();
    });

    // HS-168-05: wizard owns the body -- these must be gone
    expect(screen.queryByTestId("setup-suggestion-cards")).not.toBeInTheDocument();
    expect(screen.queryByTestId("setup-tools-row")).not.toBeInTheDocument();
    expect(screen.queryByTestId("setup-brief")).not.toBeInTheDocument();
    expect(screen.queryByTestId("setup-answer-outcome")).not.toBeInTheDocument();
    expect(screen.queryByTestId("setup-answer-signals")).not.toBeInTheDocument();

    // Back returns everything
    await act(async () => {
      fireEvent.click(screen.getByTestId("provider-wizard-back"));
    });

    await waitFor(() => {
      expect(screen.getByTestId("setup-suggestion-cards")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("provider-wizard-flow")).not.toBeInTheDocument();
    expect(screen.getByTestId("setup-brief")).toBeInTheDocument();
  });

  it("never-active-before-test: unselected GitHub proposal is not 'tested'", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected", testState: null }));

    await renderAtProposals();

    const card = screen.getByTestId("setup-card-wprop_gh_01");
    expect(card.getAttribute("data-state")).not.toBe("tested");
    expect(card.getAttribute("data-state")).not.toBe("active");
  });
});
