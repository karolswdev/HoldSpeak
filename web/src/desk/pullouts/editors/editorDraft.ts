import { forgetDraft, keepDraft, keptDraft } from "../../deskMemory";

/* PHILO-13-07 (B2): the edit the hub has not kept yet (inside the 450 ms
   wait, or a write that did not land) is kept in the workspace document per
   object, `editor/<kind>/<id>`, so a reload brings it back into the editor.
   Restore only shows it; the next edit sends it with the new words. */
export const editorDraftKey = (kind: string, id: string) => `editor/${kind}/${id}`;

/** The unsaved wire patch kept for this object (empty when none). */
export function keptEditorPatch(kind: string, id: string): Record<string, unknown> {
  try {
    const raw = keptDraft(editorDraftKey(kind, id));
    const value = raw ? JSON.parse(raw) : {};
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  } catch {
    return {};
  }
}

/** A kept patch value as the editor's field text (lists join with ", "). */
export function keptField(patch: Record<string, unknown>, wire: string, fallback: string): string {
  const value = patch[wire];
  if (Array.isArray(value)) return value.join(", ");
  return typeof value === "string" ? value : fallback;
}

/** Recovery updates only its own fields, preserving newer editor work. */
export function updateKeptEditorFields(kind: string, id: string, patch: Record<string, unknown>, remove: string[] = []) {
  const next = { ...keptEditorPatch(kind, id), ...patch };
  for (const key of remove) delete next[key];
  if (Object.keys(next).length) keepDraft(editorDraftKey(kind, id), JSON.stringify(next));
  else forgetDraft(editorDraftKey(kind, id));
}

