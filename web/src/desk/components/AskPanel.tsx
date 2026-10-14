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
import { Disclosure } from "../surface/patterns/Disclosure";
import { useEffect, useMemo, useRef, useState } from "react";
import { useDesk } from "../store";
import {
  ASK_LENSES,
  askContexts,
  askLineageLine,
  latchAskSelection,
  keepAsk,
  selectionPrompt,
  takeAskSelection,
  ASK_SELECTION_EVENT_NAME,
  runAsk,
  type AskSelectionHandoff,
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
import { apiRequest } from "../../lib/api";

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
import { SurfaceTraffic, SurfaceTrafficTurn } from "../surface/Surface";
import { countToken } from "../surface/count";
import {
  LedMeter,
  TransportKey,
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
import { humanizeWireValue } from "../../lib/productLanguage";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { useEngine, refreshEngine } from "../hooks/useEngine";
import { EngineLine, RunLine, reasonVerb, reasonWords } from "../surface";
import { openRef } from "../openObject";
import { openSurfaceOr } from "../shell";

/** The budget figure the audit names: 0.3K / 16.4K. */
const fmtK = (n: number): string => `${(n / 1000).toFixed(1)}K`;

export function AskPanel() {
  const items = useDesk((s) => s.items);
  const selectedIds = useDesk((s) => s.selectedIds);
  const { closeAsk, clearSelection, refresh, markNew } = useDesk.getState();

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
  const [sent, setSent] = useState<{
    prompt: string;
    lens: string;
    ctx: number;
    selection: AskSelectionHandoff | null;
  } | null>(null);
  const [result, setResult] = useState<AskRunResult | null>(null);
  const [failedRun, setFailedRun] = useState<AskRunResult | null>(null);
  const [runStartedAt, setRunStartedAt] = useState<number | undefined>();
  const [finishedElapsedSeconds, setFinishedElapsedSeconds] = useState<number | undefined>();
  // The run's receipt route (success or refusal): the lamp needs one.
  const [route, setRoute] = useState<TurnRoute | null>(null);
  const [error, setError] = useState("");
  const [kept, setKept] = useState(false);
  const [grounding, setGrounding] =
    useState<GroundingSelection>(emptyGrounding());
  const [rails, setRails] = useState<RailsPick[]>([]);
  const [projects, setProjects] = useState<Array<{ id: string; name: string }>>(
    [],
  );
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  const endRef = useRef<HTMLDivElement | null>(null);

  // The transcript keeps its newest transmission in view (the
  // PersonaChat grammar): the refusal turn and the printed turn are
  // never hidden below the well's fold.
  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [phase, error]);

  const context = useMemo(
    () => askContexts(items, selectedIds),
    [items, selectedIds],
  );
  const [selectedPassage, setSelectedPassage] = useState<AskSelectionHandoff | null>(() => takeAskSelection());
  useEffect(() => {
    const onSelection = (event: Event) => {
      const next = (event as CustomEvent<AskSelectionHandoff | null>).detail;
      // The mounted composer owns this handoff now. Clear the module latch so
      // a later mount cannot replay a quote already shown in this composer.
      takeAskSelection();
      setSelectedPassage(next && next.text.trim() ? next : null);
    };
    window.addEventListener(ASK_SELECTION_EVENT_NAME, onSelection);
    return () => window.removeEventListener(ASK_SELECTION_EVENT_NAME, onSelection);
  }, []);
  useEffect(() => {
    const noteItems = items.note || [];
    const noteKnown = noteItems.length > 0;
    const noteStillExists = noteItems.some((item) => qualifiedRef("note", item.id) === selectedPassage?.noteRef);
    if (selectedPassage && (!selectedIds.includes(selectedPassage.noteRef) || (noteKnown && !noteStillExists) || (context.length > 0 && !context.some((entry) => entry.ref === selectedPassage.noteRef)))) {
      setSelectedPassage(null);
    }
  }, [context, items.note, selectedIds, selectedPassage]);
  useEffect(() => {
    apiRequest("/api/projects")
      .then((response) => response.json())
      .then((body) =>
        setProjects(
          (body.projects || []).filter((project: any) => !project.is_archived),
        ),
      )
      .catch(() => setProjects([]));
  }, []);
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
  // The context is pinned at print time so keep records what was actually read
  // even if the selection changes underneath. Grounding rows join it at print
  // time (the receipts rule): the kept ask names what grounded the answer.
  const printedContext = useRef(context);

  // The editor receives the server's compatible chain. The Ask composer has no
  // browser-selected destination whose context window it can invent.
  const limitTokens = 16_384;
  const groundTokens = groundingTokens(grounding) + railsTokens(rails);
  const overBudget = groundTokens > limitTokens;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && phase !== "routing") {
        latchAskSelection(null);
        closeAsk();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [phase]);

  const ask = async () => {
    if (!prompt.trim() || phase === "routing" || overBudget) return;
    const requestSelection = selectedPassage && context.some((entry) => entry.ref === selectedPassage.noteRef)
      ? selectedPassage
      : null;
    const requestPrompt = selectionPrompt(prompt, requestSelection);
    setPhase("routing");
    setError("");
    setResult(null);
    setFailedRun(null);
    setRoute(null);
    const startedAt = Date.now();
    setRunStartedAt(startedAt);
    setFinishedElapsedSeconds(undefined);
    setSent({ prompt: requestPrompt, lens, ctx: context.length, selection: requestSelection });
    // Receipts: the grounding rows ride the pinned context so keep names them.
    printedContext.current = [
      ...context,
      ...groundingReceiptRows(grounding)
        .filter((g) => !context.some((c) => c.id === g.id))
        .map((g) => ({ id: g.id, kind: g.kind, ref: g.ref, title: g.title })),
    ];
    const r = await runAsk({
      prompt: requestPrompt,
      lens,
      context,
      grounding: buildGrounding(grounding, rails),
    });
    setRoute(routeFromWire(r.route));
    const elapsedSeconds = Math.max(0, Math.round((Date.now() - startedAt) / 1000));
    setFinishedElapsedSeconds(elapsedSeconds);
    if (!r.ok) {
      setFailedRun(r);
      setError(reasonWords(r.reason, engine.model));
      setPhase("compose");
      return;
    }
    setResult(r);
    setPhase("printed");
  };

  const keep = async () => {
    if (!result || kept) return;
    setKept(true);
    const artifactId = await keepAsk({
      lens,
      prompt: prompt.trim(),
      output: result.output,
      context: printedContext.current,
    });
    if (artifactId) {
      // The kept card is a REAL artifact — it lands on the desk wearing the
      // NEW beat (the HS-73-06 grammar), like every other run-born output.
      clearSelection();
      latchAskSelection(null);
      closeAsk();
      await refresh();
      markNew(artifactId);
    } else {
      setKept(false);
      setError("NOT KEPT · PRESS KEEP AGAIN");
    }
  };

  const bin = () => {
    latchAskSelection(null);
    clearSelection();
    closeAsk();
  };

  const receipt = result?.groundingReceipt || null;
  const flaggedClaims = (result?.groundingClaims || []).filter(
    (c) => c.flagged,
  );
  const placement = result?.actualPlacement || null;
  // Owner pick 2026-10-05 (route in footer): the turn wears only its lamp;
  // the footer names the full route once. Both come from the hub's receipt
  // route, on an answer and on a refusal that sent bytes (Astra, #875).
  const printedRoute = sent && (result || error) ? route : null;
  const printedLamp = printedRoute?.lamp ?? null;
  const printedPlace = printedRoute
    ? routeEgress(printedRoute).label || "This device"
    : engine.place;
  // A refusal that sent bytes: the failure is on the HUB> turn; the
  // footer names where they went.
  const refusedRoute = Boolean(error && printedRoute && !result);

  const turnCount = (sent ? 1 : 0) + (result || failedRun ? 1 : 0);
  const hasTraffic = Boolean(sent || failedRun || result || phase === "routing");

  // The footer receipt bar's one status line (audit §3.5): fault > routing
  // > run receipt > the compose budget tokens.
  const statusTone =
    (error && !refusedRoute) || overBudget ? ("danger" as const) : undefined;
  const statusLine = refusedRoute && printedRoute
    ? lastTurnLine(printedRoute)
    : error
    ? error
    : phase === "routing"
      ? "ROUTING"
      : phase === "printed" && printedRoute
        ? lastTurnLine(printedRoute)
        : phase === "printed" && result
          ? String(placement?.model || result.model || "")
          : [
            promptRecovered ? "DRAFT · RECOVERED" : "",
            overBudget ? "Too many notes" : "",
          ]
            .filter(Boolean)
            .join(" · ");

  return (
    <DeskWindowFrame
      id="ask"
      glyph="✦"
      label="Ask AI"
      className="desk-pullout desk-ask"
      icon={
        <span className="desk-ask-glyph" aria-hidden="true">
          ✦
        </span>
      }
      title={
        phase === "printed"
          ? askLineageLine(printedContext.current, lens)
          : "Ask AI"
      }
      open
      defaultW={520}
      defaultH={600}
      onClose={() => {
        if (phase !== "routing") bin();
      }}
    >
      <div className="desk-pullout-body desk-ask-body">
        {hasTraffic ? <SurfaceTraffic
          head={["SESSION", countToken(turnCount, "TURN")]
            .filter(Boolean)
            .join(" · ")}
          showEmpty={false}
        >
          {sent ? (
            <SurfaceTrafficTurn
              prefix="YOU>"
              meta={
                <>
                  <span className="surface-token">{sent.lens}</span>
                  {sent.ctx > 0 ? (
                    <span className="surface-token">Context {sent.ctx}</span>
                  ) : null}
                </>
              }
            >
              {sent.prompt}
            </SurfaceTrafficTurn>
          ) : null}
          {phase === "routing" ? (
            <SurfaceTrafficTurn prefix="HUB>">
              <RunLine phase="running" verb="Asking" model={engine.model} place={engine.place} startedAt={runStartedAt} />
            </SurfaceTrafficTurn>
          ) : null}
          {sent && failedRun ? (
            <SurfaceTrafficTurn
              prefix="HUB>"
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
                onRetry={failedRun.reason !== "no_engine" && reasonVerb(failedRun.reason) ? () => void ask() : undefined}
              />
            </SurfaceTrafficTurn>
          ) : null}
          {phase === "printed" && result ? (
            <SurfaceTrafficTurn
              prefix="HUB>"
              meta={<TurnLamp lamp={printedLamp} />}
              verbs={
                <>
                  <Button
                    dense
                    onClick={() => void copy(result.output)}
                  >
                    Copy
                  </Button>
                  <Button
                    dense
                    variant="ghost"
                    disabled={kept}
                    onClick={() => void keep()}
                  >
                    {kept ? "Kept" : "Keep"}
                  </Button>
                  <Button dense variant="ghost" onClick={bin}>
                    Bin
                  </Button>
                </>
              }
            >
              <RunLine
                phase="success"
                pastVerb="Answered"
                model={result.model || engine.model}
                place={printedPlace}
                elapsedSeconds={finishedElapsedSeconds}
              />
              <div
                className="desk-ask-answer"
                /* HS-101 B7 — the result drags OUT through the glass:
                   release it over the desk and it is kept (the same keep
                   verb; the desk files the minted artifact). */
                draggable={!kept}
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
                          GROUNDED ON {groundedMatchCount(receipt)} OF{" "}
                          {receipt.matchedCount}
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
          <div ref={endRef} />
        </SurfaceTraffic> : null}

        {phase !== "printed" && (
          <>
            {selectedPassage ? (
              <div className="desk-ask-selected" data-testid="ask-selected-passage">
                <p className="desk-ground-sect">Selected text</p>
                <blockquote>{selectedPassage.text}</blockquote>
                <div className="desk-ask-selection-verbs">
                  <Button dense variant="ghost" onClick={() => openRef(selectedPassage.noteRef)}>
                    Back to note
                  </Button>
                  <Button dense variant="ghost" onClick={() => { latchAskSelection(null); setSelectedPassage(null); }}>
                    Remove
                  </Button>
                </div>
              </div>
            ) : null}
            <div className="desk-chat-well">
              <div className="desk-chat-composer">
                <MicButton
                  draftScope="desk-ask"
                  onText={(t) => setPrompt((v) => (v ? v + " " + t : t))}
                />
                <textarea
                  rows={3}
                  value={prompt}
                  placeholder="Ask about your work"
                  autoFocus
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void ask();
                    }
                  }}
                />
                <TransportKey
                  compact
                  label="ASK"
                  glyph="▸"
                  disabled={
                    !prompt.trim() || phase === "routing" || overBudget
                  }
                  title={
                    overBudget
                      ? "Too many notes"
                      : phase === "routing"
                        ? "Routing"
                        : undefined
                  }
                  onClick={() => void ask()}
                />
              </div>
            </div>

            <EngineLine
              engine={engine}
              onChoose={() => openSurfaceOr("configure-runs-on", "/settings", "models")}
              onRetry={() => void refreshEngine("ask.answer")}
            />
            {context.length > 0 ? (
              <div className="desk-ask-sources" data-testid="ask-context">
                <span>With:</span>
                {context.map((source) => source.ref ? (
                  <Button key={source.id} dense variant="ghost" onClick={() => openRef(source.ref!)}>{source.title}</Button>
                ) : <span key={source.id}>{source.title}</span>)}
              </div>
            ) : null}
            <Disclosure label="Add notes">
              <GroundingSection
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
                picks={rails}
                onChange={setRails}
                limitTokens={limitTokens}
                meter={false}
              />
              {overBudget ? <div className="desk-ask-rack-lip">
                <LedMeter
                  label={`Budget ${fmtK(groundTokens)}/${fmtK(limitTokens)}`}
                  value={limitTokens > 0 ? groundTokens / limitTokens : 0}
                />
              </div> : null}
            </Disclosure>
          </>
        )}
      </div>

      <SurfaceFooter className={printedRoute ? "turn-route-footer" : undefined} egress={printedRoute ? <RouteEgressChip route={printedRoute} /> : null} receipt={copyReceipt || <span className="surface-footer-receipt-line" data-tone={statusTone} role="status">{statusLine}</span>} verbs={<><Button dense variant="ghost" disabled={phase === "routing"} onClick={bin}>{phase === "printed" ? "Bin" : "Cancel"}</Button>{phase === "printed" && result ? <Button dense disabled={kept} onClick={() => void keep()}>{kept ? "Kept" : "Keep"}</Button> : null}</>} />
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
