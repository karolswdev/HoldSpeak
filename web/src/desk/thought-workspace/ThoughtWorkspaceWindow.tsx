import { publishThoughtDraft, seatThoughtDraft, useThoughtDraftWords } from "../thoughtDrafts";
import { windowName } from "../windowName";
import { NEW_THOUGHT_TITLE } from "../thoughtTitle";
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type RefObject } from "react";
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
import { countWords, DotWord, PadGadget, ScrollHint, StatusBar, SurfaceFooter, ToolGlyph } from "../surface";
import { Material } from "../surface/Material";
import { useNoteOutcomes } from "./NoteOutcomesWell";
import { MarginNote, NoteMargin, type MarginCard } from "./NoteMargin";
import { dropMarginAsk, useMarginAsks, type MarginAsk } from "./marginAsks";
import { decisionLines, findLine, peopleNamed } from "./marginText";
import { DeskWindowFrame } from "../components/DeskWindow";
import { PULLOUT_SIZE } from "../pullouts/size";
import { ThoughtSaveFault, useThoughtNoteWriter } from "../pullouts/editors/useThoughtNoteWriter";
import { ThoughtDocumentPane } from "./ThoughtDocumentPane";
import type { DeskEditorHandle } from "../components/DeskEditor";
import { latchAskSelection } from "../ask";
import { ASK_RETURN_EVENT, takeAskReturn, validAskReturnRange } from "./askReturn";
import type { AskSelectionHandoff } from "../ask";
import { ProjectWell } from "./ProjectWell";
import { useThoughtWorkspaceController } from "./useThoughtWorkspaceController";
import { NoteSendWells } from "../documentSendsLazy";
import { SEND_OPEN, useAnnounceWindowDocument } from "../windowSend";
import { useWindowId } from "../components/window/windowIdContext";
import { useCompactViewport } from "../useCompactViewport";
import { thoughtStatusWords, thoughtWriteLine } from "./thoughtReceipt";
import { openDecisionRecord, openProjectRoomAtResource, openRef } from "../openObject";
import { openProjectRoom } from "../shell";
import type { ProjectReturn } from "../store/types";
import "./thought-workspace.css";

/** `Oct 24`: the day of the meeting a note came from. */
function shortDay(value: string): string {
  const at = new Date(value);
  return Number.isNaN(at.getTime()) ? "" : at.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/* Direction A (2026-10-27): the margin's closed state, per window. */
function readMarginClosed(key: string | null): boolean {
  if (!key) return false;
  try { return localStorage.getItem(key) === "closed"; } catch { return false; }
}
function writeMarginClosed(key: string | null, closed: boolean) {
  if (!key) return;
  try {
    if (closed) localStorage.setItem(key, "closed");
    else localStorage.removeItem(key);
  } catch { /* The margin still opens and closes in this window. */ }
}

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
  projectReturn,
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
  projectReturn?: ProjectReturn | null;
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
  /* Note canvas A, step 6: a Project this window filed the note in since
     the hub's last read (the next read names it too). */
  const [filedHere, setFiledHere] = useState<Array<{ id: string; name: string }>>([]);
  const [selectedPassage, setSelectedPassage] = useState<{ from: number; to: number; text: string; body: string } | null>(null);
  const [actionPassage, setActionPassage] = useState<string | null>(null);
  const ignoreSelectionAfterEdit = useRef(false);
  const hasProjects = useDesk((state) => state.projects.some((project) => !project.is_archived));
  const winId = useWindowId();
  const compact = useCompactViewport();
  const [revealRange, setRevealRange] = useState<{ start: number; end: number; focus?: boolean } | null>(null);
  const [returnRange, setReturnRange] = useState<{ from: number; to: number; body: string; scrollTop: number | null; nonce: number } | null>(null);
  const [changedReturn, setChangedReturn] = useState(0);
  const bodyEditorRef = useRef<DeskEditorHandle | null>(null);
  useLayoutEffect(() => {
    if (!changedReturn) return;
    // The receipt takes height from the Note. Read the live editor's caret
    // after that reflow; the Ask's captured range belongs to the old body.
    const restoreCurrentCaret = () => {
      const editor = bodyEditorRef.current;
      if (!editor) return false;
      const current = editor.getSelection();
      return editor.restoreSelection(current.from, current.to);
    };
    // A closed source can mount its CodeMirror view after the window's first
    // layout pass. Give that one frame to attach, without polling the body.
    if (restoreCurrentCaret()) return;
    const frame = requestAnimationFrame(restoreCurrentCaret);
    return () => cancelAnimationFrame(frame);
  }, [changedReturn]);
  /* HS-176-04 — the answer well is a PadGadget (the voice law): the ref
     holds its <label> and the focus reaches the textarea inside it. */
  const answerRef = useRef<HTMLLabelElement | null>(null);
  const focusAnswer = () => answerRef.current?.querySelector("textarea")?.focus();
  const sendRef = useRef<HTMLButtonElement | null>(null);
  const noteWindowRef = useRef<HTMLDivElement | null>(null);
  const sendScrollRef = useRef<HTMLDivElement | null>(null);
  const focusDoor = (door: RefObject<HTMLButtonElement | null>) => {
    const frameRoot = noteWindowRef.current?.closest(".thought-workspace-window");
    const target = door.current ?? frameRoot?.querySelector<HTMLButtonElement>(".thought-note-toolbar button[aria-label='More actions']");
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

  useEffect(() => {
    const applyReturn = (source: AskSelectionHandoff | null) => {
      if (!source) return;
      const savedBody = documentThought.working_note.body_markdown;
      const range = validAskReturnRange(source, `note:${draftNoteId}`, savedBody);
      if (source.body !== writer.draft.body || (source.range && !range)) {
        setReturnRange(null);
        say("SOURCE CHANGED");
        setChangedReturn((value) => value + 1);
        return;
      }
      say("");
      setRevealRange(null);
      if (range) setReturnRange({ ...range, body: source.body, scrollTop: source.scrollTop, nonce: Date.now() });
    };
    const onAskReturn = () => applyReturn(takeAskReturn(winId, `note:${draftNoteId}`));
    window.addEventListener(ASK_RETURN_EVENT, onAskReturn);
    applyReturn(takeAskReturn(winId, `note:${draftNoteId}`));
    return () => window.removeEventListener(ASK_RETURN_EVENT, onAskReturn);
  }, [documentThought.working_note.body_markdown, draftNoteId, winId, writer.draft.body]);

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
  const addDraft = (): Promise<boolean> => appendText(draftBody);
  /* Direction A: an Ask answer in the margin joins the note the same way,
     through the sole writer, at the note's end. */
  const appendText = async (words: string): Promise<boolean> => {
    const text = words.trim();
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
  /* Window grammar (2026-10-24): a running turn says Working in the status
     bar, with Stop as the bar's verb; the band is left for the open
     question or draft. */
  const working = !completed && running;
  const open = Boolean(question || draftBody);
  const showAskBand = !completed && open;

  const writeLine = thoughtWriteLine(writer);
  /* The status bar's relative words ("Saved just now") move on with the
     clock while the kept time is under an hour old. */
  const [clock, setClock] = useState(() => Date.now());
  const keptAge = writer.keptAt ? Date.now() - (Date.parse(writer.keptAt) || 0) : Infinity;
  useEffect(() => {
    if (!(keptAge < 3_600_000)) return;
    const timer = window.setInterval(() => setClock(Date.now()), 20_000);
    return () => window.clearInterval(timer);
  }, [keptAge < 3_600_000, writer.keptAt]); // eslint-disable-line react-hooks/exhaustive-deps
  const statusWords = thoughtStatusWords(writer, Math.max(clock, Date.now()));
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
      setReturnRange(null);
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
      const selected = bodyEditorRef.current?.getSelection() ?? null;
      const capturedBody = writer.draft.body;
      const sourceScrollTop = bodyEditorRef.current?.getScrollTop() ?? null;
      const latest = await writer.flush({ fence: true });
      const note = latest.working_note;
      const noteRef = `note:${note.id}`;
      const range = selected && capturedBody === note.body_markdown &&
        selected.from >= 0 && selected.to >= selected.from && selected.to <= note.body_markdown.length &&
        note.body_markdown.slice(selected.from, selected.to) === selected.text
        ? { from: selected.from, to: selected.to, text: selected.text } : null;
      // A failed digest must leave this Note here; Ask must never receive an
      // unpinned fallback after a successful writer flush.
      const bodySha256 = await sha256(new TextEncoder().encode(note.body_markdown));
      const desk = useDesk.getState();
      const requestNonce = (desk.askThread?.nonce ?? 0) + 1;
      // The floor can trim its icon selection while this Note is still open.
      // Ask owns the saved source and valid quote, independently of that set.
      latchAskSelection({
        noteRef,
        text: range?.text.trim() ? range.text : "",
        body: note.body_markdown,
        range,
        windowId: winId,
        scrollTop: sourceScrollTop,
        source: { id: note.id, kind: "note", ref: noteRef, title: note.title || "Note" },
        sourceSnapshot: { ref: noteRef, thought_id: latest.id, working_revision: latest.working_revision, body_sha256: bodySha256 },
        requestNonce,
        ...(projectReturn ? { projectReturn: { ...projectReturn } } : {}),
      });
      // Betterment Q5: Ask about this, with the note in About and its
      // selected text quoted in the question.
      const floorSelection = desk.selectedIds;
      desk.askAbout([{ id: note.id, kind: "note", ref: noteRef, title: note.title || "Note" }], { handoffNonce: requestNonce });
      desk.setSelected(floorSelection);
      say("Ask opened");
    } catch (cause) { sayFault(cause); }
    finally { writer.release(); setBusy(false); }
  };
  /* Direction A (owner pick 2026-10-27): what comes back lands in the
     margin beside the text, never in a band that moves the editor. */
  const asks = useMarginAsks(draftNoteId);
  const marginKey = winId ? `hs.note-margin.${winId}` : null;
  const [marginClosed, setMarginClosed] = useState(() => readMarginClosed(marginKey));
  const showMargin = () => { setMarginClosed(false); writeMarginClosed(marginKey, false); };
  const closeMargin = () => { setMarginClosed(true); writeMarginClosed(marginKey, true); };
  // A new arrival (a run of Find the tasks, a new Ask) opens the margin again.
  const seenAsks = useRef<Set<string> | null>(null);
  if (!seenAsks.current) seenAsks.current = new Set(asks.map((ask) => ask.key));
  useEffect(() => {
    const seen = seenAsks.current!;
    const fresh = asks.some((ask) => !seen.has(ask.key));
    for (const ask of asks) seen.add(ask.key);
    if (fresh) showMargin();
  }, [asks]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (outcomes.finding) showMargin(); }, [outcomes.finding]); // eslint-disable-line react-hooks/exhaustive-deps
  const askAnchor = (ask: MarginAsk): number | null => {
    const quote = ask.range?.text ?? "";
    if (!quote.trim()) return null;
    if (ask.body === shownBody && ask.range && shownBody.slice(ask.range.from, ask.range.to) === quote) return ask.range.from;
    const at = shownBody.indexOf(quote);
    return at >= 0 ? at : null;
  };
  const cards: MarginCard[] = [];
  if (showAskBand) {
    cards.push({
      key: `review:${review?.id ?? "open"}`,
      anchor: null,
      node: <MarginNote className="thought-note-ask" label="Ask about this note" testId="thought-note-ask"
        question={draftBody ? <span className="thought-note-ask-kicker">A draft from your note</span> : "A question about your note"}
        verbs={question
          ? <Button dense variant="secondary" disabled={busy || !answer.trim()} onClick={() => void addAnswer()}>Add to note</Button>
          : <Button dense variant="secondary" disabled={busy} onClick={() => void addDraft()}>Add to note</Button>}>
        {projection.workspace_state === "named_failure" && projection.terminal_status?.message
          ? <p className="thought-note-ask-reason" role="status">{projection.terminal_status.message}</p> : null}
        <div className="thought-note-ask-open">
          <p className="thought-note-ask-text">{question || draftBody}</p>
          {question ? <label ref={answerRef} className="thought-note-answer">
            <PadGadget label="Your answer" micLabel="Speak your answer" value={answer} onChange={setAnswer} rows={3} />
          </label> : null}
        </div>
      </MarginNote>,
    });
  }
  for (const ask of asks) {
    cards.push({
      key: `ask:${ask.key}`,
      anchor: askAnchor(ask),
      node: <MarginNote label={`Ask: ${ask.question}`} testId="note-margin-ask" question={`Ask: ${ask.question}`}
        verbs={<>
          {ask.state === "answered" ? <Button dense variant="secondary" disabled={busy}
            onClick={() => void appendText(ask.answer).then((added) => { if (added) dropMarginAsk(draftNoteId, ask.key); })}>Add to note</Button> : null}
          <Button dense variant="ghost" onClick={() => dropMarginAsk(draftNoteId, ask.key)}>Dismiss</Button>
        </>}>
        {ask.state === "working" ? <DotWord tone="info" className="note-margin-working">Working</DotWord>
          : ask.state === "failed" ? <DotWord tone="fail">No answer</DotWord>
          // The answer reads as the note reads (Ask's answer document): no raw Markdown.
          : <div className="note-margin-answer" data-testid="note-margin-answer"><Material>{ask.answer}</Material></div>}
      </MarginNote>,
    });
  }
  const showFound = outcomes.finding || outcomes.rows.length > 0;
  const marginHas = cards.length > 0 || showFound;
  const marginOpen = marginHas && !marginClosed;
  const noteDecisions = decisionLines(shownBody);
  const hubOnlyDecisions = outcomes.rows.filter((row) => row.kind === "decision" && !noteDecisions.some((line) => findLine(line.text, row.text)));
  const relations = [
    countWords(peopleNamed(shownBody), "person", "people"),
    countWords(noteDecisions.length + hubOnlyDecisions.length, "decision"),
  ].filter(Boolean).join(" · ");
  /* Note canvas A, step 6: the place line. The Project that files the note
     opens its Room; the meeting it came from opens the meeting. Nothing
     when the hub names nothing. */
  // The Project just filed comes first: the bar is its receipt.
  const filedIn = [...filedHere, ...(documentThought.projects ?? [])]
    .filter((project, index, all) => project.id && all.findIndex((row) => row.id === project.id) === index);
  const placeProject = filedIn[0] ?? null;
  const fromMeeting = documentThought.source_meeting?.id ? documentThought.source_meeting : null;
  const meetingDay = fromMeeting ? shortDay(fromMeeting.at) : "";
  const openDecision = (recordId: string | null) => {
    if (recordId) openDecisionRecord(recordId);
    else useDesk.getState().openSurfaceWindow("open-decisions");
  };
  const footVerbs = writer.conflicted || writer.failed || working || (marginHas && marginClosed);
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
          setReturnRange(null);
        }
        writer.edit(patch);
      }}
      disabled={busy || documentThought.state !== "working"}
      lockedReason={completed ? "FINISHED" : undefined}
      revealRange={revealRange}
      returnRange={returnRange?.body === writer.draft.body ? returnRange : null}
      editorRef={bodyEditorRef}
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
      onOpenLink={(ref) => openRef(ref, { projectReturn: projectReturn ?? null })}
      margin={marginOpen ? <NoteMargin body={shownBody} editorRef={bodyEditorRef} cards={cards}
        outcomes={outcomes} showFound={showFound} onClose={closeMargin} onOpenDecision={openDecision} /> : null}
      verbs={<>
        {/* Window grammar (2026-10-24): the verbs are the toolbar under the
            title bar, Done (the one primary) first. Betterment Q8 (one
            note): Done, Ask about this, Find the tasks (Q9), Project ▾ and
            Send…; on the phone Done sits in the title strip. */}
        {!compact ? <Button dense variant="primary" className="thought-note-primary" disabled={busy} onClick={onDone}><ToolGlyph kind="done" />Done</Button> : null}
        <Button dense variant="ghost" className="thought-note-verb" title="Ask about this" disabled={busy} onClick={() => void askFromNote()}><ToolGlyph kind="ask" /><span className="thought-note-verb-label">Ask about this</span></Button>
        <Button dense variant="ghost" disabled={busy || outcomes.finding || !writer.draft.body.trim()} loading={outcomes.finding} className="thought-note-verb" title="Find the tasks" onClick={() => void findTasks()}>{outcomes.finding ? null : <ToolGlyph kind="tasks" />}<span className="thought-note-verb-label">Find the tasks</span></Button>
        {hasProjects ? <Button dense variant="ghost" disabled={busy} aria-expanded={actionWell === "project"} className="thought-note-verb" title="Project" onClick={() => void openActionWell("project")}><ToolGlyph kind="project" /><span className="thought-note-verb-label">Project ▾</span></Button> : null}
        <Button ref={sendRef} dense variant="ghost" className="thought-note-verb" title="Send" disabled={busy} onClick={() => void openSend()}><ToolGlyph kind="send" /><span className="thought-note-verb-label">Send…</span></Button>
      </>}
    />

    {/* Direction A (2026-10-27): the open question or draft that used to
        be a band under the toolbar is a card in the margin (above); the
        editor never moves. */}
    {message ? <p className="thought-note-line" role="status">
      {message}
      {messageVerb === "reload" ? <Button dense disabled={busy} onClick={() => void reloadNote()}>Reload</Button> : null}
    </p> : null}

    {outcomes.failure ? <p className="thought-note-line" role="status">
      {outcomes.failure}
      <Button dense disabled={busy} onClick={() => void findTasks()}>Try again</Button>
    </p> : null}

    {actionWell === "project" ? <ProjectWell
      noteId={draftNoteId}
      onAdded={(_line, project) => setFiledHere((rows) => [project, ...rows])}
      onClose={() => { setActionWell(null); setActionPassage(null); }}
    /> : null}

    {/* Window grammar (2026-10-24): the kit status bar. It says the save
        state with its lamp, Working while a turn runs, and holds the one
        verb the moment needs: Reload, Retry, or Stop. */}
    <StatusBar
      className="thought-note-foot"
      items={[
        statusWords ? {
          key: "save",
          lamp: statusWords.tone === "danger" ? "fail" : statusWords.tone === "busy" ? "info" : "ok",
          /* DELIGHT: each save pulses the lamp once (the kept time changes). */
          pulse: statusWords.tone === "ok" ? writer.keptAt ?? null : null,
          text: <span className="thought-note-status" data-tone={statusWords.tone === "danger" ? "danger" : undefined} data-lamp={statusWords.tone}>{statusWords.text}</span>,
        } : null,
        working ? { key: "working", lamp: "info", text: "Working" } : null,
        placeProject ? {
          key: "project",
          testId: "note-place-project",
          text: <Button dense variant="ghost" className="thought-note-place" title={filedIn.length > 1 ? filedIn.map((row) => row.name).join(", ") : undefined}
            onClick={() => openProjectRoom(placeProject.id)}>
            <img src={spriteUrl("project", placeProject.id, "rest", null, 20)} alt="" width={14} height={14} />
            <span className="thought-note-place-words">{placeProject.name || "Project"}</span>
          </Button>,
        } : null,
        fromMeeting ? {
          key: "meeting",
          testId: "note-place-meeting",
          text: <Button dense variant="ghost" className="thought-note-place" onClick={() => openRef(`meeting:${fromMeeting.id}`)}>
            <img src={spriteUrl("meeting", fromMeeting.id, "rest", null, 20)} alt="" width={14} height={14} />
            <span className="thought-note-place-words">From {fromMeeting.title || "a meeting"}{meetingDay ? `, ${meetingDay}` : ""}</span>
          </Button>,
        } : null,
      ]}
      verbs={footVerbs ? <>
        {writer.conflicted
          ? <Button dense disabled={busy} onClick={() => void reloadNote()}>Reload</Button>
          : writer.failed ? <Button dense onClick={writer.retry}>Retry</Button> : null}
        {working ? <Button dense disabled={busy} onClick={() => void stop()}>Stop</Button> : null}
        {marginHas && marginClosed ? <Button dense variant="ghost" onClick={showMargin}>Show the margin</Button> : null}
      </> : undefined}
      // On the phone's one-line bar the place words come first; the counts
      // stay in the text.
      trailing={compact && (placeProject || fromMeeting) ? undefined : relations || undefined}
    />
    </> : <>
      <ScrollHint axis="y" scrollRef={sendScrollRef} className="thought-send-scroll">
        <div ref={sendScrollRef} className="thought-send-well" role="region" aria-label="Send note" tabIndex={-1} data-testid="thought-send" data-unsaved={unsaved || undefined}>
          {/* The writer stays mounted: only its saved revision can send. */}
          {unsaved ? <p className="thought-send-wait" role="status">
            {/* W6-G words: a dot and one sentence, never mono caps. */}
            <DotWord tone={writer.failed || writer.conflicted ? "fail" : "idle"}>
              {writer.failed || writer.conflicted
                ? "Could not save the note · Your words stay here · Send waits until it saves"
                : "Saving the note · Send waits until it saves"}
            </DotWord>
          </p> : null}
          <div className="thought-send-body" inert={unsaved} aria-hidden={unsaved || undefined}>
            <NoteSendWells id={draftNoteId} title={writer.draft.title || documentThought.working_note.title}
              version={documentThought.working_revision} onBack={() => setSending(false)} />
          </div>
        </div>
      </ScrollHint>
      <SurfaceFooter
        className="thought-send-foot"
        receipt={message || writeLine?.danger ? <span className="surface-footer-receipt-line" role="status" data-wrap="" data-tone="danger">{message || writeLine?.text}</span> : null}
        verbs={<>
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
  projectReturn,
  onClose,
}: {
  object: WorldObject;
  /** PHILO-13-05 — the id the store keeps for this card; defaults to `object.id`. */
  pulloutId?: string;
  thought: Thought;
  origin?: { x: number; y: number } | null;
  projectReturn?: ProjectReturn | null;
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
  const compact = useCompactViewport();
  const projectName = useDesk((state) => state.projects.find((project) => project.id === projectReturn?.projectId)?.name);
  const returnToProject = () => {
    if (projectReturn) openProjectRoomAtResource(projectReturn.projectId, projectReturn.resourceRef);
  };
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
    leading={!compact && projectReturn ? <Button dense variant="ghost" onClick={returnToProject}>Return to {projectName || "Project"}</Button> : undefined}
    className={`desk-pullout thought-workspace-window${sending ? " is-sending" : ""}`}
    minW={520}
    minH={sending ? 520 : 360}
    defaultW={PULLOUT_SIZE.note?.w}
    defaultH={PULLOUT_SIZE.note?.h}
    fitContent
    origin={origin}
    open
    beforeClose={() => closeHandler.current()}
    onClose={onClose}
    onBack={sending ? () => setSending(false) : projectReturn ? returnToProject : undefined}
    // Betterment Q8: Done in the title strip on the phone.
    actions={compact && !sending ? <Button dense variant="primary" className="thought-note-primary" onClick={() => void done()}>Done</Button> : undefined}
  >
    {controller.opening ? <div className="thought-workspace-opening" aria-busy="true"><span>Opening note…</span></div> : controller.error || !controller.projection ? <div className="thought-workspace-opening" role="alert"><span className="surface-token">Could not open. Note unchanged.</span><Button variant="primary" onClick={() => void controller.reload(true)}>Try again</Button></div> : <>
      <div className="thought-workspace-preserved" inert={controller.restartDetected} aria-hidden={controller.restartDetected || undefined}>
        <WorkspaceReady key={thought.id} initialThought={thought} projection={controller.projection} install={controller.install} reload={controller.reload} registerClose={registerClose} sending={sending} setSending={setSending} onDone={() => void done()} projectReturn={projectReturn} />
      </div>
      {controller.restartDetected ? <div className="thought-workspace-opening thought-workspace-restart" role="alert"><span className="surface-token">Hub restarted. Reload to continue.</span><Button variant="primary" onClick={() => void controller.reload(true)}>Reload note</Button></div> : null}
    </>}
  </DeskWindowFrame>;
}
