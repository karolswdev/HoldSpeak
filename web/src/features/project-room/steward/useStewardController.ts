// HS-163-05 -- the Steward controller: run, poll, stop, history, policy.
// Mirrors the Update controller architecture: posture state machine,
// separate busy flags, polling on non-terminal states, cleanup on unmount.

import { useCallback, useEffect, useRef, useState } from "react";
import { readableError } from "../../../lib/api";
import type { StewardRun, StewardStep, StewardPolicy, StewardWatch } from "./model";
import { isTerminal, isActive } from "./model";
import * as stewardApi from "./api";

export type StewardPosture = "off" | "list" | "detail" | "policy";

const POLL_INTERVAL_MS = 2000;

export function useStewardController(
  projectId: string,
  onRoomRefresh: () => void,
) {
  // ── Posture ──
  const [posture, setPosture] = useState<StewardPosture>("off");

  // ── List state ──
  const [runs, setRuns] = useState<StewardRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ── Detail state (single run view) ──
  const [currentRun, setCurrentRun] = useState<StewardRun | null>(null);
  const [currentSteps, setCurrentSteps] = useState<StewardStep[]>([]);

  // ── Policy state ──
  const [policy, setPolicy] = useState<StewardPolicy | null>(null);
  const [policyDraft, setPolicyDraft] = useState<{
    eligible_effect_kinds: string[];
    max_retries: number;
    max_actions_per_run: number;
    cooldown_seconds: number;
    enabled: boolean;
    unattended_enabled: boolean;
    evaluation_cadence_minutes?: number;  // HS-167-02
    nudge_template?: string | null;  // HS-173-04
  } | null>(null);
  const [policyError, setPolicyError] = useState("");

  // ── HS-164-05: project watches (for grant text + circuit) ──
  const [watches, setWatches] = useState<StewardWatch[]>([]);

  // ── Verb busy states ──
  const [runBusy, setRunBusy] = useState(false);
  const [stopBusy, setStopBusy] = useState(false);
  const [policyBusy, setPolicyBusy] = useState(false);

  // ── STW-002 refusal reason ──
  const [runDisabledReason, setRunDisabledReason] = useState("");

  // ── Polling ──
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const mountedRef = useRef(true);

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, []);

  // ── Poll a run until terminal ──
  const startPolling = useCallback(
    (runId: string) => {
      // Clear any existing poll
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }

      const doPoll = async () => {
        if (!mountedRef.current) return;
        try {
          const { run, steps } = await stewardApi.getRun(runId);
          if (!mountedRef.current) return;
          setCurrentRun(run);
          setCurrentSteps(steps);

          if (isTerminal(run.state)) {
            if (pollRef.current) {
              clearInterval(pollRef.current);
              pollRef.current = null;
            }
            // Refresh history and room on completion
            stewardApi.listRuns(projectId).then((r) => {
              if (mountedRef.current) setRuns(r);
            }).catch(() => {});
            setRunDisabledReason("");
            onRoomRefresh();
          }
        } catch {
          // Polling errors are transient; keep trying
        }
      };

      // Initial fetch
      void doPoll();
      pollRef.current = setInterval(doPoll, POLL_INTERVAL_MS);
    },
    [projectId, onRoomRefresh],
  );

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  // ── Enter steward posture (fetch run list) ──
  const enterSteward = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError("");
    try {
      const list = await stewardApi.listRuns(projectId);
      setRuns(list);
      setPosture("list");
      // Check for active run
      const active = list.find((r) => isActive(r.state));
      if (active) {
        setRunDisabledReason("A run is in progress");
      } else {
        setRunDisabledReason("");
      }
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  // ── Exit steward posture ──
  const exitSteward = useCallback(() => {
    setPosture("off");
    setRuns([]);
    setCurrentRun(null);
    setCurrentSteps([]);
    setError("");
    setRunDisabledReason("");
    stopPolling();
  }, [stopPolling]);

  // ── Run once ──
  const runOnce = useCallback(async () => {
    if (!projectId) return;
    setRunBusy(true);
    setError("");
    try {
      const result = await stewardApi.startRun(projectId);
      if (!result.success) {
        if (result.code === "active_run_exists") {
          setRunDisabledReason("A run is in progress");
        } else if (result.code === "steward_disabled") {
          setRunDisabledReason("The steward is disabled in policy");
        } else if (result.code === "cooldown_active") {
          setRunDisabledReason("Cooling down after the last run");
        } else {
          setError(result.message ?? "Failed to start run");
        }
        return;
      }
      if (result.runId) {
        setRunDisabledReason("A run is in progress");
        setPosture("detail");
        startPolling(result.runId);
      }
    } catch (reason) {
      // Check for 409 active_run_exists
      const msg = readableError(reason);
      if (msg.includes("active") || msg.includes("409")) {
        setRunDisabledReason("A run is in progress");
      } else {
        setError(msg);
      }
    } finally {
      setRunBusy(false);
    }
  }, [projectId, startPolling]);

  // ── Open a run detail ──
  const openRun = useCallback(
    (run: StewardRun) => {
      setCurrentRun(run);
      setCurrentSteps([]);
      setPosture("detail");
      setError("");

      // If non-terminal, poll; otherwise just fetch once
      if (isTerminal(run.state)) {
        void stewardApi.getRun(run.id).then(({ run: r, steps }) => {
          if (mountedRef.current) {
            setCurrentRun(r);
            setCurrentSteps(steps);
          }
        }).catch(() => {});
      } else {
        startPolling(run.id);
      }
    },
    [startPolling],
  );

  // ── Back to list ──
  const backToList = useCallback(async () => {
    setCurrentRun(null);
    setCurrentSteps([]);
    setError("");
    stopPolling();
    if (!projectId) return;
    setLoading(true);
    try {
      const list = await stewardApi.listRuns(projectId);
      setRuns(list);
      const active = list.find((r) => isActive(r.state));
      setRunDisabledReason(active ? "A run is in progress" : "");
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setLoading(false);
    }
    setPosture("list");
  }, [projectId, stopPolling]);

  // ── Stop ──
  const stopRun = useCallback(async () => {
    if (!currentRun) return;
    setStopBusy(true);
    setError("");
    try {
      await stewardApi.stopRun(currentRun.id);
      // The poll will pick up the stopping -> interrupted transition
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setStopBusy(false);
    }
  }, [currentRun]);

  // ── Policy: enter ──
  const enterPolicy = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setPolicyError("");
    try {
      const [p, w] = await Promise.all([
        stewardApi.getPolicy(projectId),
        stewardApi.listProjectWatches(projectId),
      ]);
      setPolicy(p);
      setWatches(w);
      // HS-167-02: cadence lives on the watch, shown alongside the policy.
      const watchCadence = w.length > 0 ? w[0].evaluationCadenceMinutes : 60;
      if (p) {
        setPolicyDraft({
          eligible_effect_kinds: [...p.eligibleEffectKinds],
          max_retries: p.maxRetries,
          max_actions_per_run: p.maxActionsPerRun,
          cooldown_seconds: p.cooldownSeconds,
          enabled: p.enabled,
          unattended_enabled: p.unattendedEnabled,
          evaluation_cadence_minutes: watchCadence,
          nudge_template: p.nudgeTemplate,
        });
      } else {
        setPolicyDraft({
          eligible_effect_kinds: [],
          max_retries: 3,
          max_actions_per_run: 10,
          cooldown_seconds: 0,
          enabled: true,
          unattended_enabled: false,
          evaluation_cadence_minutes: watchCadence,
          nudge_template: null,
        });
      }
      setPosture("policy");
    } catch (reason) {
      setPolicyError(readableError(reason));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  // ── Policy: save ──
  const savePolicy = useCallback(async () => {
    if (!projectId || !policyDraft) return;
    setPolicyBusy(true);
    setPolicyError("");
    try {
      const result = await stewardApi.putPolicy(projectId, policyDraft);
      if (!result.success) {
        setPolicyError(result.error ?? "Validation failed");
        return;
      }
      setPolicy(result.policy);
      setPolicyDraft({
        eligible_effect_kinds: [...result.policy.eligibleEffectKinds],
        max_retries: result.policy.maxRetries,
        max_actions_per_run: result.policy.maxActionsPerRun,
        cooldown_seconds: result.policy.cooldownSeconds,
        enabled: result.policy.enabled,
        unattended_enabled: result.policy.unattendedEnabled,
        nudge_template: result.policy.nudgeTemplate,
      });
    } catch (reason) {
      setPolicyError(readableError(reason));
    } finally {
      setPolicyBusy(false);
    }
  }, [projectId, policyDraft]);

  // ── Policy: update draft fields ──
  const updatePolicyDraft = useCallback(
    (field: string, value: unknown) => {
      setPolicyDraft((prev) => (prev ? { ...prev, [field]: value } : prev));
      setPolicyError("");
    },
    [],
  );

  // ── Policy: toggle effect kind ──
  const toggleEffectKind = useCallback(
    (kind: string) => {
      setPolicyDraft((prev) => {
        if (!prev) return prev;
        const kinds = prev.eligible_effect_kinds.includes(kind)
          ? prev.eligible_effect_kinds.filter((k) => k !== kind)
          : [...prev.eligible_effect_kinds, kind];
        return { ...prev, eligible_effect_kinds: kinds };
      });
      setPolicyError("");
    },
    [],
  );

  // ── Derived ──
  const hasActiveRun = runs.some((r) => isActive(r.state));
  const canRun = !hasActiveRun && !runBusy;
  const canStop =
    currentRun != null &&
    (currentRun.state === "running" || currentRun.state === "queued") &&
    !stopBusy;

  return {
    // Posture
    posture,
    enterSteward,
    exitSteward,
    backToList,
    enterPolicy,

    // List
    runs,
    loading,
    error,

    // Detail
    currentRun,
    currentSteps,
    openRun,

    // Run
    runOnce,
    runBusy,
    canRun,
    runDisabledReason,

    // Stop
    stopRun,
    stopBusy,
    canStop,

    // Policy
    policy,
    policyDraft,
    policyError,
    policyBusy,
    savePolicy,
    updatePolicyDraft,
    toggleEffectKind,

    // HS-164-05: watches (for grant text + circuit rendering)
    watches,
  } as const;
}

export type StewardController = ReturnType<typeof useStewardController>;
