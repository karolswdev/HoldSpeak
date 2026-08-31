// HS-159-05 -- setup controller: discriminated stage state mirroring the
// backend machine. Autosave = every accepted answer POSTs; resume = GET
// rehydration on mount (WEB-CR-009, INT-005).

import { useCallback, useEffect, useRef, useState } from "react";
import { readableError } from "../../../lib/api";
import { openSurface } from "../../../desk/shell";
import * as api from "./api";
import type {
  SetupAnswer,
  SetupProposal,
  SetupSession,
  SetupStage,
  TestResultResponse,
  FinalizeEnvelope,
  CadencePresetKey,
} from "./model";

/* ── Session storage key for resume (WEB-CR-009) ── */

const SESSION_KEY = "hs.project-setup.session-id";

function persistSessionId(id: string): void {
  try {
    sessionStorage.setItem(SESSION_KEY, id);
  } catch { /* storage can be unavailable */ }
}

function readPersistedSessionId(): string | null {
  try {
    return sessionStorage.getItem(SESSION_KEY);
  } catch {
    return null;
  }
}

function clearPersistedSessionId(): void {
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch { /* noop */ }
}

/* ── Controller state (discriminated by stage) ── */

export type ControllerState =
  | { kind: "loading" }
  | { kind: "outcome"; draft: string }
  | { kind: "signals"; draft: string; outcomeAnswer: SetupAnswer }
  | {
      kind: "proposals";
      proposals: SetupProposal[];
      outcomeAnswer: SetupAnswer;
      signalsAnswer: SetupAnswer;
      suggesting: boolean;
    }
  | {
      kind: "review";
      proposals: SetupProposal[];
      outcomeAnswer: SetupAnswer;
      signalsAnswer: SetupAnswer;
    }
  | { kind: "finalizing" }
  | { kind: "done"; projectId: string }
  | { kind: "abandoned" }
  | { kind: "error"; message: string; recoverable: boolean };

export type SetupController = ReturnType<typeof useSetupController>;

export function useSetupController() {
  const [state, setState] = useState<ControllerState>({ kind: "loading" });
  const [error, setError] = useState("");
  const sessionRef = useRef<string>("");
  const mountedRef = useRef(true);

  /* ── Lifecycle ── */

  useEffect(() => {
    mountedRef.current = true;
    void init();
    return () => {
      mountedRef.current = false;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const safe = (fn: () => void) => {
    if (mountedRef.current) fn();
  };

  /* ── Init: resume or start fresh ── */

  const init = useCallback(async () => {
    setState({ kind: "loading" });
    setError("");

    // Check for an in-progress session (WEB-CR-009)
    const existingId = readPersistedSessionId();
    if (existingId) {
      try {
        const session = await api.getSetup(existingId);
        if (session.state === "active") {
          sessionRef.current = session.id;
          safe(() => rehydrate(session));
          return;
        }
        // Session is not active (completed/abandoned/expired) -- start fresh
        clearPersistedSessionId();
      } catch {
        // Session not found or expired -- start fresh
        clearPersistedSessionId();
      }
    }

    // Start a new session
    try {
      const session = await api.startSetup();
      sessionRef.current = session.id;
      persistSessionId(session.id);
      safe(() => setState({ kind: "outcome", draft: "" }));
    } catch (reason) {
      safe(() =>
        setState({
          kind: "error",
          message: readableError(reason),
          recoverable: true,
        }),
      );
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Rehydrate from a resumed session ── */

  function rehydrate(session: SetupSession): void {
    const outcomeAnswer = session.answers.outcome ?? null;
    const signalsAnswer = session.answers.signals ?? null;

    switch (session.stage) {
      case "outcome":
        setState({
          kind: "outcome",
          draft: outcomeAnswer?.answer.normalized ?? "",
        });
        return;
      case "signals":
        if (!outcomeAnswer) {
          setState({ kind: "outcome", draft: "" });
          return;
        }
        setState({
          kind: "signals",
          draft: signalsAnswer?.answer.normalized ?? "",
          outcomeAnswer,
        });
        return;
      case "proposals":
      case "review": {
        if (!outcomeAnswer) {
          setState({ kind: "outcome", draft: "" });
          return;
        }
        if (!signalsAnswer) {
          setState({
            kind: "signals",
            draft: "",
            outcomeAnswer,
          });
          return;
        }
        const kind = session.stage === "review" ? "review" : "proposals";
        setState({
          kind,
          proposals: session.proposals,
          outcomeAnswer,
          signalsAnswer,
          ...(kind === "proposals" ? { suggesting: false } : {}),
        } as ControllerState);
        return;
      }
      default:
        setState({ kind: "outcome", draft: "" });
    }
  }

  /* ── Answer submission (autosave on accept) ── */

  const submitOutcome = useCallback(
    async (text: string) => {
      if (!sessionRef.current || !text.trim()) return;
      setError("");
      try {
        const answer = await api.submitAnswer(
          sessionRef.current,
          "outcome",
          text.trim(),
        );
        safe(() =>
          setState({
            kind: "signals",
            draft: "",
            outcomeAnswer: answer,
          }),
        );
      } catch (reason) {
        safe(() => setError(readableError(reason)));
      }
    },
    [], // eslint-disable-line react-hooks/exhaustive-deps
  );

  const submitSignals = useCallback(
    async (text: string) => {
      if (!sessionRef.current || state.kind !== "signals") return;
      setError("");
      try {
        const answer = await api.submitAnswer(
          sessionRef.current,
          "signals",
          text.trim(),
        );

        // After signals answered, trigger suggestion generation
        safe(() =>
          setState({
            kind: "proposals",
            proposals: [],
            outcomeAnswer: (state as { outcomeAnswer: SetupAnswer }).outcomeAnswer,
            signalsAnswer: answer,
            suggesting: true,
          }),
        );

        // Generate suggestions
        try {
          const proposals = await api.suggest(sessionRef.current);
          safe(() =>
            setState((prev) => {
              if (prev.kind !== "proposals") return prev;
              return { ...prev, proposals, suggesting: false };
            }),
          );
        } catch {
          // Suggest failed -- the Blank path is valid (INT-002)
          safe(() =>
            setState((prev) => {
              if (prev.kind !== "proposals") return prev;
              return { ...prev, suggesting: false };
            }),
          );
        }
      } catch (reason) {
        safe(() => setError(readableError(reason)));
      }
    },
    [state], // eslint-disable-line react-hooks/exhaustive-deps
  );

  /* ── Answer edit (re-submit with new text) ── */

  const editOutcome = useCallback(
    async (text: string) => {
      if (!sessionRef.current || !text.trim()) return;
      setError("");
      try {
        const answer = await api.submitAnswer(
          sessionRef.current,
          "outcome",
          text.trim(),
        );
        safe(() =>
          setState((prev) => {
            if (prev.kind === "signals") return { ...prev, outcomeAnswer: answer };
            if (prev.kind === "proposals") return { ...prev, outcomeAnswer: answer };
            if (prev.kind === "review") return { ...prev, outcomeAnswer: answer };
            return prev;
          }),
        );
      } catch (reason) {
        safe(() => setError(readableError(reason)));
      }
    },
    [], // eslint-disable-line react-hooks/exhaustive-deps
  );

  const editSignals = useCallback(
    async (text: string) => {
      if (!sessionRef.current) return;
      setError("");
      try {
        const answer = await api.submitAnswer(
          sessionRef.current,
          "signals",
          text.trim(),
        );
        safe(() =>
          setState((prev) => {
            if (prev.kind === "proposals") return { ...prev, signalsAnswer: answer };
            if (prev.kind === "review") return { ...prev, signalsAnswer: answer };
            return prev;
          }),
        );
      } catch (reason) {
        safe(() => setError(readableError(reason)));
      }
    },
    [], // eslint-disable-line react-hooks/exhaustive-deps
  );

  /* ── Proposal operations ── */

  const selectProp = useCallback(
    async (proposalId: string) => {
      if (!sessionRef.current) return;
      setError("");
      try {
        const updated = await api.selectProposal(
          sessionRef.current,
          proposalId,
        );
        safe(() =>
          setState((prev) => {
            if (prev.kind !== "proposals" && prev.kind !== "review") return prev;
            return {
              ...prev,
              proposals: prev.proposals.map((p) =>
                p.id === proposalId ? updated : p,
              ),
            };
          }),
        );
      } catch (reason) {
        safe(() => setError(readableError(reason)));
      }
    },
    [], // eslint-disable-line react-hooks/exhaustive-deps
  );

  const deselectProp = useCallback(
    async (proposalId: string) => {
      if (!sessionRef.current) return;
      setError("");
      try {
        const updated = await api.deselectProposal(
          sessionRef.current,
          proposalId,
        );
        safe(() =>
          setState((prev) => {
            if (prev.kind !== "proposals" && prev.kind !== "review") return prev;
            return {
              ...prev,
              proposals: prev.proposals.map((p) =>
                p.id === proposalId ? updated : p,
              ),
            };
          }),
        );
      } catch (reason) {
        safe(() => setError(readableError(reason)));
      }
    },
    [], // eslint-disable-line react-hooks/exhaustive-deps
  );

  const clarifyProp = useCallback(
    async (
      proposalId: string,
      patch: { cadence?: CadencePresetKey; action?: string; scope?: Record<string, unknown> },
    ) => {
      if (!sessionRef.current) return;
      setError("");
      try {
        const updated = await api.clarifyProposal(
          sessionRef.current,
          proposalId,
          patch,
        );
        safe(() =>
          setState((prev) => {
            if (prev.kind !== "proposals" && prev.kind !== "review") return prev;
            return {
              ...prev,
              proposals: prev.proposals.map((p) =>
                p.id === proposalId ? updated : p,
              ),
            };
          }),
        );
      } catch (reason) {
        safe(() => setError(readableError(reason)));
      }
    },
    [], // eslint-disable-line react-hooks/exhaustive-deps
  );

  const testProp = useCallback(
    async (proposalId: string): Promise<TestResultResponse | null> => {
      if (!sessionRef.current) return null;
      setError("");
      try {
        const result = await api.testProposal(
          sessionRef.current,
          proposalId,
        );
        // Update the proposal's test state in local state
        safe(() =>
          setState((prev) => {
            if (prev.kind !== "proposals" && prev.kind !== "review") return prev;
            return {
              ...prev,
              proposals: prev.proposals.map((p) =>
                p.id === proposalId
                  ? { ...p, testState: result.testState, testResult: result.result }
                  : p,
              ),
            };
          }),
        );
        return result;
      } catch (reason) {
        safe(() => setError(readableError(reason)));
        return null;
      }
    },
    [], // eslint-disable-line react-hooks/exhaustive-deps
  );

  /* ── Stage transitions ── */

  const advanceToReview = useCallback(() => {
    setState((prev) => {
      if (prev.kind !== "proposals") return prev;
      return {
        kind: "review",
        proposals: prev.proposals,
        outcomeAnswer: prev.outcomeAnswer,
        signalsAnswer: prev.signalsAnswer,
      };
    });
  }, []);

  const backToProposals = useCallback(() => {
    setState((prev) => {
      if (prev.kind !== "review") return prev;
      return {
        kind: "proposals",
        proposals: prev.proposals,
        outcomeAnswer: prev.outcomeAnswer,
        signalsAnswer: prev.signalsAnswer,
        suggesting: false,
      };
    });
  }, []);

  /* ── Finalize ── */

  const doFinalize = useCallback(async () => {
    if (!sessionRef.current) return;
    const prevState = state;
    setState({ kind: "finalizing" });
    setError("");
    try {
      const envelope = await api.finalize(sessionRef.current);
      clearPersistedSessionId();
      safe(() => setState({ kind: "done", projectId: envelope.projectId }));

      // WEB-CR-012: open the populated Room via open-project-memory
      openSurface("open-project-memory", `project:${envelope.projectId}`);
    } catch (reason) {
      safe(() => {
        setError(readableError(reason));
        // Recover to previous state (INT-006: recoverable draft)
        setState(prevState);
      });
    }
  }, [state]);

  /* ── Abandon ── */

  const doAbandon = useCallback(async () => {
    if (!sessionRef.current) return;
    setError("");
    try {
      await api.abandon(sessionRef.current);
      clearPersistedSessionId();
      safe(() => setState({ kind: "abandoned" }));
    } catch (reason) {
      safe(() => setError(readableError(reason)));
    }
  }, []);

  /* ── Draft management ── */

  const setDraft = useCallback((text: string) => {
    setState((prev) => {
      if (prev.kind === "outcome") return { ...prev, draft: text };
      if (prev.kind === "signals") return { ...prev, draft: text };
      return prev;
    });
  }, []);

  return {
    state,
    error,
    sessionId: sessionRef.current,

    // Draft
    setDraft,

    // Answer submission
    submitOutcome,
    submitSignals,
    editOutcome,
    editSignals,

    // Proposal operations
    selectProp,
    deselectProp,
    clarifyProp,
    testProp,

    // Stage transitions
    advanceToReview,
    backToProposals,

    // Terminal actions
    finalize: doFinalize,
    abandon: doAbandon,

    // Re-init
    retry: init,
  } as const;
}
