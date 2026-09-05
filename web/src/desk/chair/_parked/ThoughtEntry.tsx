// PARKED (HS-170-04)
import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { useDurableDraft } from "../../lib/durableDraft";
import { openSurfaceOr } from "../shell";
import { useDesk } from "../store";
import { createThought } from "../thoughts";
import { PadGadget } from "../surface/gadgets";
import { micStreamSupported, startStreamSession, type StreamSession } from "../../lib/micStreamSession";

function requestId(key: string): string {
  const prior = sessionStorage.getItem(key);
  if (prior) return prior;
  const next = crypto.randomUUID();
  sessionStorage.setItem(key, next);
  return next;
}

export function ThoughtEntry() {
  const { value, setDraft, clearPersisted } = useDurableDraft("thought-compose");
  const [composing, setComposing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [more, setMore] = useState(false);
  const [dictating, setDictating] = useState(false);
  const stream = useRef<StreamSession | null>(null);
  useEffect(() => () => { stream.current?.cancel(); stream.current = null; }, []);

  const start = async () => {
    if (!value.trim() || saving) return;
    setSaving(true); setMessage("");
    try {
      const raw = value.trim();
      const created = await createThought({ request_id: requestId("hs.thought.compose.request"), raw_text: value,
        title: raw.split(/\r?\n/, 1)[0].slice(0, 80) || "Thought" });
      const thought = created.thought;
      sessionStorage.setItem(`hs.thought.default-context-receipt.${thought.id}`, JSON.stringify(created.default_context_receipt));
      // The new thought now owns the next surface. Collapse the compact
      // capture controls before opening it so narrow Chair never stacks both.
      setComposing(false); setMore(false);
      clearPersisted(); sessionStorage.removeItem("hs.thought.compose.request");
      await useDesk.getState().refresh();
      useDesk.getState().openPullout(`note:${thought.working_note.id}`);
      useDesk.getState().openEditor(thought.working_note.id);
    } catch {
      setMessage("Your thought is still here. Retry.");
    } finally { setSaving(false); }
  };

  const dictate = async () => {
    const active = stream.current;
    if (active) {
      setDictating(false); stream.current = null;
      try {
        const transcript = await active.stop();
        if (transcript.trim()) setDraft((latest) => `${latest}${latest.trim() ? " " : ""}${transcript.trim()}`);
      } catch { setMessage("Dictation could not finish in this browser. Your draft is saved. Retry dictation or type instead."); }
      return;
    }
    if (!micStreamSupported()) { setMessage("Dictation is unavailable in this browser. Your draft is saved. Type your thought instead."); return; }
    setMessage("");
    try {
      stream.current = await startStreamSession((event) => {
        if (event.type === "error") setMessage(event.error);
      }, { retainScope: "thought-compose" });
      setDictating(true);
    } catch { setMessage("Could not start dictation in this browser. Your draft is saved. Retry dictation or type instead."); }
  };

  return <section className="thought-entry" data-testid="thought-entry">
    {!composing ? <>
      <Button variant="primary" className="thought-entry-primary" onClick={() => setComposing(true)}>Develop a thought</Button>
      <Button dense variant="ghost" onClick={() => setMore((open) => !open)}>More capture options</Button>
      {more ? <div className="thought-entry-more"><Button dense variant="ghost" onClick={() => openSurfaceOr("dictate", "/dictation")}>Open advanced capture</Button></div> : null}
    </> : <>
      <label htmlFor="thought-compose">What are you working through?</label>
      <PadGadget label="What are you working through?" value={value} onChange={(next) => setDraft(next)} rows={5} />
      {message ? <p role="status" className="surface-receipt-line">{message}</p> : null}
      <div className="thought-entry-actions"><Button variant="primary" disabled={!value.trim() || saving} onClick={() => void start()}>{saving ? "Starting…" : "Start developing"}</Button><Button dense variant="ghost" onClick={() => void dictate()} disabled={saving}>{dictating ? "Stop dictating" : "Dictate"}</Button><Button dense variant="ghost" onClick={() => setComposing(false)} disabled={saving || dictating}>Cancel</Button></div>
    </>}
  </section>;
}
