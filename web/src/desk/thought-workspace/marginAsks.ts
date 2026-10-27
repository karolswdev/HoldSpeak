/* Direction A, step 2 (owner pick 2026-10-27): an Ask about this note lands
 * in the note's margin, beside the line it asked about.
 *
 * The Ask window runs the question (AskPanel); it puts each run it starts for
 * a note here, and the answer when it comes. The note window reads them for
 * its own note and draws one card for each. Dismiss and Add to note take a
 * card away. Nothing here is sent to the hub: the Ask thread keeps the turn. */
import { useSyncExternalStore } from "react";

export interface MarginAsk {
  key: string;
  noteId: string;
  question: string;
  /** The answer words; empty while the run works. */
  answer: string;
  state: "working" | "answered" | "failed";
  /** The selected passage the question was about, when Ask had one. */
  range: { from: number; to: number; text: string } | null;
  /** The saved note body at the handoff (validates the range). */
  body: string;
}

const byNote = new Map<string, MarginAsk[]>();
const listeners = new Set<() => void>();
const EMPTY: MarginAsk[] = [];

function emit() {
  for (const listener of listeners) listener();
}

export function putMarginAsk(ask: MarginAsk): void {
  const rows = byNote.get(ask.noteId) ?? EMPTY;
  const at = rows.findIndex((row) => row.key === ask.key);
  const next = at >= 0 ? rows.map((row, index) => (index === at ? { ...row, ...ask } : row)) : [...rows, { ...ask }];
  byNote.set(ask.noteId, next);
  emit();
}

export function updateMarginAsk(noteId: string, key: string, patch: Partial<Pick<MarginAsk, "answer" | "state">>): void {
  const rows = byNote.get(noteId);
  if (!rows?.some((row) => row.key === key)) return;
  byNote.set(noteId, rows.map((row) => (row.key === key ? { ...row, ...patch } : row)));
  emit();
}

export function dropMarginAsk(noteId: string, key: string): void {
  const rows = byNote.get(noteId);
  if (!rows) return;
  const next = rows.filter((row) => row.key !== key);
  if (next.length) byNote.set(noteId, next);
  else byNote.delete(noteId);
  emit();
}

export function readMarginAsks(noteId: string): MarginAsk[] {
  return byNote.get(noteId) ?? EMPTY;
}

/** Tests only: forget every card. */
export function resetMarginAsks(): void {
  byNote.clear();
  emit();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

export function useMarginAsks(noteId: string): MarginAsk[] {
  return useSyncExternalStore(subscribe, () => readMarginAsks(noteId), () => EMPTY);
}
