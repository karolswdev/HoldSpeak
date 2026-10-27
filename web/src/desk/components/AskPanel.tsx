// The Ask window (Betterment Q4, "One Ask window"; DECISIONS #14).
//
// Ask and Thread are one window. Every Ask is kept as a thread from its first
// question (no Keep, no Bin): the hub writes the exchange when the answer
// lands, Recent lists the kept asks, and a follow-up continues the same
// thread in place. The window draws the conversation (You / answer pairs,
// each answer's Looked at and its verbs), the About line, the follow-up box,
// the engine line, and Stop while a question runs. The face is docked
// in-world, never a modal; the desk stays alive behind it.
//
// Betterment Q7 (Ask my whole desk; DECISIONS #16): on an engine that can
// use tools, the engine line says "Can use your desk"; each answer shows
// Looked at, and Wrote (desk changes, with Undo) and Prepared (sends, with
// Send) from the hub's record of the calls it served (MCP M2's UsedLines).
// A call the hub's tool loop holds for his press waits here with Allow once
// and Deny. Make it a task makes the same write the agent makes.
//
// Before Q4 this was HSM-16-04's Ask AI card (keep or bin one answer) and
// HS-111-05's query console; the Thread window is parked
// (`pullouts/_parked/ThreadPullout.tsx`).
import "./chrome-menus.css";
import "./ask-panel.css";
import "../surface/patterns/conversation.css";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useDesk } from "../store";
import {
  askContexts,
  askTurnsFromThread,
  decideHeldCall,
  latchAskSelection,
  makeTaskFromAnswer,
  readAskEngineTools,
  saveAnswerAsNote,
  selectionPrompt,
  takeAskSelection,
  ASK_SELECTION_EVENT_NAME,
  runAsk,
  type AskSelectionHandoff,
  type AskContext,
  type AskRunResult,
  type AskSourceSnapshot,
  type AskTurn,
  type LookedAt,
} from "../ask";
import { AboutPicker, aboutCandidates, type AboutCandidate } from "./about/AboutPicker";
import { aboutTarget, type AboutChip } from "../askAbout";
import { appendToNote, undoAppend, type NoteAppend } from "../noteAppend";
import { HAND_MIME } from "../hand/drag";
import { MicButton } from "./MicButton";
import { apiFetch, readableError } from "../../lib/api";
import { useDurableDraft } from "../../lib/durableDraft";
import { qualifiedRef } from "../api";
import { DeskWindowFrame } from "./DeskWindow";
import { Material } from "../surface/Material";
import { FoldGadget, PadGadget } from "../surface/gadgets";
import { routeFromWire, type TurnRoute } from "../turnRoute";
import { NoteSendWells } from "../documentSendsLazy";
import { Button } from "../../components/signal/Signal";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { reportWriteFailure } from "../hooks/useWriteReceipt";
import { useEngine, refreshEngine } from "../hooks/useEngine";
import { ActionNotice, StateChip, EngineLine, RunLine, StatusBar, ComposerWell, ToolGlyph, reasonVerb, reasonWords, useReadingEndAnchor, type StatusBarItem } from "../surface";
import { humanTime } from "../surface/format";
import { openProjectRoomAtResource, openRef } from "../openObject";
import { openSurfaceOr } from "../shell";
import { useOptionalRuntimeBus } from "../../runtime/RuntimeBus";
import { busyWords, otherEngineVerb, retryWords } from "../surface/waitWords";
import { deleteThread, getThread, listThreads, type ThreadWire } from "../threads";
import { UsedLines } from "./UsedLines";
import type { AgentUse } from "../used";
import { requestAskReturn } from "../thought-workspace/askReturn";
import { dropMarginAsk, putMarginAsk, updateMarginAsk } from "../thought-workspace/marginAsks";
import { AskSourceFrame } from "./AskSourceFrame";
import { ASK_GLYPH, ASK_SPRITE, AskAbout, AskAnswer, AskFresh, AskQuestion, AskThread, AskToolbar, AskTurnRow, AskVerbs } from "./askFace";
import type { DeskNavigation, ProjectReturn } from "../store/types";
import { useCompactViewport } from "../useCompactViewport";

/** The engine line of an engine that can use the desk's tools (MCP design). */
export const DESK_TOOLS_WORDS = "Can use your desk: reads meetings, people, projects, Jira, GitHub; writes notes and drafts; never sends";

/** One call the hub's tool loop holds for his press. */
interface HeldCall {
  call_id: string;
  tool: string;
  words: string;
}

/** PHILO-13-04 (A3): an Ask that did not answer says so in plain words; the
 * hub's own text (a model path, a refusal sentence) never reaches the face,
 * its title included. */
export function askFailureLabel(_output: string, reason = "did_not_answer"): { label: string; canAskAgain: boolean } {
  return { label: reasonWords(reason), canAskAgain: Boolean(reasonVerb(reason)) };
}

/** Betterment Q2: one running Ask's `ask_progress` frame from the hub. */
type AskProgress =
  | {
      state: "busy";
      job: string;
      engine: { model?: string; boundary?: string };
      alternatives: Array<{ profile_id: string; profile_revision: number; label: string; boundary?: string }>;
    }
  | { state: "retry"; attempt: number; of: number };

/** What an answer wrote, with the tasks he made from it here. */
function usedWithTasks(used: AgentUse | null | undefined, made: { ref: string; label: string } | undefined): AgentUse | null {
  if (!made) return used ?? null;
  const wrote = (used?.wrote ?? []).filter((row) => row.ref !== made.ref);
  return { ...(used ?? {}), wrote: [...wrote, { ref: made.ref, label: made.label, kind: "action_item", undo: true }] };
}

function mintInvocationId(): string {
  const hex = typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID().replace(/-/g, "")
    : Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
  return `ask_${hex}`;
}

/** The running line's words while the hub says the Ask waits. */
function progressWords(progress: AskProgress | null): string {
  if (!progress) return "Working";
  if (progress.state === "busy") return busyWords(progress.job, progress.engine?.boundary);
  return retryWords(progress.attempt, progress.of);
}


/** Forget waits this long for Undo before the thread is deleted. */
export const FORGET_UNDO_MS = 10_000;

/** The face's record of a run he stopped. */
function stoppedRun(): AskRunResult {
  return {
    ok: false, output: "", reason: "stopped", invocationId: "", refusalCode: "", egress: null,
    model: "", profileId: null, inferenceTarget: null, actualPlacement: null, contextIds: [],
    contextTitles: [], groundingClaims: [], groundingReceipt: null, threadId: "", lookedAt: [],
    used: null, deskTools: false,
  };
}

/** This copy belongs to the transmission, never to the editable draft. */
interface AskRequestSnapshot {
  question: string;
  prompt: string;
  lens: string;
  context: AskContext[];
  grounding: Parameters<typeof runAsk>[0]["grounding"];
  sourceSnapshot?: AskSourceSnapshot;
}

/** Betterment Q6: About's shortcut for no About at all. */
const WHOLE_DESK = "desk:whole";
const THIS_WEEK = "meetings:this_week";

/** Monday 00:00 of this week, local time. */
function weekStart(now = new Date()): number {
  const day = (now.getDay() + 6) % 7;
  return new Date(now.getFullYear(), now.getMonth(), now.getDate() - day).getTime();
}

interface PendingForget {
  threadId: string;
  title: string;
  timer: number;
}

export function AskPanel() {
  const items = useDesk((s) => s.items);
  const askThread = useDesk((s) => s.askThread);
  const { closeAsk, markNew } = useDesk.getState();
  const [floorContext, setFloorContext] = useState<AskContext[]>(() => {
    const desk = useDesk.getState();
    return askContexts(desk.items, desk.selectedIds);
  });

  // This window runs Ask; the parked lens catalogue does not name its jobs.
  const lens = "Ask";
  const {
    value: prompt,
    setDraft: setPrompt,
    recovered: promptRecovered,
  } = useDurableDraft("desk-ask", "");
  const engine = useEngine("ask.answer");
  // The kept thread this window shows; null until the first answer lands.
  const [threadId, setThreadId] = useState<string | null>(null);
  const [turns, setTurns] = useState<AskTurn[]>([]);
  // The About a reopened thread carries into its follow-ups.
  const [threadAbout, setThreadAbout] = useState<LookedAt[]>([]);
  // Betterment Q5: what Ask about this put in About (a note, a project, a person).
  const [seedAbout, setSeedAbout] = useState<AskContext[]>([]);
  // Betterment Q8: the note this Ask was opened from (Ask about this on a
  // note). Its answers can be added to it.
  const [fromNote, setFromNote] = useState<{ id: string; title: string } | null>(null);
  const [added, setAdded] = useState<Record<string, NoteAppend>>({});
  const [adding, setAdding] = useState<string | null>(null);
  const [threadRead, setThreadRead] = useState<{ loading: boolean; error: string }>({ loading: false, error: "" });
  const [sent, setSent] = useState<AskRequestSnapshot | null>(null);
  const [running, setRunning] = useState(false);
  const [failedRun, setFailedRun] = useState<AskRunResult | null>(null);
  const [runStartedAt, setRunStartedAt] = useState<number | undefined>();
  const [finishedElapsedSeconds, setFinishedElapsedSeconds] = useState<number | undefined>();
  const [route, setRoute] = useState<TurnRoute | null>(null);
  const [saved, setSaved] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [recentOpen, setRecentOpen] = useState(false);
  const [recent, setRecent] = useState<{ loading: boolean; error: string; rows: ThreadWire[] }>({ loading: false, error: "", rows: [] });
  const [forgotten, setForgotten] = useState<PendingForget | null>(null);
  const projects = useDesk((s) => s.projects);
  // Betterment Q6: the About picker (+) and the people it can find.
  const [picking, setPicking] = useState(false);
  const [people, setPeople] = useState<Array<{ id: string; name: string }>>([]);
  const { copy, state: copyState } = useCopyReceipt();
  const [passageOpen, setPassageOpen] = useState(true);
  const [selectedPassage, setSelectedPassage] = useState<AskSelectionHandoff | null>(() => takeAskSelection());
  const [projectReturn, setProjectReturn] = useState<ProjectReturn | null>(() => selectedPassage?.projectReturn ?? null);
  const activeProjectReturn = selectedPassage ? selectedPassage.projectReturn ?? null : projectReturn;
  const compact = useCompactViewport();
  // The asker's disc on each question: his name from Settings ▸ You, else "You".
  const [asker, setAsker] = useState("You");
  useEffect(() => {
    let live = true;
    void apiFetch<{ owner?: { name?: string } }>("/api/settings")
      .then((body) => {
        const name = String(body?.owner?.name ?? "").trim();
        if (live && name) setAsker(name);
      })
      .catch(() => undefined);
    return () => { live = false; };
  }, []);
  const projectName = useDesk((state) => state.projects.find((project) => project.id === activeProjectReturn?.projectId)?.name);
  const returnToProject = () => {
    if (activeProjectReturn) openProjectRoomAtResource(activeProjectReturn.projectId, activeProjectReturn.resourceRef);
  };
  const [sourceReturnReceipt, setSourceReturnReceipt] = useState("");
  const readingRef = useRef<HTMLDivElement | null>(null);
  const promptRef = useRef<HTMLTextAreaElement | null>(null);
  const mounted = useRef(true);
  const requestId = useRef(0);
  // Saved-thread reads have their own authority. A slow read must not repaint
  // a newer selection (or a new Ask) after the live Ask request has changed.
  const threadReadGeneration = useRef(0);
  const pendingRequest = useRef<{ id: number; controller: AbortController } | null>(null);
  // Betterment Q2: the running Ask's identity, so its progress frames
  // (busy, trying again) reach this window and no other.
  const invocationRef = useRef("");
  const [progress, setProgress] = useState<AskProgress | null>(null);
  // Betterment Q7: the calls the running Ask's tool loop holds for his press.
  const [held, setHeld] = useState<{ threadId: string; calls: HeldCall[] }>({ threadId: "", calls: [] });
  const [deciding, setDeciding] = useState<string | null>(null);
  const [deskTools, setDeskTools] = useState(false);
  const [tasks, setTasks] = useState<Record<string, { ref: string; label: string }>>({});
  const [makingTask, setMakingTask] = useState<string | null>(null);
  const bus = useOptionalRuntimeBus();
  useEffect(() => {
    if (!bus) return undefined;
    return bus.subscribe("ask_progress", (frame) => {
      const data = (frame as { data?: Record<string, unknown> }).data;
      if (!data || !invocationRef.current || data.invocation_id !== invocationRef.current) return;
      if (data.state === "hold") {
        setHeld({
          threadId: String(data.thread_id || ""),
          calls: Array.isArray(data.holds) ? (data.holds as HeldCall[]).filter((row) => row && row.call_id) : [],
        });
      } else if (data.state === "busy") {
        setProgress({
          state: "busy",
          job: String(data.job || ""),
          engine: (data.engine as { model?: string; boundary?: string }) || {},
          alternatives: Array.isArray(data.alternatives) ? data.alternatives as never : [],
        });
      } else if (data.state === "retry") {
        setProgress({ state: "retry", attempt: Number(data.attempt) || 1, of: Number(data.of) || 1 });
      }
    });
  }, [bus]);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      threadReadGeneration.current += 1;
      requestId.current += 1;
      pendingRequest.current?.controller.abort();
      pendingRequest.current = null;
    };
  }, []);

  /** Abandon this view's wait. The hub is told to stop the run. */
  const abandonRun = useCallback(() => {
    requestId.current += 1;
    pendingRequest.current?.controller.abort();
    pendingRequest.current = null;
    const waiting = invocationRef.current;
    invocationRef.current = "";
    if (waiting) void apiFetch(`/api/ask/${encodeURIComponent(waiting)}/cancel`, { method: "POST" }).catch(() => undefined);
  }, []);

  const close = useCallback(() => {
    threadReadGeneration.current += 1;
    abandonRun();
    latchAskSelection(null);
    closeAsk();
  }, [abandonRun, closeAsk]);

  /** A new Ask in this window: nothing kept is touched. */
  const startNew = useCallback((keepHandoff = false) => {
    threadReadGeneration.current += 1;
    abandonRun();
    setThreadId(null);
    setTurns([]);
    setThreadAbout([]);
    setSeedAbout([]);
    setFloorContext([]);
    if (!keepHandoff) {
      latchAskSelection(null);
      setSelectedPassage(null);
      setProjectReturn(null);
    }
    setSourceReturnReceipt("");
    setFromNote(null);
    setAdded({});
    setSent(null);
    setRunning(false);
    setFailedRun(null);
    setRoute(null);
    setProgress(null);
    setHeld({ threadId: "", calls: [] });
    setSaved({});
    setTasks({});
    setThreadRead({ loading: false, error: "" });
  }, [abandonRun]);

  /** Open a kept thread in this window (Recent, a thread's ref, a restored desk). */
  const loadThread = useCallback(async (id: string, navigation?: DeskNavigation) => {
    startNew();
    setProjectReturn(navigation?.projectReturn ? { ...navigation.projectReturn } : null);
    const generation = threadReadGeneration.current;
    setThreadId(id);
    setThreadRead({ loading: true, error: "" });
    try {
      const detail = await getThread(id);
      if (!mounted.current || generation !== threadReadGeneration.current) return;
      const { turns: kept, about } = askTurnsFromThread(detail);
      setTurns(kept);
      setThreadAbout(about);
      setThreadRead({ loading: false, error: "" });
    } catch (error) {
      if (!mounted.current || generation !== threadReadGeneration.current) return;
      setThreadRead({ loading: false, error: readableError(error) });
    }
  }, [startNew]);

  // The store asks for a thread (or a new Ask): follow each request once.
  // Betterment Q3: a new Ask can carry its question; `run` asks it once the
  // window shows it (Search's Ask row: one Enter, one answer).
  const handledNonce = useRef(0);
  const [autoRun, setAutoRun] = useState<string | null>(null);
  useEffect(() => {
    if (!askThread || askThread.nonce === handledNonce.current) return;
    handledNonce.current = askThread.nonce;
    if (askThread.threadId) void loadThread(askThread.threadId, askThread.navigation);
    else startNew(Boolean(askThread.handoffNonce === askThread.nonce &&
      selectedPassage?.requestNonce === askThread.nonce &&
      askThread.about?.some((entry) => entry.ref === selectedPassage.noteRef)));
    if (!askThread.threadId && askThread.about?.length) setSeedAbout(askThread.about.map((entry) => ({ ...entry })));
    const notes = !askThread.threadId ? (askThread.about ?? []).filter((entry) => entry.kind === "note") : [];
    if (notes.length === 1) setFromNote({ id: notes[0].id, title: notes[0].title });
    const question = askThread.question?.trim();
    if (!askThread.threadId && question) {
      setPrompt(question);
      setAutoRun(askThread.run ? question : null);
    }
  }, [askThread, loadThread, startNew, setPrompt, selectedPassage]);

  const context = useMemo(() => {
    const picked = selectedPassage?.source ? [] : floorContext;
    const selected = [...picked, ...seedAbout.filter((entry) => !picked.some((p) => p.ref === entry.ref))];
    const source = selectedPassage?.source;
    if (!source || source.ref !== selectedPassage.noteRef) return selected;
    // An explicit Note handoff names the saved source, even before a desk
    // collection read or after the floor drops a non-icon selection.
    return [...selected.filter((entry) => entry.ref !== source.ref), { ...source }];
  }, [floorContext, selectedPassage, seedAbout]);
  useEffect(() => {
    const onSelection = (event: Event) => {
      const next = (event as CustomEvent<AskSelectionHandoff | null>).detail;
      // The mounted window owns this handoff now. Clear the module latch so
      // a later mount cannot replay a quote already shown here.
      takeAskSelection();
      setSelectedPassage(next && (next.text.trim() || next.source) ? next : null);
      // Clearing a quote or About source changes inference scope, not the
      // explicit Project task the owner left. A new source replaces it.
      if (next) setProjectReturn(next.projectReturn ? { ...next.projectReturn } : null);
      if (next) setPassageOpen(true);
    };
    window.addEventListener(ASK_SELECTION_EVENT_NAME, onSelection);
    return () => window.removeEventListener(ASK_SELECTION_EVENT_NAME, onSelection);
  }, []);
  // Betterment Q6: About finds people by name (a locked or unset People
  // store answers nothing: no people rows).
  useEffect(() => {
    let live = true;
    void apiFetch<{ relationships?: Array<Record<string, unknown>> }>("/api/people/relationships")
      .then((body) => {
        if (!live) return;
        setPeople((body?.relationships ?? []).flatMap((row) => {
          const id = String(row.id ?? "");
          const name = String(row.display_name ?? "").trim();
          return id && name && row.state !== "archived" ? [{ id, name }] : [];
        }));
      })
      .catch(() => undefined);
    return () => { live = false; };
  }, []);
  // Betterment Q7: can the Answers engine use the desk? (the engine line)
  const readDeskTools = useCallback(async () => {
    const can = await readAskEngineTools();
    if (mounted.current) setDeskTools(can);
  }, []);
  useEffect(() => { void readDeskTools(); }, [readDeskTools, engine.model]);
  // Betterment Q6: everything About can find by name, grouped, newest first;
  // the shortcuts (my whole desk, this week's meetings, each person, each
  // project) before he types. Never modes, threads, results or roadmaps.
  const candidates: AboutCandidate[] = useMemo(() => {
    const listed = aboutCandidates(
      { ...items, project: projects.map((p) => ({ kind: "project", id: p.id, name: p.name })) } as Parameters<typeof aboutCandidates>[0],
      people,
    ).filter((c) => c.kind !== "set" || c.ref === THIS_WEEK)
      .map((c) => (c.kind === "person" || c.kind === "project" ? { ...c, shortcut: true } : c));
    const decisions: AboutCandidate[] = (items.decision ?? []).map((d) => ({
      ref: qualifiedRef("decision", d.id), kind: "decision", label: String(d.title || "Decision"), at: d.createdAt || undefined,
    }));
    return [{ ref: WHOLE_DESK, kind: "set", label: "My whole desk", terms: "everything all desk" }, ...listed, ...decisions];
  }, [items, projects, people]);

  // About: the objects he chose (selection, pickers) and what a reopened
  // thread was about. Empty means his whole desk.
  const about: LookedAt[] = useMemo(() => {
    const rows: LookedAt[] = [];
    const add = (ref: string | undefined, title: string) => {
      if (!ref || rows.some((row) => row.ref === ref)) return;
      rows.push({ ref, title });
    };
    for (const entry of context) add(entry.ref || qualifiedRef(entry.kind, entry.id), entry.title);
    for (const entry of threadAbout) add(entry.ref, entry.title);
    return rows;
  }, [context, threadAbout]);

  /** Betterment Q6: a pick (or a drop) becomes an About chip. */
  const addAbout = useCallback((chip: AboutChip) => {
    setSeedAbout((current) => (current.some((entry) => entry.ref === chip.ref) ? current : [...current, chip]));
  }, []);
  const pickAbout = (pick: AboutCandidate) => {
    if (pick.ref === WHOLE_DESK) {
      // No About: the question is about his whole desk.
      setSeedAbout([]);
      setThreadAbout([]);
      setFloorContext([]);
      latchAskSelection(null);
      setSelectedPassage(null);
      setPicking(false);
      return;
    }
    if (pick.ref === THIS_WEEK) {
      addAbout({ id: "this_week", kind: "set", ref: THIS_WEEK, title: pick.label });
      return;
    }
    const known = aboutTarget(pick.ref);
    if (known) { addAbout(known); return; }
    const [kind, ...rest] = pick.ref.split(":");
    const id = rest.join(":");
    // A person is read by her window's ref (people:<id>), not person:<id>.
    if (kind === "person") addAbout({ id, kind: "people", ref: `people:${id}`, title: pick.label });
    else if (id) addAbout({ id, kind, ref: pick.ref, title: pick.label });
  };
  const removeAbout = (ref: string) => {
    setSeedAbout((current) => current.filter((entry) => entry.ref !== ref));
    setThreadAbout((current) => current.filter((entry) => entry.ref !== ref));
    setFloorContext((current) => current.filter((entry) => entry.ref !== ref));
    if (selectedPassage?.noteRef === ref) {
      latchAskSelection(null);
      setSelectedPassage(null);
    }
  };
  const returnToSource = () => {
    if (!selectedPassage) return;
    const sourceWindow = selectedPassage.windowId;
    const desk = useDesk.getState();
    const noteId = selectedPassage.noteRef.slice("note:".length);
    const live = desk.pullouts.find((entry) =>
      (entry.id === selectedPassage.noteRef || entry.sourceRef === selectedPassage.noteRef) &&
      (`pullout:${entry.id}` === sourceWindow || entry.id === selectedPassage.noteRef || entry.id === noteId));
    // An old bare-key Note can close while Ask remains. The canonical reopen
    // gets a new window id; the return request must name that actual target.
    const targetWindow = `pullout:${live?.id ?? selectedPassage.noteRef}`;
    requestAskReturn({ ...selectedPassage, windowId: targetWindow });
    const navigation = { projectReturn: selectedPassage.projectReturn ?? null };
    if (live) {
      // The live window already shows this Note: it comes to the front now.
      // The qualified opener rereads Desk items first and raised it seconds
      // later: Ask covered the caret, and a later To back was undone.
      setSourceReturnReceipt("");
      desk.openPullout(selectedPassage.noteRef, undefined, navigation);
      desk.restorePanel(targetWindow);
      return;
    }
    setSourceReturnReceipt(sourceWindow ? "SOURCE WINDOW CLOSED" : "SOURCE WINDOW NOT FOUND");
    // A closed Note reopens through the qualified opener, which rereads Desk
    // items first: a vanished cache entry must not repaint a same-id object.
    openRef(selectedPassage.noteRef, navigation);
  };
  // Betterment Q6: a desk object dropped on the Ask window joins About.
  const onAboutDragOver = (event: React.DragEvent) => {
    if (!Array.from(event.dataTransfer?.types ?? []).includes(HAND_MIME)) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
  };
  const onAboutDrop = (event: React.DragEvent) => {
    const ref = event.dataTransfer?.getData(HAND_MIME);
    if (!ref) return;
    event.preventDefault();
    const chip = aboutTarget(ref);
    if (chip) addAbout(chip);
  };

  const run = async (snapshot: AskRequestSnapshot, invocationId = mintInvocationId()) => {
    if (pendingRequest.current || !mounted.current) return;
    const controller = new AbortController();
    invocationRef.current = invocationId;
    setProgress(null);
    const id = ++requestId.current;
    pendingRequest.current = { id, controller };
    setRunning(true);
    setFailedRun(null);
    setRoute(null);
    const startedAt = Date.now();
    setRunStartedAt(startedAt);
    setFinishedElapsedSeconds(undefined);
    setSent(snapshot);
    setPassageOpen(false);
    // Direction A (2026-10-27): an Ask from a note shows in the note's
    // margin, beside the passage it asked about.
    const marginNote = fromNote;
    if (marginNote) {
      const passage = snapshot.sourceSnapshot && selectedPassage?.noteRef === `note:${marginNote.id}` ? selectedPassage : null;
      putMarginAsk({
        key: invocationId, noteId: marginNote.id, question: snapshot.question, answer: "", state: "working",
        range: passage?.range ? { ...passage.range } : null, body: passage?.body ?? "",
      });
    }
    const r = await runAsk({
      prompt: snapshot.prompt,
      lens: snapshot.lens,
      context: snapshot.context,
      grounding: snapshot.grounding,
      sourceSnapshot: snapshot.sourceSnapshot,
      signal: controller.signal,
      invocationId,
      thread: threadId || true,
    });
    if (marginNote) {
      if (!mounted.current || controller.signal.aborted || pendingRequest.current?.id !== id) dropMarginAsk(marginNote.id, invocationId);
      else updateMarginAsk(marginNote.id, invocationId, r.ok ? { state: "answered", answer: r.output } : { state: "failed" });
    }
    if (!mounted.current || controller.signal.aborted || pendingRequest.current?.id !== id) return;
    pendingRequest.current = null;
    invocationRef.current = "";
    setProgress(null);
    setHeld({ threadId: "", calls: [] });
    setRunning(false);
    setRoute(routeFromWire(r.route));
    if (r.deskTools) setDeskTools(true);
    setFinishedElapsedSeconds(Math.max(0, Math.round((Date.now() - startedAt) / 1000)));
    if (!r.ok) {
      setFailedRun({ ...r, reason: r.reason || "did_not_answer" });
      return;
    }
    if (r.threadId) setThreadId(r.threadId);
    setTurns((current) => [...current, {
      key: r.answerId || `${r.threadId || "ask"}:${current.length}:${invocationId}`,
      question: snapshot.question,
      answer: r.output,
      lookedAt: r.lookedAt,
      used: r.used,
    }]);
    setSent(null);
  };

  const ask = () => {
    if (!prompt.trim() || pendingRequest.current) return;
    const selection = selectedPassage && context.some((entry) => entry.ref === selectedPassage.noteRef)
      ? { ...selectedPassage }
      : null;
    // Every nested value is built here. Later selections and picker changes
    // cannot rewrite Ask again.
    // A reopened thread's About rides its follow-ups as grounding refs.
    const carried = threadAbout.map((row) => row.ref).filter((ref) => !context.some((entry) => entry.ref === ref));
    // "This week's meetings" is read as this week's meetings when he asks.
    const since = weekStart();
    const thisWeek = (items.meeting ?? [])
      .filter((m) => Date.parse(String(m.startedAt || "")) >= since)
      .slice(0, 12)
      .map((m) => ({ id: m.id, kind: "meeting", title: String(m.title || "Meeting"), ref: qualifiedRef("meeting", m.id) }));
    const asked = context.flatMap((entry) => (entry.ref === THIS_WEEK ? thisWeek : [{ ...entry }]));
    const refs = Array.from(new Set(carried));
    const snapshot: AskRequestSnapshot = {
      question: prompt.trim(),
      prompt: selectionPrompt(prompt, selection),
      lens,
      context: asked,
      grounding: refs.length ? { meeting_ids: [], artifact_ids: [], expand: "summary", refs } : null,
      ...(selection?.sourceSnapshot && selection.sourceSnapshot.ref === selection.noteRef
        ? { sourceSnapshot: { ...selection.sourceSnapshot } } : {}),
    };
    // The snapshot is now the transmission's immutable copy. Clear the
    // durable editor at acceptance so the sent question is visible in the
    // reading area while a new follow-up can be written safely.
    setPrompt("");
    return run(snapshot);
  };

  const prefillPrompt = (text: string) => {
    setPrompt(text);
    promptRef.current?.focus();
  };

  // The seeded question runs once, on the render that shows it.
  useEffect(() => {
    if (!autoRun || threadId || prompt.trim() !== autoRun) return;
    setAutoRun(null);
    void ask();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRun, prompt, threadId]);

  /** Stop ends the wait and tells the hub; the question stays, marked
   *  stopped, with Ask again. */
  const stop = () => {
    abandonRun();
    setRunning(false);
    setProgress(null);
    setHeld({ threadId: "", calls: [] });
    setFinishedElapsedSeconds(runStartedAt ? Math.max(0, Math.round((Date.now() - runStartedAt) / 1000)) : undefined);
    setFailedRun(stoppedRun());
  };

  /** Betterment Q2: the engine is busy; run this one Ask on another engine.
   *  The waiting run is stopped, and the new run gets its own identity with a
   *  one-run assignment (scope `invocation`), so his settings do not change. */
  const askElsewhere = async (alternative: { profile_id: string; profile_revision: number }) => {
    if (!sent) return;
    const waiting = invocationRef.current;
    requestId.current += 1;
    pendingRequest.current?.controller.abort();
    pendingRequest.current = null;
    if (waiting) void apiFetch(`/api/ask/${encodeURIComponent(waiting)}/cancel`, { method: "POST" }).catch(() => undefined);
    const next = mintInvocationId();
    try {
      await apiFetch("/api/inference/assignments/set", {
        method: "POST",
        json: {
          command_id: `ask-elsewhere-${next}`,
          expected_revision: 0,
          scope: { kind: "invocation", invocation_id: next, capability_id: "ask.answer" },
          entries: [{ profile_id: alternative.profile_id, profile_revision: alternative.profile_revision }],
        },
      });
    } catch (cause) {
      // The run below still goes, on the assigned engine; the receipt says the
      // other engine was not set for this one.
      reportWriteFailure("Use another engine", cause);
    }
    await run(sent, next);
  };

  /** The answer's note: the one Save as note made, or a new one. */
  const answerNote = async (turn: AskTurn, verb: string): Promise<string | null> => {
    if (saved[turn.key]) return saved[turn.key];
    if (saving) return null;
    setSaving(turn.key);
    const ref = await saveAnswerAsNote(turn, threadId);
    if (!mounted.current) return null;
    setSaving(null);
    if (!ref) {
      reportWriteFailure(verb, new Error("The answer was not saved as a note. It is still here; try again."));
      return null;
    }
    setSaved((current) => ({ ...current, [turn.key]: ref }));
    markNew(ref.slice("note:".length));
    void useDesk.getState().refresh();
    return ref;
  };
  const saveAsNote = async (turn: AskTurn) => {
    if (saved[turn.key]) return;
    await answerNote(turn, "Save as note");
  };
  /** Betterment Q5 (FOLLOWUPS Q4): Send… prepares a send of the answer. The
   *  answer is kept as a note (the document a send carries), and the note's
   *  Send well unfolds under the answer; he presses Send there. */
  const [sending, setSending] = useState<string | null>(null);
  const sendAnswer = async (turn: AskTurn) => {
    if (sending === turn.key) { setSending(null); return; }
    const ref = await answerNote(turn, "Send");
    if (ref && mounted.current) setSending(turn.key);
  };

  /** Betterment Q8: Add to note appends the answer to the note Ask was
   *  opened from; Undo puts the note back. */
  const addToNote = async (turn: AskTurn) => {
    if (!fromNote || adding || added[turn.key]) return;
    setAdding(turn.key);
    try {
      const append = await appendToNote(fromNote.id, turn.answer);
      if (mounted.current) setAdded((current) => ({ ...current, [turn.key]: append }));
      void useDesk.getState().refresh();
    } catch (cause) {
      reportWriteFailure("Add to note", cause);
    } finally {
      if (mounted.current) setAdding(null);
    }
  };
  const undoAdd = async (turn: AskTurn) => {
    const append = added[turn.key];
    if (!append || adding) return;
    setAdding(turn.key);
    try {
      if (!await undoAppend(append)) {
        reportWriteFailure("Undo", new Error("The note changed after the answer was added. Undo did not change it."));
      } else if (mounted.current) {
        setAdded((current) => {
          const { [turn.key]: _gone, ...rest } = current;
          return rest;
        });
      }
      void useDesk.getState().refresh();
    } catch (cause) {
      reportWriteFailure("Undo", cause);
    } finally {
      if (mounted.current) setAdding(null);
    }
  };

  /** Betterment Q7: Allow once / Deny on a held call. */
  const decide = async (call: HeldCall, decision: "approve" | "deny") => {
    if (!held.threadId || deciding) return;
    setDeciding(call.call_id);
    const ok = await decideHeldCall(held.threadId, call.call_id, decision);
    if (!mounted.current) return;
    setDeciding(null);
    if (!ok) {
      reportWriteFailure(decision === "approve" ? "Allow once" : "Deny", new Error("The press did not reach the hub. Try again."));
      return;
    }
    setHeld((current) => ({ ...current, calls: current.calls.filter((row) => row.call_id !== call.call_id) }));
  };

  /** Betterment Q7: Make it a task from an answer (Wrote, with Undo). */
  const makeTask = async (turn: AskTurn) => {
    if (!threadId || makingTask || tasks[turn.key]) return;
    setMakingTask(turn.key);
    const made = await makeTaskFromAnswer(threadId, turn.answer);
    if (!mounted.current) return;
    setMakingTask(null);
    if (!made) {
      reportWriteFailure("Make it a task", new Error("The task was not made. The answer is still here; try again."));
      return;
    }
    setTasks((current) => ({ ...current, [turn.key]: made }));
    void useDesk.getState().refresh();
  };

  const readRecent = useCallback(async () => {
    setRecent((current) => ({ ...current, loading: true, error: "" }));
    try {
      const rows = await listThreads();
      if (mounted.current) setRecent({ loading: false, error: "", rows });
    } catch (error) {
      if (mounted.current) setRecent((current) => ({ ...current, loading: false, error: readableError(error) }));
    }
  }, []);
  const toggleRecent = () => {
    const next = !recentOpen;
    setRecentOpen(next);
    if (next) void readRecent();
  };

  /** More ▸ Forget: the thread leaves now; the delete waits 10 s for Undo. */
  const forget = () => {
    if (!threadId) return;
    const title = turns[0]?.question || "This ask";
    const target = threadId;
    if (forgotten) window.clearTimeout(forgotten.timer);
    const timer = window.setTimeout(() => {
      deleteThread(target).catch((cause) => reportWriteFailure("Forget", cause));
      setForgotten((current) => (current?.threadId === target ? null : current));
    }, FORGET_UNDO_MS);
    setForgotten({ threadId: target, title, timer });
    setRecent((current) => ({ ...current, rows: current.rows.filter((row) => row.id !== target) }));
    startNew();
  };
  const undoForget = () => {
    if (!forgotten) return;
    window.clearTimeout(forgotten.timer);
    const target = forgotten.threadId;
    setForgotten(null);
    void loadThread(target);
  };
  // A pending Forget still happens when the window closes.
  const forgottenRef = useRef<PendingForget | null>(null);
  forgottenRef.current = forgotten;
  useEffect(() => () => {
    const pending = forgottenRef.current;
    if (!pending) return;
    window.clearTimeout(pending.timer);
    void deleteThread(pending.threadId).catch(() => undefined);
  }, []);

  const hasConversation = turns.length > 0 || running || Boolean(failedRun) || threadRead.loading || Boolean(threadRead.error);
  useReadingEndAnchor(readingRef, hasConversation);
  const lastRoute = route;
  const savedCount = Object.keys(saved).length;
  const statusLine = running
    ? ""
    : [
        promptRecovered ? "Draft kept" : "",
        !failedRun && turns.length && finishedElapsedSeconds ? `Answered in ${finishedElapsedSeconds} s` : "",
        lastRoute?.fallback ? "Fallback" : "",
        sourceReturnReceipt,
      ].filter(Boolean).join(" · ");

  const recentPanel = recentOpen ? (
    <div className="desk-ask-recent" role="region" aria-label="Recent" data-testid="ask-recent">
      {recent.loading && !recent.rows.length ? <span className="desk-ask-recent-note">Reading</span> : null}
      {recent.error ? (
        <ActionNotice role="alert" tone="warn" action={{ label: "Try again", onClick: () => void readRecent() }}>
          <StateChip state="unreachable" label="Recent not read" />
        </ActionNotice>
      ) : null}
      {!recent.loading && !recent.error && !recent.rows.length ? <span className="desk-ask-recent-note">Nothing asked yet</span> : null}
      <ul className="desk-ask-recent-list">
        {recent.rows.map((row) => (
          <li key={row.id}>
            <Button dense variant="ghost" className="desk-ask-recent-row" aria-current={row.id === threadId ? "true" : undefined}
              onClick={() => { setRecentOpen(false); void loadThread(row.id); }}>
              <img className="desk-ask-recent-glyph" src={ASK_GLYPH} alt="" width={20} height={20} draggable={false} />
              <span className="desk-ask-recent-title">{row.title?.trim() || "An ask with no question"}</span>
              <span className="desk-ask-recent-age">{humanTime(row.last_turn_at || row.updated_at)}</span>
            </Button>
          </li>
        ))}
      </ul>
    </div>
  ) : null;

  // Window grammar: the status bar names the engine that answers (by name;
  // no place word, no address: owner ruling 2026-10-25), Asking… with Stop
  // while a turn runs, and the receipts in warm words.
  const engineWords = engine.state === "set" ? engine.model : "";
  const statusItems: StatusBarItem[] = [
    running ? { key: "asking", lamp: "info", text: "Asking…", testId: "ask-status-asking" } : null,
    !running && !failedRun && engineWords ? { key: "engine", lamp: "ok", text: engineWords, testId: "ask-status-engine" } : null,
    statusLine ? { key: "receipt", text: statusLine, testId: "ask-status-receipt" } : null,
    savedCount && !running ? { key: "saved", lamp: "ok", text: savedCount === 1 ? "Saved as note" : `${savedCount} answers saved as notes`, testId: "ask-status-saved" } : null,
    copyState === "copied" ? { key: "copy", lamp: "ok", text: "Copied", testId: "ask-status-copied" } : null,
    copyState === "failed" ? { key: "copy", lamp: "fail", text: "Not copied", testId: "ask-status-copied" } : null,
  ].filter(Boolean) as StatusBarItem[];

  const aboutLine = (
    <AskAbout
      rows={about}
      picking={picking}
      onTogglePick={() => setPicking((open) => !open)}
      onOpen={(row) => (row.ref === THIS_WEEK ? undefined : () => openRef(row.ref, { projectReturn: activeProjectReturn }))}
      onRemove={(row) => removeAbout(row.ref)}
    />
  );

  return (
    <DeskWindowFrame
      id="ask"
      glyph="✦"
      label="Ask"
      className={`desk-pullout desk-ask is-card${hasConversation ? " has-traffic" : ""}`}
      icon={<img src={ASK_SPRITE} alt="" width={24} height={24} draggable={false} />}
      title="Ask"
      leading={activeProjectReturn && !compact ? <Button dense variant="ghost" onClick={returnToProject}>Return to {projectName || "Project"}</Button> : undefined}
      open
      defaultW={880}
      defaultH={640}
      onClose={close}
      onBack={activeProjectReturn ? returnToProject : undefined}
    >
      <div className="desk-pullout-body desk-ask-body" data-testid="ask-body" onDragOver={onAboutDragOver} onDrop={onAboutDrop} onKeyDown={(event) => {
        // The frame owns Escape from this window. An IME uses Escape to
        // finish composition, so that event must not close the writer.
        if (event.key === "Escape" && event.nativeEvent.isComposing) event.stopPropagation();
      }}>
        <AskToolbar
          onNew={() => startNew()}
          recentOpen={recentOpen}
          onRecent={toggleRecent}
          onForget={threadId || turns.length ? forget : undefined}
          about={aboutLine}
        />
        {recentPanel}
        {/* Betterment Q6: the one About picker, under the toolbar (the
            matches stay in view on a phone). */}
        {picking ? (
          <div className="desk-ask-about-picker">
            <AboutPicker candidates={candidates} picked={about.map((row) => row.ref)} onPick={pickAbout} />
          </div>
        ) : null}
        {forgotten ? (
          <ActionNotice tone="info" action={{ label: "Undo", onClick: undoForget }}>
            Forgotten: {forgotten.title}
          </ActionNotice>
        ) : null}

        {hasConversation ? (
          <AskThread readingRef={readingRef}>
            {threadRead.loading ? <AskTurnRow testId={null}><AskAnswer><RunLine phase="running" verb="Opening" /></AskAnswer></AskTurnRow> : null}
            {threadRead.error ? (
              <li className="desk-ask-turn">
                <ActionNotice role="alert" tone="warn" action={threadId ? { label: "Try again", onClick: () => void loadThread(threadId) } : undefined}>
                  <StateChip state="unreachable" label="This ask was not read" />
                </ActionNotice>
              </li>
            ) : null}
            {turns.map((turn) => (
              <AskTurnRow key={turn.key}>
                <AskQuestion asker={asker}>{turn.question}</AskQuestion>
                <AskAnswer>
                  <div className="desk-ask-answer"><Material>{turn.answer}</Material></div>
                  {turn.lookedAt.length ? (
                    <FoldGadget title={`Looked at · ${turn.lookedAt.length === 1 ? turn.lookedAt[0].title : `${turn.lookedAt.length} sources`}`} className="desk-ask-reading-fold">
                      <div className="desk-ask-sources desk-ask-answer-sources" data-testid="ask-looked-at">
                        {turn.lookedAt.map((source) => (
                          <Button key={source.ref} dense variant="ghost" onClick={() => openRef(source.ref, { projectReturn: activeProjectReturn })}>{source.title}</Button>
                        ))}
                      </div>
                    </FoldGadget>
                  ) : null}
                  <UsedLines used={usedWithTasks(turn.used, tasks[turn.key])} testPrefix="ask" lookedAt={false} />
                  <AskVerbs>
                    {saved[turn.key] ? (
                      <Button dense variant="ghost" onClick={() => openRef(saved[turn.key], { projectReturn: activeProjectReturn })}><ToolGlyph kind="open" />Open note</Button>
                    ) : (
                      <Button dense variant="ghost" loading={saving === turn.key} onClick={() => void saveAsNote(turn)}>{saving === turn.key ? null : <ToolGlyph kind="note" />}Save as note</Button>
                    )}
                    <Button dense variant="ghost" onClick={() => void copy(turn.answer)}>Copy</Button>
                    <Button dense variant="ghost" aria-expanded={sending === turn.key} onClick={() => void sendAnswer(turn)}><ToolGlyph kind="send" />Send…</Button>
                    {threadId && !tasks[turn.key] && !(turn.used?.wrote ?? []).some((row) => row.ref.startsWith("action_item:")) ? (
                      <Button dense variant="ghost" loading={makingTask === turn.key} onClick={() => void makeTask(turn)}>{makingTask === turn.key ? null : <ToolGlyph kind="tasks" />}Make it a task</Button>
                    ) : null}
                    {fromNote && !added[turn.key] ? (
                      <Button dense variant="ghost" loading={adding === turn.key} onClick={() => void addToNote(turn)}>{adding === turn.key ? null : <ToolGlyph kind="note" />}Add to note</Button>
                    ) : null}
                  </AskVerbs>
                  {saved[turn.key] ? <span className="desk-ask-saved" role="status">Saved to your desk</span> : null}
                  {fromNote && added[turn.key] ? (
                    <span className="desk-ask-saved desk-ask-added" role="status" data-testid="ask-added">
                      Added to {fromNote.title || "the note"}
                      <Button dense variant="ghost" loading={adding === turn.key} onClick={() => void undoAdd(turn)}>Undo</Button>
                    </span>
                  ) : null}
                  {sending === turn.key && saved[turn.key] ? (
                    <div className="desk-ask-send-well" data-testid="ask-send">
                      <NoteSendWells id={saved[turn.key].slice("note:".length)} title={turn.question} />
                    </div>
                  ) : null}
                </AskAnswer>
              </AskTurnRow>
            ))}
            {sent && (running || failedRun) ? (
              <AskTurnRow testId={null}>
                <AskQuestion asker={asker}>{sent.question}</AskQuestion>
                {running ? (
                  <AskAnswer>
                    <RunLine
                      phase="running"
                      verb={progressWords(progress)}
                      model={progress?.state === "busy" ? "" : engine.model}
                      startedAt={runStartedAt}
                    />
                    {held.calls.map((call) => (
                      <div className="desk-ask-hold" data-testid="ask-hold" key={call.call_id} role="group" aria-label={call.words}>
                        <span className="desk-ask-hold-words">{call.words}?</span>
                        <Button dense variant="primary" loading={deciding === call.call_id} onClick={() => void decide(call, "approve")}>Allow once</Button>
                        <Button dense variant="ghost" disabled={deciding === call.call_id} onClick={() => void decide(call, "deny")}>Deny</Button>
                      </div>
                    ))}
                    {progress?.state === "busy" && progress.alternatives[0] ? (
                      <Button dense variant="ghost" data-testid="ask-elsewhere" onClick={() => void askElsewhere(progress.alternatives[0])}>
                        {otherEngineVerb(progress.alternatives[0].label, progress.alternatives[0].boundary)}
                      </Button>
                    ) : null}
                  </AskAnswer>
                ) : null}
                {failedRun ? (
                  <AskAnswer failed>
                    <RunLine
                      phase="failure"
                      reason={failedRun.reason}
                      model={engine.model}
                      elapsedSeconds={finishedElapsedSeconds}
                      onAction={failedRun.reason === "no_engine" ? () => openSurfaceOr("configure-runs-on", "/settings", "models") : undefined}
                      onRetry={failedRun.reason !== "no_engine" && failedRun.reason !== "source_changed" && failedRun.reason !== "source_gone" && reasonVerb(failedRun.reason) && sent ? () => void run(sent) : undefined}
                    />
                  </AskAnswer>
                ) : null}
              </AskTurnRow>
            ) : null}
          </AskThread>
        ) : (
          <AskThread readingRef={readingRef} empty testId="ask-empty">
            <AskFresh onPrompt={prefillPrompt} />
          </AskThread>
        )}

        <ComposerWell
          className="conversation-composer desk-ask-composer"
          details={selectedPassage?.source ? (
            <AskSourceFrame
              quote={selectedPassage.text}
              open={passageOpen}
              onToggle={setPassageOpen}
              onClear={() => {
                const source = selectedPassage.source;
                latchAskSelection(null);
                setSelectedPassage(source ? { ...selectedPassage, text: "", source } : null);
              }}
              onBack={returnToSource}
            />
          ) : undefined}
          capture={
            <MicButton
              label="Speak your question"
              draftScope="desk-ask"
              onText={(text) => setPrompt((current) => current ? `${current} ${text}` : text)}
            />
          }
          context={engine.state === "set" ? (
            <div className="surface-engine-line desk-ask-engine-line" data-testid="engine-line">
              <FoldGadget title="Tools" className="desk-ask-tools">
                <span>{deskTools ? DESK_TOOLS_WORDS : "No desk tools"}</span>
              </FoldGadget>
            </div>
          ) : !running ? (
            <EngineLine
              engine={engine}
              onChoose={() => openSurfaceOr("configure-runs-on", "/settings", "models")}
              onRetry={() => void refreshEngine("ask.answer")}
            />
          ) : null}
          actions={
            <Button
              variant="primary"
              disabled={running || !prompt.trim()}
              onClick={() => void ask()}
            >Ask</Button>
          }
        >
          <div className="desk-ask-input">
            <PadGadget
              label="Ask about your work"
              mic={false}
              rows={3}
              value={prompt}
              placeholder={turns.length ? "Ask a follow-up" : "Ask about your work"}
              autoFocus
              inputRef={promptRef}
              onChange={setPrompt}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                  e.preventDefault();
                  void ask();
                }
              }}
            />
          </div>
        </ComposerWell>
        {/* Inside the body (the surface container), so the bar takes its
            narrow form at a phone width: Stop keeps its 44 px target. */}
        <StatusBar
          className="desk-ask-status"
          data-testid="ask-status"
          items={statusItems}
          verbs={running ? <Button dense variant="secondary" onClick={stop}>Stop</Button> : undefined}
        />
      </div>

    </DeskWindowFrame>
  );
}

/** The bundle bar (the iPad's askBundle grammar): the lasso'd count + the one
 * action that gives the selection meaning. */
export function AskBar() {
  const selectedIds = useDesk((s) => s.selectedIds);
  const items = useDesk((s) => s.items);
  const askOpen = useDesk((s) => s.askOpen);
  const { clearSelection } = useDesk.getState();
  const [refusal, setRefusal] = useState("");
  useEffect(() => setRefusal(""), [selectedIds]);
  if (!selectedIds.length || askOpen) return null;
  const contexts = askContexts(items, selectedIds);
  const targets = contexts.map((entry) => aboutTarget(entry.ref));
  const supported = contexts.length === selectedIds.length && targets.every(Boolean);
  return (
    <div className="desk-askbar" onPointerDown={(e) => e.stopPropagation()}>
      <span className="desk-askbar-count">
        {selectedIds.length === 1 ? "1 selected" : `${selectedIds.length} selected`}
      </span>
      <Button dense onClick={() => {
        if (!supported) { setRefusal("SOURCE UNSUPPORTED"); return; }
        setRefusal("");
        const desk = useDesk.getState();
        const floorSelection = desk.selectedIds;
        desk.askAbout(targets as AboutChip[]);
        desk.setSelected(floorSelection);
      }}>
        <span aria-hidden="true">✦</span> Ask
      </Button>
      {refusal ? <span className="surface-token" data-chip data-tone="danger" role="status">{refusal}</span> : null}
      <Button dense variant="ghost" onClick={clearSelection} aria-label="Clear selection">
        <span aria-hidden="true">✕</span>
      </Button>
    </div>
  );
}
