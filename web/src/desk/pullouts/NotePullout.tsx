import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Note pullout content (HS-117-15). */
import { useEffect, useRef, useState } from "react";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { Material } from "../surface/Material";
import { SurfaceState } from "../surface/Surface";
import { INLINE_EDITOR_CONTENT } from "./editors";
import { ThoughtNoteEditor, type ThoughtNoteEditorHandle } from "./editors/ThoughtNoteEditor";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import type { PulloutContentProps } from "./types";
import { adoptThought, completeThought, originalThought, resumeThought, sourceLabel, thoughtForNote, type NoteThoughtStatus, type Thought, type ThoughtCompletionReceipt, type ThoughtNote } from "../thoughts";
import { ApiError } from "../../lib/api";

export function NotePullout({ object: o }: PulloutContentProps) {
  const editing = useDesk((s) => s.editingId === o.id);
  const { openEditor, closeEditor } = useDesk.getState();
  if (o.ref.kind !== "note") return null;
  const ir = o.ref;
  const Content = INLINE_EDITOR_CONTENT[o.kind];
  const resourceRef = qualifiedRef(o.kind, o.id);
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  const [status, setStatus] = useState<NoteThoughtStatus | null>(null);
  const [original, setOriginal] = useState<Thought | null>(null);
  const [adopting, setAdopting] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [completionReceipt, setCompletionReceipt] = useState<ThoughtCompletionReceipt | null>(null);
  const [message, setMessage] = useState("");
  const [ownershipLookup, setOwnershipLookup] = useState<"pending" | "ready" | "error">("pending");
  const originalReveal = useRef<HTMLElement | null>(null);
  const thoughtEditor = useRef<ThoughtNoteEditorHandle | null>(null);
  const loadOwnership = async () => {
    setOwnershipLookup("pending"); setStatus(null); setOriginal(null); setMessage("");
    try { setStatus(await thoughtForNote(o.id)); setOwnershipLookup("ready"); }
    catch { setOwnershipLookup("error"); setMessage("Could not check thought ownership on this hub. This note is unchanged. Retry the check."); }
  };
  useEffect(() => {
    let live = true;
    setOwnershipLookup("pending"); setStatus(null); setOriginal(null); setMessage("");
    void thoughtForNote(o.id).then((next) => { if (live) { setStatus(next); setOwnershipLookup("ready"); } }).catch(() => { if (live) { setOwnershipLookup("error"); setMessage("Could not check thought ownership on this hub. This note is unchanged. Retry the check."); } });
    return () => { live = false; };
  }, [o.id]);
  const thought = status?.ownership === "thought" ? status.thought : null;
  // The pullout object is a navigation snapshot. Once custody resolves, the
  // aggregate DTO is the only authoritative working Note for reading/copying.
  const body = String(thought?.working_note.body_markdown ?? (status?.ownership === "ordinary" ? status.note.body_markdown : ir.bodyMarkdown) ?? "");
  const adopt = async () => {
    if (adopting) return;
    setAdopting(true); setMessage("");
    const key = `hs.thought.adopt.${o.id}`;
    const request_id = sessionStorage.getItem(key) || crypto.randomUUID();
    sessionStorage.setItem(key, request_id);
    try {
      const fresh = await thoughtForNote(o.id);
      if (fresh.ownership === "thought") {
        setStatus(fresh); useDesk.getState().openEditor(o.id); return;
      }
      const adopted = await adoptThought({ request_id, note_id: o.id,
        expected_source_content_sha256: fresh.source_precondition.content_sha256,
        expected_source_last_modified: fresh.source_precondition.last_modified });
      sessionStorage.removeItem(key); setStatus({ ownership: "thought", thought: adopted });
      await useDesk.getState().refresh(); useDesk.getState().openEditor(o.id);
    } catch (cause) {
      const payload = cause instanceof ApiError && cause.payload && typeof cause.payload === "object"
        ? cause.payload as { error?: unknown; note?: ThoughtNote; source_precondition?: { content_sha256: string; last_modified: string } } : null;
      // Only the adoption CAS response establishes that the source changed.
      // Install its fresh source precondition so the next explicit attempt is
      // against what the owner can actually see now.
      if (payload?.error === "note_adoption_conflict") {
        if (payload.note && payload.source_precondition) {
          setStatus({ ownership: "ordinary", note: payload.note, source_precondition: payload.source_precondition });
          setOwnershipLookup("ready");
        }
        setMessage("This note changed elsewhere. Review the latest version, then develop it.");
        return;
      }
      // A committed response can be lost.  Ask the ownership projection before
      // naming this a failure so a retry never manufactures a second thought.
      try {
        const recovered = await thoughtForNote(o.id);
        if (recovered.ownership === "thought") { setStatus(recovered); sessionStorage.removeItem(key); useDesk.getState().openEditor(o.id); return; }
        setStatus(recovered); setOwnershipLookup("ready");
      } catch {
        // The commit might have landed, or the owner may be offline. Retain
        // the id but make neither claim until ownership can be read again.
        setMessage("We couldn't confirm whether this was saved. Retry developing it.");
        return;
      }
      setMessage("This note is unchanged and still here. Retry developing it.");
    } finally { setAdopting(false); }
  };
  const showOriginal = async () => {
    if (!thought || original) return;
    try { setOriginal(await originalThought(thought.id)); }
    catch { setMessage("Could not open the original on this hub. The working note is unchanged. Retry opening the original."); }
  };
  const complete = async () => {
    if (!thought || finishing || thought.state !== "working") return;
    // YOLO by default: this is the owner's immediate command, never a confirm.
    setFinishing(true); setMessage("");
    const key = `hs.thought.complete.${thought.id}`;
    const request_id = sessionStorage.getItem(key) || crypto.randomUUID();
    sessionStorage.setItem(key, request_id);
    try {
      const latest = editing && thoughtEditor.current ? await thoughtEditor.current.flush() : thought;
      const completed = await completeThought({ thought: latest, request_id });
      sessionStorage.removeItem(key);
      setStatus({ ownership: "thought", thought: completed.thought });
      setCompletionReceipt(completed.receipt);
      closeEditor();
    } catch (cause) {
      const payload = cause instanceof ApiError && cause.payload && typeof cause.payload === "object"
        ? cause.payload as { error?: string; context?: { current?: Thought } } : null;
      const current = payload?.context?.current;
      if (current?.id === thought.id) setStatus({ ownership: "thought", thought: current });
      if (payload?.error === "thought_already_completed" || payload?.error === "thought_completed") {
        closeEditor(); setMessage("This thought is already done.");
      } else if (payload?.error === "thought_revision_conflict") {
        setMessage("This thought changed elsewhere. Your latest version is shown. Review it, then try Good enough again.");
      } else if (String(cause).includes("thought save conflict")) {
        setMessage("This thought changed elsewhere. Your latest version is shown. Review it, then try Good enough again.");
      } else if (String(cause).includes("thought save failed")) {
        // The editor still owns its retained draft and Retry save truth. No
        // completion request was made, so do not invent ambiguity about it.
      } else {
        if (payload?.error === "completion_request_payload_mismatch" || payload?.error === "completion_request_superseded") {
          sessionStorage.removeItem(key);
          setMessage("That earlier completion request is no longer current. Review this thought, then press Good enough again.");
          return;
        }
        setMessage("We couldn't confirm completion on this hub. Your thought is still here. Retry Good enough.");
      }
    } finally { setFinishing(false); }
  };
  const resume = async () => {
    if (!thought || finishing || thought.state !== "completed") return;
    setFinishing(true); setMessage("");
    try {
      const resumed = await resumeThought(thought);
      sessionStorage.removeItem(`hs.thought.complete.${thought.id}`);
      setStatus({ ownership: "thought", thought: resumed }); setCompletionReceipt(null); openEditor(o.id);
    }
    catch (cause) {
      const payload = cause instanceof ApiError && cause.payload && typeof cause.payload === "object" ? cause.payload as { context?: { current?: Thought } } : null;
      if (payload?.context?.current?.id === thought.id) setStatus({ ownership: "thought", thought: payload.context.current });
      setMessage("This thought changed elsewhere. Your latest version is shown. Review it, then resume refining.");
    } finally { setFinishing(false); }
  };
  useEffect(() => {
    if (!original || !originalReveal.current) return;
    const reveal = originalReveal.current;
    reveal.scrollIntoView({ block: "nearest", behavior: "smooth" });
    // The reveal is announced for readers, but never takes a live text field
    // away from someone who is already editing this thought.
    const active = document.activeElement;
    const editingText = active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement
      || (active instanceof HTMLElement && active.isContentEditable);
    if (!editingText) reveal.focus({ preventScroll: true });
  }, [original]);

  return (
    <>
      <div className="desk-pullout-body desk-surface-body desk-editor-body">
        {thought ? <button type="button" className="desk-chip quiet" onClick={() => void showOriginal()}>
          Original kept · {sourceLabel(thought.source.kind)} · {new Date(thought.raw_captured_at).toLocaleString()}
        </button> : null}
        {original ? <section ref={originalReveal} className="surface-aerogel" aria-label="Original kept" aria-live="polite" tabIndex={-1}><strong>Original kept · {sourceLabel(original.source.kind)}</strong><pre className="thought-original-raw">{original.raw_text}</pre><button type="button" className="desk-chip quiet" onClick={() => setOriginal(null)}>Close original</button></section> : null}
        {message ? <p role="status" className="surface-receipt-line">{message}</p> : null}
        {editing && thought ? (
          <ThoughtNoteEditor ref={thoughtEditor} thought={thought} finishing={finishing} onThought={(next) => setStatus({ ownership: "thought", thought: next })} />
        ) : editing && Content ? (
          <Content object={o} onClose={closeEditor} />
        ) : body ? (
          <section>
            <Material>{body}</Material>
          </section>
        ) : (
          <section>
            <SurfaceState
              empty
              emptyLabel="Empty note"
              actionLabel="Start writing"
              onAction={() => openEditor(o.id)}
            />
          </section>
        )}
        {!editing && (
          <DeskFilingStrip
            objectRef={resourceRef}
            objectKind={o.kind}
            objectId={o.id}
          />
        )}
      </div>
      <SurfaceFooter receipt={editing ? null : completionReceipt ? <>Done</> : copyReceipt} verbs={editing && thought ? <div className="thought-completion-verbs">
        <button type="button" className="desk-chip quiet thought-completion-secondary" onClick={closeEditor}>Cancel</button>
        <button type="button" className="desk-chip is-primary thought-completion-primary" disabled={finishing} onClick={() => void complete()}>{finishing ? "Finishing…" : "Good enough"}</button>
      </div> : thought ? <>
        {thought.state === "completed" ? <>
          <div className="thought-completion-verbs"><button type="button" className="desk-chip quiet thought-completion-secondary" onClick={() => void copy(body)}>Copy</button>
          <button type="button" className="desk-chip is-primary thought-completion-primary" disabled={finishing} onClick={() => void resume()}>{finishing ? "Resuming…" : "Resume refining"}</button></div>
        </> : <>
          <div className="thought-completion-verbs"><button type="button" className="desk-chip quiet thought-completion-secondary" onClick={() => void copy(body)}>Copy</button>
          <button type="button" className="desk-chip quiet thought-completion-secondary" onClick={() => openEditor(o.id)}>Edit</button>
          <button type="button" className="desk-chip is-primary thought-completion-primary" disabled={finishing} onClick={() => void complete()}>{finishing ? "Finishing…" : "Good enough"}</button></div>
        </>}
      </> : ownershipLookup === "error" ? <>
        <button type="button" className="desk-chip is-primary" onClick={() => void loadOwnership()}>Retry checking this note</button>
      </> : ownershipLookup === "pending" ? null : <>
        <button
          type="button"
          className="desk-chip quiet"
          onClick={() => void copy(body)}
        >
          Copy
        </button>
        <button
          type="button"
          className="desk-chip quiet"
          onClick={() =>
            openSurfaceOr("dictate", "/dictation", resourceRef)
          }
        >
          Dictate about this
        </button>
        {status?.ownership === "ordinary" ? <button type="button" className="desk-chip is-primary" disabled={adopting} onClick={() => void adopt()}>{adopting ? "Developing…" : "Develop this thought"}</button> : null}
      </>} />
    </>
  );
}
