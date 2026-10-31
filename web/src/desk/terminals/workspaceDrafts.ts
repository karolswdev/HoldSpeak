export interface FileDraftState {
  text: string;
  baseSha256: string | null;
}

/** One durable Desk draft owns both text and the revision it was captured
 * from. Keeping these together prevents a reload from pairing old words with
 * a newly fetched hash and silently overwriting another writer's change. */
export function readWorkspaceFileDraft(raw: string | null | undefined): FileDraftState | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<FileDraftState>;
    if (typeof parsed.text !== "string") return null;
    return { text: parsed.text, baseSha256: typeof parsed.baseSha256 === "string" ? parsed.baseSha256 : null };
  } catch {
    return null;
  }
}

export function writeWorkspaceFileDraft(state: FileDraftState): string {
  return JSON.stringify(state);
}
