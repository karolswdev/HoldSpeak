// HS-200-11 — the Prepare posture's ONE controller: four states over one
// purpose.  `prepare` (the P3Prepare face) → `running` → `brief` (P3Brief)
// or `refused` (P3PrepareNoModel).  The purpose is persisted in
// sessionStorage the moment it changes, so a refusal, a reload or a trip
// to Settings never loses his words (AC5; ruling R2's escape hatch).
//
// Counsel-on-built (2026-09-17):
// - every run carries an ATTEMPT id; `Stop` aborts the fetch AND tells the
//   hub, which cancels the kernel operation and writes no draft (P1-4);
// - a refusal carries the hub's invoke receipt, so the face says SENT when
//   a request left (P0);
// - `Set up model` remembers Prepare as the return target even while it is
//   native-disabled; focus lands on it once the route is ready (P2 iii).

import { useCallback, useEffect, useRef, useState } from "react";
import { readableError } from "../../../lib/api";
import { onReturnToTask } from "../../../desk/returnToTask";
import * as briefApi from "./api";
import { clearPrepareDraft, readPrepareDraft, writePrepareDraft } from "./draft";
import type { Brief, BriefManifest, BriefRoute, PrepareRefusal } from "./model";

export type PreparePosture = "off" | "prepare" | "running" | "brief" | "refused";

function newAttemptId(): string {
  const rand = typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID().replace(/-/g, "")
    : `${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`;
  return `att_${rand}`.slice(0, 40);
}

export function usePrepareController(
  projectId: string,
  onRoomRefresh: () => void,
) {
  const [posture, setPosture] = useState<PreparePosture>("off");
  const [purpose, setPurposeState] = useState<string>("");
  const [route, setRoute] = useState<BriefRoute | null>(null);
  const [manifest, setManifest] = useState<BriefManifest | null>(null);
  const [brief, setBrief] = useState<Brief | null>(null);
  const [refusal, setRefusal] = useState<PrepareRefusal | null>(null);
  const [kept, setKept] = useState<Brief[]>([]);
  const [error, setError] = useState("");
  const [keepBusy, setKeepBusy] = useState(false);
  const [discardBusy, setDiscardBusy] = useState(false);
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");
  const [sourcesOpen, setSourcesOpen] = useState(false);
  /** The `STOPPED · REQUEST HAD LEFT · <host>` token after a Stop whose
   *  request had already gone out; cleared by the next run. */
  const [stopped, setStopped] = useState<{ host: string } | null>(null);
  /** A return-to-task landed while the route was refused: focus Prepare as
   *  soon as it is enabled (P2 iii). */
  const [focusPrepareWhenReady, setFocusPrepareWhenReady] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const attemptRef = useRef<string>("");

  // ── the persisted purpose ──
  const setPurpose = useCallback((next: string) => {
    setPurposeState(next);
    if (projectId) writePrepareDraft(projectId, next);
  }, [projectId]);

  useEffect(() => {
    if (!projectId) return;
    setPurposeState(readPrepareDraft(projectId));
  }, [projectId]);

  // ── the kept list (the way back from the Room, AC4) ──
  const loadKept = useCallback(async () => {
    if (!projectId) return;
    try {
      setKept(await briefApi.fetchBriefs(projectId, "kept"));
    } catch {
      // A Room without the brief wire still renders; the section is absent.
    }
  }, [projectId]);

  useEffect(() => { void loadKept(); }, [loadKept]);

  // ── the coverage BEFORE the run, and the route beside the verb ──
  const reloadCoverage = useCallback(async () => {
    if (!projectId) return;
    try {
      setManifest(await briefApi.fetchBriefManifest(projectId));
    } catch (reason) {
      setError(readableError(reason));
    }
  }, [projectId]);

  const reloadRoute = useCallback(async () => {
    if (!projectId) return;
    try {
      setRoute(await briefApi.fetchBriefRoute(projectId));
    } catch {
      setRoute(null);
    }
  }, [projectId]);

  // Return-to-task (HS-200-41): `Set up model` opens the Concierge; on its
  // Apply the route re-reads WITHOUT a reload, and a refused face that has
  // gained its route goes back to the prepare face with the purpose kept,
  // focus owed to Prepare.
  useEffect(
    () =>
      onReturnToTask(() => {
        void reloadRoute().then(() => {
          setPosture((current) => {
            if (current === "refused") {
              setRefusal(null);
              setFocusPrepareWhenReady(true);
              return "prepare";
            }
            return current;
          });
        });
      }),
    [reloadRoute],
  );

  // ── enter / exit ──
  const enterPrepare = useCallback((initialPurpose?: string) => {
    if (!projectId) return;
    if (initialPurpose && initialPurpose.trim()) setPurpose(initialPurpose.trim());
    setError("");
    setRefusal(null);
    setBrief(null);
    setStopped(null);
    setPosture("prepare");
    void reloadCoverage();
    void reloadRoute();
  }, [projectId, reloadCoverage, reloadRoute, setPurpose]);

  const exit = useCallback(() => {
    abortRef.current?.abort();
    setPosture("off");
    setRefusal(null);
    setError("");
    setSourcesOpen(false);
  }, []);

  // ── the run ──
  const prepare = useCallback(async () => {
    const words = purpose.trim();
    if (!projectId || !words) return;
    if (route && route.state !== "ready") return; // drawn refused; never sent
    const controller = new AbortController();
    const attemptId = newAttemptId();
    abortRef.current = controller;
    attemptRef.current = attemptId;
    setPosture("running");
    setError("");
    setRefusal(null);
    setStopped(null);
    try {
      const outcome = await briefApi.prepareBrief(projectId, words, { signal: controller.signal, attemptId });
      if (controller.signal.aborted) return;
      if (outcome.ok) {
        setBrief(outcome.brief);
        setPosture("brief");
        setCopyState("idle");
        setSourcesOpen(false);
      } else {
        setRefusal(outcome.refusal);
        // The hub's words for the purpose are the purpose; keep them.
        if (outcome.refusal.purpose) setPurpose(outcome.refusal.purpose);
        setPosture("refused");
      }
    } catch (reason) {
      if (controller.signal.aborted) return;
      setError(readableError(reason));
      setPosture("prepare");
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
    }
  }, [projectId, purpose, route, setPurpose]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    const attemptId = attemptRef.current;
    attemptRef.current = "";
    setPosture("prepare");
    if (!projectId || !attemptId) return;
    // The hub cancels the operation under this attempt and, if the run still
    // completes, writes no draft.  The face says whether the request had
    // already left (P1-4).
    void briefApi
      .stopBrief(projectId, attemptId)
      .then((res) => {
        const gone = res.disposition && !["not_running", "pending"].includes(res.disposition);
        if (gone) setStopped({ host: route?.host || "" });
      })
      .catch(() => { /* the abort alone already stopped the face */ });
  }, [projectId, route]);

  // ── the kept brief ──
  const keep = useCallback(async () => {
    if (!brief || brief.lifecycle === "kept") return;
    setKeepBusy(true);
    setError("");
    try {
      const next = await briefApi.keepBrief(brief.id);
      setBrief(next);
      if (projectId) clearPrepareDraft(projectId);
      await loadKept();
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setKeepBusy(false);
    }
  }, [brief, loadKept, projectId]);

  const discard = useCallback(async () => {
    if (!brief || brief.lifecycle !== "draft") return;
    setDiscardBusy(true);
    setError("");
    try {
      await briefApi.discardBrief(brief.id);
      setBrief(null);
      setPosture("prepare");
      setSourcesOpen(false);
      void reloadCoverage();
      void reloadRoute();
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setDiscardBusy(false);
    }
  }, [brief, reloadCoverage, reloadRoute]);

  const openBrief = useCallback(async (target: Brief) => {
    setError("");
    try {
      // Re-read by id: the hub re-verifies the manifest freeze on every read.
      setBrief(await briefApi.fetchBrief(target.id));
    } catch {
      setBrief(target);
    }
    setRefusal(null);
    setSourcesOpen(false);
    setCopyState("idle");
    setPosture("brief");
  }, []);

  const copy = useCallback(async () => {
    if (!brief) return;
    try {
      await navigator.clipboard.writeText(brief.bodyMd);
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }
  }, [brief]);

  const backToPrepare = useCallback(() => {
    setPosture("prepare");
    setSourcesOpen(false);
    void reloadCoverage();
    void reloadRoute();
  }, [reloadCoverage, reloadRoute]);

  const repairSource = useCallback(async (verb: string, watchIds: string[]) => {
    if (verb === "Resume") {
      const api = await import("../api");
      try { await Promise.all(watchIds.map(api.resumeWatch)); } catch { /* the row keeps its state */ }
      onRoomRefresh();
      await reloadCoverage();
      return;
    }
    if (verb === "Reconnect") {
      const { openSurfaceOr } = await import("../../../desk/shell");
      openSurfaceOr("configure-integrations", "/settings");
      return;
    }
    // Retry / Refresh: the Room re-reads its sources; the coverage follows.
    onRoomRefresh();
    await reloadCoverage();
  }, [onRoomRefresh, reloadCoverage]);

  return {
    posture,
    purpose,
    setPurpose,
    route,
    manifest,
    brief,
    refusal,
    kept,
    error,
    keepBusy,
    discardBusy,
    copyState,
    sourcesOpen,
    setSourcesOpen,
    stopped,
    focusPrepareWhenReady,
    setFocusPrepareWhenReady,
    enterPrepare,
    exit,
    prepare,
    stop,
    keep,
    discard,
    copy,
    openBrief,
    backToPrepare,
    reloadCoverage,
    reloadRoute,
    repairSource,
    loadKept,
  } as const;
}

export type PrepareController = ReturnType<typeof usePrepareController>;
