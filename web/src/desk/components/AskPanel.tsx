// The Ask AI atom (HSM-16-04, the web parity of HSM-16-09): the composer is a
// docked in-world panel — the desk stays visible and alive behind it (the
// 17-08 atelier posture, never a modal) — and the result prints as a card you
// judge: keep (a real synced Artifact carrying every card read + the exact
// instruction) or bin (nothing stored). The egress chip is per-RUN honest:
// pre-run it names the picked profile's target; printed, it names where the
// run actually went.
import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "motion/react";
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
  groundingIsEmpty,
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
import { useDeskWindow } from "./DeskWindow";

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
  const [result, setResult] = useState<AskRunResult | null>(null);
  const [error, setError] = useState("");
  const [kept, setKept] = useState(false);
  const [grounding, setGrounding] =
    useState<GroundingSelection>(emptyGrounding());
  const [rails, setRails] = useState<RailsPick[]>([]);
  const [projects, setProjects] = useState<Array<{ id: string; name: string }>>(
    [],
  );
  const ref = useRef<HTMLDivElement | null>(null);
  const win = useDeskWindow("ask");

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
  const composeEgress = useMemo(() => {
    const target = inferenceTargets.find((item) => item.id === profileId);
    return {
      scope: target?.boundary === "same_device" ? "local" : "cloud",
      text: `${target?.boundary === "same_device" ? "⌂" : "→"} ${target?.name || "This device"}`,
    };
  }, [profileId, inferenceTargets]);

  const ask = async () => {
    if (!prompt.trim() || phase === "routing" || overBudget) return;
    setPhase("routing");
    setError("");
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
        "Artifact was not saved. The Result remains open. Retry Keep as Artifact.",
      );
    }
  };

  const bin = () => {
    clearSelection();
    closeAsk();
  };

  const printedEgress = result?.egress
    ? result.egress.scope === "local"
      ? {
          scope: "local",
          text: result.model
            ? `⌂ This device · ${result.model}`
            : "⌂ This device",
        }
      : result.egress.scope === "mesh"
        ? {
            scope: "mesh",
            text: `⇄ ${["Paired", result.egress.host, result.model].filter(Boolean).join(" · ")}`,
          }
        : {
            scope: "cloud",
            text: `→ ${["Leaves device", result.egress.host, result.model].filter(Boolean).join(" · ")}`,
          }
    : null;

  return (
    <motion.div
      ref={(el: HTMLDivElement | null) => {
        ref.current = el;
        win.setEl(el);
      }}
      className={
        "desk-pullout desk-ask desk-window" +
        (win.floating ? " is-floating" : "")
      }
      style={win.style}
      initial={{ x: 60, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 320, damping: 30 }}
      onPointerDown={(e) => {
        win.focus();
        e.stopPropagation();
      }}
    >
      <header
        className="desk-pullout-head desk-window-handle"
        {...win.handleProps}
      >
        <span className="desk-ask-glyph" aria-hidden="true">
          ✦
        </span>
        <span className="desk-pullout-title">
          {phase === "printed"
            ? askLineageLine(printedContext.current, lens)
            : "Ask AI"}
        </span>
        {phase === "printed" && printedEgress ? (
          <span className={`egress-badge is-${printedEgress.scope}`}>
            {printedEgress.text}
          </span>
        ) : (
          <span className={`egress-badge is-${composeEgress.scope}`}>
            {composeEgress.text}
          </span>
        )}
        {phase !== "routing" && (
          <button
            type="button"
            className="desk-pullout-close"
            onClick={bin}
            aria-label="Close"
          >
            ✕
          </button>
        )}
      </header>

      <div className="desk-pullout-body">
        {phase !== "printed" && (
          <>
            {context.length > 0 && (
              <div className="desk-ask-context">
                {context.map((c) => (
                  <span key={c.id} className="desk-chip quiet">
                    {c.title}
                  </span>
                ))}
              </div>
            )}
            <div className="desk-ask-lenses">
              {ASK_LENSES.map((l) => (
                <button
                  key={l.name}
                  type="button"
                  className={
                    "desk-chip" +
                    (lens === l.name ? " desk-ask-lens-on" : " quiet")
                  }
                  onClick={() => {
                    setLens(l.name);
                    setPrompt(l.instruction);
                  }}
                >
                  {l.name}
                </button>
              ))}
            </div>
            <div className="desk-ask-prompt">
              <textarea
                rows={4}
                value={prompt}
                placeholder="Say what to do with these"
                autoFocus
                onChange={(e) => setPrompt(e.target.value)}
              />
              <MicButton
                draftScope="desk-ask"
                onText={(t) => setPrompt((v) => (v ? v + " " + t : t))}
              />
            </div>
            {promptRecovered ? (
              <span className="quiet">Recovered local Ask draft.</span>
            ) : null}
            <RunsOnPicker
              targets={inferenceTargets}
              selectedId={profileId}
              onChange={setProfileId}
              disabled={phase === "routing"}
            />
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
            />
            <RailsPicker
              picks={rails}
              onChange={setRails}
              limitTokens={limitTokens}
            />
            {error && <p className="desk-run-warning">⚠ {error}</p>}
          </>
        )}

        {phase === "printed" && result && (
          <div className="desk-ask-card">
            <pre className="desk-pullout-md">{result.output}</pre>
            {result.actualPlacement && (
              <p className="quiet desk-run-receipt">
                Ran on{" "}
                {String(
                  result.actualPlacement.target_name ||
                    result.actualPlacement.target_id,
                )}
                {result.actualPlacement.engine
                  ? ` · ${String(result.actualPlacement.engine)}`
                  : ""}
                {result.actualPlacement.model
                  ? ` · ${String(result.actualPlacement.model)}`
                  : ""}
                {result.actualPlacement.boundary
                  ? ` · ${String(result.actualPlacement.boundary)}`
                  : ""}
                {result.actualPlacement.fallback_reason
                  ? ` · fallback: ${String(result.actualPlacement.fallback_reason)}`
                  : ""}
              </p>
            )}
          </div>
        )}
      </div>

      <footer className="desk-pullout-foot">
        {phase === "compose" && (
          <>
            <button type="button" className="desk-chip quiet" onClick={bin}>
              Cancel
            </button>
            <button
              type="button"
              className="desk-chip"
              disabled={!prompt.trim() || overBudget}
              title={
                overBudget
                  ? "Grounding is past the window — pick less"
                  : undefined
              }
              onClick={() => void ask()}
            >
              Ask
            </button>
          </>
        )}
        {phase === "routing" && (
          <span className="desk-ask-routing">routing…</span>
        )}
        {phase === "printed" && (
          <>
            <button type="button" className="desk-chip quiet" onClick={bin}>
              Bin
            </button>
            <button
              type="button"
              className="desk-chip"
              disabled={kept}
              onClick={() => void keep()}
            >
              {kept ? "…" : "Keep"}
            </button>
          </>
        )}
      </footer>
      {win.grip}
    </motion.div>
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
