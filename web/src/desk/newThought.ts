/* Betterment Q8 (one note): New Note (⌃N, and ⌃T) opens this. `Write a
 * thought` left the Desk menu; the history below keeps its old name.
 *
 * HS-202-02 job 3 — `Write a thought` opens a place to write a thought.
 *
 * It opened the Speak dictation router instead (`LANDS IN · Codex CLI`,
 * `DICTATION · ⚠ NOT SET`, no verb that keeps anything), and the real door
 * was `Desk → New Note` — nine moves away for a stranger
 * (04-sober-eye.md, Job 3 and rank 3).
 *
 * The face this opens is HS-201-12's Thought window: title, the note, one
 * question, one foot. A thought-owned note routes there by itself
 * (`desk/components/Pullout.tsx`), so this mints the note, adopts it
 * through the SAME service the note pullout's `Develop` verb uses, and
 * opens it. `POST /api/thoughts` cannot start this: it refuses an empty
 * `raw_text` (holdspeak/services/refinement_thought_service.py:79), and a
 * new thought has no words yet.
 *
 * If the adoption is refused, the note still opens: the words must always
 * have a home, even on the ordinary note face.
 *
 * PHILO-13-16 (C6): the Desk menu's `Write a thought` (⌃T, verbRegistry.ts)
 * calls this from any window. The note is born `Thought`; the writer gives it
 * its first words on save (thoughtTitle.ts).
 *
 * Inventory 2026-10-03 (A-apps row 31) — three faults, paid here:
 *  - The window opened 2 to 5 s late: it waited for a full desk read. The
 *    create answer goes into the store (`adoptCreated`) and the window opens
 *    with no wait; the desk read follows.
 *  - The keys typed before the window opened were lost. They are kept from
 *    the press and the note field takes them (thoughtKeys.ts).
 *  - Every press made another note named `Thought` (six after one walk). A
 *    thought with no words is used again: one empty thought, never six.
 *    "No words" is the hub's record AND the draft on the glass: a thought
 *    with unsaved words is saved first and is never used again
 *    (thoughtDrafts.ts).
 */
import { apiFetch } from "../lib/api";
import { useDesk } from "./store";
import { reportWriteFailure, clearWriteFailure } from "./hooks/useWriteReceipt";
import { openNoteThought, thoughtForNote } from "./thoughts";
import { NEW_THOUGHT_TITLE } from "./thoughtTitle";
import { sendThoughtKeysTo, startThoughtKeys, stopThoughtKeys } from "./thoughtKeys";
import { keepOpenThoughts, thoughtDraftHasWords } from "./thoughtDrafts";

/** The one press in flight: a second press before the window opens joins it. */
let opening: Promise<void> | null = null;

const noWords = (title: string, body: string) =>
  title.trim() === NEW_THOUGHT_TITLE && !body.trim();


/** The newest thought that still has no words, by the hub's own record (the
 * store's copy of a note can be older than its last save). */
async function emptyThoughtNote(): Promise<string | null> {
  const notes = (useDesk.getState().items.note ?? [])
    // A draft with words the hub has not kept yet is not an empty thought.
    .filter((note) => noWords(note.title, note.bodyMarkdown) && !thoughtDraftHasWords(note.id))
    .sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)))
    .slice(0, 3);
  for (const note of notes) {
    try {
      const status = await thoughtForNote(note.id);
      if (status.ownership !== "thought") continue;
      const { state, working_note: kept } = status.thought;
      if (state === "working" && !kept.deleted && noWords(kept.title, kept.body_markdown))
        return note.id;
    } catch {
      // This note cannot be checked now; the next one, or a new note.
    }
  }
  return null;
}

async function open(): Promise<void> {
  const desk = useDesk.getState();
  // The thought on the glass is kept first; then the next one starts.
  await keepOpenThoughts();
  let noteId = await emptyThoughtNote();
  if (!noteId) {
    try {
      const created = await apiFetch<{ note?: { id?: string } }>("/api/notes", {
        method: "POST",
        json: { title: NEW_THOUGHT_TITLE, body_markdown: "", tags: [] },
      });
      noteId = String(created.note?.id ?? "");
      if (noteId) desk.adoptCreated("note", created.note);
      clearWriteFailure();
    } catch (cause) {
      /* HS-202-02 (Astra's counsel finding 4) — a refused create used to
         return in silence: `apiFetch` only throws, so nothing reached the
         desk's failure channel and the owner pressed a verb that did
         nothing, with no line and no retry. */
      stopThoughtKeys();
      reportWriteFailure("New Note", cause, () => void openNewThought());
      return;
    }
    if (!noteId) { stopThoughtKeys(); return; }
    try {
      // Betterment Q8: the hub gives the new note its thought (the window
      // asks again on open, so a refusal here only costs one more read).
      await openNoteThought(noteId);
    } catch {
      // The note exists and is the owner's. The window asks again when it opens.
    }
  }
  desk.openPullout(`note:${noteId}`);
  sendThoughtKeysTo(noteId);
  void desk.refresh();
}

/** `firstWords`: the text typed before the note existed (Capture's New note
 *  makes the record on the first character, never on the press; betterment
 *  C8). The note field takes it, then the keys typed after it. */
export function openNewThought(firstWords = ""): Promise<void> {
  startThoughtKeys(firstWords);
  opening ??= open().finally(() => { opening = null; });
  return opening;
}
