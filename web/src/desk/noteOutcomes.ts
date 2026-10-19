/** Betterment Q9 "Find the tasks": the client of a note's outcome rows.
 *
 * The hub runs the meeting's extraction over the note
 * (holdspeak/services/note_outcomes_service.py) and keeps the rows with the
 * note. Confirm makes the task (Needs you, the person's window) or the
 * proposed decision, with the note as its source. */
import { apiFetch } from "../lib/api";

export interface NoteOutcome {
  id: string;
  kind: "task" | "decision";
  text: string;
  owner: string;
  due: string;
  rationale: string;
  state: "proposed" | "confirmed";
  made_ref: string;
  found_at: string;
  model: string;
}

export interface NoteOutcomes {
  note_id: string;
  rows: NoteOutcome[];
}

const base = (noteId: string) => `/api/notes/${encodeURIComponent(noteId)}/outcomes`;

export const readNoteOutcomes = (noteId: string) => apiFetch<NoteOutcomes>(base(noteId));
export const findNoteOutcomes = (noteId: string) => apiFetch<NoteOutcomes>(`${base(noteId)}/find`, { method: "POST" });
export const confirmNoteOutcome = (noteId: string, rowId: string) =>
  apiFetch<NoteOutcomes>(`${base(noteId)}/${encodeURIComponent(rowId)}/confirm`, { method: "POST" });
