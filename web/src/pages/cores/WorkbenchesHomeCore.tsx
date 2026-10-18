// Betterment A7 — the Automations home (docs/internal/betterment/workbench/
// DESIGN.md §4, "The Automations app (home)").
//
// One row for each automation: its name, When, With, and NEW when a result
// waits (never "0 new"); Off when it has a start that is off. New automation
// opens the starters. With none yet: the one line, then the starters as
// large cards. The HS-116 card grid and its Recent runs ledger are parked
// (`_parked/WorkbenchesHomeCore.tsx`): results live on each automation.
import "../../desk/components/automation/automation-home.css";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import { useDesk } from "../../desk/store";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceState } from "../../desk/surface/Surface";
import { StateChip } from "../../desk/surface";
import { WorkbenchTemplatePicker } from "../../desk/components/WorkbenchTemplatePicker";
import {
  engineWords,
  hasStarts,
  isOn,
  whenWords,
  type AutomationDetail,
} from "../../desk/components/automation/model";
import { renderHeroSlot } from "./core-layout";
import type { CoreProps } from "./core-types";

/** The row's facts: When · With (· Off). */
export function automationRowWords(automation: AutomationDetail): string {
  const off = hasStarts(automation) && !isOn(automation) ? "Off" : null;
  return [whenWords(automation), engineWords(automation) ?? "No engine yet", off].filter(Boolean).join(" · ");
}

export function newResultCount(automation: AutomationDetail): number {
  return (automation.results ?? []).filter((result) => result.new).length;
}

export function WorkbenchesHomeCore({ hero }: CoreProps) {
  const [automations, setAutomations] = useState<AutomationDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [loadError, setLoadError] = useState("");

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
  useOnDeskChanged(() => void load(true));

  const newAutomation = () => void useDesk.getState().createPrimitive("workbench");
  const verbs = (
    <Button variant="primary" dense onClick={newAutomation} data-testid="automation-new">
      New automation
    </Button>
  );

  if (loading && !loaded) return <SurfaceState loading />;

  return (
    <>
      {renderHeroSlot(hero, verbs)}
      {loadError ? <SurfaceState error={loadError} onRetry={loading ? undefined : () => void load()} /> : null}

      {loaded && automations.length === 0 ? (
        <div className="automation-home-empty" data-testid="automation-home-empty">
          <SurfaceState empty emptyLabel="An automation does one job for you, again and again." emptyGlyph="⊞" />
          <WorkbenchTemplatePicker />
        </div>
      ) : (
        <SurfaceLedger label="Automations" data-testid="automation-home-rows">
          {automations.map((automation) => {
            const fresh = newResultCount(automation);
            return (
              <SurfaceLedgerRow
                key={automation.id}
                primary={automation.name || "Automation"}
                meta={automationRowWords(automation)}
                cells={fresh ? <StateChip state="active" label={`${fresh} NEW`} /> : undefined}
                expands={false}
                onToggle={() => useDesk.getState().openWorkbenchWindow(automation.id)}
                data-testid="automation-home-row"
              />
            );
          })}
        </SurfaceLedger>
      )}
      <SurfaceFooter />
    </>
  );
}
