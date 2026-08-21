import { forwardRef, useImperativeHandle } from "react";
import { DeskEditor } from "../../components/DeskEditor";
import { StringGadget } from "../../surface/gadgets";
import type { Thought } from "../../thoughts";
import { useThoughtNoteWriter } from "./useThoughtNoteWriter";

export type ThoughtNoteEditorHandle = { flush: () => Promise<Thought> };

/** Legacy compact presentation over the shared Thought writer. */
export const ThoughtNoteEditor = forwardRef<ThoughtNoteEditorHandle, {
  thought: Thought;
  onThought: (thought: Thought) => void;
  finishing?: boolean;
}>(function ThoughtNoteEditor({ thought, onThought, finishing = false }, ref) {
  const writer = useThoughtNoteWriter({ thought, onThought, locked: finishing });

  useImperativeHandle(ref, () => ({ flush: () => writer.flush({ fence: true }) }), [writer]);

  return <>
    <StringGadget label="Title" value={writer.draft.title} onChange={(title) => writer.edit({ title })} />
    <DeskEditor value={writer.draft.body} placeholder="Write" autoFocus onChange={(body) => writer.edit({ body })} />
    <StringGadget label="Tags" value={writer.draft.tags} onChange={(tags) => writer.edit({ tags })} />
    {writer.message ? <p role="status" className="surface-receipt-line">{writer.message} {writer.message.includes("Retry save") ? <button type="button" className="desk-chip quiet" onClick={writer.retry}>Retry save</button> : null}</p> : null}
  </>;
});
