import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Note pullout content (HS-117-15). */
import { useEffect, useRef, useState } from "react";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { Button } from "../../components/signal/Signal";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { Material } from "../surface/Material";
import { SurfaceState } from "../surface/Surface";
import { countToken } from "../surface/count";
import { INLINE_EDITOR_CONTENT } from "./editors";
import { ThoughtNoteEditor, type ThoughtNoteEditorHandle } from "./editors/ThoughtNoteEditor";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import type { PulloutContentProps } from "./types";
import { actOnReview, adoptThought, completeThought, detachThoughtContext, listThoughtContext, originalThought, reconcileThought, refineThought, refreshThoughtContext, resumeThought, reviewThought, sourceLabel, stopRefinement, thoughtForNote, type NoteThoughtStatus, type Thought, type ThoughtAttachment, type ThoughtCompletionReceipt, type ThoughtContextReceipt, type ThoughtDefaultApplicationReceipt, type ThoughtDefaultContext, type ThoughtDefaultContextReceipt, type ThoughtNote, type ThoughtReview, type ThoughtUsedContextReceipt } from "../thoughts";
import { apiFetch, ApiError } from "../../lib/api";
import { ThoughtContextPicker } from "./ThoughtContextPicker";

const REFINING_STATES = ["reserved", "in_flight", "awaiting_projection"];
function isRefining(state?: string): boolean { return !!state && REFINING_STATES.includes(state); }

function readableVersion(value: string): string {
  if (!value || /^version\b/i.test(value)) return value;
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : `version from ${date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
}

function ContextLeaves({ attachments }: { attachments: Array<Pick<ThoughtAttachment, "ref" | "leaves">> }) {
  const items = attachments.flatMap((a) =>
    a.leaves.map((leaf) => ({ key: `${a.ref}:${leaf.ref}`, title: leaf.title, ver: leaf.version_label })),
  );
  return <ul className="thought-context-leaves">{items.map((item) =>
    <li key={item.key}><span>{item.title}</span><small>{readableVersion(item.ver)}</small></li>,
  )}</ul>;
}

function UsedContext({ receipt }: { receipt: ThoughtUsedContextReceipt }) {
  const visCount = receipt.visible_count;
  const leafCount = receipt.leaf_count;
  return <details className="thought-used-context">
    <summary>{receipt.summary || `Used ${countToken(visCount, "context item", "context items") ?? "context"} · ${countToken(leafCount, "note", "notes") ?? "notes"}`}</summary>
    <ContextLeaves attachments={receipt.attachments || []} />
  </details>;
}

export function NotePullout({
  object: o,
  initialStatus,
  onThoughtOwned,
}: PulloutContentProps & {
  initialStatus?: NoteThoughtStatus;
  onThoughtOwned?: (thought: Thought) => void;
}) {
  const editing = useDesk((s) => s.editingId === o.id);
  const { openEditor, closeEditor } = useDesk.getState();
  if (o.ref.kind !== "note") return null;
  const ir = o.ref;
  const Content = INLINE_EDITOR_CONTENT[o.kind];
  const resourceRef = qualifiedRef(o.kind, o.id);
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  const [status, setStatus] = useState<NoteThoughtStatus | null>(initialStatus || null);
  const [original, setOriginal] = useState<Thought | null>(null);
  const [adopting, setAdopting] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [completionReceipt, setCompletionReceipt] = useState<ThoughtCompletionReceipt | null>(null);
  const [message, setMessage] = useState("");
  const [modelReady, setModelReady] = useState(false);
  const [review, setReview] = useState<ThoughtReview | null>(null);
  const [answer, setAnswer] = useState("");
  const [refining, setRefining] = useState(false);
  const [more, setMore] = useState(false);
  const [contextPicker, setContextPicker] = useState(false);
  const [contextBusy, setContextBusy] = useState(false);
  const [contextReceipt, setContextReceipt] = useState<ThoughtContextReceipt | null>(null);
  const [policyReceipt, setPolicyReceipt] = useState<{ summary: string; detail?: string } | null>(null);
  const [defaultApplicationReceipt, setDefaultApplicationReceipt] = useState<ThoughtDefaultApplicationReceipt | null>(null);
  const [defaultRefs, setDefaultRefs] = useState<Set<string>>(new Set());
  const [ownershipLookup, setOwnershipLookup] = useState<"pending" | "ready" | "error">(initialStatus ? "ready" : "pending");
  const originalReveal = useRef<HTMLElement | null>(null);
  const contextRow = useRef<HTMLDivElement | null>(null);
  const thoughtEditor = useRef<ThoughtNoteEditorHandle | null>(null);
  const latestThought = useRef<Thought | null>(null);
  const loadOwnership = async () => {
    setOwnershipLookup("pending"); setStatus(null); setOriginal(null); setMessage(""); setContextPicker(false); setContextReceipt(null); setPolicyReceipt(null); setDefaultApplicationReceipt(null);
    try { setStatus(await thoughtForNote(o.id)); setOwnershipLookup("ready"); }
    catch { setOwnershipLookup("error"); setMessage("Could not check thought ownership on this hub. This note is unchanged. Retry the check."); }
  };
  useEffect(() => {
    if (initialStatus) {
      setStatus(initialStatus);
      setOwnershipLookup("ready");
      return;
    }
    let live = true;
    setOwnershipLookup("pending"); setStatus(null); setOriginal(null); setMessage(""); setContextPicker(false); setContextReceipt(null); setPolicyReceipt(null); setDefaultApplicationReceipt(null);
    void thoughtForNote(o.id).then((next) => { if (live) { setStatus(next); setOwnershipLookup("ready"); } }).catch(() => { if (live) { setOwnershipLookup("error"); setMessage("Could not check thought ownership on this hub. This note is unchanged. Retry the check."); } });
    return () => { live = false; };
  }, [initialStatus, o.id]);
  const thought = status?.ownership === "thought" ? status.thought : null;
  useEffect(() => { if (thought) onThoughtOwned?.(thought); }, [onThoughtOwned, thought]);
  useEffect(() => { latestThought.current = thought; }, [thought]);
  useEffect(() => {
    if (!thought || thought.state !== "working") return;
    let live = true;
    void listThoughtContext(thought.id).then((listing) => {
      if (live) setDefaultRefs(new Set(listing.default_context.refs));
    }).catch(() => undefined);
    return () => { live = false; };
  }, [thought?.id, thought?.attachment_revision]);
  useEffect(() => {
    if (!thought) return;
    const key = `hs.thought.default-context-receipt.${thought.id}`;
    const stored = sessionStorage.getItem(key);
    if (!stored) return;
    sessionStorage.removeItem(key);
    try {
      const receipt = JSON.parse(stored) as ThoughtDefaultApplicationReceipt;
      setDefaultApplicationReceipt(receipt);
      if (receipt.status === "applied") setDefaultRefs(new Set(receipt.attachments.map((item) => item.ref)));
    }
    catch { /* A broken transient receipt is not authority and is safe to omit. */ }
  }, [thought?.id]);
  useEffect(() => {
    let live = true;
    // Refinement is deliberately pinned to the global local destination; a
    // ready paired/profile model must never make this control appear.
    void apiFetch<{ models?: Array<{ id?: string; ready?: boolean }> }>("/api/models").then((value) => { if (live) setModelReady(Array.isArray(value.models) && value.models.some((model) => model.id === "this_machine" && model.ready === true)); }).catch(() => { if (live) setModelReady(false); });
    return () => { live = false; };
  }, []);
  useEffect(() => {
    const continuity = thought?.continuity;
    if (!thought || !continuity?.invocation_id || !isRefining(continuity.state)) return;
    const timer = window.setInterval(() => {
      const current = latestThought.current;
      if (current?.id === thought.id) void reconcileThought(current, continuity.invocation_id).then((next) => setStatus({ ownership: "thought", thought: next })).catch(() => undefined);
    }, 900);
    return () => window.clearInterval(timer);
  }, [thought?.id, thought?.aggregate_revision, thought?.continuity?.state, thought?.continuity?.invocation_id]);
  useEffect(() => {
    if (!thought?.continuity?.review_result_id || thought.continuity.state !== "review_ready") { setReview(null); return; }
    void reviewThought(thought, thought.continuity.review_result_id).then(setReview).catch(() => setMessage("The refinement result could not be reviewed. Your working note is unchanged. Try again or finish instead."));
  }, [thought?.id, thought?.continuity?.review_result_id, thought?.continuity?.state]);
  useEffect(() => {
    const continuity = thought?.continuity;
    if (continuity?.state !== "named_failure" || !continuity.code) return;
    if (/^(owner_|thought_)/.test(continuity.code)) return;
    setMessage("Could not get a useful question. Your working note is unchanged. You can try again or finish instead.");
  }, [thought?.id, thought?.continuity?.state, thought?.continuity?.code]);
  // The pullout object is a navigation snapshot. Once custody resolves, the
  // aggregate DTO is the only authoritative working Note for reading/copying.
  const body = String(thought?.working_note.body_markdown ?? (status?.ownership === "ordinary" ? status.note.body_markdown : ir.bodyMarkdown) ?? "");
  const attachments = thought?.attachments || [];
  const staleAttachment = attachments.find((attachment) => attachment.state !== "current") || null;
  const applyContextResult = (result: { thought: Thought; receipt: ThoughtContextReceipt }) => {
    setStatus({ ownership: "thought", thought: result.thought });
    setContextReceipt(result.receipt);
    setPolicyReceipt(null);
    setReview(null);
  };
  const applyDefaultResult = (result: { default_context: ThoughtDefaultContext; receipt: ThoughtDefaultContextReceipt }) => {
    const names = result.receipt.selections.map((selection) => selection.title);
    setPolicyReceipt(result.receipt.refs.length
      ? { summary: `Used ${names.join(" + ")} for new Thoughts`, detail: "Existing Thoughts are unchanged." }
      : { summary: "New Thoughts start with no AI context. This Thought is unchanged." });
    setContextReceipt(null);
    setDefaultRefs(new Set(result.default_context.refs));
  };
  useEffect(() => {
    if (contextReceipt) contextRow.current?.focus();
  }, [contextReceipt, policyReceipt]);
  const openContextPicker = async () => {
    if (!thought || contextBusy) return;
    if (editing && thoughtEditor.current) {
      try {
        const latest = await thoughtEditor.current.flush();
        setStatus({ ownership: "thought", thought: latest });
      } catch {
        return;
      }
    }
    setContextPicker(true);
  };
  const closeContextPicker = () => {
    setContextPicker(false);
    requestAnimationFrame(() => contextRow.current?.focus());
  };
  const changeContext = async (action: "detach" | "refresh", attachment: ThoughtAttachment) => {
    if (!thought || contextBusy) return;
    setContextBusy(true); setMessage("");
    let base = thought;
    if (editing && thoughtEditor.current) {
      try { base = await thoughtEditor.current.flush(); }
      catch { setContextBusy(false); return; }
    }
    const key = `hs.thought.context.${action}.${base.id}.${attachment.ref}`;
    const requestId = sessionStorage.getItem(key) || crypto.randomUUID();
    sessionStorage.setItem(key, requestId);
    try {
      const result = action === "detach"
        ? await detachThoughtContext(base, attachment.ref, requestId)
        : await refreshThoughtContext(base, attachment.ref, requestId);
      sessionStorage.removeItem(key);
      applyContextResult(result);
      setContextPicker(false);
    } catch (cause) {
      const label = attachment.title || "That context";
      setMessage(cause instanceof ApiError ? cause.message : `${label} could not be ${action === "detach" ? "removed" : "updated"}. This Thought is unchanged. Try again.`);
    } finally { setContextBusy(false); }
  };
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
      sessionStorage.removeItem(key); setStatus({ ownership: "thought", thought: adopted.thought });
      sessionStorage.setItem(`hs.thought.default-context-receipt.${adopted.thought.id}`, JSON.stringify(adopted.default_context_receipt));
      setDefaultApplicationReceipt(adopted.default_context_receipt);
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
      void useDesk.getState().refresh().catch(() => undefined);
    } catch (cause) {
      const payload = cause instanceof ApiError && cause.payload && typeof cause.payload === "object"
        ? cause.payload as { error?: string; context?: { current?: Thought } } : null;
      const current = payload?.context?.current;
      if (current?.id === thought.id) setStatus({ ownership: "thought", thought: current });
      if (payload?.error === "thought_already_completed" || payload?.error === "thought_completed") {
        closeEditor(); setMessage("This thought is already done.");
      } else if (payload?.error === "thought_revision_conflict") {
        setMessage("This thought changed elsewhere. Your latest version is shown. Review it, then try Finish Thought again.");
      } else if (String(cause).includes("thought save conflict")) {
        setMessage("This thought changed elsewhere. Your latest version is shown. Review it, then try Finish Thought again.");
      } else if (String(cause).includes("thought save failed")) {
        // The editor still owns its retained draft and Retry save truth. No
        // completion request was made, so do not invent ambiguity about it.
      } else {
        if (payload?.error === "completion_request_payload_mismatch" || payload?.error === "completion_request_superseded") {
          sessionStorage.removeItem(key);
          setMessage("That earlier completion request is no longer current. Review this thought, then press Finish Thought again.");
          return;
        }
        setMessage("We couldn't confirm completion on this hub. Your thought is still here. Retry Finish Thought.");
      }
    } finally { setFinishing(false); }
  };
  const refine = async () => {
    if (!thought || refining) return;
    setRefining(true); setMessage("");
    const key = `hs.thought.refine.${thought.id}`;
    const requestId = sessionStorage.getItem(key) || crypto.randomUUID();
    sessionStorage.setItem(key, requestId);
    try { const next = await refineThought(thought, requestId); sessionStorage.removeItem(key); setStatus({ ownership: "thought", thought: next.thought }); }
    catch { setMessage("Could not start refining. Your working note is unchanged."); }
    finally { setRefining(false); }
  };
  const stop = async () => {
    const invocationId = thought?.continuity?.invocation_id;
    if (!thought || !invocationId || refining) return;
    setRefining(true);
    try { setStatus({ ownership: "thought", thought: await stopRefinement(thought, invocationId) }); setMessage("Stopped. Your working note is unchanged."); }
    catch { setMessage("Could not stop this request yet. Your working note is unchanged. Try again, or finish instead."); }
    finally { setRefining(false); }
  };
  const act = async (action: "answer" | "accept" | "reject") => {
    if (!thought || !review || refining || (action === "answer" && !answer.trim())) return;
    setRefining(true); setMessage("");
    const key = `hs.thought.review.${review.id}.${action}`;
    const requestId = sessionStorage.getItem(key) || crypto.randomUUID();
    sessionStorage.setItem(key, requestId);
    try { const result = await actOnReview({ thought, reviewId: review.id, action, request_id: requestId, answer }); sessionStorage.removeItem(key); setStatus({ ownership: "thought", thought: result.thought }); setReview(null); setAnswer(""); setMessage(action === "answer" ? "Answer added to your working note." : action === "accept" ? "Refinement accepted into your working note." : "Refinement dismissed."); }
    catch { setMessage("That review changed elsewhere. Your latest working note is shown."); }
    finally { setRefining(false); }
  };
  const resume = async () => {
    if (!thought || finishing || thought.state !== "completed") return;
    setFinishing(true); setMessage("");
    try {
      const resumed = await resumeThought(thought);
      sessionStorage.removeItem(`hs.thought.complete.${thought.id}`);
      setStatus({ ownership: "thought", thought: resumed }); setCompletionReceipt(null); openEditor(o.id);
      void useDesk.getState().refresh().catch(() => undefined);
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
        {thought ? (() => {
          const capturedAt = thought.raw_captured_at;
          return <Button variant="ghost" dense onClick={() => void showOriginal()}>
          Original kept · {sourceLabel(thought.source.kind)} · {new Date(capturedAt).toLocaleString()}
        </Button>; })() : null}
        {original ? (() => {
          const rawBody = original.raw_text;
          return <section ref={originalReveal} className="surface-aerogel" aria-label="Original kept" aria-live="polite" tabIndex={-1}><strong>Original kept · {sourceLabel(original.source.kind)}</strong><pre className="thought-original-raw">{rawBody}</pre><Button variant="ghost" dense onClick={() => setOriginal(null)}>Close original</Button></section>; })() : null}
        {message ? <p role="status" className="surface-receipt-line">{message}</p> : null}
        {thought?.state === "working" ? <div className="thought-context-wrap">
          <div ref={contextRow} className="thought-context-row" tabIndex={-1} role="region" aria-label="Thought context">
            <span className="thought-context-label">AI context</span>
            <div className="thought-context-current">
              {!attachments.length ? <span className="thought-context-none">None</span> : attachments.map((attachment) => {
                const leafCt = attachment.leaf_count;
                const isDefault = attachment.is_default;
                return <div key={attachment.ref} className="thought-context-item">
                <details className="thought-context-chip" data-state={attachment.state}>
                  <summary>{attachment.title}{countToken(leafCt, "note", "notes") ? ` · ${countToken(leafCt, "note", "notes")}` : null}{(isDefault || defaultRefs.has(attachment.ref)) ? <span className="thought-context-default-marker">Default</span> : null}</summary>
                  <ContextLeaves attachments={[attachment]} />
                  <div className="thought-context-chip-actions">
                    {attachment.state === "stale" ? <Button variant="ghost" dense disabled={contextBusy} onClick={() => void changeContext("refresh", attachment)}>Update context</Button> : null}
                    <Button variant="ghost" dense disabled={contextBusy} onClick={() => void changeContext("detach", attachment)}>Remove from this Thought</Button>
                  </div>
                </details>
                {attachment.state === "stale" ? <span className="thought-context-state">{attachment.title} changed</span> : null}
                {attachment.state === "missing" ? <span className="thought-context-state">{attachment.title} UNAVAILABLE</span> : null}
              </div>; })}
            </div>
            <Button variant="ghost" dense className="thought-context-attach" disabled={contextBusy} onClick={() => void openContextPicker()}>Attach</Button>
          </div>
          {contextReceipt ? (() => {
            const ctxChanged = contextReceipt.default_context_changed;
            const leafItems = (contextReceipt.leaves ?? []).map((leaf) => ({
              ref: leaf.ref, title: leaf.title, ver: leaf.version_label,
            }));
            return <details className="thought-context-action-receipt">
            <summary>{contextReceipt.action === "detach" && ctxChanged === false ? `Removed ${contextReceipt.title}; default unchanged` : `${contextReceipt.action === "attach" ? "Attached" : contextReceipt.action === "detach" ? "Removed" : "Updated"} ${contextReceipt.title}`}</summary>
            {leafItems.length ? <ul className="thought-context-leaves">{leafItems.map((item) => <li key={item.ref}><span>{item.title}</span><small>{readableVersion(item.ver)}</small></li>)}</ul> : null}
          </details>; })() : null}
          {policyReceipt ? <details className="thought-context-action-receipt"><summary>{policyReceipt.summary}</summary>{policyReceipt.detail ? <p>{policyReceipt.detail}</p> : null}</details> : null}
          {defaultApplicationReceipt?.status === "applied" ? <details className="thought-context-action-receipt"><summary>Attached by default</summary><span>{defaultApplicationReceipt.attachments.map((item) => item.title).join(" + ")}</span></details> : null}
          {defaultApplicationReceipt?.status === "not_applied" ? <details className="thought-context-action-receipt" open><summary>Default context not applied</summary><span>{defaultApplicationReceipt.failure?.selections.map((item) => item.title).join(" + ") || "Default AI context"}</span></details> : null}
          {contextPicker ? <ThoughtContextPicker thought={thought} anchor={contextRow.current} onApplied={applyContextResult} onDefaultApplied={applyDefaultResult} onClose={closeContextPicker} /> : null}
        </div> : null}
        {thought?.continuity && isRefining(thought.continuity.state) ? <p role="status" className="surface-receipt-line">Finding one useful question…</p> : null}
        {/* UX-CANON: needs redesign (HS-170-04) — raw textarea below */}
        {review?.kind === "question" ? (() => {
          const usedCtx = review.used_context;
          return <section className="surface-aerogel" aria-label="Refinement question"><strong>{review.question}</strong>{review.reason ? <span>{review.reason}</span> : null}{usedCtx ? <UsedContext receipt={usedCtx} /> : null}<label>Answer<textarea value={answer} onChange={(event) => setAnswer(event.target.value)} /></label></section>;
        })() : null}
        {review?.kind === "synthesis" ? (() => {
          const bodyMd = review.body_markdown;
          const usedCtx = review.used_context;
          return <section className="surface-aerogel" aria-label="Refinement suggestion"><strong>{review.title}</strong><Material>{bodyMd || ""}</Material>{usedCtx ? <UsedContext receipt={usedCtx} /> : null}</section>;
        })() : null}
        {more && thought ? <section className="surface-aerogel thought-more-menu" aria-label="More thought actions">
          {thought.continuity && isRefining(thought.continuity.state) ? <Button variant="ghost" dense disabled={finishing} onClick={() => void complete()}>Finish Thought</Button> : <><Button variant="ghost" dense onClick={() => void copy(body)}>Copy</Button><Button variant="ghost" dense onClick={() => openEditor(o.id)}>Edit working note</Button>{review ? <Button variant="ghost" dense disabled={refining} onClick={() => void act("reject")}>Reject</Button> : null}{thought.state === "working" ? <Button variant="ghost" dense disabled={finishing} onClick={() => void complete()}>Finish Thought</Button> : null}</>}
          <Button variant="ghost" dense onClick={() => setMore(false)}>Close more</Button>
        </section> : null}
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
      {/* UX-CANON: needs redesign (HS-170-04) — footer verb chain */}
      <SurfaceFooter receipt={editing ? null : completionReceipt ? <>Done</> : copyReceipt} verbs={editing && thought ? <div className="thought-completion-verbs">
        <Button variant="ghost" dense className="thought-completion-secondary thought-editor-cancel" onClick={closeEditor}>Cancel</Button>
        <Button variant="primary" dense className="thought-completion-primary" disabled={finishing} onClick={() => void complete()}>{finishing ? "Finishing…" : "Finish Thought"}</Button>
      </div> : editing ? <>
        <Button variant="ghost" dense onClick={closeEditor}>Cancel</Button>
        <Button variant="primary" dense onClick={closeEditor}>Save</Button>
      </> : thought ? <>
        {thought.state === "completed" ? <>
          <div className="thought-completion-verbs"><Button variant="ghost" dense className="thought-completion-secondary" onClick={() => void copy(body)}>Copy</Button>
          <Button variant="primary" dense className="thought-completion-primary" disabled={finishing} onClick={() => void resume()}>{finishing ? "Resuming…" : "Resume refining"}</Button></div>
        </> : thought.continuity && isRefining(thought.continuity.state) ? <div className="thought-completion-verbs"><Button variant="primary" dense className="thought-completion-primary" disabled={refining} onClick={() => void stop()}>{refining ? "Stopping…" : "Stop"}</Button><Button variant="ghost" dense className="thought-more" onClick={() => setMore(true)}>More</Button><Button variant="ghost" dense className="thought-completion-secondary" disabled={finishing} onClick={() => void complete()}>{finishing ? "Finishing…" : "Finish Thought"}</Button></div> : review?.kind === "question" ? <div className="thought-completion-verbs"><Button variant="primary" dense className="thought-completion-primary" disabled={refining || !answer.trim()} onClick={() => void act("answer")}>Answer</Button><Button variant="ghost" dense className="thought-review-direct" onClick={() => openEditor(o.id)}>Edit working note</Button><Button variant="ghost" dense className="thought-review-direct" disabled={refining} onClick={() => void act("reject")}>Reject</Button><Button variant="ghost" dense className="thought-completion-secondary" disabled={finishing} onClick={() => void complete()}>Finish Thought</Button><Button variant="ghost" dense className="thought-more" onClick={() => setMore(true)}>More</Button></div> : review?.kind === "synthesis" ? <div className="thought-completion-verbs">{staleAttachment ? <Button variant="primary" dense className="thought-completion-primary" disabled={contextBusy} onClick={() => void changeContext(staleAttachment.state === "missing" ? "detach" : "refresh", staleAttachment)}>{staleAttachment.state === "missing" ? "Remove it" : "Update context"}</Button> : <Button variant="primary" dense className="thought-completion-primary" disabled={refining} onClick={() => void act("accept")}>Accept</Button>}<Button variant="ghost" dense className="thought-review-direct" onClick={() => openEditor(o.id)}>Edit working note</Button><Button variant="ghost" dense className="thought-review-direct" disabled={refining} onClick={() => void act("reject")}>Reject</Button><Button variant="ghost" dense className="thought-completion-secondary" disabled={finishing} onClick={() => void complete()}>Finish Thought</Button><Button variant="ghost" dense className="thought-more" onClick={() => setMore(true)}>More</Button></div> : staleAttachment ? <div className="thought-completion-verbs"><Button variant="primary" dense className="thought-completion-primary" disabled={contextBusy} onClick={() => void changeContext(staleAttachment.state === "missing" ? "detach" : "refresh", staleAttachment)}>{staleAttachment.state === "missing" ? "Remove it" : "Update context"}</Button><Button variant="ghost" dense className="thought-completion-secondary" onClick={() => openEditor(o.id)}>Edit</Button><Button variant="ghost" dense className="thought-completion-secondary" disabled={finishing} onClick={() => void complete()}>Finish Thought</Button></div> : <>
          <div className="thought-completion-verbs"><Button variant="ghost" dense className="thought-completion-secondary" onClick={() => void copy(body)}>Copy</Button>
          <Button variant="ghost" dense className="thought-completion-secondary" onClick={() => openEditor(o.id)}>Edit</Button>
          <Button variant="ghost" dense className="thought-more" onClick={() => setMore(true)}>More</Button>
          {modelReady ? <Button variant="primary" dense className="thought-completion-primary" disabled={refining} onClick={() => void refine()}>{refining ? "Starting…" : "Ask AI"}</Button> : null}
          <Button variant={modelReady ? "ghost" : "primary"} dense className={modelReady ? "thought-completion-secondary" : "thought-completion-primary"} disabled={finishing} onClick={() => void complete()}>{finishing ? "Finishing…" : "Finish Thought"}</Button></div>
        </>}
      </> : ownershipLookup === "error" ? <>
        <Button variant="primary" dense onClick={() => void loadOwnership()}>Retry checking this note</Button>
      </> : ownershipLookup === "pending" ? null : <>
        <Button
          variant="ghost"
          dense
          onClick={() => void copy(body)}
        >
          Copy
        </Button>
        <Button
          variant="ghost"
          dense
          onClick={() =>
            openSurfaceOr("dictate", "/dictation", resourceRef)
          }
        >
          Dictate about this
        </Button>
        {status?.ownership === "ordinary" ? <Button variant="primary" dense disabled={adopting} onClick={() => void adopt()}>{adopting ? "Developing…" : "Develop this thought"}</Button> : null}
      </>} />
    </>
  );
}
