import { forwardRef, useImperativeHandle } from "react";
import { Button } from "../../../components/signal/Signal";
import { DeskEditor } from "../../components/DeskEditor";
import { StringGadget } from "../../surface/gadgets";
import type { Thought } from "../../thoughts";
import { thoughtWriteLine } from "../../thought-workspace/thoughtReceipt";
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
  const line = thoughtWriteLine(writer);
  const fault = line?.danger ? line : null;

  return <>
    <StringGadget label="Title" value={writer.draft.title} onChange={(title) => writer.edit({ title })} />
    <DeskEditor value={writer.draft.body} placeholder="Write" autoFocus onChange={(body) => writer.edit({ body })} />
    <StringGadget label="Tags" value={writer.draft.tags} onChange={(tags) => writer.edit({ tags })} />
    {/* PHILO-3-04 — the fault as the Thought foot states it; no prose. */}
    {fault ? <span role="status" className="surface-receipt-line" data-tone="danger">{fault.text} {writer.failed ? <Button dense onClick={writer.retry}>Retry</Button> : null}</span> : null}
  </>;
});
