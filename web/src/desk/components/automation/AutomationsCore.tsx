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
 * the rail is a strip on top of the pane. The old list view home and the
 * New Automation chooser window are parked (desk/_parked/automations/). */
import "./automation-home.css";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import type { CoreProps } from "../../../pages/cores/core-types";
import { keepPlace } from "../../deskMemory";
import { spriteUrl } from "../../sprites";
import { useDesk } from "../../store";
import { StatusBar, SurfaceState, countWords, useRovingRows, type StatusBarItem } from "../../surface";
import { useWindowInterior } from "../../surface/interior";
import { Spine } from "../../surface/patterns/Spine";
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

function RailItem({ automation, picked, onPick }: {
  automation: AutomationDetail;
  picked: boolean;
  onPick(id: string): void;
}) {
  const spine = runSpine(automation, 6);
  const fresh = endedRuns(automation).some((r) => r.new);
  const name = automation.name || "Automation";
  return (
    <Button variant="chrome" className="automation-rail-item" aria-current={picked ? "page" : undefined}
      data-picked={picked ? "" : undefined} data-new={fresh ? "" : undefined} tabIndex={picked ? 0 : -1}
      onClick={() => onPick(automation.id)} data-automation={automation.id} data-testid="automation-rail-item">
      <img className="automation-rail-sprite" src={spriteUrl("automation", automation.id, "rest", null, 20)} alt=""
        width={20} height={20} draggable={false} />
      <span className="automation-rail-name" data-testid="automation-home-name">{name}</span>
      {spine.length ? (
        <Spine className="automation-rail-spine" segments={spine} label={runSpineWords(automation, 6) ?? undefined} />
      ) : <span className="automation-rail-spine automation-rail-spine-none" aria-hidden="true" />}
      <span className="automation-rail-when">{railWhen(automation)}</span>
    </Button>
  );
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
  const rail = useRef<HTMLElement | null>(null);
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
    keepPlace(PICKED_AUTOMATION_PLACE, id);
    setMade(null);
    setMaking(false);
  };
  const reveal = (id: string) => {
    keepPlace(PICKED_AUTOMATION_PLACE, id);
    setMade(id);
    setMaking(false);
    void load(true);
    void useDesk.getState().refresh();
  };
  const toggleNew = () => setMaking((open) => !open);

  // The library's roving focus walks the rail; Enter is the Button's own press.
  useRovingRows(rail, { selector: ".automation-rail-item" });

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
      <div className="automation-frame" data-making={making || undefined}>
        <nav ref={rail} className="automation-rail" aria-label="Automations" data-testid="automation-home-rows">
          <Button variant="secondary" dense className="automation-rail-new" aria-expanded={making}
            onClick={toggleNew} data-testid="automation-new">
            New automation
          </Button>
          {automations.map((automation) => (
            <RailItem key={automation.id} automation={automation} picked={!making && automation.id === picked} onPick={pick} />
          ))}
        </nav>
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
