// HS-162-05 -- the Update controller: list, draft, edit, save, publish,
// regenerate, copy-markdown. Five verbs as separate honest state machines.
// Generator provenance visible on every draft.
// PHILO-9-03 (the Q0 ruling, the ratified copy-and-confirm canvas): Mark
// delivered on a published update -- one press mints ONE command_id and
// keeps it across its retries (Codex Astra r5). Copy does not change: the
// 2 s "Copied" feedback stays, and Mark delivered never depends on it (R4-3:
// no clipboard state is stored).

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../../../lib/api";
import { openAutomationResult as markAutomationResultRead } from "../../../desk/api";
import { plainFailure } from "../../../desk/surface/plainFailure";
import { forgetDraft, keepDraft, keepPlace, keptDraft, keptPlace } from "../../../desk/deskMemory";
import type { ProjectUpdate, UpdateLifecycle } from "./model";
import { bodyFromPlain, plainUpdateText } from "./model";
import * as updateApi from "./api";

export type UpdatePosture = "off" | "list" | "editor";
export type DraftRun = {
  phase: "idle" | "running" | "success" | "failure";
  startedAt?: number;
  elapsedSeconds?: number;
  reason?: string;
  /** The hub's plain words for why the draft was not made (P0). */
  detail?: string;
  generator?: "deterministic" | "model";
};

/** Betterment P1: the engine pass that improves the records draft. */
export type EnginePass =
  | { phase: "idle" }
  | { phase: "running"; jobId: string; startedAt: number }
  | { phase: "written"; seconds: number; model: string }
  | { phase: "ready"; jobId: string; seconds: number; model: string }
  | { phase: "failure"; reason: string; detail?: string; seconds: number };

/** How often the face asks the hub about a running pass. */
export const ENGINE_POLL_MS = 1500;

function draftCommandId(): string {
  const entropy = typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID().replace(/-/g, "").slice(0, 12)
    : Math.random().toString(36).slice(2, 14);
  return `draft-${Date.now()}-${entropy}`;
}

/* PHILO-13-07 (B2) — the Room's update place (`list` or `editor:<update>`)
   per project, and the unsaved body per update (never per project, so the
   text typed for one update never shows in another). Save clears it. */
const updatePlaceKey = (projectId: string) => `room/update/${projectId}`;
const updateDraftKey = (updateId: string) => `room/update-body/${updateId}`;

/** W6-F words: each update failure as one plain sentence (what failed ·
 *  what stayed). Keys are the old label grammar, kept for the hover title. */
const UPDATE_FAILURE_WORDS = {
  "UPDATES DID NOT LOAD": "Could not load the updates · Nothing changed",
  "UPDATE DID NOT OPEN": "Could not open the update · Nothing changed",
  "DRAFT NOT MADE": "Could not make the draft · Your words stay here",
  "NOT SAVED": "Could not save the update · Your words stay here",
  "NOT REVIEWED": "Could not mark the claim reviewed · Your words stay here",
  "NOT PUBLISHED": "Could not publish the update · It stays a draft on the hub",
  "NOT COPIED": "Could not copy it to the clipboard · Your words stay here",
} as const;

export function useUpdateController(
  projectId: string,
  onRoomRefresh: () => void,
  automationId?: string,
) {
  // ── Posture (off = normal Now, list = draft list, editor = single draft) ──
  const [posture, setPosture] = useState<UpdatePosture>("off");

  // ── List state ──
  const [updates, setUpdates] = useState<ProjectUpdate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // PHILO-13-04 (A3): a failure is plain words (never the hub's text) and
  // keeps the verb that failed, so the face can offer it again.
  const [retryFailed, setRetryFailed] = useState<(() => void) | null>(null);
  // W6-F words: the face says what failed and what stayed in a plain
  // sentence; the label-grammar reason (`NOT SAVED · HUB FAILED`) is the
  // hover title only. The verb beside it (Try again) is the next action.
  const [errorTitle, setErrorTitle] = useState("");
  const fail = (what: keyof typeof UPDATE_FAILURE_WORDS, reason: unknown, again?: () => void) => {
    setError(UPDATE_FAILURE_WORDS[what]);
    setErrorTitle(plainFailure(what, reason));
    setRetryFailed(() => again ?? null);
  };
  // PHILO-13-04 fix round (Astra counsel P1): Try again calls the LATEST
  // verb through this ref, so it reads the editor as it is NOW. A captured
  // render's `save` resent the old text and wrote it over newer words.
  const verbs = useRef<{ save: () => Promise<void>; publish: () => Promise<void> }>({
    save: async () => {},
    publish: async () => {},
  });
  // The editor text as it is now, for a save that answers after he typed on.
  const editBodyNow = useRef("");
  // The draft update the editor holds now (B2's draft key), for the handler.
  const currentId = useRef<string | null>(null);
  // Close stops the engine pass (declared below; reached through refs).
  const stopPollingRef = useRef<() => void>(() => {});
  const setEnginePassRef = useRef<(p: EnginePass) => void>(() => {});

  // ── Editor state ──
  const [current, setCurrent] = useState<ProjectUpdate | null>(null);
  const [editBody, setEditBody] = useState("");
  const [dirty, setDirty] = useState(false);

  // ── Verb busy states ──
  const [draftBusy, setDraftBusy] = useState(false);
  const [draftRun, setDraftRun] = useState<DraftRun>({ phase: "idle" });
  const [saveBusy, setSaveBusy] = useState(false);
  const [publishBusy, setPublishBusy] = useState(false);
  const [regenerateBusy, setRegenerateBusy] = useState(false);
  const [copyBusy, setCopyBusy] = useState(false);
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");

  // ── Mark delivered (the settled retry rule; Codex Astra canvases r1 F4, r2 F1) ──
  // One confirmation = one {update_id, command_id, delivered_to}, held PER
  // UPDATE. While it is pending or its result is unknown, THAT update's To
  // field is locked to the held payload, and the request always goes to the
  // HELD update_id -- never to whichever update is open. A new key is minted
  // only after the result is known: a row came back, or the hub named a
  // refusal. A lost answer keeps the update, the key and the payload; Retry
  // sends all three again, and the hub's replay returns the original row.
  // Opening another update neither takes over nor clears the lock, the
  // unknown result or the Retry: each update keeps its own.
  type Outcome = { kind: "none" } | { kind: "refused"; code: string } | { kind: "uncertain" };
  type Held = { updateId: string; key: string; to: string };
  const holds = useRef(new Map<string, Held>());
  const [toDrafts, setToDrafts] = useState<Record<string, string>>({});
  const [outcomes, setOutcomes] = useState<Record<string, Outcome>>({});
  const [busyIds, setBusyIds] = useState<Record<string, boolean>>({});
  const busyRef = useRef(new Set<string>());
  const [, setHoldTick] = useState(0);
  const openId = current?.id ?? "";
  const openHold = openId ? holds.current.get(openId) : undefined;
  const deliverTo = openHold ? openHold.to : toDrafts[openId] ?? "";
  const deliverBusy = !!busyIds[openId];
  const deliverOutcome: Outcome = outcomes[openId] ?? { kind: "none" };
  const setDeliverTo = useCallback((v: string) => {
    if (!openId || holds.current.has(openId)) return; // locked while held
    setToDrafts((d) => ({ ...d, [openId]: v }));
  }, [openId]);

  // ── PHILO-10-04: the open update's history, read again after a send
  // settles (story 01's one table). Only `deliveries` is replaced: the
  // editor's state stays. A read that gets no answer is named, never empty.
  const [deliveriesReadFailed, setDeliveriesReadFailed] = useState(false);
  const reloadDeliveries = useCallback(async () => {
    if (!projectId) return;
    try {
      const list = await updateApi.fetchUpdates(projectId);
      setUpdates(list);
      setCurrent((u) => {
        if (!u) return u;
        const fresh = list.find((x) => x.id === u.id);
        return fresh ? { ...u, deliveries: fresh.deliveries } : u;
      });
      setDeliveriesReadFailed(false);
    } catch {
      setDeliveriesReadFailed(true);
    }
  }, [projectId]);

  // ── Enter update posture (fetch list) ──
  const enterUpdates = useCallback(async () => {
    if (!projectId) return;
    // After a step aside the editor comes back as he left it (its text, its
    // failure), never a fresh list over unsaved words.
    if (posture === "off" && current) {
      setPosture("editor");
      keepPlace(updatePlaceKey(projectId), `editor:${current.id}`);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const list = await updateApi.fetchUpdates(projectId);
      setUpdates(list);
      setPosture("list");
      keepPlace(updatePlaceKey(projectId), "list");
    } catch (reason) {
      fail("UPDATES DID NOT LOAD", reason);
    } finally {
      setLoading(false);
    }
  }, [projectId, posture, current]);

  // ── Step aside (PHILO-14 A5b, Muad'Dib's ruling on Astra r2) ──
  // A proposal request shows the Room: the posture steps aside and NEVER
  // writes. The editor's update, its unsaved text (and the kept draft), its
  // failure and Try again stay as they are; the kept place is cleared so a
  // just-mounted Room does not restore the posture over the proposal.
  // `Draft update` brings the editor back as he left it.
  const stepAside = useCallback(() => {
    if (projectId) keepPlace(updatePlaceKey(projectId), "");
    setPosture("off");
  }, [projectId]);

  // ── Exit update posture ──
  const exitUpdates = useCallback(() => {
    stopPollingRef.current();
    setEnginePassRef.current({ phase: "idle" });
    if (projectId) keepPlace(updatePlaceKey(projectId), "");
    setPosture("off");
    setUpdates([]);
    setCurrent(null);
    setEditBody("");
    setDirty(false);
    setError("");
  }, [projectId]);

  // ── Open a specific update in the editor ──
  const openUpdate = useCallback((update: ProjectUpdate) => {
    setDeliveriesReadFailed(false);
    setCurrent(update);
    // An emptied body is kept as "" (its own state, never "no draft").
    const kept = update.lifecycle === "draft" ? keptDraft(updateDraftKey(update.id)) : null;
    const plain = plainUpdateText(update.bodyMd);
    setEditBody(kept ?? plain);
    setDirty(kept !== null && kept !== plain);
    setPosture("editor");
    setError("");
    if (projectId) keepPlace(updatePlaceKey(projectId), `editor:${update.id}`);
  }, [projectId]);

  // The Room's Update line is a direct doorway to the newest update. Keep
  // the list posture for an empty project, but open the newest record when
  // one exists so the verb does not add a second press.
  const openLatest = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError("");
    try {
      const list = await updateApi.fetchUpdates(projectId);
      setUpdates(list);
      if (list[0]) openUpdate(list[0]);
      else {
        setPosture("list");
        keepPlace(updatePlaceKey(projectId), "list");
      }
    } catch (reason) {
      fail("UPDATES DID NOT LOAD", reason);
    } finally {
      setLoading(false);
    }
  }, [projectId, openUpdate]);

  // Open the exact project update produced by an automation result.  The
  // artifact is marked read only after that update is fetched and confirmed
  // to belong to this project; both reads must succeed before the Room is
  // refreshed.  This keeps an owner-created draft out of the result path.
  const openAutomationResult = useCallback(async (result: {
    artifactId: string;
    updateId: string | null;
  }) => {
    if (!projectId || !automationId || !result.artifactId || !result.updateId) return;
    setLoading(true);
    setError("");
    try {
      const update = await updateApi.fetchUpdate(result.updateId);
      if (update.projectId !== projectId) {
        throw new Error("The automation result belongs to another project.");
      }
      await markAutomationResultRead(automationId, result.artifactId);
      openUpdate(update);
      onRoomRefresh();
    } catch (reason) {
      fail("UPDATE DID NOT OPEN", reason);
    } finally {
      setLoading(false);
    }
  }, [automationId, onRoomRefresh, openUpdate, projectId]);

  // ── Back to list from editor ──
  const backToList = useCallback(async () => {
    setCurrent(null);
    setEditBody("");
    setDirty(false);
    setError("");
    // Refresh the list
    if (!projectId) return;
    setLoading(true);
    try {
      const list = await updateApi.fetchUpdates(projectId);
      setUpdates(list);
    } catch (reason) {
      fail("UPDATES DID NOT LOAD", reason);
    } finally {
      setLoading(false);
    }
    setPosture("list");
    keepPlace(updatePlaceKey(projectId), "list");
  }, [projectId]);

  // ── Draft verb ──
  const draft = useCallback(async (generator: "deterministic" | "model"): Promise<ProjectUpdate | null> => {
    if (!projectId) return null;
    // A proposal request can step aside while an editor is dirty or holding a
    // failed save.  The next Draft update press returns to that same editor;
    // it does not mint a second draft or discard the owner's words.
    if (posture === "off" && current) {
      setPosture("editor");
      keepPlace(updatePlaceKey(projectId), `editor:${current.id}`);
      return null;
    }
    const startedAt = Date.now();
    setDraftRun({ phase: "running", startedAt, generator });
    setDraftBusy(true);
    setError("");
    try {
      const update = await updateApi.draftUpdate(projectId, generator, draftCommandId());
      setCurrent(update);
      setEditBody(plainUpdateText(update.bodyMd));
      setDirty(false);
      setPosture("editor");
      keepPlace(updatePlaceKey(projectId), `editor:${update.id}`);
      setDraftRun({
        phase: "success",
        startedAt,
        elapsedSeconds: Math.max(0, Math.round((Date.now() - startedAt) / 1000)),
        generator,
      });
      // P7: the first Write also creates the project's update automation;
      // refresh the Room so its When/With line appears in the same gesture.
      onRoomRefresh();
      // Refresh list in background
      updateApi.fetchUpdates(projectId).then(setUpdates).catch(() => {});
      return update;
    } catch (reason) {
      const payload = reason instanceof ApiError && reason.payload && typeof reason.payload === "object"
        ? reason.payload as Record<string, unknown>
        : null;
      setDraftRun({
        phase: "failure",
        startedAt,
        elapsedSeconds: Math.max(0, Math.round((Date.now() - startedAt) / 1000)),
        reason: String(payload?.reason || "did_not_answer"),
        detail: typeof payload?.detail === "string" ? payload.detail : undefined,
        generator,
      });
      fail("DRAFT NOT MADE", reason, () => void draft(generator));
      return null;
    } finally {
      setDraftBusy(false);
    }
  }, [current, onRoomRefresh, posture, projectId]);

  // ── Betterment P1: the engine pass (Write update) ──
  // The records draft opens at once; the engine improves it on the hub, off
  // its request loop. The face polls the job. Its draft replaces the records
  // draft (a new revision, with Undo) only while he has not edited; after an
  // edit it waits as "A better draft is ready · Use it". A failure keeps the
  // records draft and says why, with Try again.
  const [enginePass, setEnginePass] = useState<EnginePass>({ phase: "idle" });
  const dirtyNow = useRef(false);
  const pollTimer = useRef<number | null>(null);
  const passToken = useRef(0);
  const stopPolling = () => {
    passToken.current += 1;
    if (pollTimer.current !== null) window.clearTimeout(pollTimer.current);
    pollTimer.current = null;
  };
  useEffect(() => stopPolling, []);
  stopPollingRef.current = stopPolling;
  setEnginePassRef.current = setEnginePass;
  const seconds = (startedAt: number) => Math.max(0, Math.round((Date.now() - startedAt) / 1000));

  const takeEngineDraft = useCallback(async (jobId: string, startedAt: number, model: string, force: boolean) => {
    try {
      const update = await updateApi.applyEngineJob(jobId, force);
      if (currentId.current) forgetDraft(updateDraftKey(currentId.current));
      setCurrent(update);
      setEditBody(plainUpdateText(update.bodyMd));
      setDirty(false);
      if (projectId) keepPlace(updatePlaceKey(projectId), `editor:${update.id}`);
      setEnginePass({ phase: "written", seconds: seconds(startedAt), model: update.generatorModel || model });
      if (projectId) updateApi.fetchUpdates(projectId).then(setUpdates).catch(() => {});
    } catch (reason) {
      const code = reason instanceof ApiError && reason.payload && typeof reason.payload === "object"
        ? String((reason.payload as Record<string, unknown>).code ?? "") : "";
      if (code === "draft_changed" && !force) {
        setEnginePass({ phase: "ready", jobId, seconds: seconds(startedAt), model });
      } else {
        setEnginePass({ phase: "failure", reason: "did_not_answer", seconds: seconds(startedAt) });
      }
    }
  }, [projectId]);

  const startEnginePass = useCallback(async (updateId: string) => {
    stopPolling();
    const token = passToken.current;
    const startedAt = Date.now();
    let jobId: string;
    try {
      const projectAutomationId = automationId || (projectId ? `project-update-${projectId}` : undefined);
      jobId = (await updateApi.startEnginePass(updateId, projectAutomationId)).id;
    } catch {
      if (token === passToken.current) {
        setEnginePass({ phase: "failure", reason: "did_not_answer", seconds: seconds(startedAt) });
      }
      return;
    }
    if (token !== passToken.current) return;
    setEnginePass({ phase: "running", jobId, startedAt });
    const poll = async () => {
      if (token !== passToken.current) return;
      let job: updateApi.EngineJob;
      try {
        job = await updateApi.fetchEngineJob(jobId);
      } catch {
        pollTimer.current = window.setTimeout(() => void poll(), ENGINE_POLL_MS);
        return;
      }
      if (token !== passToken.current) return;
      if (job.state === "running") {
        pollTimer.current = window.setTimeout(() => void poll(), ENGINE_POLL_MS);
        return;
      }
      pollTimer.current = null;
      const model = job.generatorModel ?? "";
      if (job.state === "succeeded") {
        if (dirtyNow.current) setEnginePass({ phase: "ready", jobId, seconds: seconds(startedAt), model });
        else await takeEngineDraft(jobId, startedAt, model, false);
      } else if (job.state === "failed") {
        setEnginePass({
          phase: "failure", reason: job.reason || "did_not_answer",
          detail: job.detail ?? undefined, seconds: seconds(startedAt),
        });
      } else {
        setEnginePass({ phase: "idle" });
      }
    };
    pollTimer.current = window.setTimeout(() => void poll(), ENGINE_POLL_MS);
  }, [automationId, projectId, takeEngineDraft]);

  /** Write update: the records draft at once, then (with an engine) the pass. */
  const write = useCallback(async (withEngine: boolean) => {
    const stepBack = posture === "off" && current;
    if (!stepBack) {
      stopPolling();
      setEnginePass({ phase: "idle" });
    }
    const update = await draft("deterministic");
    if (update && withEngine) void startEnginePass(update.id);
  }, [current, draft, posture, startEnginePass]);

  const stopEnginePass = useCallback(async () => {
    if (enginePass.phase !== "running") return;
    const { jobId } = enginePass;
    stopPolling();
    setEnginePass({ phase: "idle" });
    await updateApi.stopEngineJob(jobId).catch(() => undefined);
  }, [enginePass]);

  const takeBetterDraft = useCallback(async () => {
    if (enginePass.phase !== "ready") return;
    await takeEngineDraft(enginePass.jobId, Date.now() - enginePass.seconds * 1000, enginePass.model, true);
  }, [enginePass, takeEngineDraft]);

  /** Undo: back to the draft from his records (a new revision). */
  const undoEngineDraft = useCallback(async () => {
    setEnginePass({ phase: "idle" });
    await draft("deterministic");
  }, [draft]);

  const retryEnginePass = useCallback(async () => {
    if (current?.lifecycle === "draft") await startEnginePass(current.id);
  }, [current, startEnginePass]);

  // ── Save verb (draft only) ──
  const save = useCallback(async () => {
    if (!current || current.lifecycle !== "draft") return;
    setSaveBusy(true);
    setError("");
    const sent = editBody;
    try {
      // Betterment P1: his plain text, saved over the stored body (a line he
      // did not change keeps its stored form).
      const saved = await updateApi.saveUpdate(current.id, bodyFromPlain(sent, current.bodyMd));
      setCurrent(saved);
      // Words typed while the save was in flight stay, and stay unsaved.
      if (editBodyNow.current === sent) {
        setEditBody(plainUpdateText(saved.bodyMd));
        setDirty(false);
        forgetDraft(updateDraftKey(current.id));
      }
    } catch (reason) {
      fail("NOT SAVED", reason, () => void verbs.current.save());
    } finally {
      setSaveBusy(false);
    }
  }, [current, editBody]);

  // ── PHILO-15 B64: the owner's review of one claim ──
  const [reviewBusy, setReviewBusy] = useState<string | null>(null);
  const [reviewReceipt, setReviewReceipt] = useState<string | null>(null);
  const reviewClaim = useCallback(async (spanId: string, acceptance: "accepted" | "rejected") => {
    if (!current || current.lifecycle !== "draft") return;
    setReviewBusy(spanId);
    setError("");
    try {
      const { update, reviewedAt } = await updateApi.reviewClaim(current.id, spanId, acceptance);
      setCurrent(update);
      const at = reviewedAt ? new Date(reviewedAt) : new Date();
      const pad = (n: number) => String(n).padStart(2, "0");
      setReviewReceipt(`Reviewed at ${pad(at.getHours())}:${pad(at.getMinutes())}`);
    } catch (reason) {
      fail("NOT REVIEWED", reason, () => void reviewClaim(spanId, acceptance));
    } finally {
      setReviewBusy(null);
    }
  }, [current]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Regenerate verb ──
  const regenerate = useCallback(async (generator: "deterministic" | "model") => {
    if (!current) return;
    setRegenerateBusy(true);
    setError("");
    try {
      const newDraft = await updateApi.regenerateUpdate(current.id, generator);
      forgetDraft(updateDraftKey(current.id));
      setCurrent(newDraft);
      setEditBody(plainUpdateText(newDraft.bodyMd));
      setDirty(false);
      if (projectId) keepPlace(updatePlaceKey(projectId), `editor:${newDraft.id}`);
    } catch (reason) {
      fail("DRAFT NOT MADE", reason, () => void regenerate(generator));
    } finally {
      setRegenerateBusy(false);
    }
  }, [current, projectId]);

  // ── Publish verb ──
  const publish = useCallback(async () => {
    if (!current || current.lifecycle !== "draft") return;
    setPublishBusy(true);
    setError("");
    try {
      const published = await updateApi.publishUpdate(current.id);
      forgetDraft(updateDraftKey(current.id));
      setCurrent(published);
      onRoomRefresh();
    } catch (reason) {
      // J4-07: the hub's own words (`injected failure`) never reach the face.
      fail("NOT PUBLISHED", reason, () => void verbs.current.publish());
    } finally {
      setPublishBusy(false);
    }
  }, [current, onRoomRefresh]);

  // ── Copy Markdown verb ──
  const copyMarkdown = useCallback(async () => {
    if (!current) return;
    setCopyBusy(true);
    setCopyState("idle");
    setError("");
    try {
      const md = await updateApi.fetchUpdateMarkdown(current.id);
      await navigator.clipboard.writeText(md);
      setCopyState("copied");
      setTimeout(() => setCopyState("idle"), 2000);
    } catch (reason) {
      setCopyState("failed");
      fail("NOT COPIED", reason, () => void copyMarkdown());
    } finally {
      setCopyBusy(false);
    }
  }, [current]);

  // ── Mark delivered verb ──
  const markDelivered = useCallback(async () => {
    if (!current || current.lifecycle !== "published") return;
    const uid = current.id;
    // A double-click is one press: the second click finds this update busy.
    if (busyRef.current.has(uid)) return;
    busyRef.current.add(uid);
    // A new confirmation only when this update holds none; a retry reuses
    // the held update, key AND payload.
    let held = holds.current.get(uid);
    if (!held) {
      held = { updateId: uid, key: crypto.randomUUID(), to: toDrafts[uid] ?? "" };
      holds.current.set(uid, held);
      setHoldTick((n) => n + 1);
    }
    const { updateId, key, to } = held;
    const setOutcome = (o: Outcome) => setOutcomes((m) => ({ ...m, [updateId]: o }));
    const release = () => { holds.current.delete(updateId); setHoldTick((n) => n + 1); };
    setBusyIds((b) => ({ ...b, [updateId]: true }));
    setOutcome({ kind: "none" });
    try {
      const row = await updateApi.markDelivered(updateId, to, key);
      release();
      const add = (u: ProjectUpdate) =>
        u.id === row.updateId && !u.deliveries.some((d) => d.id === row.id)
          ? { ...u, deliveries: [...u.deliveries, row] } : u;
      setCurrent((u) => (u ? add(u) : u));
      setUpdates((list) => list.map(add));
      setToDrafts((d) => ({ ...d, [updateId]: "" }));
      onRoomRefresh();
    } catch (reason) {
      const payload = reason instanceof ApiError ? (reason.payload as Record<string, unknown> | null) : null;
      const code =
        reason instanceof ApiError && reason.status >= 400 && reason.status < 500
          ? String(payload?.error_code ?? payload?.code ?? "")
          : "";
      if (code) {
        // Known result: a named refusal. The key is spent; the field unlocks
        // with his words still in it.
        release();
        setToDrafts((d) => ({ ...d, [updateId]: to }));
        setOutcome({ kind: "refused", code });
      } else {
        // Unknown result: keep the update, the key AND the payload for Retry.
        setOutcome({ kind: "uncertain" });
      }
    } finally {
      busyRef.current.delete(updateId);
      setBusyIds((b) => ({ ...b, [updateId]: false }));
    }
  }, [current, toDrafts, onRoomRefresh]);

  // ── Edit body handler ──
  const handleEditBody = useCallback((value: string) => {
    editBodyNow.current = value;
    setEditBody(value);
    setDirty(true);
    if (currentId.current) keepDraft(updateDraftKey(currentId.current), value);
  }, []);
  verbs.current = { save, publish };
  dirtyNow.current = dirty;
  currentId.current = current?.lifecycle === "draft" ? current.id : null;

  // PHILO-13-07 (B2): the Room comes back where it was — on the update list,
  // or in the editor on the same update with its unsaved text. Restore only
  // reads; it never saves or publishes.
  const restored = useRef("");
  useEffect(() => {
    if (!projectId || restored.current === projectId) return;
    restored.current = projectId;
    const place = keptPlace(updatePlaceKey(projectId));
    if (!place) return;
    let live = true;
    setLoading(true);
    void updateApi.fetchUpdates(projectId).then((list) => {
      if (!live) return;
      // A5b: the Room left the posture while the list loaded (a proposal
      // request reveals OPEN HERE): the kept place is gone, so stay out.
      if (keptPlace(updatePlaceKey(projectId)) !== place) return;
      setUpdates(list);
      const updateId = place.startsWith("editor:") ? place.slice("editor:".length) : "";
      const update = updateId ? list.find((u) => u.id === updateId) : undefined;
      if (update) openUpdate(update);
      else setPosture("list");
    }).catch(() => undefined).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [projectId, openUpdate]);
  editBodyNow.current = editBody;

  // ── Derived ──
  const isDraft = current?.lifecycle === "draft";
  const isPublished = current?.lifecycle === "published";
  const hasUpdates = updates.length > 0;
  const drafts = updates.filter((u) => u.lifecycle === "draft");
  const published = updates.filter((u) => u.lifecycle === "published");

  return {
    // Posture
    posture,
    enterUpdates,
    openLatest,
    openAutomationResult,
    exitUpdates,
    stepAside,
    openUpdate,
    backToList,

    // List
    updates,
    drafts,
    published,
    hasUpdates,
    loading,
    error,
    errorTitle,
    retryFailed,

    // Editor
    current,
    editBody,
    dirty,
    isDraft,
    isPublished,
    handleEditBody,

    // Verbs
    draft,
    write,
    enginePass,
    stopEnginePass,
    takeBetterDraft,
    undoEngineDraft,
    retryEnginePass,
    save,
    regenerate,
    publish,
    copyMarkdown,
    markDelivered,
    reviewClaim,
    reviewBusy,
    reviewReceipt,

    // Busy states
    draftBusy,
    draftRun,
    saveBusy,
    publishBusy,
    regenerateBusy,
    copyBusy,
    copyState,

    // Mark delivered (per update)
    deliverTo,
    setDeliverTo,
    deliverBusy,
    deliverOutcome,
    deliverLocked: !!openHold,

    // PHILO-10-04: the history read again after a send settles
    reloadDeliveries,
    deliveriesReadFailed,
  } as const;
}

export type UpdateController = ReturnType<typeof useUpdateController>;
