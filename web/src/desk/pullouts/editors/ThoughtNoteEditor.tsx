import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import { ApiError } from "../../../lib/api";
import { DeskEditor } from "../../components/DeskEditor";
import { StringGadget } from "../../surface/gadgets";
import { saveThoughtWorking, type Thought } from "../../thoughts";
import { useDesk } from "../../store";

type Draft = { title: string; body: string; tags: string };
const toDraft = (thought: Thought): Draft => ({ title: thought.working_note.title, body: thought.working_note.body_markdown, tags: thought.working_note.tags.join(", ") });

export type ThoughtNoteEditorHandle = { flush: () => Promise<Thought> };

/** One serialized local writer. `flush` fences first, then drains A and queued B. */
export const ThoughtNoteEditor = forwardRef<ThoughtNoteEditorHandle, { thought: Thought; onThought: (thought: Thought) => void; finishing?: boolean }>(function ThoughtNoteEditor({ thought, onThought, finishing = false }, ref) {
  const [title, setTitle] = useState(thought.working_note.title);
  const [body, setBody] = useState(thought.working_note.body_markdown);
  const [tags, setTags] = useState(thought.working_note.tags.join(", "));
  const [message, setMessage] = useState("");
  const timer = useRef<number | null>(null);
  const inFlight = useRef(false);
  const dirty = useRef(false);
  const saveFailed = useRef(false);
  const conflictFenced = useRef(false);
  const finishingRef = useRef(finishing);
  const authorityEpoch = useRef(0);
  const mounted = useRef(true);
  const draft = useRef<Draft>(toDraft(thought));
  const current = useRef(thought);
  const waiters = useRef<(() => void)[]>([]);
  const wake = () => { const pending = waiters.current.splice(0); pending.forEach((resolve) => resolve()); };
  const wait = () => new Promise<void>((resolve) => waiters.current.push(resolve));
  const clearTimer = () => { if (timer.current !== null) { clearTimeout(timer.current); timer.current = null; } };

  const installAuthoritative = (authoritative: Thought, { fence, notify }: { fence: boolean; notify: boolean }) => {
    authorityEpoch.current += 1; clearTimer(); dirty.current = false; saveFailed.current = false; conflictFenced.current = fence; current.current = authoritative;
    const next = toDraft(authoritative); draft.current = next;
    if (mounted.current) { setTitle(next.title); setBody(next.body); setTags(next.tags); }
    if (notify) onThought(authoritative);
    wake();
  };

  const drain = async (): Promise<void> => {
    timer.current = null;
    if (inFlight.current || !dirty.current || conflictFenced.current) return;
    inFlight.current = true; dirty.current = false; saveFailed.current = false;
    const requestEpoch = authorityEpoch.current;
    const sent = { ...draft.current };
    try {
      const updated = await saveThoughtWorking(current.current, { title: sent.title, body_markdown: sent.body, tags: sent.tags.split(",").map((tag) => tag.trim()).filter(Boolean) });
      inFlight.current = false;
      if (requestEpoch !== authorityEpoch.current) { wake(); return; }
      current.current = updated;
      if (mounted.current) { onThought(updated); setMessage(""); }
      void Promise.resolve(useDesk.getState().refresh()).catch(() => undefined);
      if (dirty.current && !conflictFenced.current) {
        if (finishingRef.current) await drain();
        else timer.current = window.setTimeout(() => void drain(), 0);
      }
      wake();
    } catch (cause) {
      inFlight.current = false;
      const payload = cause instanceof ApiError && cause.payload && typeof cause.payload === "object" ? cause.payload as { current?: unknown; context?: { current?: unknown } } : null;
      const authoritative = (payload?.context?.current ?? payload?.current) as Thought | undefined;
      const sameThought = authoritative?.id === current.current.id;
      const superseded = requestEpoch !== authorityEpoch.current;
      if (authoritative?.working_note && typeof authoritative.aggregate_revision === "number" && sameThought && (!superseded || authoritative.aggregate_revision > current.current.aggregate_revision)) {
        installAuthoritative(authoritative, { fence: true, notify: true });
        if (mounted.current) setMessage("This thought changed elsewhere. Your latest version is shown. Review it, then edit again.");
      } else if (!superseded) {
        dirty.current = true;
        saveFailed.current = true;
        if (mounted.current) setMessage("Could not save this thought. Your changes are still here. Retry save.");
      }
      wake();
    }
  };
  const schedule = (delay = 450) => { if (conflictFenced.current || inFlight.current || finishingRef.current) return; clearTimer(); timer.current = window.setTimeout(() => void drain(), delay); };

  useImperativeHandle(ref, () => ({
    flush: async () => {
      // This fence is synchronous: no keyboard event after this call can append B.
      finishingRef.current = true; clearTimer();
      if (saveFailed.current) throw new Error("thought save failed");
      while (inFlight.current || dirty.current) {
        if (!inFlight.current && dirty.current) await drain();
        else await wait();
        if (conflictFenced.current) throw new Error("thought save conflict");
        if (saveFailed.current) throw new Error("thought save failed");
      }
      if (conflictFenced.current) throw new Error("thought save conflict");
      if (saveFailed.current) throw new Error("thought save failed");
      return current.current;
    },
  }), []);

  useEffect(() => { finishingRef.current = finishing; }, [finishing]);
  useEffect(() => { if (thought.id !== current.current.id || thought.aggregate_revision > current.current.aggregate_revision) installAuthoritative(thought, { fence: true, notify: false }); }, [thought]);
  useEffect(() => () => { mounted.current = false; clearTimer(); wake(); }, []);
  const edit = (next: Partial<Draft>) => {
    if (finishingRef.current) return;
    draft.current = { ...draft.current, ...next }; dirty.current = true; saveFailed.current = false; conflictFenced.current = false; setMessage(""); schedule();
  };
  const retry = () => { if (inFlight.current || conflictFenced.current || finishingRef.current) return; dirty.current = true; saveFailed.current = false; setMessage(""); schedule(0); };
  const disabled = finishing;
  return <>
    <StringGadget label="Title" value={title} onChange={(next) => { if (!disabled) { setTitle(next); edit({ title: next }); } }} />
    <DeskEditor value={body} placeholder="Write" autoFocus onChange={(next) => { if (!disabled) { setBody(next); edit({ body: next }); } }} />
    <StringGadget label="Tags" value={tags} onChange={(next) => { if (!disabled) { setTags(next); edit({ tags: next }); } }} />
    {message ? <p role="status" className="surface-receipt-line">{message} {message.includes("Retry save") ? <button type="button" className="desk-chip quiet" onClick={retry}>Retry save</button> : null}</p> : null}
  </>;
});
