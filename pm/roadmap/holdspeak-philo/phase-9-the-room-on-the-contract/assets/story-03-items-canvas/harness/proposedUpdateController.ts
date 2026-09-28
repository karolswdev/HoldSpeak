// PHILO-9-03 canvas (PROPOSAL, not built) -- a copy of
// web/src/features/project-room/update/useUpdateController.ts with the
// copy-and-confirm verb added (blocks marked PROPOSAL):
//   - every update carries `deliveries` (the story 01 read-back, oldest first);
//   - markDelivered(): ONE press mints ONE command_id and keeps it across its
//     retries (Codex Astra r5); success appends the returned row.
// Copy does not change: the 2 s "Copied" feedback stays, and Mark delivered
// never depends on it (R4-3: no clipboard state is stored).
//
// HS-162-05 -- the Update controller: list, draft, edit, save, publish,
// regenerate, copy-markdown. Five verbs as separate honest state machines.
// Generator provenance visible on every draft.

import { useCallback, useRef, useState } from "react";
import { apiFetch, readableError } from "@w/lib/api";
import type { ProjectUpdate as BaseUpdate, UpdateLifecycle } from "@w/features/project-room/update/model";
import { decodeUpdate } from "@w/features/project-room/update/model";
import * as baseApi from "@w/features/project-room/update/api";

/* PROPOSAL: one row of project_update_deliveries, as the read carries it. */
export type Delivery = {
  id: string;
  updateId: string;
  deliveredAt: string;
  deliveredTo: string | null;
  operationId: string;
};
export type ProjectUpdate = BaseUpdate & { deliveries: Delivery[] };

function decodeDelivery(raw: Record<string, unknown>): Delivery {
  const to = raw.delivered_to != null ? String(raw.delivered_to).trim() : "";
  return {
    id: String(raw.id ?? ""),
    updateId: String(raw.update_id ?? ""),
    deliveredAt: String(raw.delivered_at ?? ""),
    deliveredTo: to || null,
    operationId: String(raw.operation_id ?? ""),
  };
}
function withDeliveries(raw: Record<string, unknown>): ProjectUpdate {
  const list = Array.isArray(raw.deliveries) ? (raw.deliveries as Record<string, unknown>[]) : [];
  return { ...decodeUpdate(raw), deliveries: list.map(decodeDelivery) };
}
const none = <T extends BaseUpdate>(u: T): ProjectUpdate => ({ ...u, deliveries: [] });
const updateApi = {
  ...baseApi,
  async fetchUpdates(projectId: string): Promise<ProjectUpdate[]> {
    const raw = await apiFetch<{ updates: Record<string, unknown>[] }>(
      `/api/projects/${encodeURIComponent(projectId)}/updates`,
    );
    return (raw.updates ?? []).map(withDeliveries);
  },
  draftUpdate: async (p: string, g: "deterministic" | "model") => none(await baseApi.draftUpdate(p, g)),
  saveUpdate: async (id: string, b: string) => none(await baseApi.saveUpdate(id, b)),
  regenerateUpdate: async (id: string, g: "deterministic" | "model") => none(await baseApi.regenerateUpdate(id, g)),
  publishUpdate: async (id: string) => none(await baseApi.publishUpdate(id)),
  /** PROPOSAL: POST /api/updates/{id}/delivered (story 02's route). */
  async markDelivered(id: string, deliveredTo: string, commandId: string): Promise<Delivery> {
    const raw = await apiFetch<{ delivery: Record<string, unknown> }>(
      `/api/updates/${encodeURIComponent(id)}/delivered`,
      { method: "POST", json: { delivered_to: deliveredTo.trim() || null, command_id: commandId } },
    );
    return decodeDelivery(raw.delivery);
  },
};

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

  // PROPOSAL: the confirm verb. The To field is free text, optional.
  const [deliverTo, setDeliverTo] = useState("");
  const [deliverBusy, setDeliverBusy] = useState(false);
  const [deliverError, setDeliverError] = useState("");
  // One press = one command_id, kept across its retries until it succeeds.
  const pressKey = useRef<string | null>(null);

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

  // ── PROPOSAL: Mark delivered ──
  const markDelivered = useCallback(async () => {
    if (!current || current.lifecycle !== "published" || deliverBusy) return;
    if (!pressKey.current) pressKey.current = crypto.randomUUID();
    setDeliverBusy(true);
    setDeliverError("");
    try {
      const row = await updateApi.markDelivered(current.id, deliverTo, pressKey.current);
      pressKey.current = null;
      const add = (u: ProjectUpdate) =>
        u.id === row.updateId && !u.deliveries.some((d) => d.id === row.id)
          ? { ...u, deliveries: [...u.deliveries, row] } : u;
      setCurrent((u) => (u ? add(u) : u));
      setUpdates((list) => list.map(add));
      setDeliverTo("");
      onRoomRefresh();
    } catch (reason) {
      // The key stays: the retry of this press returns the same row.
      setDeliverError(readableError(reason));
    } finally {
      setDeliverBusy(false);
    }
  }, [current, deliverBusy, deliverTo, onRoomRefresh]);

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
    // PROPOSAL
    markDelivered,
    deliverTo,
    setDeliverTo,
    deliverBusy,
    deliverError,

    // Busy states
    draftBusy,
    saveBusy,
    publishBusy,
    regenerateBusy,
    copyBusy,
    copyState,
  } as const;
}

export type UpdateController = ReturnType<typeof useUpdateController>;
