import { NEW_THOUGHT_TITLE } from "../thoughtTitle";
import { useEffect, useRef } from "react";
import { EditInPlace } from "../surface";
import { MicButton } from "../components/MicButton";
import { DeskEditor, type DeskEditorHandle } from "../components/DeskEditor";
import type { ThoughtDraft } from "../pullouts/editors/useThoughtNoteWriter";
import { claimThoughtKeys } from "../thoughtKeys";

/* HS-201-12 — bands 1 and 2 of the one clean note (the owner's first-use
   verdict of 2026-09-20).  The title wraps and is edited in place; the note
   is the text, full width, no formatting rail.  The tag row, the Info verb,
   the orphan mic and the Filed/Saved foot left THIS window: tags and the
   original capture stay in the Note pullout (`desk/pullouts/NotePullout`),
   the kept state moved to the window foot.  The mic is the note field's own
   (it writes at the cursor), never a button beside the field. */
export function ThoughtDocumentPane({
  noteId,
  draft,
  onEdit,
  disabled,
  lockedReason,
  revealRange,
}: {
  /** The thought's note. With it, the field takes the keys typed between
   *  `Write a thought` and this window (thoughtKeys.ts). */
  noteId?: string;
  draft: ThoughtDraft;
  onEdit: (patch: Partial<ThoughtDraft>) => void;
  disabled: boolean;
  /** Why the note cannot be edited right now (a finished Thought). Never a
   *  dead field without a reason — the EditInPlace contract. */
  lockedReason?: string;
  revealRange?: { start: number; end: number; focus?: boolean } | null;
}) {
  const bodyRef = useRef<DeskEditorHandle | null>(null);

  /* HS-201-12 — the reveal is re-applied when the authoritative body
     lands: the append arrives as a whole-document sync, which maps the
     decoration away.  The window clears `revealRange` on the first real
     edit, so this never re-scrolls under the owner's cursor. */
  useEffect(() => {
    if (!revealRange || !bodyRef.current) return;
    bodyRef.current.revealRange(revealRange.start, revealRange.end, { focus: revealRange.focus });
  }, [revealRange, draft.body]);

  useEffect(() => {
    if (!noteId) return;
    return claimThoughtKeys(noteId, (text) => bodyRef.current?.insertAtCursor(text));
  }, [noteId]);

  return <section className="thought-note-document" aria-label="Note">
    <EditInPlace
      className="thought-note-title"
      label="Title"
      // A thought with no title of its own has an empty title field: the
      // stored word `Thought` is not a name (windowName.ts).
      value={draft.title.trim() === NEW_THOUGHT_TITLE ? "" : draft.title}
      placeholder="New thought"
      multiline
      disabledReason={lockedReason}
      onCommit={(next) => onEdit({ title: next })}
    />
    <div className="thought-note-field">
      <DeskEditor
        ref={bodyRef}
        className="thought-note-body"
        ariaLabel="Note body"
        value={draft.body}
        editable={!disabled}
        autoFocus
        placeholder="Start with what you know…"
        showToolbar={false}
        lineWrapping
        onChange={(body) => onEdit({ body })}
      />
      <span className="thought-note-field-mic">
        <MicButton label="Speak the note" onText={(text) => bodyRef.current?.insertAtCursor(text)} />
      </span>
    </div>
  </section>;
}
