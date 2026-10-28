// Betterment A7 — the Automations home (docs/internal/betterment/workbench/
// DESIGN.md §4, "The Automations app (home)").
//
// Window grammar (2026-10-24): Toolbar [New automation] → the dense list
// view (Name · When · Engine · Last result) → StatusBar (`1 automation ·
// 1 new`, never a zero). A press selects a row; Enter or a double press
// opens the automation. The selected row's verbs (Run now, Open) sit at the
// status bar's right, as Meetings does. With none yet: the one line, then
// the starters as large cards. The HS-116 card grid and its Recent runs
// ledger are parked (`_parked/WorkbenchesHomeCore.tsx`): results live on
// each automation.
import "../../desk/components/automation/automation-home.css";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import { useDesk } from "../../desk/store";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { triggerWorkbenchRun } from "../../desk/api";
import { SurfaceState } from "../../desk/surface/Surface";
import { StatusBar, ToolGlyph, Toolbar, countWords, type StatusBarItem } from "../../desk/surface/kit";
import { useWindowInterior } from "../../desk/surface/interior";
import { ObjectList, type ObjectListRow, type ObjectListSort } from "../../desk/surface/objects/ObjectList";
import { objectSprite } from "../../desk/surface/objects/kinds";
import type { ObjectTone } from "../../desk/surface/objects/kinds";
import { WorkbenchTemplatePicker } from "../../desk/components/WorkbenchTemplatePicker";
import {
  engineWords,
  hasStarts,
  isOn,
  resultDay,
  whenWords,
  type AutomationDetail,
  type AutomationResult,
} from "../../desk/components/automation/model";
import type { CoreProps } from "./core-types";

/** The row's facts: When · With (· Off). */
export function automationRowWords(automation: AutomationDetail): string {
  const off = hasStarts(automation) && !isOn(automation) ? "Off" : null;
  return [whenWords(automation), engineWords(automation) ?? "No engine yet", off].filter(Boolean).join(" · ");
}

export function newResultCount(automation: AutomationDetail): number {
  return (automation.results ?? []).filter((result) => result.new).length;
}

/** When: the schedule, the events or the press, in his words (· Off
 *  when it has a start that is off). */
export function runsOnWords(automation: AutomationDetail): string {
  const off = hasStarts(automation) && !isOn(automation) ? "Off" : null;
  return [whenWords(automation), off].filter(Boolean).join(" · ");
}

/** The last result as a dot and a word, with its day: New (a result he has
 *  not opened), Done, Failed. Null when it has not run yet. */
export function lastResult(automation: AutomationDetail): { label: string; tone: ObjectTone; at: number } | null {
  const results = (automation.results ?? []).filter((r: AutomationResult) => r.status === "done" || r.status === "failed");
  const last = results[0];
  if (!last) return null;
  const day = resultDay(last.completed_at);
  const word = last.status === "failed" ? "Failed" : newResultCount(automation) ? "New" : "Done";
  const tone: ObjectTone = word === "Failed" ? "fail" : word === "New" ? "ask" : "ok";
  const at = last.completed_at ? new Date(last.completed_at).getTime() : 0;
  return { label: day ? `${word} · ${day}` : word, tone, at: Number.isFinite(at) ? at : 0 };
}

const COLUMNS = [
  { key: "name", word: "Name", track: "minmax(180px, 1.2fr)" },
  { key: "runs", word: "When", track: "minmax(0, 1fr)" },
  { key: "engine", word: "Engine", track: "minmax(0, 0.7fr)" },
  { key: "state", word: "Last result", track: "minmax(124px, 0.6fr)" },
] as const;

const AUTOMATION_SPRITE = objectSprite("workbench", "automations");

export function WorkbenchesHomeCore(_props: CoreProps) {
  const [automations, setAutomations] = useState<AutomationDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [sort, setSort] = useState<ObjectListSort>({ key: "name", dir: "asc" });
  const [running, setRunning] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<{ id: string; tone: "ok" | "fail"; text: string } | null>(null);
  useWindowInterior(loaded && automations.length ? "list" : null);

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

  const open = (id: string) => useDesk.getState().openWorkbenchWindow(id);
  const runNow = async (automation: AutomationDetail) => {
    setRunning(automation.id);
    setReceipt(null);
    try {
      await triggerWorkbenchRun(automation.id);
      setReceipt({ id: automation.id, tone: "ok", text: `Started · ${automation.name || "Automation"}` });
      void load(true);
    } catch (error) {
      setReceipt({ id: automation.id, tone: "fail", text: `Not run · ${readableError(error)}` });
    } finally {
      setRunning(null);
    }
  };

  const rows = useMemo<ObjectListRow[]>(() => automations.map((automation) => {
    const last = lastResult(automation);
    const engine = engineWords(automation);
    return {
      id: automation.id,
      kind: "workbench",
      name: automation.name || "Automation",
      nameTestId: "automation-home-name",
      cells: {
        runs: runsOnWords(automation),
        engine: engine ?? "No engine",
      },
      sortValues: { state: last ? -last.at : 0 },
      state: last ? { label: last.label, tone: last.tone, testId: "automation-home-result" } : undefined,
    };
  }), [automations]);

  const newAutomation = () => void useDesk.getState().createPrimitive("workbench");
  const toolbar = (
    <Toolbar label="Automations" data-testid="automation-home-toolbar">
      <Button variant="primary" dense onClick={newAutomation} data-testid="automation-new">
        <ToolGlyph kind="new" />
        New automation
      </Button>
    </Toolbar>
  );

  if (loading && !loaded) return <>{toolbar}<SurfaceState loading /></>;

  const chosen = automations.find((a) => a.id === selected) ?? null;
  const fresh = automations.reduce((sum, a) => sum + newResultCount(a), 0);
  const failed = rows.filter((row) => row.state?.tone === "fail").length;
  const items: Array<StatusBarItem | null> = [
    { key: "count", text: countWords(automations.length, "automation"), testId: "automation-home-count" },
    { key: "new", lamp: "ask", text: countWords(fresh, "new", "new") },
    { key: "failed", lamp: "fail", text: countWords(failed, "failed", "failed") },
    receipt
      ? { key: "receipt", lamp: receipt.tone, text: <span data-testid="automation-home-receipt">{receipt.text}</span> }
      : null,
  ];
  const verbs = chosen ? (
    <>
      <Button dense variant="secondary" loading={running === chosen.id} disabled={running !== null}
        onClick={() => void runNow(chosen)} data-testid="automation-home-run">
        <ToolGlyph kind="retry" />
        Run now
      </Button>
      <Button dense variant="secondary" onClick={() => open(chosen.id)} data-testid="automation-home-open">
        <ToolGlyph kind="open" />
        Open
      </Button>
    </>
  ) : null;

  return (
    <>
      {toolbar}
      {loadError ? <SurfaceState error={loadError} onRetry={loading ? undefined : () => void load()} /> : null}
      {loaded && automations.length === 0 ? (
        <div className="automation-home-empty" data-testid="automation-home-empty">
          <SurfaceState empty emptyLabel="An automation does one job for you, again and again." emptyImage={AUTOMATION_SPRITE}
            emptyKind="automation" onAction={newAutomation} actionLabel="New automation" />
          <WorkbenchTemplatePicker />
        </div>
      ) : automations.length ? (
        <div className="automation-home-list" data-testid="automation-home-rows">
          <ObjectList
            label="Automations"
            density="dense"
            rows={rows}
            columns={COLUMNS.filter((column) => column.key !== "state" || rows.some((row) => row.state))}
            sort={sort}
            onSort={(key: string) => setSort((current) => ({ key, dir: current.key === key && current.dir === "asc" ? "desc" : "asc" }))}
            selectedId={chosen?.id ?? null}
            onSelect={setSelected}
            onOpen={open}
            rowProps={() => ({ "data-testid": "automation-home-row" })}
          />
        </div>
      ) : null}
      <StatusBar data-testid="automation-home-status" items={items} verbs={verbs} />
    </>
  );
}
