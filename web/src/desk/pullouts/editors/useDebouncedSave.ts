/** Debounced save for inline editors (HS-117-15). */
import { useRef } from "react";
import { useDesk } from "../../store";
import { forgetDraft, keepDraft } from "../../deskMemory";
import { editorDraftKey as draftKey, keptEditorPatch } from "./editorDraft";

export function useDebouncedSave(kind: string, id: string) {
  const { updatePrimitive } = useDesk.getState();
  const timer = useRef<number | null>(null);
  const pending = useRef<Record<string, unknown> | null>(null);
  const inFlight = useRef<Record<string, unknown>>({});
  if (pending.current === null) pending.current = keptEditorPatch(kind, id);
  const keep = () => {
    const unsaved = { ...inFlight.current, ...pending.current };
    if (Object.keys(unsaved).length) keepDraft(draftKey(kind, id), JSON.stringify(unsaved));
    else forgetDraft(draftKey(kind, id));
  };
  return (patch: Record<string, unknown>) => {
    pending.current = { ...pending.current, ...patch };
    keep();
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      const body = pending.current ?? {};
      pending.current = {};
      inFlight.current = { ...inFlight.current, ...body };
      const before = useDesk.getState().keptAt[id];
      void Promise.resolve(updatePrimitive(kind, id, body)).then(() => {
        // Kept by the hub (the receipt's stamp moved): forget what it sent.
        if (useDesk.getState().keptAt[id] !== before) {
          inFlight.current = {};
          keep();
        }
      });
    }, 450);
  };
}
