// HS-159-05 -- setup controller: discriminated stage state mirroring the
// backend machine. Autosave = every accepted answer POSTs; resume = GET
// rehydration on mount (WEB-CR-009, INT-005).

import { useCallback, useEffect, useRef, useState } from "react";
import { readableError } from "../../../lib/api";
import { openSurface } from "../../../desk/shell";
import { useDesk } from "../../../desk/store";
import * as api from "./api";
import { fetchConnections, type ConnectionTool, type ConnectionsResponse } from "../../../pages/cores/connections/api";
import type {
  SetupAnswer,
  SetupProposal,
  SetupSession,
  SetupStage,
  TestResultResponse,
  FinalizeEnvelope,
  CadencePresetKey,
  KnownScopes,
  ProviderConnectionStatus,
  DiscoveryResponse,
  ValidateRepoResponse,
  ClarifyScopeResponse,
  JiraConnection,
  JiraKnownAccount,
  JiraDiscoveryResponse,
  JiraSearchResult,
  JiraScope,
  JiraClarifyScopeResponse,
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
  const [knownScopes, setKnownScopes] = useState<KnownScopes>({ github: [], jira: [] });

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

    // HS-168-04: restore known scopes from the session
    if (session.knownScopes) {
      setKnownScopes(session.knownScopes);
    }

    // HS-167-02: restore Jira scope from the persisted answer.
    // The scope JSON rides the answer's `original` field (same shape as
    // all other answers -- the text param carries JSON.stringify(scope)).
    const jiraScopeAnswer = session.answers["jira_scope"] ?? null;
    if (jiraScopeAnswer?.answer?.original) {
      try {
        const scope = JSON.parse(jiraScopeAnswer.answer.original);
        if (scope && typeof scope === "object") {
          setJiraScopeRaw({
            connectionRef: String(scope.connectionRef ?? ""),
            projects: Array.isArray(scope.projects) ? scope.projects : [],
            issueTypes: Array.isArray(scope.issueTypes) ? scope.issueTypes : [],
            statusCategories: Array.isArray(scope.statusCategories) ? scope.statusCategories : [],
            jql: String(scope.jql ?? ""),
          });
        }
      } catch { /* malformed scope answer -- keep default */ }
    }

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

  /* ── Known scopes refresh (HS-168-04) ── */

  // After clarify-scope succeeds, refresh session to get updated known_scopes
  const refreshKnownScopes = useCallback(async () => {
    if (!sessionRef.current) return;
    try {
      const session = await api.getSetup(sessionRef.current);
      if (session.knownScopes) {
        safe(() => setKnownScopes(session.knownScopes!));
      }
    } catch {
      // best-effort
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Provider operations (HS-161-05) ── */

  const [providerConnection, setProviderConnection] = useState<ProviderConnectionStatus | null>(null);
  const [providerDiscovery, setProviderDiscovery] = useState<DiscoveryResponse | null>(null);
  const [providerChecking, setProviderChecking] = useState(false);
  const [providerDiscovering, setProviderDiscovering] = useState(false);
  const [providerScopeState, setProviderScopeState] = useState<"unscoped" | "scoped" | null>(null);

  const checkConnection = useCallback(async () => {
    safe(() => setProviderChecking(true));
    setError("");
    try {
      const status = await api.getGitHubConnection();
      safe(() => {
        setProviderConnection(status);
        setProviderChecking(false);
      });
    } catch (reason) {
      safe(() => {
        setError(readableError(reason));
        setProviderChecking(false);
      });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const recheckConnection = useCallback(async () => {
    safe(() => setProviderChecking(true));
    setError("");
    try {
      const status = await api.recheckGitHubConnection();
      safe(() => {
        setProviderConnection(status);
        setProviderChecking(false);
      });
    } catch (reason) {
      safe(() => {
        setError(readableError(reason));
        setProviderChecking(false);
      });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const discoverRepos = useCallback(async (query?: string, cursor?: string) => {
    safe(() => setProviderDiscovering(true));
    setError("");
    try {
      const response = await api.discoverGitHub(query, cursor);
      safe(() => {
        setProviderDiscovery((prev) => {
          if (cursor && prev) {
            // Append for pagination
            return { ...response, items: [...prev.items, ...response.items] };
          }
          return response;
        });
        setProviderDiscovering(false);
      });
    } catch (reason) {
      safe(() => {
        setError(readableError(reason));
        setProviderDiscovering(false);
      });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const validateRepo = useCallback(async (ownerRepo: string): Promise<ValidateRepoResponse | null> => {
    setError("");
    try {
      return await api.validateGitHubRepo(ownerRepo);
    } catch (reason) {
      safe(() => setError(readableError(reason)));
      return null;
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const clarifyProposalScope = useCallback(
    async (proposalId: string, repo?: string): Promise<ClarifyScopeResponse | null> => {
      if (!sessionRef.current) return null;
      setError("");
      try {
        const response = await api.clarifyScope(sessionRef.current, proposalId, repo);
        if (response.scopeState === "scoped") {
          safe(() => {
            setProviderScopeState("scoped");
            // Update proposal scope in local state
            setState((prev) => {
              if (prev.kind !== "proposals" && prev.kind !== "review") return prev;
              return {
                ...prev,
                proposals: prev.proposals.map((p) =>
                  p.id === proposalId
                    ? {
                        ...p,
                        spec: {
                          ...p.spec,
                          subject: {
                            ...p.spec.subject,
                            scope: { ...p.spec.subject.scope, repository: response.repositories[0] ?? "" },
                          },
                        },
                      }
                    : p,
                ),
              };
            });
          });
          // HS-168-04: refresh known_scopes after successful clarify
          void refreshKnownScopes();
        }
        return response;
      } catch (reason) {
        safe(() => setError(readableError(reason)));
        return null;
      }
    },
    [refreshKnownScopes], // eslint-disable-line react-hooks/exhaustive-deps
  );

  const resetProviderState = useCallback(() => {
    setProviderConnection(null);
    setProviderDiscovery(null);
    setProviderChecking(false);
    setProviderDiscovering(false);
    setProviderScopeState(null);
  }, []);

  /* ── Jira operations (HS-166-04) ── */

  const [jiraConnections, setJiraConnections] = useState<JiraConnection[]>([]);
  const [jiraKnownAccounts, setJiraKnownAccounts] = useState<JiraKnownAccount[]>([]);
  const [selectedJiraRef, setSelectedJiraRef] = useState<string | null>(null);
  const [jiraProjects, setJiraProjects] = useState<JiraDiscoveryResponse | null>(null);
  const [jiraIssueTypes, setJiraIssueTypes] = useState<JiraDiscoveryResponse | null>(null);
  const [jiraStatuses, setJiraStatuses] = useState<JiraDiscoveryResponse | null>(null);
  const [jiraScope, setJiraScopeRaw] = useState<JiraScope>({ connectionRef: "", projects: [], issueTypes: [], statusCategories: [], jql: "" });
  const jiraScopeRef = useRef<JiraScope>(jiraScope);
  jiraScopeRef.current = jiraScope;
  const [jiraPreview, setJiraPreview] = useState<JiraSearchResult | null>(null);
  const [jiraLoading, setJiraLoading] = useState(false);
  const [jiraDiscovering, setJiraDiscovering] = useState(false);
  const [jiraPreviewing, setJiraPreviewing] = useState(false);

  const loadJiraConnections = useCallback(async () => {
    safe(() => setJiraLoading(true));
    setError("");
    try {
      const response = await api.getJiraConnections();
      safe(() => {
        setJiraConnections(response.connections);
        setJiraKnownAccounts(response.knownAccounts);
        setJiraLoading(false);
      });
    } catch (reason) {
      safe(() => {
        setError(readableError(reason));
        setJiraLoading(false);
      });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const addJiraConnection = useCallback(async (site: string, email: string) => {
    safe(() => setJiraLoading(true));
    setError("");
    try {
      await api.addJiraConnection(site, email);
      const response = await api.getJiraConnections();
      safe(() => {
        setJiraConnections(response.connections);
        setJiraKnownAccounts(response.knownAccounts);
        setJiraLoading(false);
      });
    } catch (reason) {
      safe(() => {
        setError(readableError(reason));
        setJiraLoading(false);
      });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const recheckJiraConnection = useCallback(async (ref: string) => {
    setError("");
    try {
      const updated = await api.recheckJiraConnection(ref);
      safe(() => {
        setJiraConnections((prev) =>
          prev.map((c) => (c.connection_ref === ref ? updated : c)),
        );
      });
    } catch (reason) {
      safe(() => setError(readableError(reason)));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const selectJiraConnection = useCallback(async (ref: string) => {
    safe(() => {
      setSelectedJiraRef(ref);
      setJiraProjects(null);
      setJiraIssueTypes(null);
      setJiraStatuses(null);
      setJiraScopeRaw((prev) => ({ ...prev, connectionRef: ref, projects: [], issueTypes: [], statusCategories: [], jql: "" }));
      setJiraPreview(null);
    });
    safe(() => setJiraDiscovering(true));
    setError("");
    try {
      const response = await api.discoverJira(ref, "projects");
      safe(() => {
        setJiraProjects(response);
        setJiraDiscovering(false);
      });
    } catch (reason) {
      safe(() => {
        setError(readableError(reason));
        setJiraDiscovering(false);
      });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const discoverJiraProjects = useCallback(async (query?: string, cursor?: number) => {
    if (!selectedJiraRef) return;
    safe(() => setJiraDiscovering(true));
    setError("");
    try {
      const response = await api.discoverJira(selectedJiraRef, "projects", { query, cursor });
      safe(() => {
        setJiraProjects((prev) => {
          if (cursor != null && prev) {
            return { ...response, items: [...prev.items, ...response.items] };
          }
          return response;
        });
        setJiraDiscovering(false);
      });
    } catch (reason) {
      safe(() => {
        setError(readableError(reason));
        setJiraDiscovering(false);
      });
    }
  }, [selectedJiraRef]); // eslint-disable-line react-hooks/exhaustive-deps

  const discoverJiraTypes = useCallback(async (projectKey: string) => {
    if (!selectedJiraRef) return;
    safe(() => setJiraDiscovering(true));
    setError("");
    try {
      const response = await api.discoverJira(selectedJiraRef, "issue_types", { projectKey });
      safe(() => {
        setJiraIssueTypes(response);
        setJiraDiscovering(false);
      });
    } catch (reason) {
      safe(() => {
        setError(readableError(reason));
        setJiraDiscovering(false);
      });
    }
  }, [selectedJiraRef]); // eslint-disable-line react-hooks/exhaustive-deps

  const discoverJiraStatuses = useCallback(async (projectKey: string) => {
    if (!selectedJiraRef) return;
    safe(() => setJiraDiscovering(true));
    setError("");
    try {
      const response = await api.discoverJira(selectedJiraRef, "statuses", { projectKey });
      safe(() => {
        setJiraStatuses(response);
        setJiraDiscovering(false);
      });
    } catch (reason) {
      safe(() => {
        setError(readableError(reason));
        setJiraDiscovering(false);
      });
    }
  }, [selectedJiraRef]); // eslint-disable-line react-hooks/exhaustive-deps

  const validateJiraScopeAction = useCallback(async (projectKey: string) => {
    if (!selectedJiraRef) return null;
    setError("");
    try {
      return await api.validateJiraScope(selectedJiraRef, projectKey);
    } catch (reason) {
      safe(() => setError(readableError(reason)));
      return null;
    }
  }, [selectedJiraRef]); // eslint-disable-line react-hooks/exhaustive-deps

  const previewJiraPopulation = useCallback(async (jql: string, limit?: number) => {
    if (!selectedJiraRef) return;
    safe(() => setJiraPreviewing(true));
    setError("");
    try {
      const result = await api.searchJira(selectedJiraRef, jql, limit);
      safe(() => {
        setJiraPreview(result);
        setJiraPreviewing(false);
      });
    } catch (reason) {
      safe(() => {
        setError(readableError(reason));
        setJiraPreviewing(false);
      });
    }
  }, [selectedJiraRef]); // eslint-disable-line react-hooks/exhaustive-deps

  const clarifyJiraProposalScope = useCallback(
    async (proposalId: string): Promise<JiraClarifyScopeResponse | null> => {
      if (!sessionRef.current) return null;
      setError("");
      try {
        const response = await api.clarifyJiraScope(
          sessionRef.current,
          proposalId,
          jiraScope.connectionRef,
          jiraScope.projects,
          jiraScope.issueTypes,
        );
        if (response.scopeState === "scoped") {
          safe(() => {
            setState((prev) => {
              if (prev.kind !== "proposals" && prev.kind !== "review") return prev;
              return {
                ...prev,
                proposals: prev.proposals.map((p) =>
                  p.id === proposalId
                    ? {
                        ...p,
                        spec: {
                          ...p.spec,
                          subject: {
                            ...p.spec.subject,
                            scope: {
                              ...p.spec.subject.scope,
                              connection_ref: jiraScope.connectionRef,
                              projects: response.projects,
                              issue_types: jiraScope.issueTypes,
                            },
                          },
                        },
                      }
                    : p,
                ),
              };
            });
          });
          // HS-168-04: refresh known_scopes after successful clarify
          void refreshKnownScopes();
        }
        return response;
      } catch (reason) {
        safe(() => setError(readableError(reason)));
        return null;
      }
    },
    [jiraScope, refreshKnownScopes], // eslint-disable-line react-hooks/exhaustive-deps
  );

  const updateJiraScope = useCallback((partial: Partial<JiraScope>) => {
    // HS-167-02: the next scope is computed from the ref (never inside
    // the state updater -- updaters may run twice under StrictMode and
    // must stay pure); the persisted answer is best-effort so resume
    // restores the toggles.
    const next = { ...jiraScopeRef.current, ...partial };
    jiraScopeRef.current = next;
    setJiraScopeRaw(next);
    if (sessionRef.current) {
      void Promise.resolve()
        .then(() => api.submitAnswer(sessionRef.current, "jira_scope", JSON.stringify(next)))
        .catch(() => {});
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const resetJiraState = useCallback(() => {
    setJiraConnections([]);
    setJiraKnownAccounts([]);
    setSelectedJiraRef(null);
    setJiraProjects(null);
    setJiraIssueTypes(null);
    setJiraStatuses(null);
    setJiraScopeRaw({ connectionRef: "", projects: [], issueTypes: [], statusCategories: [], jql: "" });
    setJiraPreview(null);
    setJiraLoading(false);
    setJiraDiscovering(false);
    setJiraPreviewing(false);
  }, []);

  /* ── Connections read + re-read subscription (HS-168-04) ── */

  const [connectionTools, setConnectionTools] = useState<ConnectionTool[]>([]);
  const connectionToolsRef = useRef<ConnectionTool[]>([]);
  connectionToolsRef.current = connectionTools;

  /** Read GET /api/connections from the 02 wire (via the 03 worker's client). */
  const readConnections = useCallback(async () => {
    try {
      const resp = await fetchConnections();
      safe(() => setConnectionTools(resp.tools));
      return resp;
    } catch {
      return null;
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /** Re-suggest on the existing session.  The server is idempotent
   *  (HS-168-04): existing ids, states, scopes and test results are
   *  returned unchanged; only genuinely new candidates are added. */
  const reSuggest = useCallback(async () => {
    if (!sessionRef.current) return;
    try {
      const proposals = await api.suggest(sessionRef.current);
      safe(() =>
        setState((prev) => {
          if (prev.kind !== "proposals") return prev;
          return { ...prev, proposals, suggesting: false };
        }),
      );
    } catch {
      // Re-suggest failed -- keep current proposals
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /** Open Settings -> Connections in place (D2: the connect card verb). */
  const openConnectionsInPlace = useCallback(() => {
    useDesk.getState().openSurfaceWindow("configure-settings", "integrations");
  }, []);

  // Read connections on mount + when the session enters proposals stage
  useEffect(() => {
    void readConnections();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Extract known scopes from the session on rehydration
  useEffect(() => {
    if (state.kind === "proposals" || state.kind === "review") {
      // Re-read connections when entering proposals to get fresh state
      void readConnections();
    }
  }, [state.kind]); // eslint-disable-line react-hooks/exhaustive-deps

  // HS-168-04: Subscribe to desk store's windowsById for the settings window.
  // When "surface-settings" LEAVES windowsById, re-read connections and
  // re-suggest if a provider went from not-connected to connected.
  const SETTINGS_WINDOW_ID = "surface-settings";
  useEffect(() => {
    let prevHadSettings = SETTINGS_WINDOW_ID in useDesk.getState().windowsById;
    const unsub = useDesk.subscribe((deskState) => {
      const nowHasSettings = SETTINGS_WINDOW_ID in deskState.windowsById;
      // The settings window just left the map
      if (prevHadSettings && !nowHasSettings) {
        const oldTools = connectionToolsRef.current;
        void readConnections().then((resp) => {
          if (!resp || !mountedRef.current) return;
          // Check if any provider went from not-connected to connected
          const wasConnected = new Set(
            oldTools.filter((t) => t.state === "connected").map((t) => t.provider_id),
          );
          const nowConnected = resp.tools.filter((t) => t.state === "connected");
          const newlyConnected = nowConnected.some((t) => !wasConnected.has(t.provider_id));
          if (newlyConnected) {
            void reSuggest();
          }
        });
      }
      prevHadSettings = nowHasSettings;
    });
    return unsub;
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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

    // Provider operations (HS-161-05)
    providerConnection,
    providerDiscovery,
    providerChecking,
    providerDiscovering,
    providerScopeState,
    checkConnection,
    recheckConnection,
    discoverRepos,
    validateRepo,
    clarifyProposalScope,
    resetProviderState,

    // Jira operations (HS-166-04)
    jiraConnections,
    jiraKnownAccounts,
    selectedJiraRef,
    jiraProjects,
    jiraIssueTypes,
    jiraStatuses,
    jiraScope,
    jiraPreview,
    jiraLoading,
    jiraDiscovering,
    jiraPreviewing,
    loadJiraConnections,
    addJiraConnection,
    recheckJiraConnection,
    selectJiraConnection,
    discoverJiraProjects,
    discoverJiraTypes,
    discoverJiraStatuses,
    validateJiraScope: validateJiraScopeAction,
    previewJiraPopulation,
    clarifyJiraProposalScope,
    updateJiraScope,
    resetJiraState,

    // Connections + known scopes (HS-168-04)
    connectionTools,
    knownScopes,
    readConnections,
    openConnectionsInPlace,
    refreshKnownScopes,
  } as const;
}
