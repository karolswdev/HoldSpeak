/** Betterment Q8 (one note): Ask ▸ Add to note.
 *
 * In Ask opened from a note, Add to note appends an answer to that note, so
 * the note grows from the conversation. Undo puts the note back as it was,
 * when nothing else changed it since. The write is the note's own thought
 * write (the hub adopts a plain note first, as opening it does); an open
 * sticky of the note reads it again (NOTE_GREW_EVENT). */
import { NOTE_GREW_EVENT, openNoteThought, saveThoughtWorking } from "./thoughts";

export interface NoteAppend {
  noteId: string;
  before: string;
  after: string;
}

function grew(noteId: string): void {
  window.dispatchEvent(new CustomEvent(NOTE_GREW_EVENT, { detail: { noteId } }));
}

/** The note's body with `text` after it, one blank line between. */
export function appendedBody(body: string, text: string): string {
  const gap = !body ? "" : body.endsWith("\n\n") ? "" : body.endsWith("\n") ? "\n" : "\n\n";
  return `${body}${gap}${text.trim()}`;
}

export async function appendToNote(noteId: string, text: string): Promise<NoteAppend> {
  const thought = await openNoteThought(noteId);
  const note = thought.working_note;
  const after = appendedBody(note.body_markdown, text);
  await saveThoughtWorking(thought, { title: note.title, body_markdown: after, tags: note.tags });
  grew(noteId);
  return { noteId, before: note.body_markdown, after };
}

/** Undo one append. False when the note changed since: Undo never removes
 *  words he wrote after it. */
export async function undoAppend(append: NoteAppend): Promise<boolean> {
  const thought = await openNoteThought(append.noteId);
  const note = thought.working_note;
  if (note.body_markdown !== append.after) return false;
  await saveThoughtWorking(thought, { title: note.title, body_markdown: append.before, tags: note.tags });
  grew(append.noteId);
  return true;
}
