import { useGuideView } from "../walk/viewState";
/* Programs (the language, 2026-11-08; ProgramsBold canvas, owner: "the
 * Programs window as one object"): the app window `surface-programs`, ⌃7,
 * beside Agents. The window IS the Program.
 *
 * Window grammar: title bar → the shared rail of Programs at the left:
 * New program, the active Programs, the ones done this week, the night;
 * ProgramRail.tsx → the Program at the right (ProgramBody, host "pane":
 * the mast, the step spine, the step plate, Earlier steps; the same
 * component the Program window `pullout:program:<id>` hosts) → the
 * StatusBar ("6 programs · 1 waits on you · 2 running · tonight 23:00 · 3
 * queued"; no count of zero). New program opens the wizard
 * (ProgramWizard.tsx) in the right pane; the made Program is then the
 * picked one. At 393 the rail opens the pane with one Back path. Empty: the 64 px
 * program object, one line, one Button. */
import { useEffect, useMemo, useRef, useState } from "react";
import type { CoreProps } from "../../pages/cores/core-types";
import { keepPlace } from "../deskMemory";
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import { StatusBar, SurfaceState, countWords, type StatusBarItem } from "../surface";
import { useWindowInterior } from "../surface/interior";
import { NEW_PROGRAM_PLACE, type NewProgramPrefill } from "./newProgram";
import { openProgram } from "./open";
import { usePrograms } from "./api";
import { ProgramWizard } from "./ProgramWizard";
import { ProgramBody } from "./ProgramWindow";
import { ProgramRail, defaultPick } from "./ProgramRail";
import "./programs.css";

export { openProgram };

const PICKED = "programs/picked";

export function ProgramsCore({ scope }: CoreProps) {
  const { loading, error, list, reload } = usePrograms();
  const scopeProjectId = scope?.startsWith("project:") ? scope.slice("project:".length) : null;
  // The open wizard (its template and its flow), or null.
  const [making, setMaking] = useState<{ template: string; flow: number; prefill?: NewProgramPrefill } | null>(null);
  const [busy, setBusy] = useState(false);
  const flows = useRef(0);
  const kept = useDesk((s) => s.places[PICKED]) || null;
  // The Program the wizard just made is picked before the list has read it.
  const [made, setMade] = useState<string | null>(null);
  const picked = made ?? defaultPick(list.programs, kept);
  useGuideView(() => ({made,making,kept}), saved => {setMade(saved.made);setMaking(saved.making);keepPlace(PICKED,saved.kept ?? "");}, undefined, 1);
  useWindowInterior("list");

  const pick = (id: string) => {
    if (busy) return;
    keepPlace(PICKED, id);
    setMade(null);
    setMaking(null);
  };
  const make = (template: string) => {
    if (busy) return;
    setMaking({ template, flow: ++flows.current });
  };
  // Another window asked for New program, filled in (openNewProgram): read once, then cleared.
  const asked = useDesk((s) => s.places[NEW_PROGRAM_PLACE]) || "";
  useEffect(() => {
    if (!asked) return;
    keepPlace(NEW_PROGRAM_PLACE, "");
    let prefill: NewProgramPrefill | null = null;
    try { prefill = JSON.parse(asked) as NewProgramPrefill; } catch { prefill = null; }
    if (prefill && typeof prefill.title === "string") setMaking({ template: "fast-cycle", flow: ++flows.current, prefill });
  }, [asked]);
  // "+" toggles the wizard; closing it gives the focus back to "+".
  const toggle = () => {
    if (busy) return;
    if (making) closeWizard();
    else make("fast-cycle");
  };
  const closeWizard = () => {
    setMaking(null);
    document.querySelector<HTMLButtonElement>("[data-testid=programs-new]")?.focus();
  };
  // The made Program is the picked one (it opens in the right pane).
  const reveal = (id: string) => {
    keepPlace(PICKED, id);
    setMade(id);
    setMaking(null);
  };

  // The wizard's project card says how many Programs its project has.
  const programsOf = useMemo(() => {
    const out: Record<string, number> = {};
    for (const row of list.programs) {
      const id = row.project?.id ?? row.project_id;
      if (id) out[id] = (out[id] ?? 0) + 1;
    }
    return out;
  }, [list.programs]);

  const counts = list.counts;
  const night = list.night;
  const status: Array<StatusBarItem | null> = [
    list.programs.length ? { key: "total", text: countWords(list.programs.length, "program"), testId: "programs-status-total" } : null,
    counts.waiting ? { key: "waiting", text: `${counts.waiting} ${counts.waiting === 1 ? "waits" : "wait"} on you`, tick: counts.waiting, testId: "programs-status-waiting" } : null,
    counts.running ? { key: "running", text: `${counts.running} running`, tick: counts.running, testId: "programs-status-running" } : null,
    night?.queued ? { key: "night", text: `tonight ${night.start}`, testId: "programs-status-night" } : null,
    night?.queued ? { key: "queued", text: `${night.queued} queued`, testId: "programs-status-queued" } : null,
  ];

  let pane;
  if (making) {
    pane = (
      <ProgramWizard key={making.flow} template={making.template} prefill={making.prefill} scopeProjectId={scopeProjectId} programsOf={programsOf}
        onClose={closeWizard} onMade={reveal} onPending={setBusy} reload={reload} />
    );
  } else if (loading || (error && !list.programs.length)) {
    pane = <SurfaceState loading={loading} error={error ? "The programs did not load. Nothing changed. Try again." : undefined} onRetry={() => void reload()} />;
  } else if (!list.programs.length) {
    pane = (
      <SurfaceState empty emptyKind="program" emptyImage={spriteUrl("program", "programs")} emptyLabel="No program yet"
        emptyHint="A program is a goal cut into steps. An agent does each step."
        actionLabel="New program" onAction={() => make("fast-cycle")} />
    );
  } else if (!picked) {
    pane = (
      <SurfaceState empty emptyKind="program" emptyImage={spriteUrl("program", "programs")} emptyLabel="No program this week"
        actionLabel="New program" onAction={() => make("fast-cycle")} />
    );
  } else {
    pane = <ProgramBody key={picked} programId={picked} host="pane" />;
  }

  return (
    <div className="pg-window pg-programs" data-testid="programs-window">
      <div className="pg-frame surface-rail-layout">
        <ProgramRail list={list} picked={picked} making={Boolean(making)} busy={busy} onPick={pick} onNew={toggle} />
        <div className="pg-pane" data-testid="programs-pane" data-program={making ? undefined : picked ?? undefined}>{pane}</div>
      </div>
      <StatusBar className="pg-status-mono" data-testid="programs-status" items={status} />
    </div>
  );
}

export default ProgramsCore;
