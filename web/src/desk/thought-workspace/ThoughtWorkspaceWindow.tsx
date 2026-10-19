import { publishThoughtDraft, seatThoughtDraft, useThoughtDraftWords } from "../thoughtDrafts";
import { windowName } from "../windowName";
import { NEW_THOUGHT_TITLE } from "../thoughtTitle";
import { useCallback, useEffect, useRef, useState, type RefObject } from "react";
import { ApiError, readableError } from "../../lib/api";
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import { onReturnToTask } from "../returnToTask";
import {
  actOnReview,
  NOTE_GREW_EVENT,
  stopRefinement,
  type Thought,
  type ThoughtAppendEffect,
  type ThoughtWorkspaceProjection,
} from "../thoughts";
import type { WorldObject } from "../world";
import { Button } from "../../components/signal/Signal";
import { PadGadget, RunLine, ScrollHint, SurfaceFooter } from "../surface";
import { NoteOutcomesWell, useNoteOutcomes } from "./NoteOutcomesWell";
import { DeskWindowFrame } from "../components/DeskWindow";
import { ThoughtSaveFault, useThoughtNoteWriter } from "../pullouts/editors/useThoughtNoteWriter";
import { ThoughtDocumentPane } from "./ThoughtDocumentPane";
import { latchAskSelection } from "../ask";
import { ProjectWell } from "./ProjectWell";
import { useThoughtWorkspaceController } from "./useThoughtWorkspaceController";
import { NoteSendWells } from "../documentSendsLazy";
import { SEND_OPEN, useAnnounceWindowDocument } from "../windowSend";
import { useWindowId } from "../components/window/windowIdContext";
import { thoughtWriteLine } from "./thoughtReceipt";
import "./thought-workspace.css";

const workspaceRequestIds = new Map<string, string | null>();
function stableId(key: string): string {
  let id = workspaceRequestIds.get(key);
  if (!workspaceRequestIds.has(key)) {
    try { id = sessionStorage.getItem(key) || id; } catch { /* Memory owns this retry. */ }
  }
  if (!id) id = crypto.randomUUID();
  workspaceRequestIds.set(key, id);
  try { sessionStorage.setItem(key, id); } catch { /* Memory owns this retry. */ }
  return id;
}
function clearStableId(key: string) {
  workspaceRequestIds.set(key, null);
  try { sessionStorage.removeItem(key); workspaceRequestIds.delete(key); } catch { /* Apply the accepted result. */ }
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
  registerClose,
  sending,
  setSending,
  onDone,
}: {
  initialThought: Thought;
  projection: ThoughtWorkspaceProjection;
  install: (projection: ThoughtWorkspaceProjection) => boolean;
  reload: (adoptRestartedHub?: boolean) => Promise<ThoughtWorkspaceProjection>;
  registerClose: (handler: () => Promise<boolean>) => () => void;
  sending: boolean;
  setSending: (sending: boolean) => void;
  /** Betterment Q8: Done closes the window (it saves first); nothing else. */
  onDone: () => void;
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
  const [actionWell, setActionWell] = useState<"project" | null>(null);
  const [selectedPassage, setSelectedPassage] = useState<{ from: number; to: number; text: string; body: string } | null>(null);
  const [actionPassage, setActionPassage] = useState<string | null>(null);
  const ignoreSelectionAfterEdit = useRef(false);
  const hasProjects = useDesk((state) => state.projects.some((project) => !project.is_archived));
  const winId = useWindowId();
  const [revealRange, setRevealRange] = useState<{ start: number; end: number; focus?: boolean } | null>(null);
  /* HS-176-04 — the answer well is a PadGadget (the voice law): the ref
     holds its <label> and the focus reaches the textarea inside it. */
  const answerRef = useRef<HTMLLabelElement | null>(null);
  const focusAnswer = () => answerRef.current?.querySelector("textarea")?.focus();
  const sendRef = useRef<HTMLButtonElement | null>(null);
  const noteWindowRef = useRef<HTMLDivElement | null>(null);
  const sendScrollRef = useRef<HTMLDivElement | null>(null);
  const focusDoor = (door: RefObject<HTMLButtonElement | null>) => {
    const frameRoot = noteWindowRef.current?.closest(".thought-workspace-window");
    const target = door.current ?? frameRoot?.querySelector<HTMLButtonElement>(".thought-note-foot button[aria-label='More actions']");
    target?.focus();
  };
  useEffect(() => {
    if (!sending) return;
    const frame = requestAnimationFrame(() => sendScrollRef.current?.focus());
    return () => cancelAnimationFrame(frame);
  }, [sending]);
  const wasSending = useRef(sending);
  useEffect(() => {
    const returning = wasSending.current && !sending;
    wasSending.current = sending;
    if (!returning) return;
    const frame = requestAnimationFrame(() => focusDoor(sendRef));
    return () => cancelAnimationFrame(frame);
  }, [sending]);
  const reloading = useRef(false);
  const writer = useThoughtNoteWriter({
    thought: documentThought,
    onThought: setDocumentThought,
    onProjection: install,
    locked: busy || documentThought.state !== "working",
    workspaceCursor: projection.workspace_cursor,
    onCursorConflict: () => reload(false),
  });

  // `Write a thought` asks this window if its draft has words, and saves it
  // before the next thought starts (thoughtDrafts.ts).
  const draftSeat = useRef<{ words: () => boolean; flush: () => Promise<unknown> }>({ words: () => false, flush: async () => undefined });
  draftSeat.current = {
    words: () => Boolean(writer.draft.body.trim()) || (writer.draft.title.trim() !== "" && writer.draft.title.trim() !== NEW_THOUGHT_TITLE),
    flush: () => writer.flush(),
  };
  const draftNoteId = documentThought.working_note.id;
  // Betterment Q9: Find the tasks; the rows stay with the note.
  const outcomes = useNoteOutcomes(draftNoteId);
  useEffect(() => {
    setSelectedPassage((current) => current && current.body === writer.draft.body ? current : null);
  }, [writer.draft.body]);
  useAnnounceWindowDocument({ kind: "note", id: draftNoteId });
  useEffect(() => seatThoughtDraft(draftNoteId, {
    words: () => draftSeat.current.words(),
    flush: () => draftSeat.current.flush(),
  }), [draftNoteId]);
  // The window's name follows the draft at once (windowName.ts).
  const shownTitle = writer.draft.title;
  const shownBody = writer.draft.body;
  const withdrawWords = useRef<() => void>(() => undefined);
  // The kept note is the writer's current saved record (it changes on each
  // save), never the record the window opened with.
  const keptBody = documentThought.working_note.body_markdown;
  useEffect(() => { withdrawWords.current = publishThoughtDraft(draftNoteId, { title: shownTitle, body: shownBody, keptBody }); }, [draftNoteId, shownTitle, shownBody, keptBody]);
  useEffect(() => () => withdrawWords.current(), [draftNoteId]);

  useEffect(() => {
    const onOpen = (event: Event) => {
      if ((event as CustomEvent<{ winId?: string }>).detail?.winId === winId) void openSend();
    };
    window.addEventListener(SEND_OPEN, onOpen);
    return () => window.removeEventListener(SEND_OPEN, onOpen);
  });

  /* Betterment Q8: Ask ▸ Add to note grew this note. A window with no
     unsaved words reads it again; one with unsaved words keeps them, and its
     next save shows CHANGED ELSEWHERE with Reload. */
  const reloadNoteRef = useRef<() => Promise<void>>(async () => undefined);
  useEffect(() => {
    const onGrew = (event: Event) => {
      if ((event as CustomEvent<{ noteId?: string }>).detail?.noteId !== draftNoteId) return;
      if (writer.dirty || writer.pending || writer.saving) return;
      void reloadNoteRef.current();
    };
    window.addEventListener(NOTE_GREW_EVENT, onGrew);
    return () => window.removeEventListener(NOTE_GREW_EVENT, onGrew);
  });

  useEffect(() => {
    if (projection.thought.id === documentThought.id && projection.thought.aggregate_revision > documentThought.aggregate_revision) {
      setDocumentThought(projection.thought);
    }
  }, [documentThought.aggregate_revision, documentThought.id, projection.thought]);

  useEffect(() => registerClose(async () => {
    if (busy) return false;
    setBusy(true); say("");
    try {
      await writer.flush({ fence: true });
      return true;
    } catch (cause) {
      sayFault(cause);
      writer.release();
      setBusy(false);
      return false;
    }
  }), [busy, registerClose, writer]);

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
    setSelectedPassage(null);
    setActionPassage(null);
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
      const result = await actOnReview({ thought: latest, reviewId, action: "answer", request_id: stableId(key), answer, workspace_cursor: writer.getWorkspaceCursor() ?? projection.workspace_cursor });
      clearStableId(key);
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

  const completed = documentThought.state === "completed" || projection.workspace_state === "completed";
  const running = ["reserved", "in_flight", "awaiting_projection"].includes(projection.workspace_state);
  /* Betterment Q8 (one note): "develop" is Ask about this, in the one Ask
     window. The band is left only for what an older thought still holds: a
     running turn (Stop), or its open question or draft (Add to note). */
  const askRow: { token: string; label: string; act: () => void } | null = !completed && running
    ? { token: "WORKING", label: "Stop", act: () => void stop() }
    : null;
  const open = Boolean(question || draftBody);
  const showAskBand = !completed && Boolean(open || askRow);

  const writeLine = thoughtWriteLine(writer);
  const unsaved = Boolean(writer.pending || writer.saving || writer.failed || writer.conflicted);
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
      setSelectedPassage(null);
      setActionPassage(null);
      setRevealRange(null);
      writer.edit({ title: note.title, body: note.body_markdown, tags: note.tags.join(", ") });
    } catch (cause) {
      sayFault(cause);
    } finally {
      reloading.current = false;
    }
  };
  reloadNoteRef.current = reloadNote;
  /* Betterment Q9: the extraction reads the stored note, so the sole writer
     saves first. */
  const findTasks = async () => {
    if (busy || outcomes.finding) return;
    setBusy(true); say("");
    try {
      await writer.flush({ fence: true });
    } catch (cause) { sayFault(cause); writer.release(); setBusy(false); return; }
    writer.release(); setBusy(false);
    await outcomes.find();
  };
  /* The well sends the stored note, so the sole writer saves first. */
  const openSend = async () => {
    if (busy) return;
    setBusy(true); say("");
    try {
      await writer.flush({ fence: true });
      setActionWell(null);
      setActionPassage(null);
      setSending(true);
    } catch (cause) { sayFault(cause); }
    finally { writer.release(); setBusy(false); }
  };
  const openActionWell = async (kind: "project") => {
    if (busy) return;
    setBusy(true); say("");
    try {
      const selected = selectedPassage;
      const latest = await writer.flush({ fence: true });
      setActionPassage(selected && selected.text.trim() && selected.body === latest.working_note.body_markdown ? selected.text : null);
      setActionWell((current) => current === kind ? null : kind);
    } catch (cause) { sayFault(cause); }
    finally { writer.release(); setBusy(false); }
  };
  const askFromNote = async () => {
    if (busy) return;
    setBusy(true); say("");
    try {
      const selected = selectedPassage;
      const latest = await writer.flush({ fence: true });
      const note = latest.working_note;
      const noteRef = `note:${note.id}`;
      // The floor can trim its icon selection while this Note is still open.
      // Ask owns the saved source and valid quote, independently of that set.
      latchAskSelection({
        noteRef,
        text: selected && selected.text.trim() && selected.body === note.body_markdown ? selected.text : "",
        source: { id: note.id, kind: "note", ref: noteRef, title: note.title || "Note" },
      });
      // Betterment Q5: Ask about this, with the note in About and its
      // selected text quoted in the question.
      useDesk.getState().askAbout([{ id: note.id, kind: "note", ref: noteRef, title: note.title || "Note" }]);
      say("Ask opened");
    } catch (cause) { sayFault(cause); }
    finally { writer.release(); setBusy(false); }
  };
  return <div ref={noteWindowRef} className="thought-note-window" onKeyDown={(event) => {
    if (sending) return;
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
    onDone();
  }}>
    {!sending ? <>
    <ThoughtDocumentPane
      noteId={documentThought.working_note.id}
      draft={writer.draft}
      onEdit={(patch) => {
        setRevealRange(null);
        if (patch.body !== undefined) {
          ignoreSelectionAfterEdit.current = true;
          setSelectedPassage(null);
          setActionPassage(null);
        }
        writer.edit(patch);
      }}
      disabled={busy || documentThought.state !== "working"}
      lockedReason={completed ? "FINISHED" : undefined}
      revealRange={revealRange}
      onSelectionChange={(selection) => {
        if (ignoreSelectionAfterEdit.current) {
          ignoreSelectionAfterEdit.current = false;
          setSelectedPassage(null);
          return;
        }
        setSelectedPassage(selection.text.trim()
          ? { from: selection.from, to: selection.to, text: selection.text, body: writer.draft.body }
          : null);
      }}
    />

    {showAskBand ? <section className="thought-note-ask" aria-label="Ask about this note">
      <div className="thought-note-ask-row">
        {askRow?.token ? <span className="surface-token" data-chip>{askRow.token}</span> : null}
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
    </section> : null}

    {message ? <p className="thought-note-line" role="status">
      {message}
      {messageVerb === "reload" ? <Button dense disabled={busy} onClick={() => void reloadNote()}>Reload</Button> : null}
    </p> : null}

    {outcomes.finding ? <RunLine phase="running" verb="Finding the tasks" startedAt={outcomes.startedAt} /> : null}
    {outcomes.failure ? <p className="thought-note-line" role="status">
      {outcomes.failure}
      <Button dense disabled={busy} onClick={() => void findTasks()}>Try again</Button>
    </p> : null}
    <NoteOutcomesWell outcomes={outcomes} />

    {actionWell === "project" ? <ProjectWell
      noteId={draftNoteId}
      onAdded={say}
      onClose={() => { setActionWell(null); setActionPassage(null); }}
    /> : null}

    <SurfaceFooter
      className="thought-note-foot"
      receipt={<>
        {/* PHILO-3-04: the receipt keeps its whole words and wraps; the
            library's wrap token ([data-wrap], surface-footer.css) lifts the
            one-line clip a plain foot receipt wears (B27). */}
        {writeLine ? <span className="surface-footer-receipt-line" role="status" data-wrap="" data-tone={writeLine.danger ? "danger" : undefined}>{writeLine.text}</span> : null}
      </>}
      verbs={<span className="surface-footer-verbs-group">
        {writer.conflicted
          ? <Button dense disabled={busy} onClick={() => void reloadNote()}>Reload</Button>
          : writer.failed ? <Button dense onClick={writer.retry}>Retry</Button> : null}
        {/* Betterment Q8 (one note): the foot is Ask about this, Find the
            tasks (Q9), Project ▾, Send… and Done. Add a note, Copy, Task (a
            paste of the whole note) and Finish / Resume left the face. */}
        <Button dense disabled={busy} onClick={() => void askFromNote()}>Ask about this</Button>
        <Button dense disabled={busy || outcomes.finding || !writer.draft.body.trim()} loading={outcomes.finding} onClick={() => void findTasks()}>Find the tasks</Button>
        {hasProjects ? <Button dense disabled={busy} aria-expanded={actionWell === "project"} onClick={() => void openActionWell("project")}>Project ▾</Button> : null}
        <Button ref={sendRef} dense disabled={busy} onClick={() => void openSend()}>Send…</Button>
        <Button variant="primary" className="thought-note-primary" disabled={busy} onClick={onDone}>Done</Button>
      </span>}
    />
    </> : <>
      <ScrollHint axis="y" scrollRef={sendScrollRef} className="thought-send-scroll">
        <div ref={sendScrollRef} className="thought-send-well" role="region" aria-label="Send note" tabIndex={-1} data-testid="thought-send" data-unsaved={unsaved || undefined}>
          {/* The writer stays mounted: only its saved revision can send. */}
          {unsaved ? <p className="thought-send-wait" role="status">
            <span className="surface-token" data-chip data-tone={writer.failed || writer.conflicted ? "danger" : undefined}>
              {writer.failed || writer.conflicted ? "NOT SAVED · SEND WAITS" : "SAVING… · SEND WAITS"}
            </span>
          </p> : null}
          <div className="thought-send-body" inert={unsaved} aria-hidden={unsaved || undefined}>
            <NoteSendWells id={draftNoteId} title={writer.draft.title || documentThought.working_note.title}
              version={documentThought.working_revision} />
          </div>
        </div>
      </ScrollHint>
      <SurfaceFooter
        className="thought-send-foot"
        receipt={message || writeLine?.danger ? <span className="surface-footer-receipt-line" role="status" data-wrap="" data-tone="danger">{message || writeLine?.text}</span> : null}
        verbs={<>
          <Button dense variant="ghost" onClick={() => setSending(false)}>Back</Button>
          {writer.conflicted
            ? <Button dense disabled={busy} onClick={() => void reloadNote()}>Reload</Button>
            : writer.failed ? <Button dense onClick={writer.retry}>Retry</Button> : null}
        </>}
      />
    </>}
  </div>;
}

export function ThoughtWorkspaceWindow({
  object,
  pulloutId,
  thought,
  origin,
  onClose,
}: {
  object: WorldObject;
  /** PHILO-13-05 — the id the store keeps for this card; defaults to `object.id`. */
  pulloutId?: string;
  thought: Thought;
  origin?: { x: number; y: number } | null;
  onClose: () => void;
}) {
  const controller = useThoughtWorkspaceController(thought);
  const [sending, setSending] = useState(false);
  const closeHandler = useRef<() => Promise<boolean>>(async () => true);
  const registerClose = useCallback((handler: () => Promise<boolean>) => {
    closeHandler.current = handler;
    return () => { if (closeHandler.current === handler) closeHandler.current = async () => true; };
  }, []);
  /* Betterment Q8: Done saves the note (the close guard) and closes the
     window. It changes no other state. */
  const done = async () => {
    if (await closeHandler.current()) onClose();
  };
  useEffect(() => {
    if (useDesk.getState().editingId === thought.working_note.id) useDesk.getState().closeEditor();
  }, [thought.working_note.id]);
  // The name of the thought: the owner's title, else its first words, else
  // `New thought`; from the draft on the glass when the window holds one.
  const words = useThoughtDraftWords(thought.working_note.id);
  const name = windowName({
    kind: "thought",
    title: words?.title ?? thought.working_note.title,
    body: words?.body ?? thought.working_note.body_markdown,
    keptBody: words?.keptBody ?? thought.working_note.body_markdown,
  }, thought.working_note.id);
  return <DeskWindowFrame
    id={`pullout:${pulloutId ?? object.id}`}
    glyph="▤"
    label={name}
    kindWord="Note"
    icon={<img src={spriteUrl("note", object.id)} alt="" width={24} height={24} />}
    title={name}
    className={`desk-pullout thought-workspace-window${sending ? " is-sending" : ""}`}
    minW={520}
    minH={sending ? 520 : 360}
    defaultW={520}
    defaultH={360}
    fitContent
    origin={origin}
    open
    beforeClose={() => closeHandler.current()}
    onClose={onClose}
    onBack={sending ? () => setSending(false) : undefined}
  >
    {controller.opening ? <div className="thought-workspace-opening" aria-busy="true"><span>Opening note…</span></div> : controller.error || !controller.projection ? <div className="thought-workspace-opening" role="alert"><span className="surface-token">Could not open. Note unchanged.</span><Button variant="primary" onClick={() => void controller.reload(true)}>Try again</Button></div> : <>
      <div className="thought-workspace-preserved" inert={controller.restartDetected} aria-hidden={controller.restartDetected || undefined}>
        <WorkspaceReady key={thought.id} initialThought={thought} projection={controller.projection} install={controller.install} reload={controller.reload} registerClose={registerClose} sending={sending} setSending={setSending} onDone={() => void done()} />
      </div>
      {controller.restartDetected ? <div className="thought-workspace-opening thought-workspace-restart" role="alert"><span className="surface-token">Hub restarted. Reload to continue.</span><Button variant="primary" onClick={() => void controller.reload(true)}>Reload note</Button></div> : null}
    </>}
  </DeskWindowFrame>;
}
