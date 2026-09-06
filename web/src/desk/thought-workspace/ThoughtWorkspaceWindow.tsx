import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { ApiError, readableError } from "../../lib/api";
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import {
  actOnReview,
  answerAndContinue,
  completeThought,
  detachThoughtContext,
  refineThought,
  refreshThoughtContext,
  resumeThought,
  stopRefinement,
  type Thought,
  type ThoughtAppendEffect,
  type ThoughtAttachment,
  type ThoughtContextReceipt,
  type ThoughtDefaultApplicationReceipt,
  type ThoughtWorkspaceActionKind,
  type ThoughtWorkspaceProjection,
} from "../thoughts";
import type { WorldObject } from "../world";
import { Button } from "../../components/signal/Signal";
import { countToken, PadGadget } from "../surface";
import { DeskWindowFrame } from "../components/DeskWindow";
import { ThoughtContextPicker } from "../pullouts/ThoughtContextPicker";
import { useThoughtNoteWriter } from "../pullouts/editors/useThoughtNoteWriter";
import { ThoughtDocumentPane } from "./ThoughtDocumentPane";
import { useThoughtWorkspaceController } from "./useThoughtWorkspaceController";
import "./thought-workspace.css";

function stableId(key: string): string {
  const prior = sessionStorage.getItem(key);
  if (prior) return prior;
  const next = crypto.randomUUID();
  sessionStorage.setItem(key, next);
  return next;
}

function useNarrowWorkspace(): boolean {
  const read = () => typeof matchMedia === "function" && matchMedia("(max-width: 720px)").matches;
  const [narrow, setNarrow] = useState(read);
  useEffect(() => {
    if (typeof matchMedia !== "function") return;
    const media = matchMedia("(max-width: 720px)");
    const update = () => setNarrow(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  return narrow;
}

function actionLabel(kind: ThoughtWorkspaceActionKind): string {
  switch (kind) {
    case "refine": return "Ask AI";
    case "configure_ai": return "Set up AI";
    case "stop_refinement": return "Stop";
    case "answer_and_continue": return "Add & ask next";
    case "answer_review": return "Add to Note";
    case "accept_review": return "Use this draft";
    case "refresh_context": return "Update context";
    case "detach_context": return "Remove it";
    case "complete": return "Finish Thought";
    case "resume": return "Resume";
    case "reject_review": return "Reject";
  }
}

export function utf8OffsetToIndex(value: string, byteOffset: number): number | null {
  if (byteOffset < 0) return null;
  let bytes = 0;
  let index = 0;
  for (const character of value) {
    if (bytes === byteOffset) return index;
    bytes += new TextEncoder().encode(character).length;
    index += character.length;
    if (bytes > byteOffset) return null;
  }
  return bytes === byteOffset ? index : null;
}

async function sha256(value: Uint8Array): Promise<string> {
  const source = new Uint8Array(value);
  const digest = await crypto.subtle.digest("SHA-256", source.buffer);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function verifiedReveal(thought: Thought, effect?: ThoughtAppendEffect): Promise<{ start: number; end: number } | null> {
  if (!effect || effect.thought_id !== thought.id || effect.working_revision !== thought.working_revision) return null;
  const bytes = new TextEncoder().encode(thought.working_note.body_markdown);
  if (effect.append_utf8_start < 0 || effect.append_utf8_end < effect.append_utf8_start || effect.append_utf8_end > bytes.length) return null;
  if (await sha256(bytes) !== effect.body_sha256) return null;
  if (await sha256(bytes.slice(0, effect.append_utf8_start)) !== effect.prior_body_sha256) return null;
  if (await sha256(bytes.slice(effect.append_utf8_start, effect.append_utf8_end)) !== effect.append_sha256) return null;
  const start = utf8OffsetToIndex(thought.working_note.body_markdown, effect.append_utf8_start);
  const end = utf8OffsetToIndex(thought.working_note.body_markdown, effect.append_utf8_end);
  return start === null || end === null ? null : { start, end };
}

function Placement({ projection }: { projection: ThoughtWorkspaceProjection }) {
  const placement = projection.review?.placement;
  if (!placement) {
    return projection.inference.intended_placement ? <span className="thought-placement intended surface-token">{projection.inference.intended_placement.target_name}</span> : null;
  }
  if (placement.state === "unavailable") return <span className="thought-placement surface-token">Placement unavailable</span>;
  const location = placement.egress.scope === "local" ? "Local" : placement.egress.host || placement.egress.scope;
  return <span className="thought-placement actual surface-token">{placement.actual_placement.target_name} · {location}</span>;
}

function UsedContext({ projection }: { projection: ThoughtWorkspaceProjection }) {
  const used = projection.review?.used_context;
  if (!used) return null;
  return <details className="thought-workspace-used-context"><summary>{used.summary}</summary><ul>{used.attachments.flatMap((attachment) => attachment.leaves.map((leaf) => <li key={`${attachment.ref}:${leaf.ref}`}>{leaf.title} <small>{leaf.version_label}</small></li>))}</ul></details>;
}

type WorkspaceMutation = {
  thought: Thought;
  workbench?: ThoughtWorkspaceProjection;
  receipt?: unknown;
};

function appendEffect(receipt: unknown): ThoughtAppendEffect | undefined {
  if (!receipt || typeof receipt !== "object") return undefined;
  const effect = (receipt as { effect?: unknown }).effect;
  return effect && typeof effect === "object" && (effect as { kind?: unknown }).kind === "clarification_appended"
    ? effect as ThoughtAppendEffect
    : undefined;
}

function WorkspaceReady({
  initialThought,
  projection,
  install,
  reload,
  onClose,
  registerClose,
}: {
  initialThought: Thought;
  projection: ThoughtWorkspaceProjection;
  install: (projection: ThoughtWorkspaceProjection) => boolean;
  reload: (adoptRestartedHub?: boolean) => Promise<ThoughtWorkspaceProjection>;
  onClose: () => void;
  registerClose: (handler: () => void) => () => void;
}) {
  const [documentThought, setDocumentThought] = useState(projection.thought || initialThought);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [tab, setTab] = useState<"note" | "interview">("note");
  const [picker, setPicker] = useState(false);
  const [pickerThought, setPickerThought] = useState<Thought | null>(null);
  const restoreContextFocus = useRef(false);
  const [contextReceipt, setContextReceipt] = useState<ThoughtContextReceipt | null>(null);
  const [defaultReceipt] = useState<ThoughtDefaultApplicationReceipt | null>(() => {
    const key = `hs.thought.default-context-receipt.${initialThought.id}`;
    const value = sessionStorage.getItem(key);
    if (!value) return null;
    sessionStorage.removeItem(key);
    try { return JSON.parse(value) as ThoughtDefaultApplicationReceipt; }
    catch { return null; }
  });
  const [revealRange, setRevealRange] = useState<{ start: number; end: number; focus?: boolean } | null>(null);
  const [inserted, setInserted] = useState(false);
  /* HS-176-04 — the answer well is a PadGadget (the voice law): the ref
     holds its <label> and the focus reaches the textarea inside it. */
  const answerRef = useRef<HTMLLabelElement | null>(null);
  const focusAnswer = () => answerRef.current?.querySelector("textarea")?.focus();
  const setupRef = useRef<HTMLButtonElement | null>(null);
  const contextRef = useRef<HTMLDivElement | null>(null);
  useLayoutEffect(() => {
    if (picker || !restoreContextFocus.current) return;
    restoreContextFocus.current = false;
    contextRef.current?.focus();
  }, [picker]);
  const narrow = useNarrowWorkspace();
  const writer = useThoughtNoteWriter({
    thought: documentThought,
    onThought: setDocumentThought,
    onProjection: install,
    locked: busy || documentThought.state !== "working",
    workspaceCursor: projection.workspace_cursor,
    onCursorConflict: () => reload(false),
  });

  useEffect(() => {
    if (projection.thought.id === documentThought.id && projection.thought.aggregate_revision > documentThought.aggregate_revision) {
      setDocumentThought(projection.thought);
    }
  }, [documentThought.aggregate_revision, documentThought.id, projection.thought]);

  useEffect(() => registerClose(() => {
    if (busy) return;
    setBusy(true); setMessage("");
    void writer.flush({ fence: true }).then(() => onClose()).catch((cause) => {
      setMessage(readableError(cause));
      writer.release();
      setBusy(false);
    });
  }), [busy, onClose, registerClose, writer]);

  useEffect(() => {
    if (!["reserved", "in_flight", "awaiting_projection"].includes(projection.workspace_state) || writer.dirty || writer.saving) return;
    const timer = window.setInterval(() => { void reload(false).catch(() => undefined); }, 900);
    return () => window.clearInterval(timer);
  }, [projection.workspace_state, reload, writer.dirty, writer.saving]);

  useEffect(() => {
    if (projection.inference.availability !== "unavailable") return;
    const recheck = () => { void reload(false).catch(() => undefined); };
    window.addEventListener("holdspeak:settings-updated", recheck);
    return () => window.removeEventListener("holdspeak:settings-updated", recheck);
  }, [projection.inference.availability, reload]);

  const installMutation = async (result: WorkspaceMutation, reveal: "note" | "marker" | "none" = "none") => {
    if (result.workbench && !install(result.workbench)) return false;
    setDocumentThought(result.thought);
    if (result.workbench) { /* installed above */ }
    else await reload();
    const effect = appendEffect(result.receipt);
    const range = await verifiedReveal(result.thought, effect);
    if (effect && !range) {
      setMessage("The answer was added, but its exact place in the Note could not be verified. Reload the workspace.");
      return true;
    }
    if (reveal === "note" && range) {
      setRevealRange(range);
      setTab("note");
      setMessage("Answer added to the Note");
    } else if (reveal === "marker" && range) {
      setRevealRange({ ...range, focus: false });
      setInserted(true);
      setMessage("");
    }
    return true;
  };

  const afterFlush = async (command: (latest: Thought) => Promise<WorkspaceMutation>, reveal: "note" | "marker" | "none" = "none") => {
    if (busy) return false;
    setInserted(false);
    setBusy(true);
    setMessage("");
    try {
      const latest = await writer.flush({ fence: true });
      return await installMutation(await command(latest), reveal);
    } catch (cause) {
      const payload = cause instanceof ApiError && cause.payload && typeof cause.payload === "object" ? cause.payload as { error?: string; code?: string; workbench?: ThoughtWorkspaceProjection; context?: { current?: unknown } } : null;
      const current = payload?.workbench || (payload?.context?.current && typeof payload.context.current === "object" && "workspace_cursor" in payload.context.current
        ? payload.context.current as ThoughtWorkspaceProjection
        : null);
      const code = payload?.code || payload?.error;
      if (current) {
        if (install(current)) setDocumentThought(current.thought);
      } else if (code === "workspace_cursor_conflict") {
        await reload(false).catch(() => undefined);
      }
      setMessage(code === "refinement_continuation_unavailable"
        ? "Couldn't start the next turn. Your answer is still here. Add it to the Note."
        : readableError(cause));
      return false;
    } finally {
      writer.release();
      setBusy(false);
    }
  };

  const answerReview = async (continueNext: boolean) => {
    const reviewId = projection.review?.id;
    if (!reviewId || !answer.trim()) return;
    const key = continueNext ? `hs.thought.answer-next.${reviewId}` : `hs.thought.review.${reviewId}.answer`;
    const succeeded = await afterFlush(async (latest) => {
      if (!continueNext) return actOnReview({ thought: latest, reviewId, action: "answer", request_id: stableId(key), answer, workspace_cursor: projection.workspace_cursor });
      const stored = sessionStorage.getItem(key);
      const payload = stored ? JSON.parse(stored) as Parameters<typeof answerAndContinue>[0] : {
        thought_id: latest.id,
        reviewId,
        command_id: crypto.randomUUID(),
        answer,
        expected_aggregate_revision: latest.aggregate_revision,
        expected_working_revision: latest.working_revision,
        expected_attachment_revision: latest.attachment_revision,
        workspace_cursor: projection.workspace_cursor,
      };
      if (!stored) sessionStorage.setItem(key, JSON.stringify(payload));
      return answerAndContinue(payload);
    }, continueNext ? "marker" : "note");
    if (succeeded) {
      setAnswer("");
      sessionStorage.removeItem(key);
    } else {
      requestAnimationFrame(() => focusAnswer());
    }
  };

  const ask = () => afterFlush(async (latest) => {
    const key = `hs.thought.refine.${latest.id}`;
    const result = await refineThought(latest, stableId(key), projection.workspace_cursor);
    sessionStorage.removeItem(key);
    return result;
  });
  const finish = () => afterFlush(async (latest) => {
    const key = `hs.thought.complete.${latest.id}`;
    const result = await completeThought({ thought: latest, request_id: stableId(key), workspace_cursor: projection.workspace_cursor });
    sessionStorage.removeItem(key);
    return result;
  });
  const resume = () => afterFlush(async (latest) => ({ thought: await resumeThought(latest, projection.workspace_cursor) }));
  const stop = async () => {
    if (!projection.thought.continuity?.invocation_id || busy) return;
    setInserted(false);
    setBusy(true); setMessage("");
    try {
      const snapshot = await writer.pause();
      const invocation = snapshot.thought.continuity?.invocation_id;
      if (!invocation) throw new Error("The running turn is no longer available.");
      await stopRefinement(snapshot.thought, invocation, snapshot.workspaceCursor || projection.workspace_cursor);
      await reload();
      setMessage("Stopped. Your Note is unchanged.");
    } catch (cause) { setMessage(readableError(cause)); }
    finally { writer.resume(); setBusy(false); }
  };
  const reviewAction = (action: "accept" | "reject") => {
    const reviewId = projection.review?.id;
    if (!reviewId) return;
    return afterFlush(async (latest) => {
      const key = `hs.thought.review.${reviewId}.${action}`;
      const result = await actOnReview({ thought: latest, reviewId, action, request_id: stableId(key), workspace_cursor: projection.workspace_cursor });
      sessionStorage.removeItem(key);
      return result;
    });
  };
  const repair = async (attachment: ThoughtAttachment) => {
    await afterFlush(async (latest) => {
      const action = attachment.state === "missing" ? "detach" : "refresh";
      const key = `hs.thought.context.${action}.${latest.id}.${attachment.ref}`;
      const result = action === "detach"
        ? await detachThoughtContext(latest, attachment.ref, stableId(key), projection.workspace_cursor)
        : await refreshThoughtContext(latest, attachment.ref, stableId(key), projection.workspace_cursor);
      sessionStorage.removeItem(key);
      setContextReceipt(result.receipt);
      return result;
    });
  };

  const primary = projection.actions.primary;
  const stale = documentThought.attachments?.find((attachment) => attachment.state !== "current") || null;
  const noteProxy = narrow && tab === "note" && projection.workspace_state === "question";
  const primaryKind = primary?.kind;
  const setupProxy = narrow && tab === "note" && primaryKind === "configure_ai";
  const primaryLabel = projection.workspace_state === "named_failure" && projection.terminal_status?.category === "retryable" && primaryKind === "refine"
    ? "Try again"
    : primaryKind ? actionLabel(primaryKind) : "Finish Thought";
  const primaryDisabled = busy || (!noteProxy && (primaryKind === "answer_review" || primaryKind === "answer_and_continue") && !answer.trim());
  const setupAI = () => {
    setMessage("Models opened. Choose where AI runs; this Thought will recheck automatically.");
    openSurfaceOr("configure-runs-on", "/settings", "models");
  };
  const invokePrimary = () => {
    if (noteProxy) { setTab("interview"); requestAnimationFrame(() => focusAnswer()); return; }
    if (setupProxy) { setTab("interview"); requestAnimationFrame(() => setupRef.current?.focus()); return; }
    switch (primaryKind) {
      case "refine": void ask(); break;
      case "configure_ai": setupAI(); break;
      case "stop_refinement": void stop(); break;
      case "answer_and_continue": void answerReview(true); break;
      case "answer_review": void answerReview(false); break;
      case "accept_review": void reviewAction("accept"); break;
      case "refresh_context": if (stale) void repair(stale); break;
      case "detach_context": if (stale) void repair(stale); break;
      case "complete": void finish(); break;
      case "resume": void resume(); break;
      default: break;
    }
  };

  const currentQuestion = projection.workspace_state === "question" && projection.review?.kind === "question";
  const continuationReady = projection.inference.continuation_admission === "ready";
  const attachments = documentThought.attachments || [];
  const openPicker = async () => {
    if (busy) return;
    setBusy(true); setMessage("");
    try {
      const latest = await writer.flush({ fence: true });
      setPickerThought(latest);
      setPicker(true);
    } catch (cause) { setMessage(readableError(cause)); }
    finally { writer.release(); setBusy(false); }
  };
  return <div className="thought-workspace-content" onKeyDown={(event) => {
    if (!(event.metaKey || event.ctrlKey) || event.nativeEvent.isComposing) return;
    if (event.key.toLowerCase() === "s") {
      event.preventDefault();
      if (busy) return;
      void writer.flush().then(() => setMessage("Saved")).catch((cause) => setMessage(readableError(cause)));
      return;
    }
    if (event.key !== "Enter") return;
    event.preventDefault();
    invokePrimary();
  }}>
    <nav className="thought-workspace-tabs" aria-label="Thought workspace panes">
      <Button variant="ghost" dense aria-current={tab === "note" ? "page" : undefined} onClick={() => setTab("note")}>Note</Button>
      <Button variant="ghost" dense aria-current={tab === "interview" ? "page" : undefined} onClick={() => setTab("interview")}>Interview{currentQuestion ? " 1" : ""}</Button>
    </nav>
    <div className="thought-workspace-main">
      <div className="thought-workspace-note-pane" hidden={narrow && tab !== "note"} aria-hidden={narrow && tab !== "note"} inert={narrow && tab !== "note"}>
        <ThoughtDocumentPane thoughtId={documentThought.id} draft={writer.draft} onEdit={(patch) => { setInserted(false); writer.edit(patch); }} disabled={busy || documentThought.state !== "working"} message={writer.message} onRetry={writer.retry} revealRange={revealRange} />
        {inserted && !narrow ? <Button variant="ghost" dense className="thought-inserted-marker thought-inserted-marker-note" onClick={() => setRevealRange((value) => value ? { ...value, focus: true } : value)}>Added to Note</Button> : null}
        <div className="thought-document-foot"><span>{documentThought.filing_status === "filed" ? "Filed" : "Not in a drawer"}</span><span>{writer.saving ? "Saving…" : "Saved"}</span></div>
      </div>
      <section className="thought-interview" aria-label="Interview" hidden={narrow && tab !== "interview"} aria-hidden={narrow && tab !== "interview"} inert={narrow && tab !== "interview"}>
        <header><span>Interview</span></header>
        <div className="thought-interview-body">
          {projection.workspace_state === "idle" ? projection.inference.availability === "unavailable"
            ? <div className="thought-interview-empty thought-interview-setup"><p className="thought-question-kicker">One quick setup</p><strong>AI needs a model</strong><span className="surface-token">Choose a model destination</span><Button ref={setupRef} variant="primary" className="thought-setup-ai" disabled={busy} onClick={setupAI}>Set up AI</Button><span className="thought-interview-run-hint surface-token">Opens Models settings</span></div>
            : <div className="thought-interview-empty"><p className="thought-question-kicker">Ready when you are</p><strong>Ask AI</strong><span className="surface-token">Reads your Note, asks one question</span><span className="thought-interview-run-hint surface-token"><b>Ask AI</b> or <kbd>⌘↵</kbd></span><Placement projection={projection} /></div> : null}
          {["reserved", "in_flight", "awaiting_projection"].includes(projection.workspace_state) ? <div role="status" className="thought-interview-working"><strong>Finding one useful question…</strong><span className="surface-token">Note v{projection.thought.working_revision}</span><p>Editing now will replace this question.</p></div> : null}
          {currentQuestion ? <div className="thought-question"><p className="thought-question-kicker">One thing to sharpen</p><h2>{projection.review?.question}</h2>{projection.review?.reason ? <p>{projection.review.reason}</p> : null}<Placement projection={projection} /><UsedContext projection={projection} /><label ref={answerRef}><span>Your answer</span><PadGadget label="Your answer" value={answer} onChange={setAnswer} rows={5} /></label>{continuationReady ? <Button variant="ghost" dense className="thought-add-quiet" disabled={busy || !answer.trim()} onClick={() => void answerReview(false)}>Add to Note</Button> : null}</div> : null}
          {projection.workspace_state === "synthesis" && projection.review?.kind === "synthesis" ? <div className="thought-synthesis"><p className="thought-question-kicker">A draft from your Note</p><h2>{projection.review.title}</h2><div className="thought-synthesis-body">{projection.review.body_markdown}</div><Placement projection={projection} /><UsedContext projection={projection} /><Button variant="ghost" dense className="thought-add-quiet" disabled={busy} onClick={() => void reviewAction("reject")}>Reject</Button></div> : null}
          {projection.workspace_state === "stale" ? <div className="thought-interview-exception"><strong>{stale?.state === "missing" ? `${stale.title} is no longer available.` : `${stale?.title || "AI context"} changed.`}</strong><span className="surface-token">Repair context to continue</span></div> : null}
          {projection.workspace_state === "named_failure" ? <div className="thought-interview-exception"><strong>That question did not land.</strong><span className="surface-token">{projection.terminal_status?.message || "Note unchanged. Try again or finish."}</span></div> : null}
          {projection.workspace_state === "completed" ? <div className="thought-interview-empty"><strong>Thought finished</strong><span className="surface-token">Finished. Resume any time.</span></div> : null}
          {inserted && narrow ? <Button variant="ghost" dense className="thought-inserted-marker" onClick={() => { setTab("note"); setRevealRange((value) => value ? { ...value, focus: true } : value); }}>Added to Note · View</Button> : null}
        </div>
      </section>
    </div>
    <div ref={contextRef} className="thought-workspace-context" tabIndex={-1} aria-label="AI context">
      <span>AI context</span><div className="thought-workspace-context-items">{attachments.length ? attachments.map((attachment) => <span key={attachment.ref}>{attachment.title}{countToken(attachment.leaf_count, "NOTE") ? ` · ${countToken(attachment.leaf_count, "NOTE")}` : ""}{attachment.is_default ? <small>Default</small> : null}</span>) : <strong>None</strong>}</div>
      <Button variant="ghost" dense disabled={busy} onClick={() => void openPicker()}>Attach</Button>
    </div>
    {contextReceipt ? <p className="thought-workspace-receipt" role="status">{contextReceipt.action === "attach" ? "Attached" : contextReceipt.action === "detach" ? "Removed" : "Updated"} {contextReceipt.title}</p> : null}
    {defaultReceipt?.status === "applied" ? <p className="thought-workspace-receipt" role="status">Default · {defaultReceipt.attachments.map((item) => item.title).join(" + ")}</p> : null}
    {defaultReceipt?.status === "not_applied" ? <p className="thought-workspace-receipt" role="alert">Default context skipped · {defaultReceipt.failure?.selections.map((item) => item.title).join(" + ") || "saved set"} unavailable</p> : null}
    {message ? <p className="thought-workspace-message" role="status">{message}</p> : null}
    <div className="thought-workspace-command">
      {projection.workspace_state !== "completed" && primaryKind !== "complete" ? <Button variant="ghost" className="thought-finish" disabled={busy} onClick={() => void finish()}>Finish Thought</Button> : <span />}
      {primaryKind === "configure_ai" && !setupProxy ? <span aria-hidden="true" /> : <Button variant="primary" className="thought-state-primary" disabled={primaryDisabled} onClick={invokePrimary}>{busy ? "Working…" : noteProxy ? "Answer question" : primaryLabel}</Button>}
    </div>
    {picker && pickerThought ? <ThoughtContextPicker thought={pickerThought} workspaceCursor={projection.workspace_cursor} anchor={contextRef.current} onApplied={(result) => { setDocumentThought(result.thought); setContextReceipt(result.receipt); if (result.workbench) install(result.workbench); else void reload(); }} onDefaultApplied={() => { setMessage("Default AI context updated for new Thoughts."); }} onClose={() => { restoreContextFocus.current = true; setPicker(false); setPickerThought(null); }} /> : null}
  </div>;
}

export function ThoughtWorkspaceWindow({
  object,
  thought,
  origin,
  onClose,
}: {
  object: WorldObject;
  thought: Thought;
  origin?: { x: number; y: number } | null;
  onClose: () => void;
}) {
  const controller = useThoughtWorkspaceController(thought);
  const closeHandler = useRef(onClose);
  closeHandler.current = onClose;
  const registerClose = (handler: () => void) => {
    closeHandler.current = handler;
    return () => { closeHandler.current = onClose; };
  };
  useEffect(() => {
    if (useDesk.getState().editingId === thought.working_note.id) useDesk.getState().closeEditor();
  }, [thought.working_note.id]);
  return <DeskWindowFrame
    id={`pullout:${object.id}`}
    glyph="▤"
    label="Thought"
    icon={<img src={spriteUrl("note", object.id)} alt="" width={24} height={24} />}
    title="Thought"
    className="desk-pullout thought-workspace-window"
    minW={860}
    minH={560}
    defaultW={1080}
    defaultH={680}
    origin={origin}
    open
    onClose={() => closeHandler.current()}
  >
    {controller.opening ? <div className="thought-workspace-opening" aria-busy="true"><span>Opening Thought…</span></div> : controller.error || !controller.projection ? <div className="thought-workspace-opening" role="alert"><span className="surface-token">Could not open. Note unchanged.</span><Button variant="primary" onClick={() => void controller.reload(true)}>Try again</Button></div> : <>
      <div className="thought-workspace-preserved" inert={controller.restartDetected} aria-hidden={controller.restartDetected || undefined}>
        <WorkspaceReady key={thought.id} initialThought={thought} projection={controller.projection} install={controller.install} reload={controller.reload} onClose={onClose} registerClose={registerClose} />
      </div>
      {controller.restartDetected ? <div className="thought-workspace-opening thought-workspace-restart" role="alert"><span className="surface-token">Hub restarted. Reload to continue.</span><Button variant="primary" onClick={() => void controller.reload(true)}>Reload Thought</Button></div> : null}
    </>}
  </DeskWindowFrame>;
}
