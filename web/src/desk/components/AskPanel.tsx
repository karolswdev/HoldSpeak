import { SurfaceFooter } from "../surface/SurfaceFooter";
// The Ask AI atom (HSM-16-04, the web parity of HSM-16-09): the composer is a
// docked in-world panel — the desk stays visible and alive behind it (the
// 17-08 atelier posture, never a modal) — and the result prints as a turn you
// judge: keep (a real synced Artifact carrying every card read + the exact
// instruction) or bin (nothing stored). The egress lamp is per-RUN honest:
// pre-run it names the picked profile's target; printed, it names where the
// run actually went.
// HS-111-05 — the query console (audit §3): the exchange is SurfaceTraffic
// (the OS's one conversation grammar, HS-111-04), the input deck keeps the
// one-well grammar, the pickers ride one etched GROUNDING rack with the
// shared LedMeter budget, the footer is frame-owned, and the
// server's grounding receipt (GROUNDED ON N OF M + openable citations)
// finally reaches this glass.
import "./chrome-menus.css";
import "./ask-panel.css";
import "../surface/patterns/conversation.css";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useDesk } from "../store";
import {
  ASK_LENSES,
  askContexts,
  latchAskSelection,
  keepAsk,
  selectionPrompt,
  takeAskSelection,
  ASK_SELECTION_EVENT_NAME,
  runAsk,
  type AskSelectionHandoff,
  type AskContext,
  type AskRunResult,
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

/** PHILO-13-04 (A3): an Ask that did not answer says so in plain words; the
 * hub's own text (a model path, a refusal sentence) never reaches the face,
 * its title included. A failure that can be asked again names the kept ask
 * and the next step (the product-copy failure facts). */
export function askFailureLabel(_output: string, reason = "did_not_answer"): { label: string; canAskAgain: boolean } {
  return { label: reasonWords(reason), canAskAgain: Boolean(reasonVerb(reason)) };
}
import { useDurableDraft } from "../../lib/durableDraft";
import { qualifiedRef } from "../api";
import { DeskWindowFrame } from "./DeskWindow";
import { Material } from "../surface/Material";
import { ScrollHint, SurfaceState, SurfaceTraffic, SurfaceTrafficTurn } from "../surface/Surface";
import {
  LedMeter,
  FoldGadget,
  PadGadget,
} from "../surface/gadgets";
import {
  RouteEgressChip,
  TurnLamp,
  lastTurnLine,
  routeFromWire,
  routeEgress,
  type TurnRoute,
} from "../turnRoute";
import { CitationChips, groundedMatchCount } from "../surface/citations";
import { Button } from "../../components/signal/Signal";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { reportWriteFailure } from "../hooks/useWriteReceipt";
import { useEngine, refreshEngine } from "../hooks/useEngine";
import { ActionNotice, StateChip, EngineLine, RunLine, reasonVerb, reasonWords } from "../surface";
import { openRef } from "../openObject";
import { openSurfaceOr } from "../shell";
import { useOptionalRuntimeBus } from "../../runtime/RuntimeBus";
import { busyWords, otherEngineVerb, retryWords } from "../surface/waitWords";

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
  if (!progress) return "Asking";
  if (progress.state === "busy") return busyWords(progress.job, progress.engine?.boundary);
  return retryWords(progress.attempt, progress.of);
}

/** The budget figure the audit names: 0.3K / 16.4K. */
const fmtK = (n: number): string => `${(n / 1000).toFixed(1)}K`;

/** This copy belongs to the transmission, never to the editable draft. */
interface AskRequestSnapshot {
  prompt: string;
  lens: string;
  context: AskContext[];
  grounding: ReturnType<typeof buildGrounding>;
  selection: AskSelectionHandoff | null;
  keepContext: AskContext[];
  railSources: RailsPick[];
}

export function AskPanel() {
  const items = useDesk((s) => s.items);
  const selectedIds = useDesk((s) => s.selectedIds);
  const { closeAsk, clearSelection, markNew } = useDesk.getState();

  // The desk lens strip is parked; its default still names the run.
  const lens = ASK_LENSES[0].name;
  const {
    value: prompt,
    setDraft: setPrompt,
    recovered: promptRecovered,
  } = useDurableDraft("desk-ask", "");
  const engine = useEngine("ask.answer");
  const [phase, setPhase] = useState<"compose" | "routing" | "printed">(
    "compose",
  );
  // The transmission on the log: the YOU> turn as it was sent (the draft
  // keeps editing underneath without rewriting the transcript).
  const [sent, setSent] = useState<AskRequestSnapshot | null>(null);
  const [result, setResult] = useState<AskRunResult | null>(null);
  const [failedRun, setFailedRun] = useState<AskRunResult | null>(null);
  const [runStartedAt, setRunStartedAt] = useState<number | undefined>();
  const [finishedElapsedSeconds, setFinishedElapsedSeconds] = useState<number | undefined>();
  // The run's receipt route (success or refusal): the lamp needs one.
  const [route, setRoute] = useState<TurnRoute | null>(null);
  const [keepError, setKeepError] = useState("");
  const [savedAnswerRef, setSavedAnswerRef] = useState<string | null>(null);
  const kept = Boolean(savedAnswerRef);
  const [isKeeping, setIsKeeping] = useState(false);
  const [grounding, setGrounding] =
    useState<GroundingSelection>(emptyGrounding());
  const [rails, setRails] = useState<RailsPick[]>([]);
  const [projects, setProjects] = useState<Array<{ id: string; name: string }>>(
    [],
  );
  const [projectsRead, setProjectsRead] = useState<{ loading: boolean; known: boolean; error: string }>({ loading: true, known: false, error: "" });
  const projectsReads = useRef(0);
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  const [editingQuestion, setEditingQuestion] = useState(true);
  const [passageOpen, setPassageOpen] = useState(true);
  const questionGeneration = useRef(0);
  const readingRef = useRef<HTMLDivElement | null>(null);
  const questionContextRef = useRef<HTMLDivElement | null>(null);
  const answerRef = useRef<HTMLDivElement | null>(null);
  const mounted = useRef(true);
  const abandoned = useRef(false);
  const requestId = useRef(0);
  const pendingRequest = useRef<{ id: number; controller: AbortController } | null>(null);
  const keeping = useRef(false);
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

  // Abort abandons this view's wait. It makes no claim about the server run.
  const bin = useCallback(() => {
    abandoned.current = true;
    requestId.current += 1;
    pendingRequest.current?.controller.abort();
    pendingRequest.current = null;
    latchAskSelection(null);
    clearSelection();
    closeAsk();
  }, [clearSelection, closeAsk]);

  // A collapsed Question leaves the answer at the top of the new reading.
  // Editing, receipts and source reads must not move the reading position.
  useEffect(() => {
    const reading = readingRef.current;
    if (result && reading) reading.scrollTop = 0;
  }, [result]);

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
      // The mounted composer owns this handoff now. Clear the module latch so
      // a later mount cannot replay a quote already shown in this composer.
      takeAskSelection();
      setSelectedPassage(next && (next.text.trim() || next.source) ? next : null);
      if (next) {
        questionGeneration.current += 1;
        setEditingQuestion(true);
        setPassageOpen(true);
      }
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
      ...(items.note || []).map((item) => ({
        ref: qualifiedRef("note", item.id),
        kind: "Note",
        id: item.id,
        title: String(item.title || item.id),
      })),
      ...(items.kb || []).map((item) => ({
        ref: qualifiedRef("kb", item.id),
        kind: "Knowledge",
        id: item.id,
        title: String(item.name || item.id),
      })),
      ...(items.directory || []).map((item) => ({
        ref: qualifiedRef("directory", item.id),
        kind: "Zone",
        id: item.id,
        title: String(item.name || item.id),
      })),
      ...projects.map((project) => ({
        ref: `project:${project.id}`,
        kind: "Project",
        id: project.id,
        title: project.name || project.id,
      })),
    ],
    [items, projects],
  );
  // The editor receives the server's compatible chain. The Ask composer has no
  // browser-selected destination whose context window it can invent.
  const limitTokens = 16_384;
  const groundTokens = groundingTokens(grounding) + railsTokens(rails);
  const overBudget = groundTokens > limitTokens;

  const editPrompt = (next: Parameters<typeof setPrompt>[0]) => {
    questionGeneration.current += 1;
    setPrompt(next);
  };

  const run = async (snapshot: AskRequestSnapshot, invocationId = mintInvocationId()) => {
    if (pendingRequest.current || abandoned.current || !mounted.current) return;
    const controller = new AbortController();
    invocationRef.current = invocationId;
    setProgress(null);
    const id = ++requestId.current;
    const generation = questionGeneration.current;
    pendingRequest.current = { id, controller };
    setPhase("routing");
    setKeepError("");
    setSavedAnswerRef(null);
    setResult(null);
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
    });
    if (!mounted.current || abandoned.current || controller.signal.aborted || pendingRequest.current?.id !== id) return;
    pendingRequest.current = null;
    invocationRef.current = "";
    setProgress(null);
    setRoute(routeFromWire(r.route));
    const elapsedSeconds = Math.max(0, Math.round((Date.now() - startedAt) / 1000));
    setFinishedElapsedSeconds(elapsedSeconds);
    if (!r.ok) {
      setFailedRun({ ...r, reason: r.reason || "did_not_answer" });
      setPhase("compose");
      return;
    }
    setResult(r);
    if (generation === questionGeneration.current) setEditingQuestion(false);
    setPhase("printed");
  };

  const ask = () => {
    if (!prompt.trim() || pendingRequest.current || keeping.current || overBudget) return;
    const selection = selectedPassage?.text.trim() && context.some((entry) => entry.ref === selectedPassage.noteRef)
      ? { ...selectedPassage }
      : null;
    const copiedContext = context.map((entry) => ({ ...entry }));
    const keepContext = [
      ...copiedContext,
      ...groundingReceiptRows(grounding)
        .filter((entry) => !copiedContext.some((source) => source.ref === entry.ref))
        .map((entry) => ({ ...entry })),
    ];
    // Every nested value is built here. Later selections and picker changes
    // cannot rewrite Retry or the lineage of this answer.
    const snapshot: AskRequestSnapshot = {
      prompt: selectionPrompt(prompt, selection),
      lens,
      context: copiedContext,
      grounding: buildGrounding(grounding, rails),
      selection,
      keepContext,
      railSources: rails.map((source) => ({ ...source })),
    };
    return run(snapshot);
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

  const keep = async () => {
    if (!result || !sent || kept || keeping.current || abandoned.current) return;
    keeping.current = true;
    const id = requestId.current;
    setKeepError("");
    setIsKeeping(true);
    const artifactId = await keepAsk({
      lens: sent.lens,
      prompt: sent.prompt,
      output: result.output,
      context: sent.keepContext,
    });
    keeping.current = false;
    if (!mounted.current || abandoned.current || requestId.current !== id) return;
    setIsKeeping(false);
    if (artifactId) {
      const ref = `artifact:${artifactId}`;
      setSavedAnswerRef(ref);
      markNew(artifactId);
      // The canonical opener hydrates the exact saved artifact. Keep this
      // mounted writer behind it, including any newer question or sources.
      openRef(ref);
    } else {
      setSavedAnswerRef(null);
      setKeepError("Not kept");
    }
  };

  const receipt = result?.groundingReceipt || null;
  const groundedMatches = groundedMatchCount(receipt);
  const flaggedClaims = (result?.groundingClaims || []).filter(
    (c) => c.flagged,
  );
  // The answer lamp and footer egress come from the hub's receipt route,
  // including a refusal that sent bytes. The 2026-10-17 composition keeps
  // the unchanged detailed receipt in Run details below the answer.
  const printedRoute = sent && (result || failedRun) ? route : null;
  const printedLamp = printedRoute?.lamp ?? null;
  const printedPlace = printedRoute
    ? routeEgress(printedRoute).label || "This device"
    : engine.place;
  // A refusal that sent bytes: the failure is on the HUB> turn; the
  // footer names where they went.
  const hasTraffic = Boolean(sent || failedRun || result || phase === "routing");
  const sourceContext = [
    ...context,
    ...groundingReceiptRows(grounding).filter((source) => !context.some((entry) => entry.ref === source.ref)),
  ];

  // The footer receipt bar's one status line (audit §3.5): fault > routing
  // > plain completion > the compose budget tokens.
  const statusTone = keepError || overBudget ? ("danger" as const) : undefined;
  const statusLine = keepError || (phase === "printed"
      ? `Answered${(finishedElapsedSeconds ?? 0) > 0 ? ` in ${finishedElapsedSeconds} s` : ""}`
      : [
            promptRecovered ? "DRAFT · RECOVERED" : "",
            overBudget ? "Too many notes" : "",
          ]
            .filter(Boolean)
            .join(" · "));

  return (
    <DeskWindowFrame
      id="ask"
      glyph="✦"
      label="Ask AI"
      className={`desk-pullout desk-ask is-card${hasTraffic ? " has-traffic" : ""}`}
      icon={
        <span className="desk-ask-glyph" aria-hidden="true">
          ✦
        </span>
      }
      title="Ask AI"
      open
      defaultW={740}
      defaultH={620}
      onClose={bin}
    >
      <div className="desk-pullout-body desk-ask-body" onKeyDown={(event) => {
        // The frame owns Escape from this window. An IME uses Escape to
        // finish composition, so that event must not close the writer.
        if (event.key === "Escape" && event.nativeEvent.isComposing) event.stopPropagation();
      }}>
        {hasTraffic ? <ScrollHint axis="y" scrollRef={readingRef} className="desk-ask-reading-wrap"><div ref={readingRef} className="conversation-reading desk-ask-reading" role="region" aria-label="Ask answer" tabIndex={0}><SurfaceTraffic showEmpty={false}>
          {sent ? (
            <FoldGadget key={requestId.current} title="Question" className="desk-ask-reading-fold desk-ask-sent-question">
              <div className="desk-ask-question-text">{sent.prompt}</div>
            </FoldGadget>
          ) : null}
          {phase === "routing" ? (
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
          {sent && failedRun ? (
            <SurfaceTrafficTurn
              prefix="Answer"
              error
              meta={<TurnLamp lamp={printedLamp} />}
            >
              <RunLine
                phase="failure"
                reason={failedRun.reason}
                model={engine.model}
                place={printedPlace}
                elapsedSeconds={finishedElapsedSeconds}
                onAction={failedRun.reason === "no_engine"
                  ? () => openSurfaceOr("configure-runs-on", "/settings", "models")
                  : undefined}
                onRetry={failedRun.reason !== "no_engine" && reasonVerb(failedRun.reason) && sent ? () => void run(sent) : undefined}
              />
            </SurfaceTrafficTurn>
          ) : null}
          {result ? (
            <SurfaceTrafficTurn
              prefix="Answer"
              meta={<TurnLamp lamp={printedLamp} />}
              verbs={
                <>
                  <Button
                    dense
                    onClick={() => void copy(result.output)}
                  >
                    Copy
                  </Button>
                </>
              }
            >
              <div
                className="desk-ask-answer"
                ref={answerRef}
                /* HS-101 B7 — the result drags OUT through the glass:
                   release it over the desk and it is kept (the same keep
                   verb; the desk files the minted artifact). */
                draggable={!kept && !isKeeping}
                title={kept ? undefined : "Drag onto the desk to keep"}
                onDragStart={(e) => {
                  e.dataTransfer.setData(
                    "application/x-holdspeak-chip",
                    "ask",
                  );
                  e.dataTransfer.effectAllowed = "copy";
                }}
                onDragEnd={(e) => {
                  const under = document.elementFromPoint(
                    e.clientX,
                    e.clientY,
                  );
                  if (
                    under &&
                    (under.closest(".desk-world") ||
                      under.classList.contains("desk-world-canvas")) &&
                    !kept
                  ) {
                    void keep();
                  }
                }}
              >
                <Material>{result.output}</Material>
                {/* HS-111-05 — the honesty law reaches this surface: the
                    server's cited retrieval receipt, never inferred, and
                    omitted entirely on a context-free ask. */}
                {receipt || flaggedClaims.length > 0 ? (
                  <div className="desk-ask-receipt">
                    {receipt ? (
                      <>
                        <p className="desk-ask-grounded">
                          {groundedMatches > 0
                            ? `GROUNDED ON ${groundedMatches} OF ${receipt.matchedCount}`
                            : "UNGROUNDED"}
                        </p>
                        <CitationChips refs={receipt.sourceRefs} />
                      </>
                    ) : null}
                    {flaggedClaims.map((c, i) => (
                      <p
                        key={i}
                        className="desk-ask-claim"
                        title="Possibly unsupported by the cited material"
                      >
                        {c.label === "partial" ? "◐" : "◇"} {c.text}
                      </p>
                    ))}
                  </div>
                ) : null}
              </div>
            </SurfaceTrafficTurn>
          ) : null}
          {result && sent && (sent.keepContext.length || sent.railSources.length) ? (
            <FoldGadget title="Sources" className="desk-ask-reading-fold">
              <div className="desk-ask-sources desk-ask-answer-sources" data-testid="ask-answer-sources">
                {sent.keepContext.map((source) => source.ref ? (
                  <Button key={source.ref} dense variant="ghost" onClick={() => openRef(source.ref!)}>{source.title}</Button>
                ) : <span key={source.id}>{source.title}</span>)}
                {sent.railSources.map((source) => <span className="surface-token" key={`${source.repo}:${source.kind}:${source.id}`}>{source.title}</span>)}
              </div>
            </FoldGadget>
          ) : null}
          {printedRoute ? (
            <FoldGadget title="Run details" className="desk-ask-reading-fold">
              <div className="desk-ask-run-details">{lastTurnLine(printedRoute)}</div>
            </FoldGadget>
          ) : null}
        </SurfaceTraffic></div></ScrollHint> : null}

        {editingQuestion && (
          <div className="conversation-composer desk-ask-composer">
            <div className="desk-ask-input">
                <PadGadget
                  label="Ask about your work"
                  mic={false}
                  rows={hasTraffic ? 2 : 6}
                  value={prompt}
                  placeholder="Ask about your work"
                  autoFocus
                  onChange={editPrompt}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                      e.preventDefault();
                      void ask();
                    }
                  }}
                />
                <MicButton
                  label="Speak Ask about your work"
                  draftScope="desk-ask"
                  onText={(text) => editPrompt((current) => current ? `${current} ${text}` : text)}
                />
            </div>
            <ScrollHint axis="y" scrollRef={questionContextRef} className="desk-ask-context-wrap"><div ref={questionContextRef} className="desk-ask-question-context">
            {sourceContext.length || rails.length ? (
              <div className="desk-ask-sources" data-testid="ask-context">
                <span>Question sources:</span>
                {sourceContext.map((source) => source.ref ? (
                  <Button key={source.ref} dense variant="ghost" onClick={() => openRef(source.ref!)}>{source.title}</Button>
                ) : <span key={source.id}>{source.title}</span>)}
                {rails.map((source) => <span className="surface-token" key={`${source.repo}:${source.kind}:${source.id}`}>{source.title}</span>)}
              </div>
            ) : null}
            {selectedPassage?.text.trim() ? (
              <div className="desk-ask-passage" data-testid="ask-selected-passage">
                <FoldGadget title="Selected text" open={passageOpen} onToggle={setPassageOpen}>
                <blockquote>{selectedPassage.text}</blockquote>
                <div className="desk-ask-selection-verbs">
                  <Button dense variant="ghost" onClick={() => openRef(selectedPassage.noteRef)}>
                    Back to note
                  </Button>
                  <Button dense variant="ghost" onClick={() => {
                    const source = selectedPassage.source;
                    latchAskSelection(null);
                    setSelectedPassage(source ? { noteRef: selectedPassage.noteRef, text: "", source } : null);
                  }}>
                    Remove
                  </Button>
                </div>
                </FoldGadget>
              </div>
            ) : null}
              <div className="desk-ask-context-tools">
              <GroundingSection
                label="Add notes"
                showBudget={false}
                meetings={(items.meeting || []).map((m) => ({
                  id: m.id,
                  title: String(m.title || "Meeting with no title"),
                  startedAt: m.startedAt,
                }))}
                resources={groundableResources}
                selection={grounding}
                onChange={setGrounding}
                limitTokens={limitTokens}
                meter={false}
              />
              <RailsPicker
                showBudget={false}
                picks={rails}
                onChange={setRails}
                limitTokens={limitTokens}
                meter={false}
              />
              {projectsRead.error ? <ActionNotice role="alert" tone="warn" action={{ label: "Retry Projects", onClick: () => void readProjects() }}>
                <StateChip state="unreachable" label="Projects unavailable" />
                {projectsRead.known ? <>{" · "}<StateChip state="warning" label="Last read" /></> : null}
                {" · "}<span>{projectsRead.error}</span>
              </ActionNotice> : null}
              </div>
            </div></ScrollHint>
            <div className="desk-ask-compose-actions">
              <div className="desk-ask-send">
              {phase !== "routing" && !failedRun ? <EngineLine
                engine={engine}
                onChoose={() => openSurfaceOr("configure-runs-on", "/settings", "models")}
                onRetry={() => void refreshEngine("ask.answer")}
              /> : null}
              <Button
                variant="primary"
                disabled={!prompt.trim() || phase === "routing" || isKeeping || overBudget}
                title={overBudget ? "Too many notes" : phase === "routing" ? "Asking" : undefined}
                onClick={() => void ask()}
              >Ask</Button>
              </div>
            </div>
            {overBudget ? <div className="desk-ask-rack-lip">
                <LedMeter
                  label={`Budget ${fmtK(groundTokens)}/${fmtK(limitTokens)}`}
                  value={limitTokens > 0 ? groundTokens / limitTokens : 0}
                />
              </div> : null}
          </div>
        )}
        {!editingQuestion && result ? <div className="desk-ask-edit-question"><Button dense variant="ghost" onClick={() => setEditingQuestion(true)}>Edit question</Button></div> : null}
      </div>

      <SurfaceFooter className={printedRoute ? "turn-route-footer" : undefined} egress={printedRoute ? <RouteEgressChip route={printedRoute} /> : null} receipt={keepError ? <SurfaceState error={keepError} /> : copyReceipt || <span className="surface-footer-receipt-line" data-tone={statusTone} role="status">{[statusLine, printedRoute?.fallback ? "Fallback" : ""].filter(Boolean).join(" · ")}</span>} verbs={<><Button dense variant="ghost" onClick={bin}>{result ? "Bin" : "Cancel"}</Button>{result ? <Button dense variant="primary" loading={isKeeping} onClick={() => savedAnswerRef ? openRef(savedAnswerRef) : void keep()}>{savedAnswerRef ? "Open saved answer" : "Keep"}</Button> : null}</>} />
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
        {selectedIds.length === 1
          ? "1 selected"
          : `${selectedIds.length} selected`}
      </span>
      <Button dense onClick={openAsk}>
        <span aria-hidden="true">✦</span> Ask AI
      </Button>
      <Button
        dense
        variant="ghost"
        onClick={clearSelection}
        aria-label="Clear selection"
      >
        <span aria-hidden="true">✕</span>
      </Button>
    </div>
  );
}
