import { useEffect, useRef, useState } from "react";
import { ApiError, readableError } from "../../lib/api";
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { onReturnToTask, rememberTaskFocus } from "../returnToTask";
import {
  actOnReview,
  completeThought,
  detachThoughtContext,
  refineThought,
  refreshThoughtContext,
  resumeThought,
  stopRefinement,
  type Thought,
  type ThoughtAppendEffect,
  type ThoughtAttachment,
  type ThoughtWorkspaceProjection,
} from "../thoughts";
import type { WorldObject } from "../world";
import { Button } from "../../components/signal/Signal";
import { countToken, EgressChip, PadGadget, SurfaceFooter } from "../surface";
import { DeskWindowFrame } from "../components/DeskWindow";
import { ThoughtSaveFault, useThoughtNoteWriter } from "../pullouts/editors/useThoughtNoteWriter";
import { ThoughtDocumentPane } from "./ThoughtDocumentPane";
import { ThoughtReadsWell, type ReadsResult } from "./ThoughtReadsWell";
import { useThoughtWorkspaceController } from "./useThoughtWorkspaceController";
import { thoughtFilingLine, thoughtWriteLine } from "./thoughtReceipt";
import "./thought-workspace.css";

function stableId(key: string): string {
  const prior = sessionStorage.getItem(key);
  if (prior) return prior;
  const next = crypto.randomUUID();
  sessionStorage.setItem(key, next);
  return next;
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

/* HS-201-12 — the engine the ask would reach, read from the projection
   BEFORE dispatch (design condition 4).  `same_device` is the deployment
   revision's word for "here"; every other boundary names its own target,
   never a raw wire token (162's no-raw-ids law). */
function engineEgress(placement: ThoughtWorkspaceProjection["inference"]["intended_placement"]):
  { label: string; scope: "local" | "cloud" } | null {
  if (!placement) return null;
  if (placement.boundary === "same_device" || placement.target_kind === "this_device") {
    return { label: "THIS DEVICE", scope: "local" };
  }
  const name = (placement.target_name || "").trim();
  if (!name) return null;
  return { label: name.toUpperCase(), scope: placement.boundary === "private_network" ? "local" : "cloud" };
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
  const [messageVerb, setMessageVerb] = useState<"reload" | null>(null);
  /* One line at a time, and the verb belongs to the line that set it. */
  const say = (line: string) => { setMessage(line); setMessageVerb(null); };
  /* PHILO-3-04 — the writer's own refusal is stated by the foot (DID NOT
     SAVE / CHANGED ELSEWHERE), never again as prose on the message line. */
  const sayFault = (cause: unknown) => say(cause instanceof ThoughtSaveFault ? "" : readableError(cause));
  const [reads, setReads] = useState(false);
  const [revealRange, setRevealRange] = useState<{ start: number; end: number; focus?: boolean } | null>(null);
  /* HS-176-04 — the answer well is a PadGadget (the voice law): the ref
     holds its <label> and the focus reaches the textarea inside it. */
  const answerRef = useRef<HTMLLabelElement | null>(null);
  const focusAnswer = () => answerRef.current?.querySelector("textarea")?.focus();
  const readsRef = useRef<HTMLButtonElement | null>(null);
  const reloading = useRef(false);
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
    setBusy(true); say("");
    void writer.flush({ fence: true }).then(() => onClose()).catch((cause) => {
      sayFault(cause);
      writer.release();
      setBusy(false);
    });
  }), [busy, onClose, registerClose, writer]);

  useEffect(() => {
    if (!["reserved", "in_flight", "awaiting_projection"].includes(projection.workspace_state) || writer.dirty || writer.saving) return;
    const timer = window.setInterval(() => { void reload(false).catch(() => undefined); }, 900);
    return () => window.clearInterval(timer);
  }, [projection.workspace_state, reload, writer.dirty, writer.saving]);

  // HS-200-41: the one shared subscription (`desk/returnToTask.ts`).
  useEffect(() => {
    if (projection.inference.availability !== "unavailable") return;
    return onReturnToTask(() => { void reload(false).catch(() => undefined); });
  }, [projection.inference.availability, reload]);

  const installMutation = async (result: WorkspaceMutation, reveal: boolean) => {
    if (result.workbench && !install(result.workbench)) return false;
    setDocumentThought(result.thought);
    if (!result.workbench) await reload();
    const effect = appendEffect(result.receipt);
    const range = await verifiedReveal(result.thought, effect);
    if (effect && !range) {
      /* HS-201-12 CI fallout — a failure line carries what failed, the work
         that is kept, and the next action (`product_copy.py:406`), and the
         action is a REAL verb beside the line, never a word the owner
         cannot press. */
      setMessage("The answer is in the note, and your text is kept. Its exact place could not be checked. Reload the note.");
      setMessageVerb("reload");
      return true;
    }
    if (reveal && range) setRevealRange({ ...range, focus: false });
    return true;
  };

  const afterFlush = async (command: (latest: Thought) => Promise<WorkspaceMutation>, reveal = false) => {
    if (busy) return false;
    setBusy(true);
    say("");
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
      sayFault(cause);
      return false;
    } finally {
      writer.release();
      setBusy(false);
    }
  };

  const review = projection.review;
  const question = projection.workspace_state === "question" && review?.kind === "question" ? (review.question || "").trim() : "";
  const draft = projection.workspace_state === "synthesis" && review?.kind === "synthesis" ? review : null;
  const draftBody = (draft?.body_markdown || "").trim();

  /* HS-201-12 — one verb under the question: the answer joins the note.
     The chained turn ("Add & ask next") left this window with the settled
     design; `Ask` asks the next question when the owner wants one. */
  const addAnswer = async (): Promise<boolean> => {
    const reviewId = review?.id;
    if (!reviewId || !answer.trim()) return false;
    const key = `hs.thought.review.${reviewId}.answer`;
    const succeeded = await afterFlush(async (latest) => {
      const result = await actOnReview({ thought: latest, reviewId, action: "answer", request_id: stableId(key), answer, workspace_cursor: projection.workspace_cursor });
      sessionStorage.removeItem(key);
      return result;
    }, true);
    if (succeeded) setAnswer("");
    else requestAnimationFrame(() => focusAnswer());
    return succeeded;
  };

  /* HS-201-12 counsel round (Astra finding 1, a (b) defect) — a draft is
     APPENDED, never accepted: the hub's `accept` REPLACES title, body and
     tags (refinement_thought_service.py:1060), which would delete the
     owner's own words.  The append goes through the sole writer, and that
     durable edit supersedes the frozen review by itself ("owner_edited",
     refinement_thought_service.py:509), so the band folds with no second
     command.  The reveal lands on the appended range. */
  const addDraft = async (): Promise<boolean> => {
    const text = draftBody;
    if (!text || busy) return false;
    const body = writer.draft.body;
    const gap = !body ? "" : body.endsWith("\n\n") ? "" : body.endsWith("\n") ? "\n" : "\n\n";
    const next = `${body}${gap}${text}`;
    const start = body.length + gap.length;
    setBusy(true);
    say("");
    try {
      writer.edit({ body: next });
      const saved = await writer.flush({ fence: true });
      setDocumentThought(saved);
      setRevealRange({ start, end: next.length, focus: false });
      await reload(false).catch(() => undefined);
      return true;
    } catch (cause) {
      sayFault(cause);
      return false;
    } finally {
      writer.release();
      setBusy(false);
    }
  };

  const ask = () => afterFlush(async (latest) => {
    const key = `hs.thought.refine.${latest.id}`;
    const result = await refineThought(latest, stableId(key), projection.workspace_cursor);
    sessionStorage.removeItem(key);
    return result;
  });

  const keep = (fresh?: ThoughtWorkspaceProjection | null) => afterFlush(async (latest) => {
    /* The answer that just landed advanced BOTH the revisions and the
       workspace cursor; completing against the stale pair is the 409
       `workspace_cursor_conflict` Astra's probe recorded (finding 2). */
    const source = fresh?.thought ?? latest;
    const key = `hs.thought.complete.${source.id}`;
    const result = await completeThought({
      thought: source,
      request_id: stableId(key),
      workspace_cursor: fresh?.workspace_cursor ?? projection.workspace_cursor,
    });
    sessionStorage.removeItem(key);
    return result;
  });

  /* HS-201-12 (design condition 2) — Finish keeps in ONE gesture: a typed
     answer that is not in the note yet joins it first, then the Thought is
     kept.  No prompt, no second press. */
  const finish = async () => {
    if (!(question && answer.trim())) {
      await keep();
      return;
    }
    if (!await addAnswer()) return;
    await keep(await reload(false).catch(() => null));
  };

  const resume = () => afterFlush(async (latest) => ({ thought: await resumeThought(latest, projection.workspace_cursor) }));

  const stop = async () => {
    if (!projection.thought.continuity?.invocation_id || busy) return;
    setBusy(true); say("");
    try {
      const snapshot = await writer.pause();
      const invocation = snapshot.thought.continuity?.invocation_id;
      if (!invocation) throw new Error("The running turn is no longer available.");
      await stopRefinement(snapshot.thought, invocation, snapshot.workspaceCursor || projection.workspace_cursor);
      await reload();
      say("Stopped. The note did not change.");
    } catch (cause) { sayFault(cause); }
    finally { writer.resume(); setBusy(false); }
  };

  const repair = (attachment: ThoughtAttachment) => afterFlush(async (latest) => {
    const action = attachment.state === "missing" ? "detach" : "refresh";
    const key = `hs.thought.context.${action}.${latest.id}.${attachment.ref}`;
    const result = action === "detach"
      ? await detachThoughtContext(latest, attachment.ref, stableId(key), projection.workspace_cursor)
      : await refreshThoughtContext(latest, attachment.ref, stableId(key), projection.workspace_cursor);
    sessionStorage.removeItem(key);
    return result;
  });

  const setupAI = () => {
    // HS-200-41: remember the verb he left before the handoff, so the
    // Apply on the other side can send focus back here (design D2(a)).
    rememberTaskFocus();
    openSurfaceOr("configure-runs-on", "/settings", "models");
  };

  const attachments = documentThought.attachments || [];
  const stale = attachments.find((attachment) => attachment.state !== "current") || null;
  const completed = documentThought.state === "completed" || projection.workspace_state === "completed";
  const running = ["reserved", "in_flight", "awaiting_projection"].includes(projection.workspace_state);
  const placement = projection.inference.intended_placement;
  const engine = engineEgress(placement);
  const remoteEngine = Boolean(placement && placement.target_kind !== "this_device" && placement.boundary !== "same_device");
  const ready = projection.inference.availability === "ready";
  const open = Boolean(question || draftBody);

  // Band 3's one row: the state token and the ONE verb it owns.
  const askRow: { token: string; label: string; act: () => void } | null = completed
    ? null
    : running
      ? { token: "WORKING", label: "Stop", act: () => void stop() }
      : projection.workspace_state === "stale" && stale
        ? { token: stale.state === "missing" ? "CONTEXT MISSING" : "CONTEXT CHANGED", label: stale.state === "missing" ? "Remove it" : "Update it", act: () => void repair(stale) }
        : !ready
          /* HS-201-12 (design condition 5, corrected by Astra finding 4) —
             three truthful states, and the projection distinguishes all
             three: a READY target with unavailable inference is the
             coordinator, not the engine (refinement_application_service.py:80);
             THIS DEVICE is never unreachable, only missing its model
             (`_this_machine_readiness`, inference_targets.py:243); a target
             on another machine that is not ready cannot be reached. */
          ? placement?.readiness === "ready"
            ? { token: "ENGINE BUSY", label: "Try again", act: () => void ask() }
            : remoteEngine
              ? { token: "ENGINE NOT REACHABLE", label: "Check", act: setupAI }
              : { token: "NO ENGINE YET", label: "Choose an engine", act: setupAI }
          : projection.workspace_state === "named_failure"
            ? { token: "", label: projection.terminal_status?.retryable === false ? "Ask" : "Try again", act: () => void ask() }
            : open
              ? null
              : { token: "", label: "Ask", act: () => void ask() };

  const readsToken = attachments.length
    ? attachments.map((item) => {
      const count = countToken(item.leaf_count, "NOTE");
      const state = item.state === "current" ? "" : item.state === "missing" ? " · MISSING" : " · CHANGED";
      return `${item.title}${count ? ` · ${count}` : ""}${state}`;
    }).join(" · ")
    : "NOTHING";

  const writeLine = thoughtWriteLine(writer);
  /* Astra finding 4 — `writer.retry` returns during a conflict
     (useThoughtNoteWriter.ts:238), so "Try again" there was a verb that
     does nothing (A.11).  The honest verb re-reads the note: the hub's
     text replaces the draft through the sole writer, which also clears the
     conflict fence (`edit`, useThoughtNoteWriter.ts:213). */
  const reloadNote = async () => {
    /* A ref, not `busy`: `busy` raises the writer's command fence, and the
       fence would swallow the very `edit` that re-seats the note
       (useThoughtNoteWriter.ts:212). */
    if (busy || reloading.current) return;
    reloading.current = true;
    say("");
    try {
      const fresh = await reload(false);
      const note = fresh.thought.working_note;
      setDocumentThought(fresh.thought);
      setRevealRange(null);
      writer.edit({ title: note.title, body: note.body_markdown, tags: note.tags.join(", ") });
    } catch (cause) {
      sayFault(cause);
    } finally {
      reloading.current = false;
    }
  };
  /* The well writes against the workspace cursor, so the sole writer drains
     first — a dirty note under an attach is a cursor conflict (HS-141-05). */
  const openReads = async () => {
    if (reads) { setReads(false); return; }
    if (busy) return;
    setBusy(true); say("");
    try {
      await writer.flush({ fence: true });
      setReads(true);
    } catch (cause) { sayFault(cause); }
    finally { writer.release(); setBusy(false); }
  };
  const readsResult = (result: ReadsResult) => {
    setDocumentThought(result.thought);
    if (result.workbench) install(result.workbench);
    else void reload();
  };

  return <div className="thought-note-window" onKeyDown={(event) => {
    if (!(event.metaKey || event.ctrlKey) || event.nativeEvent.isComposing) return;
    if (event.key.toLowerCase() === "s") {
      event.preventDefault();
      if (busy) return;
      void writer.flush().catch((cause) => sayFault(cause));
      return;
    }
    if (event.key !== "Enter") return;
    event.preventDefault();
    if (busy) return;
    if (question && answer.trim()) { void addAnswer(); return; }
    if (draftBody) { void addDraft(); return; }
    askRow?.act();
  }}>
    <ThoughtDocumentPane
      draft={writer.draft}
      onEdit={(patch) => { setRevealRange(null); writer.edit(patch); }}
      disabled={busy || documentThought.state !== "working"}
      lockedReason={completed ? "FINISHED" : undefined}
      revealRange={revealRange}
    />

    {completed ? null : <section className="thought-note-ask" aria-label="One question">
      <div className="thought-note-ask-row">
        <span className="thought-note-ask-label">ONE QUESTION</span>
        {askRow?.token ? <span className="surface-token" data-chip>{askRow.token}</span> : null}
        {/* The destination before dispatch (A.9) — and never beside the
            no-engine token, which already says there is nowhere to go. */}
        {engine && (ready || remoteEngine) ? <EgressChip label={engine.label} scope={engine.scope} title={`The ask reaches ${engine.label}.`} /> : null}
        {askRow ? <Button dense disabled={busy} onClick={askRow.act}>{askRow.label}</Button> : null}
      </div>
      {projection.workspace_state === "named_failure" && projection.terminal_status?.message
        ? <p className="thought-note-ask-reason" role="status">{projection.terminal_status.message}</p> : null}
      {open ? <div className="thought-note-ask-open">
        {draftBody ? <span className="thought-note-ask-kicker">A draft from your note</span> : null}
        <p className="thought-note-ask-text">{question || draftBody}</p>
        {question ? <>
          <label ref={answerRef} className="thought-note-answer">
            <PadGadget label="Your answer" micLabel="Speak your answer" value={answer} onChange={setAnswer} rows={4} />
          </label>
          <div className="thought-note-ask-verbs">
            <Button dense disabled={busy || !answer.trim()} onClick={() => void addAnswer()}>Add to note</Button>
          </div>
        </> : <div className="thought-note-ask-verbs">
          <Button dense disabled={busy} onClick={() => void addDraft()}>Add to note</Button>
        </div>}
      </div> : null}
    </section>}

    {message ? <p className="thought-note-line" role="status">
      {message}
      {messageVerb === "reload" ? <Button dense disabled={busy} onClick={() => void reloadNote()}>Reload</Button> : null}
    </p> : null}

    {reads ? <ThoughtReadsWell
      thought={documentThought}
      cursor={projection.workspace_cursor}
      disabled={busy}
      onApplied={readsResult}
      onClose={() => { setReads(false); requestAnimationFrame(() => readsRef.current?.focus()); }}
    /> : null}

    <SurfaceFooter
      className="thought-note-foot"
      egress={<span className="thought-note-reads" title={`Reads ${readsToken}`}>READS · {readsToken}</span>}
      receipt={<>
        {writeLine ? <span className="surface-footer-receipt-line" role="status" data-tone={writeLine.danger ? "danger" : undefined}>{writeLine.text}</span> : null}
        <span className="surface-footer-receipt-line" data-line="filing">{thoughtFilingLine(documentThought, completed)}</span>
      </>}
      verbs={<>
        {writer.conflicted
          ? <Button dense disabled={busy} onClick={() => void reloadNote()}>Reload</Button>
          : writer.failed ? <Button dense onClick={writer.retry}>Retry</Button> : null}
        <Button ref={readsRef} dense aria-expanded={reads} disabled={busy} onClick={() => void openReads()}>Change</Button>
        {completed
          ? <Button variant="primary" className="thought-note-primary" disabled={busy} onClick={() => void resume()}>Resume</Button>
          : <Button variant="primary" className="thought-note-primary" disabled={busy} onClick={() => void finish()}>Finish</Button>}
      </>}
    />
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
    minW={560}
    minH={520}
    defaultW={820}
    defaultH={640}
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
