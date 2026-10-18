import { SurfaceFooter } from "../surface/SurfaceFooter";
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
// Before Q4 this was HSM-16-04's Ask AI card (keep or bin one answer) and
// HS-111-05's query console; the Thread window is parked
// (`pullouts/_parked/ThreadPullout.tsx`).
import "./chrome-menus.css";
import "./ask-panel.css";
import "../surface/patterns/conversation.css";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useDesk } from "../store";
import {
  ASK_LENSES,
  askContexts,
  askTurnsFromThread,
  latchAskSelection,
  saveAnswerAsNote,
  selectionPrompt,
  takeAskSelection,
  ASK_SELECTION_EVENT_NAME,
  runAsk,
  type AskSelectionHandoff,
  type AskContext,
  type AskRunResult,
  type AskTurn,
  type LookedAt,
} from "../ask";
import {
  buildGrounding,
  emptyGrounding,
  groundingReceiptRows,
  groundingTokens,
  railsTokens,
  type GroundingSelection,
  type RailsPick,
} from "../grounding";
import { GroundingSection } from "./GroundingSection";
import { RailsPicker } from "./RailsPicker";
import { MicButton } from "./MicButton";
import { apiFetch, readableError } from "../../lib/api";
import { useOnDeskChanged } from "../useDeskChangedRefresh";
import { useDurableDraft } from "../../lib/durableDraft";
import { qualifiedRef } from "../api";
import { DeskWindowFrame } from "./DeskWindow";
import { Material } from "../surface/Material";
import { ScrollHint, SurfaceTraffic, SurfaceTrafficTurn } from "../surface/Surface";
import { LedMeter, FoldGadget, PadGadget } from "../surface/gadgets";
import { RouteEgressChip, TurnLamp, routeFromWire, type TurnRoute } from "../turnRoute";
import { Button } from "../../components/signal/Signal";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { reportWriteFailure } from "../hooks/useWriteReceipt";
import { useEngine, refreshEngine } from "../hooks/useEngine";
import { ActionNotice, StateChip, EngineLine, RunLine, reasonVerb, reasonWords } from "../surface";
import { humanTime } from "../surface/format";
import { openRef } from "../openObject";
import { openSurfaceOr } from "../shell";
import { useOptionalRuntimeBus } from "../../runtime/RuntimeBus";
import { busyWords, otherEngineVerb, retryWords } from "../surface/waitWords";
import { deleteThread, getThread, listThreads, type ThreadWire } from "../threads";

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

/** The budget figure: 0.3K / 16.4K. */
const fmtK = (n: number): string => `${(n / 1000).toFixed(1)}K`;

/** Forget waits this long for Undo before the thread is deleted. */
export const FORGET_UNDO_MS = 10_000;

/** The egress chip names the lamp, never the host (no host strings on Ask). */
function withoutHost(route: TurnRoute): TurnRoute {
  return { ...route, host: "" };
}

/** The face's record of a run he stopped. */
function stoppedRun(): AskRunResult {
  return {
    ok: false, output: "", reason: "stopped", invocationId: "", refusalCode: "", egress: null,
    model: "", profileId: null, inferenceTarget: null, actualPlacement: null, contextIds: [],
    contextTitles: [], groundingClaims: [], groundingReceipt: null, threadId: "", lookedAt: [],
  };
}

/** This copy belongs to the transmission, never to the editable draft. */
interface AskRequestSnapshot {
  question: string;
  prompt: string;
  lens: string;
  context: AskContext[];
  grounding: ReturnType<typeof buildGrounding>;
}

interface PendingForget {
  threadId: string;
  title: string;
  timer: number;
}

export function AskPanel() {
  const items = useDesk((s) => s.items);
  const selectedIds = useDesk((s) => s.selectedIds);
  const askThread = useDesk((s) => s.askThread);
  const { closeAsk, clearSelection, markNew } = useDesk.getState();

  // The desk lens strip is parked; its default still names the run.
  const lens = ASK_LENSES[0].name;
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
  const [grounding, setGrounding] = useState<GroundingSelection>(emptyGrounding());
  const [rails, setRails] = useState<RailsPick[]>([]);
  const [projects, setProjects] = useState<Array<{ id: string; name: string }>>([]);
  const [projectsRead, setProjectsRead] = useState<{ loading: boolean; known: boolean; error: string }>({ loading: true, known: false, error: "" });
  const projectsReads = useRef(0);
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  const [passageOpen, setPassageOpen] = useState(true);
  const readingRef = useRef<HTMLDivElement | null>(null);
  const aboutRef = useRef<HTMLDivElement | null>(null);
  const mounted = useRef(true);
  const requestId = useRef(0);
  const pendingRequest = useRef<{ id: number; controller: AbortController } | null>(null);
  // Betterment Q2: the running Ask's identity, so its progress frames
  // (busy, trying again) reach this window and no other.
  const invocationRef = useRef("");
  const [progress, setProgress] = useState<AskProgress | null>(null);
  const bus = useOptionalRuntimeBus();
  useEffect(() => {
    if (!bus) return undefined;
    return bus.subscribe("ask_progress", (frame) => {
      const data = (frame as { data?: Record<string, unknown> }).data;
      if (!data || !invocationRef.current || data.invocation_id !== invocationRef.current) return;
      if (data.state === "busy") {
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
    abandonRun();
    latchAskSelection(null);
    clearSelection();
    closeAsk();
  }, [abandonRun, clearSelection, closeAsk]);

  /** A new Ask in this window: nothing kept is touched. */
  const startNew = useCallback(() => {
    abandonRun();
    setThreadId(null);
    setTurns([]);
    setThreadAbout([]);
    setSent(null);
    setRunning(false);
    setFailedRun(null);
    setRoute(null);
    setProgress(null);
    setSaved({});
    setThreadRead({ loading: false, error: "" });
  }, [abandonRun]);

  /** Open a kept thread in this window (Recent, a thread's ref, a restored desk). */
  const loadThread = useCallback(async (id: string) => {
    startNew();
    setThreadId(id);
    setThreadRead({ loading: true, error: "" });
    try {
      const detail = await getThread(id);
      if (!mounted.current) return;
      const { turns: kept, about } = askTurnsFromThread(detail);
      setTurns(kept);
      setThreadAbout(about);
      setThreadRead({ loading: false, error: "" });
    } catch (error) {
      if (!mounted.current) return;
      setThreadRead({ loading: false, error: readableError(error) });
    }
  }, [startNew]);

  // The store asks for a thread (or a new Ask): follow each request once.
  const handledNonce = useRef(0);
  useEffect(() => {
    if (!askThread || askThread.nonce === handledNonce.current) return;
    handledNonce.current = askThread.nonce;
    if (askThread.threadId) void loadThread(askThread.threadId);
    else startNew();
  }, [askThread, loadThread, startNew]);

  // The newest answer stays in view.
  useEffect(() => {
    const reading = readingRef.current;
    if (reading && typeof reading.scrollTo === "function") reading.scrollTo({ top: reading.scrollHeight });
  }, [turns.length, running]);

  const [selectedPassage, setSelectedPassage] = useState<AskSelectionHandoff | null>(() => takeAskSelection());
  const context = useMemo(() => {
    const selected = askContexts(items, selectedIds);
    const source = selectedPassage?.source;
    if (!source || source.ref !== selectedPassage.noteRef) return selected;
    // An explicit Note handoff names the saved source, even before a desk
    // collection read or after the floor drops a non-icon selection.
    return [...selected.filter((entry) => entry.ref !== source.ref), { ...source }];
  }, [items, selectedIds, selectedPassage]);
  useEffect(() => {
    const onSelection = (event: Event) => {
      const next = (event as CustomEvent<AskSelectionHandoff | null>).detail;
      // The mounted window owns this handoff now. Clear the module latch so
      // a later mount cannot replay a quote already shown here.
      takeAskSelection();
      setSelectedPassage(next && (next.text.trim() || next.source) ? next : null);
      if (next) setPassageOpen(true);
    };
    window.addEventListener(ASK_SELECTION_EVENT_NAME, onSelection);
    return () => window.removeEventListener(ASK_SELECTION_EVENT_NAME, onSelection);
  }, []);
  useEffect(() => {
    if (selectedPassage?.source) return;
    const noteItems = items.note || [];
    const noteKnown = noteItems.length > 0;
    const noteStillExists = noteItems.some((item) => qualifiedRef("note", item.id) === selectedPassage?.noteRef);
    if (selectedPassage && (!selectedIds.includes(selectedPassage.noteRef) || (noteKnown && !noteStillExists) || (context.length > 0 && !context.some((entry) => entry.ref === selectedPassage.noteRef)))) {
      setSelectedPassage(null);
    }
  }, [context, items.note, selectedIds, selectedPassage]);
  const readProjects = useCallback(async () => {
    const order = ++projectsReads.current;
    setProjectsRead((current) => ({ ...current, loading: true }));
    try {
      const body = await apiFetch<{ projects?: Array<{ id: string; name: string; is_archived?: boolean }> }>("/api/projects");
      if (!mounted.current || order !== projectsReads.current) return;
      setProjects((body.projects ?? []).filter((project) => !project.is_archived));
      setProjectsRead({ loading: false, known: true, error: "" });
    } catch (error) {
      if (mounted.current && order === projectsReads.current) setProjectsRead((current) => ({ ...current, loading: false, error: readableError(error) }));
    }
  }, []);
  useEffect(() => { void readProjects(); }, [readProjects]);
  useOnDeskChanged(() => { void readProjects(); });
  const groundableResources = useMemo(
    () => [
      ...(items.note || []).map((item) => ({ ref: qualifiedRef("note", item.id), kind: "Note", id: item.id, title: String(item.title || "Note with no title") })),
      ...(items.kb || []).map((item) => ({ ref: qualifiedRef("kb", item.id), kind: "Knowledge", id: item.id, title: String(item.name || "Collection with no name") })),
      ...(items.directory || []).map((item) => ({ ref: qualifiedRef("directory", item.id), kind: "Zone", id: item.id, title: String(item.name || "Drawer with no name") })),
      ...projects.map((project) => ({ ref: `project:${project.id}`, kind: "Project", id: project.id, title: project.name || "Project with no name" })),
    ],
    [items, projects],
  );
  // The editor receives the server's compatible chain. The Ask window has no
  // browser-selected destination whose context window it can invent.
  const limitTokens = 16_384;
  const groundTokens = groundingTokens(grounding) + railsTokens(rails);
  const overBudget = groundTokens > limitTokens;

  // About: the objects he chose (selection, pickers) and what a reopened
  // thread was about. Empty means his whole desk.
  const about: LookedAt[] = useMemo(() => {
    const rows: LookedAt[] = [];
    const add = (ref: string | undefined, title: string) => {
      if (!ref || rows.some((row) => row.ref === ref)) return;
      rows.push({ ref, title });
    };
    for (const entry of context) add(entry.ref || qualifiedRef(entry.kind, entry.id), entry.title);
    for (const entry of groundingReceiptRows(grounding)) add(entry.ref, entry.title);
    for (const entry of threadAbout) add(entry.ref, entry.title);
    return rows;
  }, [context, grounding, threadAbout]);

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
    const r = await runAsk({
      prompt: snapshot.prompt,
      lens: snapshot.lens,
      context: snapshot.context,
      grounding: snapshot.grounding,
      signal: controller.signal,
      invocationId,
      thread: threadId || true,
    });
    if (!mounted.current || controller.signal.aborted || pendingRequest.current?.id !== id) return;
    pendingRequest.current = null;
    invocationRef.current = "";
    setProgress(null);
    setRunning(false);
    setRoute(routeFromWire(r.route));
    setFinishedElapsedSeconds(Math.max(0, Math.round((Date.now() - startedAt) / 1000)));
    if (!r.ok) {
      setFailedRun({ ...r, reason: r.reason || "did_not_answer" });
      return;
    }
    if (r.threadId) setThreadId(r.threadId);
    setTurns((current) => [...current, {
      key: `${r.threadId || "ask"}:${current.length}:${invocationId}`,
      question: snapshot.question,
      answer: r.output,
      lookedAt: r.lookedAt,
    }]);
    setSent(null);
    // The question was asked: the follow-up box starts empty.
    setPrompt("");
  };

  const ask = () => {
    if (!prompt.trim() || pendingRequest.current || overBudget) return;
    const selection = selectedPassage?.text.trim() && context.some((entry) => entry.ref === selectedPassage.noteRef)
      ? { ...selectedPassage }
      : null;
    // Every nested value is built here. Later selections and picker changes
    // cannot rewrite Ask again.
    // A reopened thread's About rides its follow-ups as grounding refs.
    const picked = buildGrounding(grounding, rails);
    const carried = threadAbout.map((row) => row.ref).filter((ref) => !context.some((entry) => entry.ref === ref));
    const refs = Array.from(new Set([...(picked?.refs ?? []), ...carried]));
    const snapshot: AskRequestSnapshot = {
      question: prompt.trim(),
      prompt: selectionPrompt(prompt, selection),
      lens,
      context: context.map((entry) => ({ ...entry })),
      grounding: refs.length
        ? { meeting_ids: [], artifact_ids: [], expand: "summary", ...picked, refs }
        : picked,
    };
    return run(snapshot);
  };

  /** Stop ends the wait and tells the hub; the question stays, marked
   *  stopped, with Ask again. */
  const stop = () => {
    abandonRun();
    setRunning(false);
    setProgress(null);
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

  const saveAsNote = async (turn: AskTurn) => {
    if (saving || saved[turn.key]) return;
    setSaving(turn.key);
    const ref = await saveAnswerAsNote(turn);
    if (!mounted.current) return;
    setSaving(null);
    if (!ref) {
      reportWriteFailure("Save as note", new Error("The answer was not saved as a note. It is still here; try again."));
      return;
    }
    setSaved((current) => ({ ...current, [turn.key]: ref }));
    markNew(ref.slice("note:".length));
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
  const lastRoute = route;
  const statusLine = running
    ? ""
    : [
        promptRecovered ? "Draft kept" : "",
        overBudget ? "Too many notes" : "",
        !failedRun && turns.length && finishedElapsedSeconds ? `Answered in ${finishedElapsedSeconds} s` : "",
        lastRoute?.fallback ? "Fallback" : "",
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
              <span className="desk-ask-recent-title">{row.title?.trim() || "An ask with no question"}</span>
              <span className="desk-ask-recent-age">{humanTime(row.last_turn_at || row.updated_at)}</span>
            </Button>
          </li>
        ))}
      </ul>
    </div>
  ) : null;

  return (
    <DeskWindowFrame
      id="ask"
      glyph="✦"
      label="Ask"
      className={`desk-pullout desk-ask is-card${hasConversation ? " has-traffic" : ""}`}
      icon={<span className="desk-ask-glyph" aria-hidden="true">✦</span>}
      title="Ask"
      actions={<Button dense variant="ghost" aria-expanded={recentOpen} onClick={toggleRecent}>Recent</Button>}
      open
      defaultW={880}
      defaultH={640}
      onClose={close}
    >
      <div className="desk-pullout-body desk-ask-body" onKeyDown={(event) => {
        // The frame owns Escape from this window. An IME uses Escape to
        // finish composition, so that event must not close the writer.
        if (event.key === "Escape" && event.nativeEvent.isComposing) event.stopPropagation();
      }}>
        {recentPanel}
        {forgotten ? (
          <ActionNotice tone="info" action={{ label: "Undo", onClick: undoForget }}>
            Forgotten: {forgotten.title}
          </ActionNotice>
        ) : null}

        <ScrollHint axis="y" scrollRef={aboutRef} className="desk-ask-context-wrap"><div ref={aboutRef} className="desk-ask-question-context">
          <div className="desk-ask-sources desk-ask-about" data-testid="ask-context">
            <span className="desk-ask-about-label">About</span>
            {about.length ? about.map((source) => (
              <Button key={source.ref} dense variant="ghost" onClick={() => openRef(source.ref)}>{source.title}</Button>
            )) : <span className="desk-ask-about-desk">My whole desk</span>}
            {rails.map((source) => <span className="surface-token" key={`${source.repo}:${source.kind}:${source.id}`}>{source.title}</span>)}
            {threadAbout.length ? <Button dense variant="ghost" aria-label="Clear About" onClick={() => setThreadAbout([])}>✕</Button> : null}
          </div>
          <div className="desk-ask-context-tools">
            <GroundingSection
              label="Add to About"
              showBudget={false}
              meetings={(items.meeting || []).map((m) => ({ id: m.id, title: String(m.title || "Meeting with no title"), startedAt: m.startedAt }))}
              resources={groundableResources}
              selection={grounding}
              onChange={setGrounding}
              limitTokens={limitTokens}
              meter={false}
            />
            <RailsPicker showBudget={false} picks={rails} onChange={setRails} limitTokens={limitTokens} meter={false} />
            {projectsRead.error ? <ActionNotice role="alert" tone="warn" action={{ label: "Retry Projects", onClick: () => void readProjects() }}>
              <StateChip state="unreachable" label="Projects unavailable" />
              {projectsRead.known ? <>{" · "}<StateChip state="warning" label="Last read" /></> : null}
            </ActionNotice> : null}
          </div>
        </div></ScrollHint>

        {hasConversation ? <ScrollHint axis="y" scrollRef={readingRef} className="desk-ask-reading-wrap"><div ref={readingRef} className="conversation-reading desk-ask-reading" role="region" aria-label="Ask conversation" tabIndex={0}><SurfaceTraffic showEmpty={false}>
          {threadRead.loading ? <SurfaceTrafficTurn prefix="Ask"><RunLine phase="running" verb="Opening" /></SurfaceTrafficTurn> : null}
          {threadRead.error ? (
            <ActionNotice role="alert" tone="warn" action={threadId ? { label: "Try again", onClick: () => void loadThread(threadId) } : undefined}>
              <StateChip state="unreachable" label="This ask was not read" />
            </ActionNotice>
          ) : null}
          {turns.map((turn, index) => (
            <div className="desk-ask-turn" key={turn.key} data-testid="ask-turn">
              <SurfaceTrafficTurn prefix="You">
                <div className="desk-ask-question-text">{turn.question}</div>
              </SurfaceTrafficTurn>
              <SurfaceTrafficTurn
                prefix="Answer"
                meta={index === turns.length - 1 && lastRoute ? <TurnLamp lamp={lastRoute.lamp} /> : null}
                verbs={<>
                  {saved[turn.key] ? (
                    <Button dense variant="ghost" onClick={() => openRef(saved[turn.key])}>Open note</Button>
                  ) : (
                    <Button dense loading={saving === turn.key} onClick={() => void saveAsNote(turn)}>Save as note</Button>
                  )}
                  <Button dense variant="ghost" onClick={() => void copy(turn.answer)}>Copy</Button>
                </>}
              >
                <div className="desk-ask-answer"><Material>{turn.answer}</Material></div>
                {turn.lookedAt.length ? (
                  <FoldGadget title={`Looked at · ${turn.lookedAt.length === 1 ? turn.lookedAt[0].title : `${turn.lookedAt.length} sources`}`} className="desk-ask-reading-fold">
                    <div className="desk-ask-sources desk-ask-answer-sources" data-testid="ask-looked-at">
                      {turn.lookedAt.map((source) => (
                        <Button key={source.ref} dense variant="ghost" onClick={() => openRef(source.ref)}>{source.title}</Button>
                      ))}
                    </div>
                  </FoldGadget>
                ) : null}
                {saved[turn.key] ? <span className="desk-ask-saved" role="status">Saved to your desk</span> : null}
              </SurfaceTrafficTurn>
            </div>
          ))}
          {sent && (running || failedRun) ? (
            <SurfaceTrafficTurn prefix="You">
              <div className="desk-ask-question-text">{sent.question}</div>
            </SurfaceTrafficTurn>
          ) : null}
          {running ? (
            <SurfaceTrafficTurn prefix="Answer">
              <RunLine
                phase="running"
                verb={progressWords(progress)}
                model={progress?.state === "busy" ? "" : engine.model}
                place={progress?.state === "busy" ? "" : engine.place}
                startedAt={runStartedAt}
              />
              {progress?.state === "busy" && progress.alternatives[0] ? (
                <Button dense variant="ghost" data-testid="ask-elsewhere" onClick={() => void askElsewhere(progress.alternatives[0])}>
                  {otherEngineVerb(progress.alternatives[0].label, progress.alternatives[0].boundary)}
                </Button>
              ) : null}
            </SurfaceTrafficTurn>
          ) : null}
          {failedRun ? (
            <SurfaceTrafficTurn prefix="Answer" error meta={<TurnLamp lamp={route?.lamp ?? null} />}>
              <RunLine
                phase="failure"
                reason={failedRun.reason}
                model={engine.model}
                place={route ? "" : engine.place}
                elapsedSeconds={finishedElapsedSeconds}
                onAction={failedRun.reason === "no_engine" ? () => openSurfaceOr("configure-runs-on", "/settings", "models") : undefined}
                onRetry={failedRun.reason !== "no_engine" && reasonVerb(failedRun.reason) && sent ? () => void run(sent) : undefined}
              />
            </SurfaceTrafficTurn>
          ) : null}
        </SurfaceTraffic></div></ScrollHint> : null}

        <div className="conversation-composer desk-ask-composer">
          {selectedPassage?.text.trim() ? (
            <div className="desk-ask-passage" data-testid="ask-selected-passage">
              <FoldGadget title="Selected text" open={passageOpen} onToggle={setPassageOpen}>
                <blockquote>{selectedPassage.text}</blockquote>
                <div className="desk-ask-selection-verbs">
                  <Button dense variant="ghost" onClick={() => openRef(selectedPassage.noteRef)}>Back to note</Button>
                  <Button dense variant="ghost" onClick={() => {
                    const source = selectedPassage.source;
                    latchAskSelection(null);
                    setSelectedPassage(source ? { noteRef: selectedPassage.noteRef, text: "", source } : null);
                  }}>Remove</Button>
                </div>
              </FoldGadget>
            </div>
          ) : null}
          <div className="desk-ask-input">
            <PadGadget
              label="Ask about your work"
              mic={false}
              rows={hasConversation ? 2 : 6}
              value={prompt}
              placeholder={turns.length ? "Ask a follow-up" : "Ask about your work"}
              autoFocus
              onChange={setPrompt}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                  e.preventDefault();
                  void ask();
                }
              }}
            />
            <MicButton
              label="Speak your question"
              draftScope="desk-ask"
              onText={(text) => setPrompt((current) => current ? `${current} ${text}` : text)}
            />
          </div>
          <div className="desk-ask-compose-actions">
            <div className="desk-ask-send">
              {!running ? (
                engine.state === "set" ? (
                  <div className="surface-engine-line" data-testid="engine-line">
                    {[engine.model, engine.place, "reads only what is in About"].filter(Boolean).join(" · ")}
                  </div>
                ) : (
                  <EngineLine
                    engine={engine}
                    onChoose={() => openSurfaceOr("configure-runs-on", "/settings", "models")}
                    onRetry={() => void refreshEngine("ask.answer")}
                  />
                )
              ) : null}
              {running ? (
                <Button variant="primary" onClick={stop}>Stop</Button>
              ) : (
                <Button
                  variant="primary"
                  disabled={!prompt.trim() || overBudget}
                  title={overBudget ? "Too many notes" : undefined}
                  onClick={() => void ask()}
                >Ask</Button>
              )}
            </div>
          </div>
          {overBudget ? <div className="desk-ask-rack-lip">
            <LedMeter label={`Budget ${fmtK(groundTokens)}/${fmtK(limitTokens)}`} value={limitTokens > 0 ? groundTokens / limitTokens : 0} />
          </div> : null}
        </div>
      </div>

      <SurfaceFooter
        className={lastRoute ? "turn-route-footer" : undefined}
        egress={lastRoute ? <RouteEgressChip route={withoutHost(lastRoute)} /> : null}
        receipt={copyReceipt || (statusLine ? <span className="surface-footer-receipt-line" data-tone={overBudget ? "danger" : undefined} role="status">{statusLine}</span> : null)}
        verbs={threadId || turns.length ? <>
          <FoldGadget title="More" className="desk-ask-more">
            <Button dense variant="ghost" onClick={forget}>Forget</Button>
          </FoldGadget>
          <Button dense variant="ghost" onClick={startNew}>New ask</Button>
        </> : null}
      />
    </DeskWindowFrame>
  );
}

/** The bundle bar (the iPad's askBundle grammar): the lasso'd count + the one
 * action that gives the selection meaning. */
export function AskBar() {
  const selectedIds = useDesk((s) => s.selectedIds);
  const askOpen = useDesk((s) => s.askOpen);
  const { openAsk, clearSelection } = useDesk.getState();
  if (!selectedIds.length || askOpen) return null;
  return (
    <div className="desk-askbar" onPointerDown={(e) => e.stopPropagation()}>
      <span className="desk-askbar-count">
        {selectedIds.length === 1 ? "1 selected" : `${selectedIds.length} selected`}
      </span>
      <Button dense onClick={() => openAsk()}>
        <span aria-hidden="true">✦</span> Ask
      </Button>
      <Button dense variant="ghost" onClick={clearSelection} aria-label="Clear selection">
        <span aria-hidden="true">✕</span>
      </Button>
    </div>
  );
}
