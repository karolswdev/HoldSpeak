// HS-166-04 -- controller tests for the Jira section: connection loading,
// add, recheck, select (auto-discover), scope update, reset.
// GitHub actions remain unchanged (tested in useSetupController.test.ts).

import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";

/* ── Mock api module (all routes) ── */
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
const mockGetJiraConnections = vi.fn();
const mockAddJiraConnection = vi.fn();
const mockRecheckJiraConnection = vi.fn();
const mockDiscoverJira = vi.fn();
const mockSearchJira = vi.fn();
const mockValidateJiraScope = vi.fn();
const mockClarifyJiraScope = vi.fn();

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
  getJiraConnections: (...args: unknown[]) => mockGetJiraConnections(...args),
  addJiraConnection: (...args: unknown[]) => mockAddJiraConnection(...args),
  recheckJiraConnection: (...args: unknown[]) => mockRecheckJiraConnection(...args),
  discoverJira: (...args: unknown[]) => mockDiscoverJira(...args),
  searchJira: (...args: unknown[]) => mockSearchJira(...args),
  validateJiraScope: (...args: unknown[]) => mockValidateJiraScope(...args),
  clarifyJiraScope: (...args: unknown[]) => mockClarifyJiraScope(...args),
}));

const mockOpenSurface = vi.fn();
vi.mock("../../../../desk/shell", () => ({
  openSurface: (...args: unknown[]) => mockOpenSurface(...args),
}));

import { useSetupController } from "../useSetupController";

/* ── Wire fixture data ── */

const JIRA_CONNECTIONS_RESPONSE = {
  connections: [
    {
      provider_id: "jira",
      connection_ref: "alpha.atlassian.net|user@example.com",
      state: "connected",
      account: { site: "alpha.atlassian.net", email: "user@example.com" },
      error_code: null,
      error_detail: null,
      recovery: null,
      checked_at: "2026-09-02T10:00:00+00:00",
      last_connected_at: "2026-09-02T10:00:00+00:00",
    },
  ],
  knownAccounts: [
    {
      site: "alpha.atlassian.net",
      email: "user@example.com",
      displayName: "Test User",
      authType: "oauth",
      ref: "alpha.atlassian.net|user@example.com",
      current: true,
    },
  ],
};

const JIRA_DISCOVERY_RESPONSE = {
  state: "ready",
  items: [{ id: "KAN", key: "KAN", name: "Kanban", type: "software" }],
  cursor: null,
  errorCode: null,
  errorDetail: null,
  connectionRef: "alpha.atlassian.net|user@example.com",
};

const JIRA_UPDATED_CONNECTION = {
  provider_id: "jira",
  connection_ref: "alpha.atlassian.net|user@example.com",
  state: "connected",
  account: { site: "alpha.atlassian.net", email: "user@example.com" },
  error_code: null,
  error_detail: null,
  recovery: null,
  checked_at: "2026-09-02T11:00:00+00:00",
  last_connected_at: "2026-09-02T11:00:00+00:00",
};

beforeEach(() => {
  vi.clearAllMocks();
  // Default: startSetup returns a fresh session
  mockStartSetup.mockResolvedValue({
    id: "psetup_jira_test",
    state: "active",
    stage: "outcome",
    draftSchema: "ProjectSetup@1",
    expiresAt: "2026-09-01T10:00:00+00:00",
    projectId: null,
    createdAt: "2026-08-31T10:00:00",
    updatedAt: "2026-08-31T10:00:00",
    answers: {},
    proposals: [],
  });
  // Session storage mock
  try { sessionStorage.clear(); } catch { /* noop */ }
});

describe("Jira controller actions", () => {
  it("loadJiraConnections calls api and sets state", async () => {
    mockGetJiraConnections.mockResolvedValue(JIRA_CONNECTIONS_RESPONSE);

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).not.toBe("loading"));

    await act(async () => {
      result.current.loadJiraConnections();
    });

    await waitFor(() => {
      expect(mockGetJiraConnections).toHaveBeenCalled();
      expect(result.current.jiraConnections).toHaveLength(1);
      expect(result.current.jiraConnections[0].connection_ref).toBe("alpha.atlassian.net|user@example.com");
      expect(result.current.jiraKnownAccounts).toHaveLength(1);
    });
  });

  it("addJiraConnection calls api and reloads connections", async () => {
    const newConn = {
      provider_id: "jira",
      connection_ref: "new.atlassian.net|new@example.com",
      state: "disconnected",
      account: { site: "new.atlassian.net", email: "new@example.com" },
      error_code: null,
      error_detail: null,
      recovery: null,
      checked_at: null,
      last_connected_at: null,
    };
    mockAddJiraConnection.mockResolvedValue(newConn);
    mockGetJiraConnections.mockResolvedValue({
      connections: [newConn],
      knownAccounts: [],
    });

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).not.toBe("loading"));

    await act(async () => {
      result.current.addJiraConnection("new.atlassian.net", "new@example.com");
    });

    await waitFor(() => {
      expect(mockAddJiraConnection).toHaveBeenCalledWith("new.atlassian.net", "new@example.com");
      expect(mockGetJiraConnections).toHaveBeenCalled();
    });
  });

  it("recheckJiraConnection updates the specific connection", async () => {
    mockGetJiraConnections.mockResolvedValue(JIRA_CONNECTIONS_RESPONSE);
    mockRecheckJiraConnection.mockResolvedValue(JIRA_UPDATED_CONNECTION);

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).not.toBe("loading"));

    // Load first
    await act(async () => { result.current.loadJiraConnections(); });
    await waitFor(() => expect(result.current.jiraConnections).toHaveLength(1));

    // Recheck
    await act(async () => {
      result.current.recheckJiraConnection("alpha.atlassian.net|user@example.com");
    });

    await waitFor(() => {
      expect(mockRecheckJiraConnection).toHaveBeenCalledWith("alpha.atlassian.net|user@example.com");
      expect(result.current.jiraConnections[0].checked_at).toBe("2026-09-02T11:00:00+00:00");
    });
  });

  it("selectJiraConnection sets ref and triggers project discovery", async () => {
    mockGetJiraConnections.mockResolvedValue(JIRA_CONNECTIONS_RESPONSE);
    mockDiscoverJira.mockResolvedValue(JIRA_DISCOVERY_RESPONSE);

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).not.toBe("loading"));

    await act(async () => { result.current.loadJiraConnections(); });
    await waitFor(() => expect(result.current.jiraConnections).toHaveLength(1));

    await act(async () => {
      result.current.selectJiraConnection("alpha.atlassian.net|user@example.com");
    });

    await waitFor(() => {
      expect(result.current.selectedJiraRef).toBe("alpha.atlassian.net|user@example.com");
      expect(mockDiscoverJira).toHaveBeenCalledWith(
        "alpha.atlassian.net|user@example.com",
        "projects",
      );
    });
  });

  it("updateJiraScope merges partial scope", async () => {
    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).not.toBe("loading"));

    act(() => {
      result.current.updateJiraScope({ projects: ["KAN"] });
    });
    expect(result.current.jiraScope.projects).toEqual(["KAN"]);
    expect(result.current.jiraScope.jql).toBe("");

    act(() => {
      result.current.updateJiraScope({ jql: "project = KAN" });
    });
    expect(result.current.jiraScope.projects).toEqual(["KAN"]);
    expect(result.current.jiraScope.jql).toBe("project = KAN");
  });

  it("resetJiraState clears all jira state", async () => {
    mockGetJiraConnections.mockResolvedValue(JIRA_CONNECTIONS_RESPONSE);

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).not.toBe("loading"));

    await act(async () => { result.current.loadJiraConnections(); });
    await waitFor(() => expect(result.current.jiraConnections).toHaveLength(1));

    act(() => { result.current.updateJiraScope({ projects: ["KAN"] }); });

    act(() => { result.current.resetJiraState(); });

    expect(result.current.jiraConnections).toEqual([]);
    expect(result.current.jiraKnownAccounts).toEqual([]);
    expect(result.current.selectedJiraRef).toBeNull();
    expect(result.current.jiraScope.projects).toEqual([]);
    expect(result.current.jiraScope.jql).toBe("");
    expect(result.current.jiraProjects).toBeNull();
  });

  it("GitHub actions remain unchanged after Jira additions", async () => {
    // The gitHub connection actions should still exist and work
    mockGetGitHubConnection.mockResolvedValue({
      state: "connected",
      errorCode: null,
      errorDetail: null,
      display: { account: "testuser", recoveryHint: null },
    });

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).not.toBe("loading"));

    await act(async () => { result.current.checkConnection(); });

    await waitFor(() => {
      expect(mockGetGitHubConnection).toHaveBeenCalled();
      expect(result.current.providerConnection).not.toBeNull();
    });
  });
});
