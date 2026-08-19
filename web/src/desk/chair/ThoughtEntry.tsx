import { useEffect, useRef, useState } from "react";
import { useDurableDraft } from "../../lib/durableDraft";
import { openSurfaceOr } from "../shell";
import { useDesk } from "../store";
import { createThought, sourceLabel, unfinishedThoughts, type UnfinishedThought } from "../thoughts";
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
  const [unfinished, setUnfinished] = useState<UnfinishedThought[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [resumeOpen, setResumeOpen] = useState(false);
  const [more, setMore] = useState(false);
  const [dictating, setDictating] = useState(false);
  const loaded = useRef(false);
  const stream = useRef<StreamSession | null>(null);

  const loadUnfinished = async (cursor?: string) => {
    const page = await unfinishedThoughts(cursor);
    setUnfinished((items) => cursor ? [...items, ...page.items] : page.items);
    setNextCursor(page.next_cursor);
  };
  useEffect(() => { if (!loaded.current) { loaded.current = true; void loadUnfinished().catch(() => undefined); } }, []);
  useEffect(() => () => { stream.current?.cancel(); stream.current = null; }, []);

  const start = async () => {
    if (!value.trim() || saving) return;
    setSaving(true); setMessage("");
    try {
      const raw = value.trim();
      const thought = await createThought({ request_id: requestId("hs.thought.compose.request"), raw_text: value,
        title: raw.split(/\r?\n/, 1)[0].slice(0, 80) || "Thought" });
      // The new thought now owns the next surface. Collapse the compact
      // capture controls before opening it so narrow Chair never stacks both.
      setComposing(false); setResumeOpen(false); setMore(false);
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
      <button type="button" className="btn btn--primary thought-entry-primary" onClick={() => setComposing(true)}>Develop a thought</button>
      {unfinished.length ? <button type="button" className="desk-chip quiet" onClick={() => setResumeOpen((open) => !open)}>Resume unfinished thoughts</button> : null}
      <button type="button" className="desk-chip quiet" onClick={() => setMore((open) => !open)}>More capture options</button>
      {more ? <div className="thought-entry-more"><button type="button" className="desk-chip quiet" onClick={() => openSurfaceOr("dictate", "/dictation")}>Open advanced capture</button></div> : null}
      {resumeOpen ? <div className="thought-resume" role="list">{unfinished.map((thought) => <button role="listitem" aria-label={`${sourceLabel(thought.source_kind)} thought ${thought.title || "Untitled thought"}`} type="button" className="thought-resume-row" key={thought.id} onClick={() => { setResumeOpen(false); useDesk.getState().openPullout(`note:${thought.working_note_id}`); }}><strong>{sourceLabel(thought.source_kind)} thought · {thought.title || "Untitled thought"}</strong><span>{thought.body_preview || "No text yet"}</span><time dateTime={thought.updated_at}>Updated {new Date(thought.updated_at).toLocaleString()}</time>{thought.filing_status === "missing" ? <em>This thought isn't in a drawer yet. Open it to choose where it belongs.</em> : null}</button>)}{nextCursor ? <button type="button" className="desk-chip quiet" onClick={() => void loadUnfinished(nextCursor)}>Show more</button> : null}</div> : null}
    </> : <>
      <label htmlFor="thought-compose">What are you working through?</label>
      <textarea id="thought-compose" value={value} onChange={(event) => setDraft(event.target.value)} autoFocus rows={5} />
      {message ? <p role="status" className="surface-receipt-line">{message}</p> : null}
      <div className="thought-entry-actions"><button type="button" className="btn btn--primary" disabled={!value.trim() || saving} onClick={() => void start()}>{saving ? "Starting…" : "Start developing"}</button><button type="button" className="desk-chip quiet" onClick={() => void dictate()} disabled={saving}>{dictating ? "Stop dictating" : "Dictate"}</button><button type="button" className="desk-chip quiet" onClick={() => setComposing(false)} disabled={saving || dictating}>Cancel</button></div>
    </>}
  </section>;
}
