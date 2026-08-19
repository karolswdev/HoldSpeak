import { useEffect, useRef, useState } from "react";
import { ApiError } from "../../../lib/api";
import { DeskEditor } from "../../components/DeskEditor";
import { StringGadget } from "../../surface/gadgets";
import { saveThoughtWorking, type Thought } from "../../thoughts";
import { useDesk } from "../../store";

type Draft = { title: string; body: string; tags: string };
const toDraft = (thought: Thought): Draft => ({
  title: thought.working_note.title,
  body: thought.working_note.body_markdown,
  tags: thought.working_note.tags.join(", "),
});

/**
 * One serialized writer for a thought-owned Note.  A later keystroke is never
 * sent using a cursor captured before the prior save completed.
 */
export function ThoughtNoteEditor({ thought, onThought }: { thought: Thought; onThought: (thought: Thought) => void }) {
  const [title, setTitle] = useState(thought.working_note.title);
  const [body, setBody] = useState(thought.working_note.body_markdown);
  const [tags, setTags] = useState(thought.working_note.tags.join(", "));
  const [message, setMessage] = useState("");
  const timer = useRef<number | null>(null);
  const inFlight = useRef(false);
  const dirty = useRef(false);
  const conflictFenced = useRef(false);
  const authorityEpoch = useRef(0);
  const mounted = useRef(true);
  const draft = useRef<Draft>(toDraft(thought));
  const current = useRef(thought);

  const clearTimer = () => {
    if (timer.current !== null) { clearTimeout(timer.current); timer.current = null; }
  };
  const installAuthoritative = (authoritative: Thought, { fence, notify }: { fence: boolean; notify: boolean }) => {
    // Parent and CAS DTOs are a new authority epoch.  A request that started
    // before this point cannot install its late response over this state.
    authorityEpoch.current += 1;
    clearTimer();
    dirty.current = false;
    conflictFenced.current = fence;
    current.current = authoritative;
    const next = toDraft(authoritative);
    draft.current = next;
    if (mounted.current) { setTitle(next.title); setBody(next.body); setTags(next.tags); }
    if (notify) onThought(authoritative);
  };

  const drain = async (): Promise<void> => {
    timer.current = null;
    if (inFlight.current || !dirty.current || conflictFenced.current) return;
    inFlight.current = true;
    dirty.current = false;
    const requestEpoch = authorityEpoch.current;
    const sent = { ...draft.current };
    try {
      const updated = await saveThoughtWorking(current.current, {
        title: sent.title,
        body_markdown: sent.body,
        tags: sent.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
      });
      // Advance cursors after a successful request, even when the user typed
      // while it was in flight — unless a newer authoritative epoch won.
      inFlight.current = false;
      if (requestEpoch !== authorityEpoch.current) {
        // A newer parent/CAS DTO already won. Do not publish or regress it;
        // if the owner edited after that install, continue from that DTO.
        if (mounted.current && dirty.current && !conflictFenced.current) {
          timer.current = window.setTimeout(() => void drain(), 0);
        }
        return;
      }
      current.current = updated;
      if (!mounted.current) return;
      onThought(updated); setMessage("");
      void Promise.resolve(useDesk.getState().refresh()).catch(() => undefined);
      if (dirty.current && !conflictFenced.current) {
        timer.current = window.setTimeout(() => void drain(), 0);
      }
    } catch (cause) {
      inFlight.current = false;
      if (!mounted.current) return;
      const payload = cause instanceof ApiError && cause.payload && typeof cause.payload === "object"
        ? cause.payload as { current?: unknown; context?: { current?: unknown } } : null;
      const authoritative = (payload?.context?.current ?? payload?.current) as Thought | undefined;
      // A same-thought CAS answer is authoritative unless a newer parent/CAS
      // epoch already won; an accepted one discards queued local mutation.
      const isThoughtCurrent = authoritative?.id === current.current.id;
      const superseded = requestEpoch !== authorityEpoch.current;
      if (authoritative?.working_note && typeof authoritative.aggregate_revision === "number" && isThoughtCurrent
          && (!superseded || authoritative.aggregate_revision > current.current.aggregate_revision)) {
        installAuthoritative(authoritative, { fence: true, notify: true });
        if (mounted.current) setMessage("This thought changed elsewhere. Your latest version is shown. Review it, then edit again.");
        return;
      }
      if (authoritative?.working_note && typeof authoritative.aggregate_revision === "number" && superseded) {
        // This old/equal (or wrong-thought) CAS snapshot lost to a parent/CAS
        // authority install. Preserve that state and only continue a post-
        // install explicit edit against its cursors.
        if (dirty.current && !conflictFenced.current) {
          timer.current = window.setTimeout(() => void drain(), 0);
        }
        return;
      }
      // Transport/unknown failures do not tell us whether the server accepted
      // anything. Preserve the exact local draft and make retry explicit.
      dirty.current = true;
      if (mounted.current) setMessage("Could not save this thought. Your changes are still here. Retry save.");
    }
  };
  const schedule = (delay = 450) => {
    if (conflictFenced.current || inFlight.current) return;
    clearTimer();
    timer.current = window.setTimeout(() => void drain(), delay);
  };

  useEffect(() => {
    if (thought.id !== current.current.id || thought.aggregate_revision > current.current.aggregate_revision) {
      installAuthoritative(thought, { fence: true, notify: false });
    }
  }, [thought]);
  useEffect(() => () => { mounted.current = false; clearTimer(); }, []);

  const edit = (next: Partial<Draft>) => {
    draft.current = { ...draft.current, ...next };
    dirty.current = true;
    conflictFenced.current = false;
    setMessage("");
    schedule();
  };
  const retry = () => {
    if (inFlight.current || conflictFenced.current) return;
    dirty.current = true;
    setMessage("");
    schedule(0);
  };

  return <>
    <StringGadget label="Title" value={title} onChange={(next) => { setTitle(next); edit({ title: next }); }} />
    <DeskEditor value={body} placeholder="Write" autoFocus onChange={(next) => { setBody(next); edit({ body: next }); }} />
    <StringGadget label="Tags" value={tags} onChange={(next) => { setTags(next); edit({ tags: next }); }} />
    {message ? <p role="status" className="surface-receipt-line">{message} {message.includes("Retry save") ? <button type="button" className="desk-chip quiet" onClick={retry}>Retry save</button> : null}</p> : null}
  </>;
}
