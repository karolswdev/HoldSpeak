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
import { plainFailure } from "../../../desk/surface/plainFailure";
import { forgetDraft, keepDraft, keepPlace, keptDraft, keptPlace } from "../../../desk/deskMemory";
import type { ProjectUpdate, UpdateLifecycle } from "./model";
import * as updateApi from "./api";

export type UpdatePosture = "off" | "list" | "editor";

/* PHILO-13-07 (B2) — the Room's update place (`list` or `editor:<update>`)
   per project, and the unsaved body per update (never per project, so the
   text typed for one update never shows in another). Save clears it. */
const updatePlaceKey = (projectId: string) => `room/update/${projectId}`;
const updateDraftKey = (updateId: string) => `room/update-body/${updateId}`;

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
  // PHILO-13-04 (A3): a failure is plain words (never the hub's text) and
  // keeps the verb that failed, so the face can offer it again.
  const [retryFailed, setRetryFailed] = useState<(() => void) | null>(null);
  const fail = (what: string, reason: unknown, again?: () => void) => {
    setError(plainFailure(what, reason));
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
  }, [projectId]);

  // ── Exit update posture ──
  const exitUpdates = useCallback(() => {
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
    setEditBody(kept ?? update.bodyMd);
    setDirty(kept !== null && kept !== update.bodyMd);
    setPosture("editor");
    setError("");
    if (projectId) keepPlace(updatePlaceKey(projectId), `editor:${update.id}`);
  }, [projectId]);

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
      keepPlace(updatePlaceKey(projectId), `editor:${update.id}`);
      // Refresh list in background
      updateApi.fetchUpdates(projectId).then(setUpdates).catch(() => {});
    } catch (reason) {
      fail("DRAFT NOT MADE", reason, () => void draft(generator));
    } finally {
      setDraftBusy(false);
    }
  }, [projectId]);

  // ── Save verb (draft only) ──
  const save = useCallback(async () => {
    if (!current || current.lifecycle !== "draft") return;
    setSaveBusy(true);
    setError("");
    const sent = editBody;
    try {
      const saved = await updateApi.saveUpdate(current.id, sent);
      setCurrent(saved);
      // Words typed while the save was in flight stay, and stay unsaved.
      if (editBodyNow.current === sent) {
        setEditBody(saved.bodyMd);
        setDirty(false);
        forgetDraft(updateDraftKey(current.id));
      }
    } catch (reason) {
      fail("NOT SAVED", reason, () => void verbs.current.save());
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
      forgetDraft(updateDraftKey(current.id));
      setCurrent(newDraft);
      setEditBody(newDraft.bodyMd);
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

    // PHILO-10-04: the history read again after a send settles
    reloadDeliveries,
    deliveriesReadFailed,
  } as const;
}

export type UpdateController = ReturnType<typeof useUpdateController>;
