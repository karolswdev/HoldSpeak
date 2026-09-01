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

describe("Provider wizard mounted path", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    try { sessionStorage.clear(); } catch { /* noop */ }
  });

  afterEach(() => {
    try { sessionStorage.clear(); } catch { /* noop */ }
  });

  /** Helper: render SetupCore with a proposals session already loaded. */
  async function renderAtProposals(proposals?: Record<string, unknown>[]) {
    sessionStorage.setItem("hs.project-setup.session-id", "psetup_test");
    mockGetSetup.mockResolvedValue(proposalsSession(proposals));

    const result = render(<SetupCore scope="" />);

    // Wait for proposals stage
    await waitFor(() => {
      expect(screen.getByTestId("setup-root")).toBeInTheDocument();
    });

    // Wait for suggestion cards to appear
    await waitFor(() => {
      expect(screen.getByTestId("setup-suggestion-cards")).toBeInTheDocument();
    });

    return result;
  }

  it("selecting a GitHub proposal enters the provider wizard (wizard mounts)", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));

    await renderAtProposals();

    // Click the GitHub proposal card
    const card = screen.getByTestId("setup-card-wprop_gh_01");
    await act(async () => {
      fireEvent.click(card);
    });

    // Wizard should mount
    await waitFor(() => {
      expect(screen.getByTestId("provider-wizard-flow")).toBeInTheDocument();
    });

    // Connection status card should render
    await waitFor(() => {
      expect(screen.getByTestId("provider-status-card")).toBeInTheDocument();
    });
  });

  it("connected state shows discovery list with repos", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));

    await renderAtProposals();

    // Select the GitHub proposal
    await act(async () => {
      fireEvent.click(screen.getByTestId("setup-card-wprop_gh_01"));
    });

    // Wait for wizard and discovery
    await waitFor(() => {
      expect(screen.getByTestId("provider-wizard-flow")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByTestId("provider-discovery")).toBeInTheDocument();
    });

    // Discovery items should render
    await waitFor(() => {
      expect(screen.getByTestId("discovery-card-acme/platform")).toBeInTheDocument();
    });
  });

  it("full flow: connection -> scope -> test -> done", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));
    mockClarifyScope.mockResolvedValue(CLARIFY_SCOPED);
    mockTestProposal.mockResolvedValue(TEST_PASSED);

    await renderAtProposals();

    // Step 1: Select GitHub proposal -> enters wizard
    await act(async () => {
      fireEvent.click(screen.getByTestId("setup-card-wprop_gh_01"));
    });

    await waitFor(() => {
      expect(screen.getByTestId("provider-wizard-flow")).toBeInTheDocument();
    });

    // Step 2: Select a repo from discovery -> clarify-scope
    await waitFor(() => {
      expect(screen.getByTestId("discovery-card-acme/platform")).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByTestId("discovery-card-acme/platform"));
    });

    // Should call clarifyScope on the wire
    await waitFor(() => {
      expect(mockClarifyScope).toHaveBeenCalledWith("psetup_test", "wprop_gh_01", "acme/platform");
    });

    // Step 3: Scoped -> test button appears
    await waitFor(() => {
      expect(screen.getByTestId("provider-wizard-scoped")).toBeInTheDocument();
    });

    // Click test
    await act(async () => {
      fireEvent.click(screen.getByTestId("provider-test-btn"));
    });

    await waitFor(() => {
      expect(mockTestProposal).toHaveBeenCalledWith("psetup_test", "wprop_gh_01");
    });

    // Step 4: Done -> back to cards
    await act(async () => {
      fireEvent.click(screen.getByTestId("provider-wizard-done"));
    });

    // Wizard should unmount, suggestion cards should reappear
    await waitFor(() => {
      expect(screen.queryByTestId("provider-wizard-flow")).not.toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByTestId("setup-suggestion-cards")).toBeInTheDocument();
    });
  });

  it("typed-repo fallback works in mounted wizard", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));
    mockValidateGitHubRepo.mockResolvedValue({ valid: true, message: null });
    mockClarifyScope.mockResolvedValue(CLARIFY_SCOPED);

    await renderAtProposals();

    // Enter wizard
    await act(async () => {
      fireEvent.click(screen.getByTestId("setup-card-wprop_gh_01"));
    });

    await waitFor(() => {
      expect(screen.getByTestId("provider-typed-repo")).toBeInTheDocument();
    });

    // Type a repo
    const input = screen.getByPlaceholderText("owner/repo");
    await act(async () => {
      fireEvent.change(input, { target: { value: "acme/platform" } });
    });

    await act(async () => {
      fireEvent.click(screen.getByText("Use this repo"));
    });

    await waitFor(() => {
      expect(mockValidateGitHubRepo).toHaveBeenCalledWith("acme/platform");
    });

    await waitFor(() => {
      expect(mockClarifyScope).toHaveBeenCalled();
    });
  });

  it("SETFLOW-003: unauthenticated path renders recovery in the mounted flow", async () => {
    mockGetGitHubConnection.mockResolvedValue(UNAUTH_STATUS);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));

    await renderAtProposals();

    // Enter wizard
    await act(async () => {
      fireEvent.click(screen.getByTestId("setup-card-wprop_gh_01"));
    });

    // Wizard mounts with owner_action_required
    await waitFor(() => {
      expect(screen.getByTestId("provider-wizard-flow")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByTestId("provider-status-card")).toBeInTheDocument();
    });

    // Recovery card renders with command
    await waitFor(() => {
      expect(screen.getByTestId("provider-recovery")).toBeInTheDocument();
    });
    expect(screen.getByText("gh auth login")).toBeInTheDocument();

    // Recheck button present
    expect(screen.getByTestId("provider-recheck-btn")).toBeInTheDocument();

    // Discovery should NOT render when unauthed
    expect(screen.queryByTestId("provider-discovery")).not.toBeInTheDocument();
  });

  it("SETFLOW-003: recheck transitions from unauthed to connected in mounted flow", async () => {
    // First call returns unauthed, recheck returns connected
    mockGetGitHubConnection.mockResolvedValue(UNAUTH_STATUS);
    mockRecheckGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));

    await renderAtProposals();

    // Enter wizard
    await act(async () => {
      fireEvent.click(screen.getByTestId("setup-card-wprop_gh_01"));
    });

    // Wait for unauthed state
    await waitFor(() => {
      expect(screen.getByTestId("provider-recovery")).toBeInTheDocument();
    });

    // Click recheck
    await act(async () => {
      fireEvent.click(screen.getByTestId("provider-recheck-btn"));
    });

    // Should now show connected + discovery
    await waitFor(() => {
      const card = screen.getByTestId("provider-status-card");
      expect(card).toHaveAttribute("data-state", "connected");
    });
  });

  it("setup state preserved: suggestion cards return after wizard done", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected" }));

    await renderAtProposals();

    // Enter wizard
    await act(async () => {
      fireEvent.click(screen.getByTestId("setup-card-wprop_gh_01"));
    });

    await waitFor(() => {
      expect(screen.getByTestId("provider-wizard-flow")).toBeInTheDocument();
    });

    // Cards should be hidden
    expect(screen.queryByTestId("setup-suggestion-cards")).not.toBeInTheDocument();

    // Press done (back to suggestions)
    await act(async () => {
      fireEvent.click(screen.getByTestId("provider-wizard-done"));
    });

    // Cards should return
    await waitFor(() => {
      expect(screen.getByTestId("setup-suggestion-cards")).toBeInTheDocument();
    });

    // Wizard should be gone
    expect(screen.queryByTestId("provider-wizard-flow")).not.toBeInTheDocument();
  });

  it("never-active-before-test: GitHub proposal without test is not 'tested' in mounted flow", async () => {
    mockGetGitHubConnection.mockResolvedValue(CONNECTED_STATUS);
    mockDiscoverGitHub.mockResolvedValue(DISCOVER_RESPONSE);
    // Select returns selected but no test state
    mockSelectProposal.mockResolvedValue(githubProposal({ state: "selected", testState: null }));

    await renderAtProposals();

    // The card should not be in "tested" state before selection
    const card = screen.getByTestId("setup-card-wprop_gh_01");
    expect(card.getAttribute("data-state")).not.toBe("tested");
    expect(card.getAttribute("data-state")).not.toBe("active");
  });
});
