/** The inline editor's autosave authority, shared with its local host. */
import { createElement, Fragment, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { useDesk } from "../../store";
import { qualifiedRef } from "../../api";
import { forgetDraft, keepDraft } from "../../deskMemory";
import { currentWriteFailure, writeFailureReason } from "../../hooks/useWriteReceipt";
import { editorDraftKey as draftKey, keptEditorPatch } from "./editorDraft";
import type { RegisterCloseGuard } from "../types";

export type EditorWriter = ((patch: Record<string, unknown>) => void) & {
  state: "idle" | "pending" | "saving" | "saved" | "error" | "recovered";
  savedAt: number | null;
  reason: string;
  flush: () => Promise<boolean>;
  retry: () => Promise<boolean>;
};
export type PublishEditorWriter = (writer: EditorWriter | null) => void;

export function usePublishEditorWriter(writer: EditorWriter, publish?: PublishEditorWriter) {
  useEffect(() => { publish?.(writer); }, [publish, writer]);
  useEffect(() => () => publish?.(null), [publish]);
}

export function useDebouncedSave(kind: string, id: string, publish?: PublishEditorWriter): EditorWriter {
  const initial = useRef<Record<string, unknown> | null>(null);
  if (initial.current === null) {
    initial.current = keptEditorPatch(kind, id);
    // Knowledge is a member collection. Keep old text for explicit Note
    // recovery; never submit it as a successfully saved Knowledge field.
    if (kind === "kb") { delete initial.current.body_markdown; delete initial.current.recovery_note_id; }
  }
  const pending = useRef({ ...initial.current });
  const failed = useRef<Record<string, unknown>>({});
  const sending = useRef<Record<string, unknown>>({});
  const active = useRef<Promise<boolean> | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mounted = useRef(true);
  const [status, setStatus] = useState<Pick<EditorWriter, "state" | "savedAt" | "reason">>(() => ({
    state: Object.keys(initial.current || {}).length ? "recovered" : "idle", savedAt: null, reason: "",
  }));
  const keep = useCallback(() => {
    const retained = kind === "kb" ? keptEditorPatch(kind, id).body_markdown : undefined;
    const recoveredId = kind === "kb" ? keptEditorPatch(kind, id).recovery_note_id : undefined;
    const unsaved = { ...(typeof retained === "string" && retained ? { body_markdown: retained } : {}), ...(typeof recoveredId === "string" && recoveredId ? { recovery_note_id: recoveredId } : {}), ...failed.current, ...sending.current, ...pending.current };
    if (Object.keys(unsaved).length) keepDraft(draftKey(kind, id), JSON.stringify(unsaved));
    else forgetDraft(draftKey(kind, id));
  }, [kind, id]);

  const write = useCallback(async function drain(retry: boolean): Promise<boolean> {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    while (active.current) {
      if (!(await active.current)) return false;
    }
    const body = { ...(retry ? failed.current : {}), ...pending.current };
    if (!Object.keys(body).length) return !Object.keys(failed.current).length;
    pending.current = {};
    sending.current = body;
    if (mounted.current) setStatus((s) => ({ ...s, state: "saving", reason: "" }));
    const request = (async () => {
      let kept = false;
      let reason = "Write refused";
      try {
        kept = (await useDesk.getState().updatePrimitive(kind, id, body)) === true;
        const failure = currentWriteFailure();
        if (failure?.subject === qualifiedRef(kind, id)) reason = failure.reason;
      } catch (cause) { reason = writeFailureReason(cause); }
      if (kept) {
        // Acknowledgement removes only values this request actually kept.
        for (const key of Object.keys(body)) {
          delete failed.current[key];
        }
      } else failed.current = { ...failed.current, ...body };
      sending.current = {};
      keep();
      if (mounted.current) setStatus((s) => ({
        state: Object.keys(failed.current).length ? "error" : Object.keys(pending.current).length ? "pending" : "saved",
        savedAt: kept ? Date.now() : s.savedAt,
        reason: Object.keys(failed.current).length ? reason : "",
      }));
      return kept;
    })();
    active.current = request;
    const kept = await request;
    active.current = null;
    if (!kept) return false;
    if (Object.keys(pending.current).length) return drain(retry);
    return !Object.keys(failed.current).length;
  }, [kind, id, keep]);

  const queue = useCallback((patch: Record<string, unknown>) => {
    pending.current = { ...pending.current, ...patch };
    keep();
    setStatus((s) => ({ ...s, state: "pending", reason: "" }));
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => { void write(false); }, 450);
  }, [keep, write]);
  const flush = useCallback(() => write(true), [write]);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; if (timer.current) clearTimeout(timer.current); };
  }, []);
  const writer = useMemo(() => Object.assign((patch: Record<string, unknown>) => queue(patch), { ...status, flush, retry: flush }), [queue, status, flush]);
  usePublishEditorWriter(writer, publish);
  return writer;
}

/** Local host state only: Done and the frame close await this writer. */
export function useEditorSession(onDone: () => void, registerClose?: RegisterCloseGuard) {
  const writer = useRef<EditorWriter | null>(null);
  const [current, setCurrent] = useState<EditorWriter | null>(null);
  const onWriter = useCallback<PublishEditorWriter>((next) => { writer.current = next; setCurrent(() => next); }, []);
  const flush = useCallback(async () => writer.current ? writer.current.flush() : true, []);
  useEffect(() => registerClose?.(flush), [registerClose, flush]);
  const done = useCallback(async () => { if (await flush()) onDone(); }, [flush, onDone]);
  const receipt = current && current.state !== "idle" ? createElement("span", { role: "status", className: "editor-save-receipt" },
    current.state === "error" ? `Not saved · ${current.reason}` : current.state === "recovered" ? "Recovered changes" : current.state === "pending" || current.state === "saving" ? "Saving…" : current.savedAt ? `Saved ${new Date(current.savedAt).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}` : null,
  ) : null;
  const verbs = createElement(Fragment, null,
    current?.state === "error" || current?.state === "recovered" ? createElement(Button, { dense: true, variant: "ghost", onClick: () => void writer.current?.retry() }, "Retry") : null,
    createElement(Button, { dense: true, variant: "primary", disabled: current?.state === "saving", onClick: () => void done() }, "Done"),
  );
  return { onWriter, flush, done, receipt, verbs };
}
