// HS-162-05 -- the Update controller: list, draft, edit, save, publish,
// regenerate, copy-markdown. Five verbs as separate honest state machines.
// Generator provenance visible on every draft.
// PHILO-9-03 (the Q0 ruling, the ratified copy-and-confirm canvas): Mark
// delivered on a published update -- one press mints ONE command_id and
// keeps it across its retries (Codex Astra r5). Copy does not change: the
// 2 s "Copied" feedback stays, and Mark delivered never depends on it (R4-3:
// no clipboard state is stored).

import { useCallback, useRef, useState } from "react";
import { ApiError, readableError } from "../../../lib/api";
import type { ProjectUpdate, UpdateLifecycle } from "./model";
import * as updateApi from "./api";

export type UpdatePosture = "off" | "list" | "editor";

export function useUpdateController(
  projectId: string,
  onRoomRefresh: () => void,
) {
  // ── Posture (off = normal Now, list = draft list, editor = single draft) ──
  const [posture, setPosture] = useState<UpdatePosture>("off");

  // ── List state ──
  const [updates, setUpdates] = useState<ProjectUpdate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ── Editor state ──
  const [current, setCurrent] = useState<ProjectUpdate | null>(null);
  const [editBody, setEditBody] = useState("");
  const [dirty, setDirty] = useState(false);

  // ── Verb busy states ──
  const [draftBusy, setDraftBusy] = useState(false);
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

  // ── Enter update posture (fetch list) ──
  const enterUpdates = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError("");
    try {
      const list = await updateApi.fetchUpdates(projectId);
      setUpdates(list);
      setPosture("list");
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  // ── Exit update posture ──
  const exitUpdates = useCallback(() => {
    setPosture("off");
    setUpdates([]);
    setCurrent(null);
    setEditBody("");
    setDirty(false);
    setError("");
  }, []);

  // ── Open a specific update in the editor ──
  const openUpdate = useCallback((update: ProjectUpdate) => {
    setCurrent(update);
    setEditBody(update.bodyMd);
    setDirty(false);
    setPosture("editor");
    setError("");
  }, []);

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
      setError(readableError(reason));
    } finally {
      setLoading(false);
    }
    setPosture("list");
  }, [projectId]);

  // ── Draft verb ──
  const draft = useCallback(async (generator: "deterministic" | "model") => {
    if (!projectId) return;
    setDraftBusy(true);
    setError("");
    try {
      const update = await updateApi.draftUpdate(projectId, generator);
      setCurrent(update);
      setEditBody(update.bodyMd);
      setDirty(false);
      setPosture("editor");
      // Refresh list in background
      updateApi.fetchUpdates(projectId).then(setUpdates).catch(() => {});
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setDraftBusy(false);
    }
  }, [projectId]);

  // ── Save verb (draft only) ──
  const save = useCallback(async () => {
    if (!current || current.lifecycle !== "draft") return;
    setSaveBusy(true);
    setError("");
    try {
      const saved = await updateApi.saveUpdate(current.id, editBody);
      setCurrent(saved);
      setEditBody(saved.bodyMd);
      setDirty(false);
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setSaveBusy(false);
    }
  }, [current, editBody]);

  // ── Regenerate verb ──
  const regenerate = useCallback(async (generator: "deterministic" | "model") => {
    if (!current) return;
    setRegenerateBusy(true);
    setError("");
    try {
      const newDraft = await updateApi.regenerateUpdate(current.id, generator);
      setCurrent(newDraft);
      setEditBody(newDraft.bodyMd);
      setDirty(false);
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setRegenerateBusy(false);
    }
  }, [current]);

  // ── Publish verb ──
  const publish = useCallback(async () => {
    if (!current || current.lifecycle !== "draft") return;
    setPublishBusy(true);
    setError("");
    try {
      const published = await updateApi.publishUpdate(current.id);
      setCurrent(published);
      onRoomRefresh();
    } catch (reason) {
      setError(readableError(reason));
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
      setError(readableError(reason));
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
    setEditBody(value);
    setDirty(true);
  }, []);

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
    exitUpdates,
    openUpdate,
    backToList,

    // List
    updates,
    drafts,
    published,
    hasUpdates,
    loading,
    error,

    // Editor
    current,
    editBody,
    dirty,
    isDraft,
    isPublished,
    handleEditBody,

    // Verbs
    draft,
    save,
    regenerate,
    publish,
    copyMarkdown,
    markDelivered,

    // Busy states
    draftBusy,
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
  } as const;
}

export type UpdateController = ReturnType<typeof useUpdateController>;
