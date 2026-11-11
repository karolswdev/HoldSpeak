/* Parked: the live kit owns the Programs window grammar. */
import { useGuideView } from "../walk/viewState";
import { useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { Rail, type RailItem, type SpineTone } from "../surface";
import { spriteUrl } from "../sprites";
import type { ProgramList, ProgramState, ProgramSummary } from "./types";

const WEEK_MS = 7 * 24 * 60 * 60 * 1000;

/** The order of the active tiles: what waits on him first. */
const ORDER: readonly ProgramState[] = ["waiting", "failed", "running", "drafting", "parked"];

const STATE_WORDS: Record<string, string> = {
  waiting: "waits on you", failed: "failed", running: "running", drafting: "drafting", parked: "parked", done: "done",
};

const byNewest = (a: ProgramSummary, b: ProgramSummary) => String(b.updated_at).localeCompare(String(a.updated_at));

/** An automation's runs are Programs (2026-11-08): the rail keeps one tile
 *  per automation, its latest run, so a daily run does not fill the rail. */
export function latestRuns(programs: readonly ProgramSummary[]): ProgramSummary[] {
  const newest = new Map<string, ProgramSummary>();
  for (const row of programs) {
    if (!row.automation_id) continue;
    const seen = newest.get(row.automation_id);
    if (!seen || String(row.created_at).localeCompare(String(seen.created_at)) > 0) newest.set(row.automation_id, row);
  }
  return programs.filter((row) => !row.automation_id || newest.get(row.automation_id) === row);
}

/** The rail's two groups: the active Programs (waiting first) and the
 *  ones done in the last seven days. */
export function railGroups(all: readonly ProgramSummary[], now = Date.now()): { active: ProgramSummary[]; done: ProgramSummary[] } {
  const programs = latestRuns(all);
  // A Program parked with a reason (a proof, done with it: #1707) is done with: no tile.
  const active = ORDER.flatMap((state) => programs.filter((row) => row.state === state && !row.parked_as).sort(byNewest));
  const done = programs.filter((row) => row.state === "done" && now - Date.parse(row.updated_at) <= WEEK_MS).sort(byNewest);
  return { active, done };
}

/** The Program the window shows when he has picked none (or his pick left). */
export function defaultPick(programs: readonly ProgramSummary[], picked: string | null, now = Date.now()): string | null {
  if (picked && programs.some((row) => row.id === picked)) return picked;
  const { active, done } = railGroups(programs, now);
  return active[0]?.id ?? done[0]?.id ?? null;
}

/** "The Room lists its Programs, waits on you"; a Done one says its mark ("…, finished"). */
export const tileWords = (row: ProgramSummary) =>
  `${row.title}, ${row.state === "done" && row.finished_words ? row.finished_words : STATE_WORDS[row.state] ?? row.state_word}`;

const TONES: Record<ProgramState, SpineTone> = { waiting: "brass", failed: "coral", running: "steel", drafting: "idle", parked: "graphite", done: "moss" };

export function ProgramRail({ list, picked, making, busy = false, onPick, onNew }: {
  list: ProgramList; picked: string | null; making: boolean; busy?: boolean;
  onPick(id: string): void; onNew(): void;
}) {
  const { active, done } = railGroups(list.programs);
  const night = list.night;
  const item = (row: ProgramSummary): RailItem => ({
    id: row.id, label: row.title, accessibleLabel: tileWords(row),
    glyph: <img src={spriteUrl("program", row.id, "rest", null, 32)} alt="" draggable={false} />,
    state: <span data-state={row.state}>{row.state === "done" && row.finished_words ? row.finished_words : STATE_WORDS[row.state] ?? row.state_word}</span>,
    spine: { tone: TONES[row.state] }, data: { "data-program": row.id, "data-state": row.state, "data-testid": "programs-rail-tile" },
  });
  const [paneOpen, setPaneOpen] = useState(false);
  useGuideView(() => paneOpen, saved => setPaneOpen(saved));
  useEffect(() => { if (making) setPaneOpen(true); }, [making]);
  return <Rail label="Programs" data-testid="programs-rail" picked={making ? null : picked} onPick={(id) => { setPaneOpen(true); onPick(id); }}
    hostBack={making} paneOpen={paneOpen} onBack={() => setPaneOpen(false)}
    head={<Button variant="primary" dense aria-expanded={making} disabled={busy} onClick={onNew} data-testid="programs-new">New program</Button>}
    groups={[
      { id: "active", label: "In progress", items: active.map(item) },
      { id: "done", label: "Done this week", items: done.map(item) },
      { id: "night", label: "Tonight", items: night?.queued && night.program_id ? [{
        id: night.program_id, label: `Tonight ${night.start}`, count: night.queued,
        accessibleLabel: `Tonight ${night.start}, ${night.queued} queued`,
        data: { "data-program": night.program_id, "data-testid": "programs-rail-night" },
      }] : [] },
    ]} />;
}
