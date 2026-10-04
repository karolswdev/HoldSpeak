/* The open Thought windows and the words they hold.
 *
 * `Write a thought` uses a thought with no words again (newThought.ts). The
 * hub's record alone cannot say that: the writer saves after a pause, so a
 * thought the owner has just typed in is still empty on the hub. Two thoughts
 * became one note (`First thoughtSecond thought`; Astra's condition on #790).
 * Each open Thought window states here whether its draft has words, and
 * gives its save, so the first thought is kept before the next one starts. */

import { useSyncExternalStore } from "react";

export interface ThoughtDraftSeat {
  /** The draft on the glass has words (a title of its own, or a note). */
  words: () => boolean;
  /** Save the draft now. */
  flush: () => Promise<unknown>;
}

const seats = new Map<string, ThoughtDraftSeat>();

/* The words on the glass now, for the window's name. The window frame is
 * above the writer, and the name follows the draft at once (windowName.ts),
 * before the hub keeps the note. */
export interface ThoughtDraftWords { title: string; body: string }
const words = new Map<string, ThoughtDraftWords>();
const wordListeners = new Set<() => void>();
const tellWords = () => { for (const l of wordListeners) l(); };

/** State the draft's title and note. Returns the withdrawal. */
export function publishThoughtDraft(noteId: string, draft: ThoughtDraftWords): () => void {
  const now = words.get(noteId);
  if (!now || now.title !== draft.title || now.body !== draft.body) {
    words.set(noteId, { title: draft.title, body: draft.body });
    tellWords();
  }
  return () => {
    if (words.delete(noteId)) tellWords();
  };
}

/** The draft of this note on the glass now; null when no window holds it. */
export function useThoughtDraftWords(noteId: string): ThoughtDraftWords | null {
  return useSyncExternalStore(
    (cb) => { wordListeners.add(cb); return () => { wordListeners.delete(cb); }; },
    () => words.get(noteId) ?? null,
  );
}

export function seatThoughtDraft(noteId: string, seat: ThoughtDraftSeat): () => void {
  seats.set(noteId, seat);
  return () => {
    if (seats.get(noteId) === seat) seats.delete(noteId);
  };
}

/** The draft of this note, on the glass now, has words. */
export function thoughtDraftHasWords(noteId: string): boolean {
  return seats.get(noteId)?.words() ?? false;
}

/** Save every open thought that has words. A refused save is named by its
 * own window's foot; it never stops the next thought. */
export async function keepOpenThoughts(): Promise<void> {
  await Promise.all(
    [...seats.values()].filter((seat) => seat.words()).map((seat) => seat.flush().catch(() => undefined)),
  );
}
