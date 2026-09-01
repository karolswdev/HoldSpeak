// HS-162-05 -- the Update controller: list, draft, edit, save, publish,
// regenerate, copy-markdown. Five verbs as separate honest state machines.
// Generator provenance visible on every draft.

import { useCallback, useState } from "react";
import { readableError } from "../../../lib/api";
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
