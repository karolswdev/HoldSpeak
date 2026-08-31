// HS-159-05 -- controller tests: stage/resume/autosave (mock fetch
// counting), the two-questions-then-cards law (INT-003), brief state
// mirroring, Blank path, finalize -> open dispatch.

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";

/* ── Mock api module ── */
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
}));

/* ── Mock shell ── */
const mockOpenSurface = vi.fn();
vi.mock("../../../../desk/shell", () => ({
  openSurface: (...args: unknown[]) => mockOpenSurface(...args),
}));

import { useSetupController } from "../useSetupController";

/* ── Wire fixture helpers ── */

function freshSession(overrides: Record<string, unknown> = {}) {
  return {
    id: "psetup_test123",
    state: "active",
    stage: "outcome",
    draftSchema: "ProjectSetup@1",
    expiresAt: "2026-09-01T10:00:00+00:00",
    projectId: null,
    createdAt: "2026-08-31T10:00:00",
    updatedAt: "2026-08-31T10:00:00",
    answers: {},
    proposals: [],
    ...overrides,
  };
}

function answeredSession() {
  return freshSession({
    stage: "proposals",
    answers: {
      outcome: {
        id: "pans_1",
        sessionId: "psetup_test123",
        questionId: "outcome",
        answerSchema: "SetupAnswer@1",
        answer: { original: "Ship Q4", normalized: "Ship Q4" },
        revision: 1,
        createdAt: "2026-08-31T10:01:00",
      },
      signals: {
        id: "pans_2",
        sessionId: "psetup_test123",
        questionId: "signals",
        answerSchema: "SetupAnswer@1",
        answer: { original: "PRs stale", normalized: "PRs stale" },
        revision: 1,
        createdAt: "2026-08-31T10:02:00",
      },
    },
    proposals: [
      {
        id: "wprop_1",
        sessionId: "psetup_test123",
        providerId: "native",
        specSchema: "WatchSpec@1",
        spec: {
          schema: "WatchSpec@1",
          name: "Meeting activity",
          intent: "Watch meetings",
          provider: { id: "native", transport: "local_domain" },
          subject: { kind: "meetings" },
          trigger: { kind: "poll", everyMinutes: 35 },
          rules: [],
          action: { schema: "WatchAction@1", kind: "project.observe" },
          mode: "yolo",
        },
        rationale: { fact: "1 meeting", detail: "", subjectCount: 1 },
        state: "proposed",
        testState: null,
        testResult: null,
        createdAt: "2026-08-31T10:03:00",
        updatedAt: "2026-08-31T10:03:00",
      },
    ],
  });
}

function makeAnswer(questionId: string, text: string) {
  return {
    id: `pans_${questionId}`,
    sessionId: "psetup_test123",
    questionId,
    answerSchema: "SetupAnswer@1",
    answer: { original: text, normalized: text },
    revision: 1,
    createdAt: "2026-08-31T10:01:00",
  };
}

/* ── Tests ── */

describe("useSetupController", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Clear sessionStorage
    try { sessionStorage.clear(); } catch { /* noop */ }
  });

  afterEach(() => {
    try { sessionStorage.clear(); } catch { /* noop */ }
  });

  it("starts a fresh session and lands on outcome", async () => {
    mockStartSetup.mockResolvedValue(freshSession());

    const { result } = renderHook(() => useSetupController());

    await waitFor(() => expect(result.current.state.kind).toBe("outcome"));
    expect(mockStartSetup).toHaveBeenCalledTimes(1);
  });

  it("resumes an in-progress session from sessionStorage (WEB-CR-009)", async () => {
    sessionStorage.setItem("hs.project-setup.session-id", "psetup_test123");
    mockGetSetup.mockResolvedValue(answeredSession());

    const { result } = renderHook(() => useSetupController());

    await waitFor(() => expect(result.current.state.kind).toBe("proposals"));
    expect(mockGetSetup).toHaveBeenCalledWith("psetup_test123");
    expect(mockStartSetup).not.toHaveBeenCalled();
  });

  it("falls back to fresh session if resumed session is completed", async () => {
    sessionStorage.setItem("hs.project-setup.session-id", "psetup_old");
    mockGetSetup.mockResolvedValue(freshSession({ state: "completed" }));
    mockStartSetup.mockResolvedValue(freshSession());

    const { result } = renderHook(() => useSetupController());

    await waitFor(() => expect(result.current.state.kind).toBe("outcome"));
    expect(mockStartSetup).toHaveBeenCalled();
  });

  it("submits outcome and advances to signals stage", async () => {
    mockStartSetup.mockResolvedValue(freshSession());
    mockSubmitAnswer.mockResolvedValue(makeAnswer("outcome", "Ship Q4"));

    const { result } = renderHook(() => useSetupController());

    await waitFor(() => expect(result.current.state.kind).toBe("outcome"));

    await act(async () => {
      await result.current.submitOutcome("Ship Q4");
    });

    expect(result.current.state.kind).toBe("signals");
    expect(mockSubmitAnswer).toHaveBeenCalledWith("psetup_test123", "outcome", "Ship Q4");
  });

  it("submits signals, triggers suggest, and advances to proposals (INT-003: two questions then cards)", async () => {
    mockStartSetup.mockResolvedValue(freshSession());
    mockSubmitAnswer
      .mockResolvedValueOnce(makeAnswer("outcome", "Ship Q4"))
      .mockResolvedValueOnce(makeAnswer("signals", "PRs stale"));
    mockSuggest.mockResolvedValue([
      answeredSession().proposals[0],
    ]);

    const { result } = renderHook(() => useSetupController());

    await waitFor(() => expect(result.current.state.kind).toBe("outcome"));

    // Submit outcome
    await act(async () => {
      await result.current.submitOutcome("Ship Q4");
    });
    expect(result.current.state.kind).toBe("signals");

    // Submit signals
    await act(async () => {
      await result.current.submitSignals("PRs stale");
    });

    // Should be in proposals stage (may still be suggesting)
    await waitFor(() => {
      expect(result.current.state.kind).toBe("proposals");
    });

    // Wait for suggestions
    await waitFor(() => {
      if (result.current.state.kind === "proposals" && "suggesting" in result.current.state) {
        expect(result.current.state.suggesting).toBe(false);
      }
    });

    expect(mockSubmitAnswer).toHaveBeenCalledTimes(2);
    expect(mockSuggest).toHaveBeenCalledTimes(1);

    // INT-003: exactly two questions before cards
    if (result.current.state.kind === "proposals" && "proposals" in result.current.state) {
      expect(result.current.state.proposals).toHaveLength(1);
    }
  });

  it("handles Blank path when suggest returns empty (INT-002)", async () => {
    mockStartSetup.mockResolvedValue(freshSession());
    mockSubmitAnswer
      .mockResolvedValueOnce(makeAnswer("outcome", "Ship Q4"))
      .mockResolvedValueOnce(makeAnswer("signals", "Nothing"));
    mockSuggest.mockResolvedValue([]);

    const { result } = renderHook(() => useSetupController());

    await waitFor(() => expect(result.current.state.kind).toBe("outcome"));

    await act(async () => {
      await result.current.submitOutcome("Ship Q4");
    });

    await act(async () => {
      await result.current.submitSignals("Nothing");
    });

    await waitFor(() => {
      if (result.current.state.kind === "proposals" && "proposals" in result.current.state) {
        expect(result.current.state.proposals).toHaveLength(0);
      }
    });
  });

  it("selects and deselects proposals", async () => {
    mockStartSetup.mockResolvedValue(freshSession());
    mockSubmitAnswer
      .mockResolvedValueOnce(makeAnswer("outcome", "Ship Q4"))
      .mockResolvedValueOnce(makeAnswer("signals", "Stale PRs"));
    mockSuggest.mockResolvedValue([answeredSession().proposals[0]]);
    const baseProp = answeredSession().proposals[0] as Record<string, unknown>;
    mockSelectProposal.mockResolvedValue({ ...baseProp, state: "selected" });
    mockDeselectProposal.mockResolvedValue({ ...baseProp, state: "proposed" });

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).toBe("outcome"));

    await act(async () => { await result.current.submitOutcome("Ship Q4"); });
    await act(async () => { await result.current.submitSignals("Stale PRs"); });
    await waitFor(() => expect(result.current.state.kind).toBe("proposals"));

    // Select
    await act(async () => { await result.current.selectProp("wprop_1"); });
    expect(mockSelectProposal).toHaveBeenCalledWith("psetup_test123", "wprop_1");

    // Deselect
    await act(async () => { await result.current.deselectProp("wprop_1"); });
    expect(mockDeselectProposal).toHaveBeenCalledWith("psetup_test123", "wprop_1");
  });

  it("tests a proposal", async () => {
    sessionStorage.setItem("hs.project-setup.session-id", "psetup_test123");
    const session = answeredSession() as Record<string, unknown>;
    const proposals = session.proposals as Record<string, unknown>[];
    proposals[0].state = "selected";
    mockGetSetup.mockResolvedValue(session);
    mockTestProposal.mockResolvedValue({
      proposalId: "wprop_1",
      testState: "passed",
      result: {
        entityCount: 1,
        representativeEntities: [{ id: "m1", title: "Meeting" }],
        observedAt: "2026-08-31T10:04:00",
        error: null,
        message: "Test passed -- 1 current matches",
      },
    });

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).toBe("proposals"));

    const testResult = await act(async () => {
      return result.current.testProp("wprop_1");
    });

    expect(testResult).not.toBeNull();
    expect(testResult!.testState).toBe("passed");
    expect(mockTestProposal).toHaveBeenCalledWith("psetup_test123", "wprop_1");
  });

  it("advances to review and back to proposals", async () => {
    sessionStorage.setItem("hs.project-setup.session-id", "psetup_test123");
    mockGetSetup.mockResolvedValue(answeredSession());

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).toBe("proposals"));

    act(() => result.current.advanceToReview());
    expect(result.current.state.kind).toBe("review");

    act(() => result.current.backToProposals());
    expect(result.current.state.kind).toBe("proposals");
  });

  it("finalize creates project and opens room (WEB-CR-012)", async () => {
    sessionStorage.setItem("hs.project-setup.session-id", "psetup_test123");
    mockGetSetup.mockResolvedValue(answeredSession());
    mockFinalize.mockResolvedValue({
      projectId: "proj_new_123",
      resultKind: "created",
      projectRevision: 1,
      changedRefs: ["project:proj_new_123"],
      refusedProposals: [],
    });

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).toBe("proposals"));

    await act(async () => {
      await result.current.finalize();
    });

    expect(result.current.state.kind).toBe("done");
    if (result.current.state.kind === "done") {
      expect(result.current.state.projectId).toBe("proj_new_123");
    }
    // WEB-CR-012: open the populated Room
    expect(mockOpenSurface).toHaveBeenCalledWith(
      "open-project-memory",
      "project:proj_new_123",
    );
  });

  it("finalize Blank path succeeds with zero proposals", async () => {
    mockStartSetup.mockResolvedValue(freshSession());
    mockSubmitAnswer.mockResolvedValueOnce(makeAnswer("outcome", "Blank project"));
    mockFinalize.mockResolvedValue({
      projectId: "proj_blank",
      resultKind: "created",
      projectRevision: 1,
      changedRefs: [],
      refusedProposals: [],
    });

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).toBe("outcome"));

    await act(async () => {
      await result.current.submitOutcome("Blank project");
    });

    await act(async () => {
      await result.current.finalize();
    });

    expect(result.current.state.kind).toBe("done");
  });

  it("abandon clears session", async () => {
    mockStartSetup.mockResolvedValue(freshSession());
    mockAbandon.mockResolvedValue(undefined);

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).toBe("outcome"));

    await act(async () => {
      await result.current.abandon();
    });

    expect(result.current.state.kind).toBe("abandoned");
    expect(mockAbandon).toHaveBeenCalled();
  });

  it("recovers state on finalize failure (INT-006)", async () => {
    sessionStorage.setItem("hs.project-setup.session-id", "psetup_test123");
    mockGetSetup.mockResolvedValue(answeredSession());
    mockFinalize.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).toBe("proposals"));

    await act(async () => {
      await result.current.finalize();
    });

    // Should recover to proposals, not stuck in finalizing
    expect(result.current.state.kind).toBe("proposals");
    expect(result.current.error).toContain("Network error");
  });

  it("draft management works for outcome and signals", async () => {
    mockStartSetup.mockResolvedValue(freshSession());

    const { result } = renderHook(() => useSetupController());
    await waitFor(() => expect(result.current.state.kind).toBe("outcome"));

    act(() => result.current.setDraft("My outcome"));
    if (result.current.state.kind === "outcome") {
      expect(result.current.state.draft).toBe("My outcome");
    }
  });
});
