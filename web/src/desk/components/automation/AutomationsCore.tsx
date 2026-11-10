/* Automations (the language, 2026-11-08): the app window
 * `surface-workbenches`, one native object window, as Programs is.
 *
 * Window grammar: title bar → the rail of automations at the left (New
 * automation on top; each automation its sprite, its name, the spine of
 * its last runs and its next run in mono) → the chosen automation at the
 * right (AutomationBody: the mast, the sentence, the plate, the ledger of
 * runs; the same body an automation's own window hosts) → the StatusBar
 * ("3 automations · 1 new · 1 failed"; no count of zero). New automation
 * shows the starters as pictogram cards in the right pane (Starters.tsx);
 * the made automation is then the chosen one. With none yet: the
 * automation object, one line, New automation, and the starters. At 393
 * the rail opens the pane with one Back path. The old list view home and the
 * New Automation chooser window are parked (desk/_parked/automations/). */
import "./automation-home.css";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import type { CoreProps } from "../../../pages/cores/core-types";
import { keepPlace } from "../../deskMemory";
import { spriteUrl } from "../../sprites";
import { useDesk } from "../../store";
import { StatusBar, SurfaceState, countWords, Rail, type StatusBarItem } from "../../surface";
import { useWindowInterior } from "../../surface/interior";
import { WORKBENCH_CHANGE_KINDS, useOnDeskChanged } from "../../useDeskChangedRefresh";
import { AutomationBody } from "./AutomationBody";
import { AutomationStarters } from "./Starters";
import { NEW_AUTOMATION_PLACE, PICKED_AUTOMATION_PLACE } from "./places";
import {
  endedRuns,
  hasStarts,
  isOn,
  nextWords,
  runSpine,
  runSpineWords,
  whenWords,
  type AutomationDetail,
} from "./model";

/** The rail's mono line: the next run, else when it runs (· Off). */
export function railWhen(automation: AutomationDetail): string {
  if (hasStarts(automation) && !isOn(automation)) return `${whenWords(automation)} · Off`;
  const next = nextWords(automation.next_run_at);
  return next ? next.replace(/^Next: /, "next ") : whenWords(automation);
}

export function AutomationsCore(_props: CoreProps) {
  const [automations, setAutomations] = useState<AutomationDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [making, setMaking] = useState(false);
  // The automation a starter just made is chosen before the list has read it.
  const [made, setMade] = useState<string | null>(null);
  const kept = useDesk((s) => s.places[PICKED_AUTOMATION_PLACE]) || null;
  const [paneOpen, setPaneOpen] = useState(false);
  useWindowInterior("list");

  const load = useCallback(async (quiet = false) => {
    if (!quiet) {
      setLoading(true);
      setLoadError("");
    }
    try {
      const answer = await apiFetch<{ workbenches?: AutomationDetail[] }>("/api/workbenches");
      setAutomations(answer.workbenches || []);
      setLoaded(true);
      setLoadError("");
    } catch (error) {
      setLoadError(`Automations not loaded: ${readableError(error)}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);
  // The pane's own read of the chosen automation keeps its rail item true
  // (its runs, its next run) with no second read of the list.
  const onRead = useCallback((detail: AutomationDetail) => {
    setAutomations((list) => list.map((a) => (a.id === detail.id ? { ...a, ...detail } : a)));
  }, []);
  useOnDeskChanged(() => void load(true), WORKBENCH_CHANGE_KINDS);

  // Another window asked for New automation (the desk's New menu): read once, then cleared.
  const asked = useDesk((s) => s.places[NEW_AUTOMATION_PLACE]) || "";
  useEffect(() => {
    if (!asked) return;
    keepPlace(NEW_AUTOMATION_PLACE, "");
    setMaking(true);
  }, [asked]);

  const picked = made
    ?? (kept && automations.some((a) => a.id === kept) ? kept : automations[0]?.id ?? null);

  const pick = (id: string) => {
    setPaneOpen(true);
    keepPlace(PICKED_AUTOMATION_PLACE, id);
    setMade(null);
    setMaking(false);
  };
  const reveal = (id: string) => {
    setPaneOpen(true);
    keepPlace(PICKED_AUTOMATION_PLACE, id);
    setMade(id);
    setMaking(false);
    void load(true);
    void useDesk.getState().refresh();
  };
  const toggleNew = () => { setPaneOpen(true); setMaking((open) => !open); };


  const counts = useMemo(() => {
    let fresh = 0;
    let failed = 0;
    for (const automation of automations) {
      const runs = endedRuns(automation);
      fresh += runs.filter((r) => r.new).length;
      if (runs[0]?.status === "failed") failed += 1;
    }
    return { fresh, failed };
  }, [automations]);
  const status: Array<StatusBarItem | null> = [
    automations.length ? { key: "count", text: countWords(automations.length, "automation"), testId: "automation-home-count" } : null,
    counts.fresh ? { key: "new", lamp: "ask", text: `${counts.fresh} new` } : null,
    counts.failed ? { key: "failed", lamp: "fail", text: `${counts.failed} failed` } : null,
  ];

  let pane;
  if (making || (loaded && !automations.length && !made)) {
    pane = (
      <div className="automation-new-pane" data-testid={automations.length ? "automation-new-pane" : "automation-home-empty"}>
        {automations.length ? null : (
          <SurfaceState empty emptyLabel="An automation does one job for you, again and again."
            emptyImage={spriteUrl("automation", "automations")} emptyKind="automation" />
        )}
        <AutomationStarters onCreated={reveal} />
      </div>
    );
  } else if (!loaded) {
    pane = <SurfaceState loading={loading} error={loadError || undefined} onRetry={loading ? undefined : () => void load()} />;
  } else if (picked) {
    pane = <AutomationBody key={picked} workbenchId={picked} onRead={onRead} />;
  }

  return (
    <div className="automation-app" data-testid="automations-window">
      <div className="automation-frame surface-rail-layout" data-making={making || undefined}>
        <Rail label="Automations" data-testid="automation-home-rows" picked={making ? null : picked} onPick={pick}
          paneOpen={paneOpen || making} onBack={() => { setPaneOpen(false); setMaking(false); }}
          head={<Button variant="primary" dense aria-expanded={making} onClick={toggleNew} data-testid="automation-new">New automation</Button>}
          items={automations.map((automation) => ({
            id: automation.id, label: <span data-testid="automation-home-name">{automation.name || "Automation"}</span>,
            glyph: <img src={spriteUrl("automation", automation.id, "rest", null, 20)} alt="" draggable={false} />,
            facts: railWhen(automation), state: endedRuns(automation).some((r) => r.new) ? "New" : undefined,
            spine: { segments: runSpine(automation, 6), label: runSpineWords(automation, 6) ?? undefined },
            data: { "data-testid": "automation-rail-item", "data-automation": automation.id },
          }))} />
        <div className="automation-app-pane" data-testid="automations-pane">
          {loadError && loaded ? <SurfaceState error={loadError} onRetry={() => void load()} /> : null}
          {pane}
        </div>
      </div>
      <StatusBar data-testid="automation-home-status" items={status} />
    </div>
  );
}

export default AutomationsCore;
