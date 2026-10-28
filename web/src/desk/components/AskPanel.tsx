// The Ask window (Betterment Q4, "One Ask window"; DECISIONS #14).
//
// Ask D1 "The question at the top" (canvas ask-direction-2026-10-27,
// ratified 2026-10-27): the composer is the toolbar row (Recent, the scope
// word ▾, the one-line field, the mic, the engine, Ask ⏎); the Recent rail
// folds at the left; the answer is a document whose References are object
// rows that open their windows; a fresh Ask offers three questions built
// from this desk; an Ask that did not answer says why in one line with the
// one verb that fixes it. The parts are askFace.tsx.
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
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { useDesk } from "../store";
import {
  askContexts,
  askTurnsFromThread,
  decideHeldCall,
  dropPendingAsk,
  putPendingAsk,
  readAskRuns,
  readPendingAsks,
  supportedClaims,
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
  type AskRun,
  type PendingAsk,
} from "../ask";
import { aboutCandidates, type AboutCandidate } from "./about/AboutPicker";
import { aboutTarget, type AboutChip } from "../askAbout";
import { appendToNote, undoAppend, type NoteAppend } from "../noteAppend";
import { HAND_MIME } from "../hand/drag";
import { MicButton } from "./MicButton";
import { apiFetch, readableError } from "../../lib/api";
import { useDurableDraft } from "../../lib/durableDraft";
import { qualifiedRef } from "../api";
import { DeskWindowFrame } from "./DeskWindow";
import { Material } from "../surface/Material";
import { PadGadget } from "../surface/gadgets";
import { routeFromWire, type TurnRoute } from "../turnRoute";
import { NoteSendWells } from "../documentSendsLazy";
import { Button } from "../../components/signal/Signal";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { reportWriteFailure } from "../hooks/useWriteReceipt";
import { useEngine, refreshEngine } from "../hooks/useEngine";
import { ActionNotice, StateChip, RunLine, StatusBar, ToolGlyph, reasonVerb, reasonWords, useReadingEndAnchor, type StatusBarItem } from "../surface";
import { openProjectRoomAtResource, openRef, refOpener } from "../openObject";
import { openSurfaceOr } from "../shell";
import { useOptionalRuntimeBus } from "../../runtime/RuntimeBus";
import { busyWords, otherEngineVerb, retryWords } from "../surface/waitWords";
import { deleteThread, getThread, listThreads, type ThreadWire } from "../threads";
import { UsedLines } from "./UsedLines";
import type { AgentUse } from "../used";
import { requestAskReturn } from "../thought-workspace/askReturn";
import { dropMarginAsk, putMarginAsk, updateMarginAsk } from "../thought-workspace/marginAsks";
import { AskSourceFrame } from "./AskSourceFrame";
import {
  ASK_SPRITE, AskClaims, AskComposer, AskEngineWord, AskGroundedWord, AskMore, AskNotAnswered, AskPage, AskPrompts, AskRail, AskReferences, AskScope,
  AskSendButton, AskTurnDoc, AskVerbs, askReasonLine, type AskReferenceRowData,
} from "./askFace";
import { chosenScopeWords, deskPrompts, wholeDeskWords } from "../askPrompts";
import { useNeedsYou } from "../needsYou";
import { humanTime } from "../surface/format";
import { countWords } from "../surface/kit";
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


/** The reasons that mean the engine itself did not answer. */
const ENGINE_DOWN_REASONS = new Set(["did_not_answer", "not_reachable", "timed_out"]);

/** Pass 2 (Ask): one rail row per question. Rows come newest first; a
 *  thread id is listed once, and the same question asked again as a new
 *  ask is one row (the newest), so Recent never repeats a line. */
export function dedupeRailRows<T extends { id: string; title: string }>(rows: readonly T[]): T[] {
  const ids = new Set<string>();
  const questions = new Set<string>();
  const out: T[] = [];
  for (const row of rows) {
    const question = row.title.trim().replace(/\s+/g, " ").toLowerCase();
    if (ids.has(row.id) || (question && questions.has(question))) continue;
    ids.add(row.id);
    if (question) questions.add(question);
    out.push(row);
  }
  return out;
}

/** A row's facts: a bare kind word (`Decision`, `Note`) says nothing more. */
const BARE_KIND_WORDS = new Set(["decision", "note", "task", "project", "person", "meeting", "drawer", "pull request"]);
function factsOf(meta: string | undefined): string {
  return meta && !BARE_KIND_WORDS.has(meta.trim().toLowerCase()) ? meta : "";
}

/** Pass 2 (Ask): one reference row per record. The same ref is one row; the
 *  same name of the same kind with the same facts (a decision kept twice, a
 *  meeting and its memory page) is one row too, the one that opens and says
 *  the most. */
export function dedupeReferenceRows(rows: readonly AskReferenceRowData[]): AskReferenceRowData[] {
  const out: AskReferenceRowData[] = [];
  const score = (row: AskReferenceRowData) => (row.onOpen ? 4 : 0) + (row.lamp ? 2 : 0) + (row.meta ? 1 : 0);
  for (const row of rows) {
    const name = row.title.trim().replace(/\s+/g, " ").toLowerCase();
    // Two rows that read the same (kind, name and facts) are one record to him.
    const at = out.findIndex((known) => known.ref === row.ref || (Boolean(name) && known.kind === row.kind
      && known.title.trim().replace(/\s+/g, " ").toLowerCase() === name
      // W6-B (defect 5): a decision in two states (Proposed, Active) is one
      // decision; the hub keeps its current state, this keeps older answers.
      && (row.kind === "decision" || !factsOf(known.meta) || !factsOf(row.meta) || known.meta === row.meta)));
    if (at < 0) out.push(row);
    else if (score(row) > score(out[at])) out[at] = row;
  }
  return out;
}

/** W6-B (atlas pass 3, defect 6): an answer never cites his own earlier
 *  ask. The hub leaves them out of new answers; this keeps older ones clean. */
export function citedRefs<T extends { ref: string }>(rows: readonly T[]): T[] {
  return rows.filter((row) => !row.ref.startsWith("thread:"));
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

/** Ask D1: the Recent rail's fold, kept per viewer. */
const RAIL_KEY = "holdspeak.ask.rail";
function readRailOpen(): boolean {
  try { return localStorage.getItem(RAIL_KEY) !== "folded"; } catch { return true; }
}
function writeRailOpen(open: boolean): void {
  try { localStorage.setItem(RAIL_KEY, open ? "open" : "folded"); } catch { /* the fold is a convenience */ }
}

/** Only Ask's own threads go on the rail: an interview or a specialist
 *  (a mode or a recipe) thread is not an ask. */
export function isAskThread(row: ThreadWire): boolean {
  return !row.interview && !row.mode && !row.recipe_id;
}

const RELATIONSHIP_WORD: Record<string, string> = {
  direct_report: "Direct report", peer: "Peer", manager: "Manager", skip: "Skip level", stakeholder: "Stakeholder",
};

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
  // Pass 2 (Ask): the engine did not answer this window's last ask, so the
  // toolbar's dot says so until an answer lands (or its check says ready).
  const [engineDown, setEngineDown] = useState(false);
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
  const compact = useCompactViewport();
  const [railPref, setRailPref] = useState(readRailOpen);
  // On a phone the rail is a sheet over the page: closed until asked for.
  const [railSheet, setRailSheet] = useState(false);
  const railOpen = compact ? railSheet : railPref;
  const [recent, setRecent] = useState<{ loading: boolean; error: string; rows: ThreadWire[] }>({ loading: false, error: "", rows: [] });
  const [forgotten, setForgotten] = useState<PendingForget | null>(null);
  const projects = useDesk((s) => s.projects);
  // Betterment Q6: the people the scope menu can find; Ask D1: who waits on him.
  const [people, setPeople] = useState<Array<{ id: string; name: string; kind: string; youOwe: number }>>([]);
  const needs = useNeedsYou();
  const { copy, state: copyState } = useCopyReceipt();
  const [passageOpen, setPassageOpen] = useState(true);
  const [selectedPassage, setSelectedPassage] = useState<AskSelectionHandoff | null>(() => takeAskSelection());
  const [projectReturn, setProjectReturn] = useState<ProjectReturn | null>(() => selectedPassage?.projectReturn ?? null);
  const activeProjectReturn = selectedPassage ? selectedPassage.projectReturn ?? null : projectReturn;
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
  // Ask hub gap 3: which answers show their claims and records.
  const [groundedOpen, setGroundedOpen] = useState<Record<string, boolean>>({});
  const bus = useOptionalRuntimeBus();
  // Ask hub gap 1: the answer's words so far, as the hub sends them.
  const [arriving, setArriving] = useState("");
  useEffect(() => {
    if (!bus) return undefined;
    return bus.subscribe("ask_text", (frame) => {
      const data = (frame as { data?: Record<string, unknown> }).data;
      if (!data || !invocationRef.current || data.invocation_id !== invocationRef.current) return;
      if (typeof data.text === "string") setArriving(data.text);
    });
  }, [bus]);
  // Ask hub gap 5: the asks this viewer left running, claimed back from
  // the hub; `adoptedRef` is the one this window shows while it writes.
  const [pendingAsks, setPendingAsks] = useState<Array<PendingAsk & { run?: AskRun }>>(() => readPendingAsks());
  const adoptedRef = useRef("");
  const liveRef = useRef("");
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

  /** Leave this view's wait. Ask hub gap 5: the hub keeps writing the
   *  answer (only Stop ends a run); the ask stays in Recent as Writing… and
   *  its answer lands there. */
  const abandonRun = useCallback(() => {
    requestId.current += 1;
    pendingRequest.current?.controller.abort();
    pendingRequest.current = null;
    invocationRef.current = "";
    liveRef.current = "";
    adoptedRef.current = "";
    setArriving("");
    setPendingAsks(readPendingAsks());
  }, []);

  /** Stop: the hub is told to stop this run. */
  const cancelRun = (invocationId: string) => {
    if (!invocationId) return;
    dropPendingAsk(invocationId);
    void apiFetch(`/api/ask/${encodeURIComponent(invocationId)}/cancel`, { method: "POST" }).catch(() => undefined);
  };

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
    void apiFetch<{ relationships?: Array<Record<string, unknown>> }>("/api/people/relationships?counts=1")
      .then((body) => {
        if (!live) return;
        setPeople((body?.relationships ?? []).flatMap((row) => {
          const id = String(row.id ?? "");
          const name = String(row.display_name ?? "").trim();
          return id && name && row.state !== "archived"
            ? [{ id, name, kind: String(row.relationship_kind ?? ""), youOwe: Number(row.you_owe_count) || 0 }]
            : [];
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
  /** Ask D1: one pick in the scope menu changes the word: the pick
   *  replaces what the question was about (a drop still adds). */
  const pickAbout = (pick: AboutCandidate) => {
    setSeedAbout([]);
    setThreadAbout([]);
    setFloorContext([]);
    latchAskSelection(null);
    setSelectedPassage(null);
    // No About: the question is about his whole desk.
    if (pick.ref === WHOLE_DESK) return;
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
    liveRef.current = invocationId;
    adoptedRef.current = "";
    setArriving("");
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
    putPendingAsk({ invocationId, question: snapshot.question, threadId: threadId || "", startedAt });
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
    liveRef.current = "";
    dropPendingAsk(invocationId);
    setArriving("");
    setProgress(null);
    setHeld({ threadId: "", calls: [] });
    setRunning(false);
    setRoute(routeFromWire(r.route));
    if (r.deskTools) setDeskTools(true);
    setFinishedElapsedSeconds(Math.max(0, Math.round((Date.now() - startedAt) / 1000)));
    if (!r.ok) {
      const reason = r.reason || "did_not_answer";
      if (ENGINE_DOWN_REASONS.has(reason)) setEngineDown(true);
      setFailedRun({ ...r, reason });
      return;
    }
    setEngineDown(false);
    if (r.threadId) setThreadId(r.threadId);
    setTurns((current) => [...current, {
      key: r.answerId || `${r.threadId || "ask"}:${current.length}:${invocationId}`,
      question: snapshot.question,
      answer: r.output,
      lookedAt: r.lookedAt,
      used: r.used,
      askedAt: startedAt,
      claims: supportedClaims(r.groundingClaims),
    }]);
    setSent(null);
    // The rail shows the new (or continued) ask at the top.
    void readRecent();
  };

  const ask = () => {
    if (!prompt.trim() || pendingRequest.current) return;
    const question = prompt.trim();
    // The snapshot is now the transmission's immutable copy. Clear the
    // durable editor at acceptance so the sent question is visible in the
    // reading area while a new follow-up can be written safely.
    setPrompt("");
    return askQuestion(question, prompt);
  };

  /** Ask a question (the composer's, or an answer's Ask again). */
  const askQuestion = (question: string, typed: string = question) => {
    if (!question.trim() || pendingRequest.current) return;
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
      question: question.trim(),
      prompt: selectionPrompt(typed, selection),
      lens,
      context: asked,
      grounding: refs.length ? { meeting_ids: [], artifact_ids: [], expand: "summary", refs } : null,
      ...(selection?.sourceSnapshot && selection.sourceSnapshot.ref === selection.noteRef
        ? { sourceSnapshot: { ...selection.sourceSnapshot } } : {}),
    };
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
    cancelRun(invocationRef.current);
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
    cancelRun(waiting);
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
      const rows = (await listThreads()).filter(isAskThread);
      if (mounted.current) setRecent({ loading: false, error: "", rows });
    } catch (error) {
      if (mounted.current) setRecent((current) => ({ ...current, loading: false, error: readableError(error) }));
    }
  }, []);
  // Ask D1: the rail is open by default at a desk width, so Recent is read
  // when the window opens (and again after each answer).
  useEffect(() => { void readRecent(); }, [readRecent]);

  /** Ask hub gap 5: what the hub says about the asks this viewer left
   *  running. An answered one joins Recent (and lands here when this window
   *  shows it); one the hub could not answer reads as not answered. */
  const refreshPending = useCallback(async () => {
    const rows = readPendingAsks().filter((row) => row.invocationId !== liveRef.current);
    if (!rows.length) { setPendingAsks([]); return; }
    const runs = await readAskRuns(rows.map((row) => row.invocationId));
    if (!mounted.current) return;
    if (!runs.length) { setPendingAsks(rows); return; }
    const byId = new Map(runs.map((run) => [run.invocationId, run]));
    const kept: Array<PendingAsk & { run?: AskRun }> = [];
    let answered = false;
    for (const row of rows) {
      const run = byId.get(row.invocationId);
      const shown = adoptedRef.current === row.invocationId;
      if (run?.state === "answered") {
        dropPendingAsk(row.invocationId);
        answered = true;
        if (shown && run.threadId) void loadThread(run.threadId);
        continue;
      }
      if (shown && run && run.state !== "running") {
        dropPendingAsk(row.invocationId);
        adoptedRef.current = "";
        invocationRef.current = "";
        setArriving("");
        setRunning(false);
        setFinishedElapsedSeconds(Math.max(0, Math.round((Date.now() - row.startedAt) / 1000)));
        setFailedRun({ ...stoppedRun(), reason: run.reason || "did_not_answer" });
        continue;
      }
      if (shown && run?.text) setArriving((current) => (run.text.length > current.length ? run.text : current));
      kept.push({ ...row, run });
    }
    setPendingAsks(kept);
    if (answered) void readRecent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [readRecent]);
  useEffect(() => { void refreshPending(); }, [refreshPending]);
  const waitingOnHub = pendingAsks.some((row) => !row.run || row.run.state === "running");
  useEffect(() => {
    if (!waitingOnHub) return undefined;
    const timer = window.setInterval(() => { void refreshPending(); }, 2000);
    return () => window.clearInterval(timer);
  }, [waitingOnHub, refreshPending]);

  /** A Writing… (or Not answered) row of the rail, shown on the page. */
  const adoptPending = (row: PendingAsk & { run?: AskRun }) => {
    if (row.threadId) void loadThread(row.threadId);
    else startNew();
    const snapshot: AskRequestSnapshot = { question: row.question, prompt: row.question, lens, context: [], grounding: null };
    setSent(snapshot);
    setRunStartedAt(row.startedAt);
    if (row.run && row.run.state !== "running") {
      dropPendingAsk(row.invocationId);
      setPendingAsks((current) => current.filter((known) => known.invocationId !== row.invocationId));
      setFinishedElapsedSeconds(undefined);
      setFailedRun({ ...stoppedRun(), reason: row.run.reason || "did_not_answer" });
      return;
    }
    adoptedRef.current = row.invocationId;
    invocationRef.current = row.invocationId;
    setArriving(row.run?.text || "");
    setRunning(true);
  };
  const toggleRail = () => {
    if (compact) { setRailSheet((open) => !open); return; }
    setRailPref((open) => {
      writeRailOpen(!open);
      return !open;
    });
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
  // Pass 2 (Ask): an answer lands at its question, not at its References.
  // When a turn is added (an answer, or a kept ask opened from Recent) the
  // page puts the newest question at its top; the end anchor then keeps out.
  const newestTurn = turns.at(-1)?.key ?? "";
  useLayoutEffect(() => {
    const reading = readingRef.current;
    if (!newestTurn || !reading) return;
    const heads = reading.querySelectorAll<HTMLElement>("[data-testid=ask-turn] .desk-ask-q");
    const head = heads[heads.length - 1];
    if (!head) return;
    const offset = head.getBoundingClientRect().top - reading.getBoundingClientRect().top;
    reading.scrollTop = Math.max(0, reading.scrollTop + offset - 8);
  }, [newestTurn]);
  const lastRoute = route;
  const savedCount = Object.keys(saved).length;
  // Ask D1: the status bar counts the running answer's seconds (no spinner).
  const [runSeconds, setRunSeconds] = useState(0);
  useEffect(() => {
    if (!running || !runStartedAt) { setRunSeconds(0); return undefined; }
    const tick = () => setRunSeconds(Math.max(0, Math.floor((Date.now() - runStartedAt) / 1000)));
    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [running, runStartedAt]);
  const statusLine = running
    ? ""
    : [
        promptRecovered ? "Draft kept" : "",
        lastRoute?.fallback ? "Fallback" : "",
        sourceReturnReceipt,
      ].filter(Boolean).join(" · ");

  // What the scope covers (the status bar of a fresh Ask).
  const since = weekStart();
  const meetingsThisWeek = (items.meeting ?? []).filter((m) => Date.parse(String(m.startedAt || "")) >= since).length;
  const coverage = about.length
    ? chosenScopeWords(about.map((row) => row.ref))
    : wholeDeskWords({ projects: projects.length, meetingsThisWeek, people: people.length, decisions: (items.decision ?? []).length }, compact);
  const prompts = useMemo(() => deskPrompts({
    needsCount: needs.count,
    decisions: (items.decision ?? []).map((d) => ({ title: String(d.title || ""), status: d.status, tags: d.tags, createdAt: d.createdAt, decidedAt: d.decidedAt })),
    waiting: people.filter((p) => p.youOwe > 0),
    meetingsThisWeek,
  }), [needs.count, items.decision, people, meetingsThisWeek]);

  const chooseEngine = () => openSurfaceOr("configure-runs-on", "/settings", "models");

  /** A reference row. Ask hub gap 2: the hub sends each row's kind, time
   *  and state; the desk store fills what the hub did not send. A ref with
   *  no desk window (a pull request) names what was read and does not open. */
  const referenceRow = (row: LookedAt): AskReferenceRowData => {
    const [rawPrefix, ...rest] = row.ref.split(":");
    const prefix = row.kind || rawPrefix;
    const id = rest.join(":");
    const open = refOpener(row.ref) ? () => openRef(row.ref, { projectReturn: activeProjectReturn }) : undefined;
    const base = { ref: row.ref, title: row.title, onOpen: open };
    const word = (state: string) => state.charAt(0).toUpperCase() + state.slice(1).replace(/_/g, " ");
    const timed = (noun: string, at?: string) => {
      const when = at ? humanTime(at) : "";
      return when ? `${noun} · ${when}` : noun;
    };
    switch (prefix) {
      case "meeting": {
        const m = (items.meeting ?? []).find((x) => x.id === id);
        return { ...base, kind: "meeting", meta: timed("Meeting", row.at || m?.startedAt) };
      }
      case "note": {
        const n = (items.note ?? []).find((x) => x.id === id);
        return { ...base, kind: "note", meta: timed("Note", row.at || n?.createdAt) };
      }
      case "desk_decision":
      case "decision_record":
      case "decision": {
        const d = (items.decision ?? []).find((x) => x.id === id);
        const status = row.state || d?.status || "";
        return { ...base, kind: "decision", meta: status ? word(status) : "Decision", lamp: status === "accepted" || status === "active" ? "ok" : status === "proposed" ? "info" : status ? "idle" : undefined };
      }
      case "project": return { ...base, kind: "project", meta: row.state ? `Project · ${word(row.state)}` : "Project" };
      case "people":
      case "person": {
        const p = people.find((x) => x.id === id);
        return { ...base, kind: "person", meta: (p && RELATIONSHIP_WORD[p.kind]) || "Person" };
      }
      case "action":
      case "action_item": return { ...base, kind: "action", meta: row.state ? `Task · ${word(row.state)}` : "Task" };
      case "directory": return { ...base, kind: "directory", meta: "Drawer" };
      // A kept ask the answer read: named as one, with the Ask drawing.
      case "thread": return { ...base, kind: "thread", meta: "Earlier ask" };
      // A calendar entry is the meeting it books (one row with the meeting).
      case "calendar_event": return { ...base, kind: "meeting", meta: timed("Meeting", row.at) };
      case "pr":
      case "github": {
        const meta = [row.state ? word(row.state) : "", row.at ? humanTime(row.at) : ""].filter(Boolean).join(" · ");
        return { ...base, kind: "pr", meta: meta ? `Pull request · ${meta}` : "Pull request", lamp: row.state === "open" ? "info" : row.state === "merged" ? "ok" : undefined };
      }
      default: return { ...base, kind: "note", meta: row.state ? word(row.state) : undefined };
    }
  };

  // Window grammar: the status bar says what runs (with Stop), why an Ask
  // was not answered, what the scope covers, and the receipts in warm words.
  // The engine is named in the composer row (by name; no place word, no
  // address: owner ruling 2026-10-25).

  // The records said are the rows References shows (after the dedupe).
  const newestTurnRefs = turns.at(-1)?.lookedAt;
  const newestRefs = newestTurnRefs ? dedupeReferenceRows(citedRefs(newestTurnRefs).map(referenceRow)).length : 0;
  const answered = !running && !failedRun && turns.length > 0
    ? ["Answered", countWords(newestRefs, "record"), finishedElapsedSeconds ? `${finishedElapsedSeconds} s` : ""].filter(Boolean).join(" · ")
    : "";
  const statusItems: StatusBarItem[] = [
    answered ? { key: "answered", lamp: "ok", text: answered, testId: "ask-status-answered" } : null,
    running ? { key: "asking", lamp: "info", text: `Writing the answer · ${runSeconds} s`, testId: "ask-status-asking" } : null,
    !running && failedRun ? { key: "failed", text: failedRun.reason === "stopped" ? "Stopped · your question is kept" : "Not answered · your question is kept", testId: "ask-status-failed" } : null,
    statusLine ? { key: "receipt", text: statusLine, testId: "ask-status-receipt" } : null,
    savedCount && !running ? { key: "saved", lamp: "ok", text: savedCount === 1 ? "Saved as note" : `${savedCount} answers saved as notes`, testId: "ask-status-saved" } : null,
    copyState === "copied" ? { key: "copy", lamp: "ok", text: "Copied", testId: "ask-status-copied" } : null,
    copyState === "failed" ? { key: "copy", lamp: "fail", text: "Not copied", testId: "ask-status-copied" } : null,
    // The scope line stays whenever nothing else is said (a kept ask opening).
    coverage && (!hasConversation || (!running && !failedRun && !answered)) ? { key: "scope", text: coverage, testId: "ask-status-scope" } : null,
  ].filter(Boolean) as StatusBarItem[];

  const PENDING_ROW = "pending:";
  const railRows = dedupeRailRows([
    ...pendingAsks.map((row) => ({
      id: `${PENDING_ROW}${row.invocationId}`, title: row.question || "An ask with no question", at: row.startedAt,
      state: (row.run && row.run.state !== "running" ? "not_answered" : "writing") as "writing" | "not_answered",
    })),
    ...recent.rows
      .filter((row) => row.id !== forgotten?.threadId)
      .map((row) => ({ id: row.id, title: row.title?.trim() || "An ask with no question", at: row.last_turn_at || row.updated_at })),
  ]);
  const pickRail = (id: string) => {
    if (!id.startsWith(PENDING_ROW)) { void loadThread(id); return; }
    const row = pendingAsks.find((known) => `${PENDING_ROW}${known.invocationId}` === id);
    if (row) adoptPending(row);
  };

  const notAnswered = (result: AskRunResult) => {
    const reason = result.reason || "did_not_answer";
    const words = askReasonLine(reason, reasonWords(reason, engine.model, finishedElapsedSeconds));
    const label = reason === "no_engine" ? "Choose engine"
      : reason === "source_changed" || reason === "source_gone" ? "" : reasonVerb(reason);
    const verb = !label ? undefined : reason === "no_engine"
      ? <Button dense variant="primary" onClick={chooseEngine}>{label}</Button>
      : sent ? <Button dense variant="secondary" onClick={() => void run(sent)}>{label}</Button> : undefined;
    return <AskNotAnswered reason={reason} words={words} verb={verb} />;
  };

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
      <div className="desk-pullout-body desk-ask-body" data-testid="ask-body" data-rail={railOpen ? "open" : "folded"} onDragOver={onAboutDragOver} onDrop={onAboutDrop} onKeyDown={(event) => {
        // The frame owns Escape from this window. An IME uses Escape to
        // finish composition, so that event must not close the writer.
        if (event.key === "Escape" && event.nativeEvent.isComposing) event.stopPropagation();
        // ⌘N: a new ask in this window (the rail's first row).
        if ((event.metaKey || event.ctrlKey) && !event.shiftKey && event.key.toLowerCase() === "n") {
          event.preventDefault();
          startNew();
          promptRef.current?.focus();
        }
      }}>
        <AskComposer
          className="conversation-composer desk-ask-composer"
          data-testid="ask-toolbar"
          railOpen={railOpen}
          onRail={toggleRail}
          scope={
            <AskScope
              rows={about}
              candidates={candidates}
              weekCount={meetingsThisWeek}
              onPick={pickAbout}
              onRemove={(row) => removeAbout(row.ref)}
              onOpenRow={(row) => (row.ref === THIS_WEEK ? undefined : () => openRef(row.ref, { projectReturn: activeProjectReturn }))}
              compact={compact}
            />
          }
          field={
            <PadGadget
              label="Ask about your work"
              mic={false}
              rows={1}
              autoGrow
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
          }
          capture={
            <MicButton
              label="Speak your question"
              draftScope="desk-ask"
              onText={(text) => setPrompt((current) => current ? `${current} ${text}` : text)}
            />
          }
          engine={
            <AskEngineWord
              state={engine.state}
              name={engine.model}
              down={engineDown || Boolean(engine.down)}
              title={engine.state === "set" ? (deskTools ? DESK_TOOLS_WORDS : "No desk tools") : undefined}
              onPress={engine.state === "failed" ? () => void refreshEngine("ask.answer") : chooseEngine}
            />
          }
          action={<AskSendButton disabled={running || !prompt.trim()} onClick={() => void ask()} />}
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
        />
        {forgotten ? (
          <ActionNotice tone="info" action={{ label: "Undo", onClick: undoForget }}>
            Forgotten: {forgotten.title}
          </ActionNotice>
        ) : null}

        <div className="desk-ask-main">
          {railOpen ? (
            <AskRail
              rows={railRows}
              selectedId={adoptedRef.current ? `pending:${adoptedRef.current}` : threadId}
              sheet={compact}
              loading={recent.loading}
              failed={Boolean(recent.error)}
              onRetry={() => void readRecent()}
              onNew={() => { setRailSheet(false); startNew(); promptRef.current?.focus(); }}
              onPick={(id) => { setRailSheet(false); pickRail(id); }}
            />
          ) : null}
          {hasConversation ? (
            <AskPage readingRef={readingRef}>
              {threadRead.loading ? <li className="desk-ask-turn"><RunLine phase="running" verb="Opening" /></li> : null}
              {threadRead.error ? (
                <li className="desk-ask-turn">
                  <ActionNotice role="alert" tone="warn" action={threadId ? { label: "Try again", onClick: () => void loadThread(threadId) } : undefined}>
                    <StateChip state="unreachable" label="This ask was not read" />
                  </ActionNotice>
                </li>
              ) : null}
              {turns.map((turn) => (
                <AskTurnDoc key={turn.key} question={turn.question} at={turn.askedAt}>
                  <div className="desk-ask-answer"><Material>{turn.answer}</Material></div>
                  <AskReferences rows={dedupeReferenceRows(citedRefs(turn.lookedAt).map(referenceRow))} />
                  <UsedLines used={usedWithTasks(turn.used, tasks[turn.key])} testPrefix="ask" lookedAt={false} />
                  <AskVerbs>
                    {saved[turn.key] ? (
                      <Button dense variant="secondary" onClick={() => openRef(saved[turn.key], { projectReturn: activeProjectReturn })}><ToolGlyph kind="open" />Open note</Button>
                    ) : (
                      <Button dense variant="secondary" loading={saving === turn.key} onClick={() => void saveAsNote(turn)}>{saving === turn.key ? null : <ToolGlyph kind="note" />}Save as note</Button>
                    )}
                    <Button dense variant="ghost" onClick={() => void copy(turn.answer)}><ToolGlyph kind="copy" />Copy</Button>
                    <Button dense variant="ghost" disabled={running} onClick={() => void askQuestion(turn.question)}><ToolGlyph kind="retry" />Ask again</Button>
                    <Button dense variant="ghost" aria-expanded={sending === turn.key} onClick={() => void sendAnswer(turn)}><ToolGlyph kind="send" />Send…</Button>
                    <AskGroundedWord
                      records={new Set(supportedClaims(turn.claims).map((claim) => claim.ref)).size}
                      open={Boolean(groundedOpen[turn.key])}
                      onToggle={() => setGroundedOpen((current) => ({ ...current, [turn.key]: !current[turn.key] }))}
                    />
                    <AskMore>
                      {(closeMore) => (
                        <>
                          {threadId && !tasks[turn.key] && !(turn.used?.wrote ?? []).some((row) => row.ref.startsWith("action_item:")) ? (
                            <Button variant="chrome" loading={makingTask === turn.key} onClick={() => { closeMore(); void makeTask(turn); }}>
                              <ToolGlyph kind="tasks" /><span className="desk-menu-label">Make it a task</span>
                            </Button>
                          ) : null}
                          {fromNote && !added[turn.key] ? (
                            <Button variant="chrome" loading={adding === turn.key} onClick={() => { closeMore(); void addToNote(turn); }}>
                              <ToolGlyph kind="note" /><span className="desk-menu-label">Add to note</span>
                            </Button>
                          ) : null}
                          {threadId || turns.length ? (
                            <Button variant="chrome" onClick={() => { closeMore(); forget(); }}>
                              <span className="desk-menu-label">Forget</span>
                            </Button>
                          ) : null}
                        </>
                      )}
                    </AskMore>
                  </AskVerbs>
                  {groundedOpen[turn.key] && supportedClaims(turn.claims).length ? (
                    <AskClaims
                      claims={supportedClaims(turn.claims)}
                      onOpen={(ref) => (refOpener(ref) ? () => openRef(ref, { projectReturn: activeProjectReturn }) : undefined)}
                    />
                  ) : null}
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
                </AskTurnDoc>
              ))}
              {sent && (running || failedRun) ? (
                <AskTurnDoc testId={null} question={sent.question} at={runStartedAt}>
                  {running ? (
                    <div className="desk-ask-running">
                      {/* Ask hub gap 1: the words arrive here as the hub
                          sends them; before the first word, one quiet line.
                          The seconds and Stop are in the status bar. */}
                      {arriving ? (
                        <div className="desk-ask-answer desk-ask-arriving" data-testid="ask-arriving" aria-live="polite"><Material>{arriving}</Material></div>
                      ) : (
                        <span className="desk-ask-reading-line" data-testid="run-line" data-state="running">
                          {progress ? progressWords(progress) : "Reading your desk"}
                        </span>
                      )}
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
                    </div>
                  ) : null}
                  {failedRun ? notAnswered(failedRun) : null}
                </AskTurnDoc>
              ) : null}
            </AskPage>
          ) : (
            <AskPage readingRef={readingRef} empty testId="ask-empty">
              <AskPrompts prompts={prompts} onPrompt={prefillPrompt} />
            </AskPage>
          )}
        </div>
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
