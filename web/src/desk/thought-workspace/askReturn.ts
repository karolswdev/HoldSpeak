import type { AskSelectionHandoff } from "../ask";

/** A one-shot request delivered only to the Thought window that opened Ask. */
export const ASK_RETURN_EVENT = "holdspeak:ask-return-to-thought";
let pending: AskSelectionHandoff | null = null;

export function validAskReturnRange(source: AskSelectionHandoff, noteRef: string, body: string): { from: number; to: number } | null {
  const range = source.range;
  if (source.noteRef !== noteRef || source.body !== body || !range) return null;
  if (range.from < 0 || range.to < range.from || range.to > body.length) return null;
  if (body.slice(range.from, range.to) !== source.text) return null;
  return { ...range };
}

export function requestAskReturn(source: AskSelectionHandoff): void {
  pending = { ...source, range: source.range ? { ...source.range } : null };
  window.dispatchEvent(new CustomEvent(ASK_RETURN_EVENT, { detail: source }));
}

/** Consume only at the captured Note window; a different window cannot steal it. */
export function takeAskReturn(windowId: string | null, noteRef: string): AskSelectionHandoff | null {
  if (!pending || !windowId || pending.windowId !== windowId || pending.noteRef !== noteRef) return null;
  const source = pending;
  pending = null;
  return source;
}
