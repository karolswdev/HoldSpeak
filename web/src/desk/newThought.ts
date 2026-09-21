/* HS-202-02 job 3 — `Write a thought` opens a place to write a thought.
 *
 * It opened the Speak dictation router instead (`LANDS IN · Codex CLI`,
 * `DICTATION · ⚠ NOT SET`, no verb that keeps anything), and the real door
 * was `Desk → New Note` — nine moves away for a stranger
 * (04-sober-eye.md, Job 3 and rank 3).
 *
 * The face this opens is HS-201-12's Thought window: title, the note, one
 * question, one foot. A thought-owned note routes there by itself
 * (`desk/components/Pullout.tsx:123`), so this mints the note, adopts it
 * through the SAME service the note pullout's `Develop` verb uses, and
 * opens it. `POST /api/thoughts` cannot start this: it refuses an empty
 * `raw_text` (holdspeak/services/refinement_thought_service.py:79), and a
 * new thought has no words yet.
 *
 * If the adoption is refused, the note still opens: the words must always
 * have a home, even on the ordinary note face.
 */
import { apiFetch } from "../lib/api";
import { useDesk } from "./store";
import { reportWriteFailure, clearWriteFailure } from "./hooks/useWriteReceipt";
import { adoptThought, thoughtForNote } from "./thoughts";

export async function openNewThought(): Promise<void> {
  let noteId = "";
  try {
    const created = await apiFetch<{ note?: { id?: string } }>("/api/notes", {
      method: "POST",
      json: { title: "Thought", body_markdown: "", tags: [] },
    });
    noteId = String(created.note?.id ?? "");
    clearWriteFailure();
  } catch (cause) {
    /* HS-202-02 (Astra's counsel finding 4) — a refused create used to
       return in silence: `apiFetch` only throws, so nothing reached the
       desk's failure channel and the owner pressed a verb that did
       nothing, with no line and no retry. */
    reportWriteFailure("Write a thought", cause, () => void openNewThought());
    return;
  }
  if (!noteId) return;
  try {
    const status = await thoughtForNote(noteId);
    if (status.ownership === "ordinary")
      await adoptThought({
        request_id: crypto.randomUUID(),
        note_id: noteId,
        expected_source_content_sha256:
          status.source_precondition.content_sha256,
        expected_source_last_modified: status.source_precondition.last_modified,
      });
  } catch {
    // The note exists and is the owner's. It opens on the ordinary note
    // face, where `Develop` can adopt it when the hub answers again.
  }
  await useDesk.getState().refresh();
  useDesk.getState().openPullout(`note:${noteId}`);
}
