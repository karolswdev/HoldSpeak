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
import { egressBadge } from "../setup";
import {
  ASK_LENSES, askContexts, askLineageLine, keepAsk, runAsk,
  type AskRunResult,
} from "../ask";
import {
  emptyGrounding, groundingIsEmpty, groundingReceiptRows, groundingTokens, hubGrounding,
  type GroundingSelection,
} from "../grounding";
import { GroundingSection } from "./GroundingSection";
import { MicButton } from "./MicButton";

export function AskPanel() {
  const items = useDesk((s) => s.items);
  const profiles = useDesk((s) => s.profiles);
  const setup = useDesk((s) => s.setup);
  const selectedIds = useDesk((s) => s.selectedIds);
  const { closeAsk, clearSelection, refresh, markNew } = useDesk.getState();

  const [lens, setLens] = useState(ASK_LENSES[0].name);
  const [prompt, setPrompt] = useState(ASK_LENSES[0].instruction);
  const [profileId, setProfileId] = useState("");
  const [phase, setPhase] = useState<"compose" | "routing" | "printed">("compose");
  const [result, setResult] = useState<AskRunResult | null>(null);
  const [error, setError] = useState("");
  const [kept, setKept] = useState(false);
  const [grounding, setGrounding] = useState<GroundingSelection>(emptyGrounding());
  const ref = useRef<HTMLDivElement | null>(null);

  const context = useMemo(() => askContexts(items, selectedIds), [items, selectedIds]);
  // The context is pinned at print time so keep records what was actually read
  // even if the selection changes underneath. Grounding rows join it at print
  // time (the receipts rule): the kept ask names what grounded the answer.
  const printedContext = useRef(context);

  // The gauge's budget: the picked profile's window, else the ceiling the iPad
  // assumes for an endpoint it doesn't control.
  const limitTokens = useMemo(() => {
    const p = profiles.find((x) => x.id === profileId);
    return Number(p?.context_limit) > 0 ? Number(p?.context_limit) : 16_384;
  }, [profileId, profiles]);
  const groundTokens = groundingTokens(grounding);
  const overBudget = groundTokens > limitTokens;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && phase !== "routing") closeAsk();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [phase]);

  // The compose-time egress chip: the picked profile's target, else the hub's
  // app-wide badge (the run answers with where it ACTUALLY went).
  const composeEgress = useMemo(() => {
    if (profileId) {
      const p = profiles.find((x) => x.id === profileId);
      if (p) {
        const cloud = (p.kind || "onDevice") !== "onDevice";
        return cloud
          ? { scope: "cloud", text: `☁ ${String(p.base_url || "endpoint").replace(/^https?:\/\//, "").split("/")[0]}` }
          : { scope: "local", text: "⌂ On device" };
      }
    }
    const b = egressBadge(setup);
    return { scope: b.scope, text: b.text };
  }, [profileId, profiles, setup]);

  const ask = async () => {
    if (!prompt.trim() || phase === "routing" || overBudget) return;
    setPhase("routing");
    setError("");
    // Receipts: the grounding rows ride the pinned context so keep names them.
    printedContext.current = [
      ...context,
      ...groundingReceiptRows(grounding)
        .filter((g) => !context.some((c) => c.id === g.id))
        .map((g) => ({ id: g.id, kind: "grounding", title: g.title })),
    ];
    const r = await runAsk({
      prompt: prompt.trim(), lens, context,
      profileId: profileId || undefined,
      grounding: hubGrounding(grounding),
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
      lens, prompt: prompt.trim(), output: result.output, context: printedContext.current,
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
      setError("Keep failed — the hub did not store it.");
    }
  };

  const bin = () => {
    clearSelection();
    closeAsk();
  };

  const printedEgress = result?.egress
    ? result.egress.scope === "local"
      ? { scope: "local", text: result.model ? `⌂ ${result.model}` : "⌂ On this machine" }
      : { scope: "cloud", text: `☁ ${[result.model, result.egress.host].filter(Boolean).join(" · ")}` }
    : null;

  return (
    <motion.div
      ref={ref}
      className="desk-pullout desk-ask"
      initial={{ x: 60, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 320, damping: 30 }}
      onPointerDown={(e) => e.stopPropagation()}
    >
      <header className="desk-pullout-head">
        <span className="desk-ask-glyph" aria-hidden="true">✦</span>
        <span className="desk-pullout-title">
          {phase === "printed" ? askLineageLine(printedContext.current, lens) : "Ask AI"}
        </span>
        {phase === "printed" && printedEgress ? (
          <span className={`egress-badge is-${printedEgress.scope}`}>{printedEgress.text}</span>
        ) : (
          <span className={`egress-badge is-${composeEgress.scope}`}>{composeEgress.text}</span>
        )}
        {phase !== "routing" && (
          <button type="button" className="desk-pullout-close" onClick={bin} aria-label="Close">
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
                  <span key={c.id} className="desk-chip quiet">{c.title}</span>
                ))}
              </div>
            )}
            <div className="desk-ask-lenses">
              {ASK_LENSES.map((l) => (
                <button
                  key={l.name}
                  type="button"
                  className={"desk-chip" + (lens === l.name ? " desk-ask-lens-on" : " quiet")}
                  onClick={() => { setLens(l.name); setPrompt(l.instruction); }}
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
              <MicButton onText={(t) => setPrompt((v) => (v ? v + " " + t : t))} />
            </div>
            {profiles.length > 0 && (
              <select
                className="desk-ask-runson"
                value={profileId}
                aria-label="Runs on"
                onChange={(e) => setProfileId(e.target.value)}
              >
                <option value="">Hub default</option>
                {profiles.map((p) => (
                  <option key={String(p.id)} value={String(p.id)}>
                    {String(p.name || p.id)}
                  </option>
                ))}
              </select>
            )}
            <GroundingSection
              meetings={(items.meeting || []).map((m) => ({
                id: m.id, title: String(m.title || "Untitled meeting"), startedAt: (m as any).startedAt,
              }))}
              selection={grounding}
              onChange={setGrounding}
              limitTokens={limitTokens}
            />
            {error && <p className="desk-run-warning">⚠ {error}</p>}
          </>
        )}

        {phase === "printed" && result && (
          <div className="desk-ask-card">
            <pre className="desk-pullout-md">{result.output}</pre>
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
              title={overBudget ? "Grounding is past the window — pick less" : undefined}
              onClick={() => void ask()}
            >
              Ask
            </button>
          </>
        )}
        {phase === "routing" && <span className="desk-ask-routing">routing…</span>}
        {phase === "printed" && (
          <>
            <button type="button" className="desk-chip quiet" onClick={bin}>
              Bin
            </button>
            <button type="button" className="desk-chip" disabled={kept} onClick={() => void keep()}>
              {kept ? "…" : "Keep"}
            </button>
          </>
        )}
      </footer>
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
        {selectedIds.length === 1 ? "1 selected" : `${selectedIds.length} selected`}
      </span>
      <button type="button" className="desk-chip" onClick={openAsk}>
        ✦ Ask AI
      </button>
      <button type="button" className="desk-chip quiet" onClick={clearSelection} aria-label="Clear selection">
        ✕
      </button>
    </div>
  );
}
