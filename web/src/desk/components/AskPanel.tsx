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
// shared LedMeter budget, the footer is the surface-receiptbar, and the
// server's grounding receipt (GROUNDED ON N OF M + openable citations)
// finally reaches this glass.
import { useEffect, useMemo, useRef, useState } from "react";
import { useDesk } from "../store";
import {
  ASK_LENSES,
  askContexts,
  askLineageLine,
  keepAsk,
  runAsk,
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
import { useDurableDraft } from "../../lib/durableDraft";
import { qualifiedRef } from "../api";
import { RunsOnPicker } from "./RunsOnPicker";
import { DeskWindowFrame } from "./DeskWindow";
import { Material } from "../surface/Material";
import { SurfaceTraffic, SurfaceTrafficTurn } from "../surface/Surface";
import {
  GadgetGroup,
  LampGadget,
  LedMeter,
  MxRadio,
  TransportKey,
} from "../surface/gadgets";
import {
  boundaryEgressLamp,
  egressScopeLamp,
  inferenceEgressLamp,
} from "../inferenceEgress";
import { CitationChips, groundedMatchCount } from "../surface/citations";
import { Button } from "../../components/signal/Signal";

/** The budget figure the audit names: 0.3K / 16.4K. */
const fmtK = (n: number): string => `${(n / 1000).toFixed(1)}K`;

export function AskPanel() {
  const items = useDesk((s) => s.items);
  const inferenceTargets = useDesk((s) => s.inferenceTargets);
  const selectedIds = useDesk((s) => s.selectedIds);
  const { closeAsk, clearSelection, refresh, markNew } = useDesk.getState();

  const [lens, setLens] = useState(ASK_LENSES[0].name);
  const {
    value: prompt,
    setDraft: setPrompt,
    recovered: promptRecovered,
  } = useDurableDraft("desk-ask", ASK_LENSES[0].instruction);
  const [profileId, setProfileId] = useState("this_machine");
  const [phase, setPhase] = useState<"compose" | "routing" | "printed">(
    "compose",
  );
  // The transmission on the log: the YOU> turn as it was sent (the draft
  // keeps editing underneath without rewriting the transcript).
  const [sent, setSent] = useState<{
    prompt: string;
    lens: string;
    ctx: number;
  } | null>(null);
  const [result, setResult] = useState<AskRunResult | null>(null);
  const [error, setError] = useState("");
  const [kept, setKept] = useState(false);
  const [grounding, setGrounding] =
    useState<GroundingSelection>(emptyGrounding());
  const [rails, setRails] = useState<RailsPick[]>([]);
  const [projects, setProjects] = useState<Array<{ id: string; name: string }>>(
    [],
  );
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

  // The gauge's budget comes from the same destination view model as the picker.
  const limitTokens = useMemo(() => {
    const target = inferenceTargets.find((x) => x.id === profileId);
    return Number(target?.context_limit) > 0
      ? Number(target?.context_limit)
      : 16_384;
  }, [profileId, inferenceTargets]);
  const groundTokens = groundingTokens(grounding) + railsTokens(rails);
  const overBudget = groundTokens > limitTokens;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && phase !== "routing") closeAsk();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [phase]);

  // Before execution this names the selected boundary; the printed receipt is
  // the hub's actual placement, never a client-side inference.
  const composeTarget = useMemo(
    () => inferenceTargets.find((item) => item.id === profileId),
    [profileId, inferenceTargets],
  );
  const composeLamp = inferenceEgressLamp(composeTarget);
  const composeEgress = {
    local: composeLamp.tone === "ok",
    text: composeTarget?.name || "No model",
  };

  const ask = async () => {
    if (!prompt.trim() || phase === "routing" || overBudget) return;
    setPhase("routing");
    setError("");
    setResult(null);
    setSent({ prompt: prompt.trim(), lens, ctx: context.length });
    // Receipts: the grounding rows ride the pinned context so keep names them.
    printedContext.current = [
      ...context,
      ...groundingReceiptRows(grounding)
        .filter((g) => !context.some((c) => c.id === g.id))
        .map((g) => ({ id: g.id, kind: g.kind, ref: g.ref, title: g.title })),
    ];
    const r = await runAsk({
      prompt: prompt.trim(),
      lens,
      context,
      inferenceTargetId: profileId,
      grounding: buildGrounding(grounding, rails),
    });
    if (!r.ok) {
      setError(r.output);
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
      closeAsk();
      await refresh();
      markNew(artifactId);
    } else {
      setKept(false);
      setError(
        "Save failed. Retry.",
      );
    }
  };

  const bin = () => {
    clearSelection();
    closeAsk();
  };

  const receipt = result?.groundingReceipt || null;
  const flaggedClaims = (result?.groundingClaims || []).filter(
    (c) => c.flagged,
  );
  const placement = result?.actualPlacement || null;
  const printedBoundary = placement?.boundary;
  const printedLamp =
    typeof printedBoundary === "string"
      ? boundaryEgressLamp(printedBoundary)
      : egressScopeLamp(result?.egress?.scope);
  const placementTokens = placement
    ? [
        placement.engine ? String(placement.engine) : "",
        placement.model ? String(placement.model) : "",
        placement.fallback_reason
          ? `fallback: ${String(placement.fallback_reason)}`
          : "",
      ].filter(Boolean)
    : [];

  const turnCount = (sent ? 1 : 0) + (result || (error && sent) ? 1 : 0);

  // The footer receipt bar's one status line (audit §3.5): fault > routing
  // > run receipt > the compose budget tokens.
  const statusTone =
    error || overBudget ? ("danger" as const) : undefined;
  const statusLine = error
    ? error
    : phase === "routing"
      ? "ROUTING"
      : phase === "printed" && result
        ? [
            `RAN ON ${String(
              placement?.target_name ||
                placement?.target_id ||
                result.model ||
                "this device",
            )}`,
            placement?.model ? String(placement.model) : "",
          ]
            .filter(Boolean)
            .join(" · ")
        : [
            promptRecovered ? "DRAFT · RECOVERED" : "",
            `CTX ${fmtK(groundTokens)}/${fmtK(limitTokens)}`,
            overBudget
              ? "PAST THE WINDOW"
              : composeEgress.local
                ? "LOCAL"
                : composeEgress.text,
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
      onClose={() => {
        if (phase !== "routing") bin();
      }}
    >
      <div className="desk-pullout-body desk-ask-body">
        <SurfaceTraffic
          head={`SESSION · ${turnCount} ${turnCount === 1 ? "TURN" : "TURNS"}`}
          showEmpty={!sent && phase !== "routing"}
        >
          {sent ? (
            <SurfaceTrafficTurn
              prefix="YOU>"
              meta={
                <>
                  <span className="surface-token">{sent.lens}</span>
                  {sent.ctx > 0 ? (
                    <span className="surface-token">CTX {sent.ctx}</span>
                  ) : null}
                </>
              }
            >
              {sent.prompt}
            </SurfaceTrafficTurn>
          ) : null}
          {phase === "routing" ? (
            <SurfaceTrafficTurn prefix="HUB>">
              <LedMeter label="RX" value={0} scanning />
            </SurfaceTrafficTurn>
          ) : null}
          {sent && error && !result ? (
            <SurfaceTrafficTurn prefix="HUB>" error>
              {error}
            </SurfaceTrafficTurn>
          ) : null}
          {phase === "printed" && result ? (
            <SurfaceTrafficTurn
              prefix="HUB>"
              meta={
                <>
                  {result.egress ? (
                    <span className="surface-detail">
                      ran on{" "}
                      <LampGadget on {...printedLamp} />
                      {[result.egress.host, result.model]
                        .filter(Boolean)
                        .map((detail) => ` · ${detail}`)}
                    </span>
                  ) : null}
                  {placementTokens.map((token) => (
                    <span key={token} className="surface-token">
                      {token}
                    </span>
                  ))}
                </>
              }
              verbs={
                <>
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
        </SurfaceTraffic>

        {phase !== "printed" && (
          <>
            <div className="desk-chat-well">
              <div className="desk-chat-composer">
                <MicButton
                  draftScope="desk-ask"
                  onText={(t) => setPrompt((v) => (v ? v + " " + t : t))}
                />
                <textarea
                  rows={3}
                  value={prompt}
                  placeholder="Instruction"
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
                      ? "Grounding is past the window: pick less"
                      : phase === "routing"
                        ? "Routing"
                        : undefined
                  }
                  onClick={() => void ask()}
                />
              </div>
              <MxRadio
                label="Lens"
                value={lens}
                options={ASK_LENSES.map((l) => ({
                  value: l.name,
                  label: l.name.toUpperCase(),
                }))}
                onChange={(next) => {
                  setLens(next);
                  const picked = ASK_LENSES.find((l) => l.name === next);
                  if (picked) setPrompt(picked.instruction);
                }}
              />
              <div className="desk-chat-well-foot">
                <RunsOnPicker
                  targets={inferenceTargets}
                  selectedId={profileId}
                  onChange={setProfileId}
                  disabled={phase === "routing"}
                />
                {context.length > 0 && (
                  <span className="surface-token">
                    CTX · {context.length}{" "}
                    {context.length === 1 ? "CARD" : "CARDS"}
                  </span>
                )}
                <LampGadget on {...composeLamp} />
                {composeTarget?.name ? (
                  <span className="surface-detail">{composeTarget.name}</span>
                ) : null}
              </div>
            </div>

            {/* HS-111-05 — the grounding rack: one etched rack, both
                pickers, the shared budget on the rack lip. */}
            <GadgetGroup label="GROUNDING">
              {context.length > 0 && (
                <div className="desk-ask-ctx">
                  <p className="desk-ground-sect">
                    CONTEXT · {context.length}
                  </p>
                  <ul className="desk-ground-list">
                    {context.map((c) => (
                      <li key={c.id} className="desk-ground-row">
                        <div className="desk-ground-line is-fact">
                          <span className="desk-rails-kind">{c.kind}</span>
                          <span className="desk-ground-name">{c.title}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <GroundingSection
                meetings={(items.meeting || []).map((m) => ({
                  id: m.id,
                  title: String(m.title || "Untitled meeting"),
                  startedAt: (m as any).startedAt,
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
              <div className="desk-ask-rack-lip">
                <LedMeter
                  label={`CTX ${fmtK(groundTokens)}/${fmtK(limitTokens)}`}
                  value={limitTokens > 0 ? groundTokens / limitTokens : 0}
                />
              </div>
            </GadgetGroup>
          </>
        )}
      </div>

      <footer className="surface-status surface-receiptbar desk-ask-foot">
        <span className="surface-receiptbar-verbs">
          <Button
            dense
            variant="ghost"
            disabled={phase === "routing"}
            onClick={bin}
          >
            {phase === "printed" ? "Bin" : "Cancel"}
          </Button>
        </span>
        <span
          className="surface-receiptbar-receipt"
          data-tone={statusTone}
          role="status"
        >
          {statusLine}
        </span>
        <span className="surface-receiptbar-verbs">
          {phase === "printed" && result ? (
            <Button dense disabled={kept} onClick={() => void keep()}>
              {kept ? "Kept" : "Keep"}
            </Button>
          ) : null}
        </span>
      </footer>
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
      <button type="button" className="desk-chip" onClick={openAsk}>
        ✦ Ask AI
      </button>
      <button
        type="button"
        className="desk-chip quiet"
        onClick={clearSelection}
        aria-label="Clear selection"
      >
        ✕
      </button>
    </div>
  );
}
