// Parked: app-owned rail replaced by surface Rail.
/* The rail of Programs (the language, 2026-11-08; ProgramsBold canvas):
 * the left edge of the Programs window, 64 px. One tile per Program: its
 * sprite at 32 px with a state dot at the corner (brass waits on you,
 * steel running, moss done, coral failed, graphite parked, none for a
 * draft); a draft is a dashed outline tile. The picked tile is ringed,
 * in brass when it waits on him. "+" (New program) at the top, a rule, the
 * active Programs (waiting first), a rule, the ones done this week, and
 * at the foot the night tile (navy) with the queued count in mono, when
 * the hub names a night; a press opens the night Program. Hover and focus say the name (title and
 * aria-label); ↑ and ↓ (← and → on the phone strip) move the focus, Enter
 * picks. At 393 the rail is a strip at the window's foot (programs.css). */
import { useRef, type KeyboardEvent } from "react";
import { Button } from "../../components/signal/Signal";
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

function Tile({ row, picked, onPick }: { row: ProgramSummary; picked: boolean; onPick(id: string): void }) {
  const draft = row.state === "drafting";
  return (
    <Button variant="chrome" className="pg-rail-tile" data-state={row.state} data-picked={picked ? "" : undefined}
      aria-current={picked ? "page" : undefined} aria-label={tileWords(row)} title={tileWords(row)} tabIndex={picked ? 0 : -1}
      onClick={() => onPick(row.id)} data-program={row.id} data-testid="programs-rail-tile">
      {draft ? null : <img className="pg-rail-sprite" src={spriteUrl("program", row.id, "rest", null, 32)} alt="" width={32} height={32} draggable={false} />}
      {draft ? null : <i className="pg-rail-dot" data-state={row.state} aria-hidden="true" />}
    </Button>
  );
}

export function ProgramRail({ list, picked, making, busy = false, onPick, onNew }: {
  list: ProgramList; picked: string | null; making: boolean;
  /** A create in flight: "+" waits for its answer. */
  busy?: boolean;
  onPick(id: string): void; onNew(): void;
}) {
  const ref = useRef<HTMLElement | null>(null);
  const { active, done } = railGroups(list.programs);
  const night = list.night ?? null;
  // The night tile opens the night Program (the rail's own pick); with no
  // Program to open there is no tile (never a dead verb).
  const nightId = night?.queued ? night.program_id : null;
  // ↑ ↓ (and ← → on the strip) move the focus along the tiles; Enter is the Button's own press.
  const onKeys = (event: KeyboardEvent<HTMLElement>) => {
    const step = event.key === "ArrowDown" || event.key === "ArrowRight" ? 1 : event.key === "ArrowUp" || event.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    const tiles = [...(ref.current?.querySelectorAll<HTMLButtonElement>(".pg-rail-tile") ?? [])];
    const at = tiles.indexOf(document.activeElement as HTMLButtonElement);
    if (!tiles.length) return;
    event.preventDefault();
    tiles[Math.min(tiles.length - 1, Math.max(0, at < 0 ? 0 : at + step))]?.focus();
  };
  return (
    <nav ref={ref} className="pg-rail" aria-label="Programs" onKeyDown={onKeys} data-testid="programs-rail">
      <Button variant="chrome" className="pg-rail-tile pg-rail-new" aria-label="New program" title="New program"
        aria-expanded={making} disabled={busy} onClick={onNew} data-testid="programs-new">+</Button>
      {active.length ? <i className="pg-rail-rule" aria-hidden="true" /> : null}
      {active.map((row) => <Tile key={row.id} row={row} picked={!making && row.id === picked} onPick={onPick} />)}
      {done.length ? <i className="pg-rail-rule" aria-hidden="true" /> : null}
      {done.map((row) => <Tile key={row.id} row={row} picked={!making && row.id === picked} onPick={onPick} />)}
      <span className="pg-rail-fill" aria-hidden="true" />
      {night && nightId ? (
        <Button variant="chrome" className="pg-rail-tile pg-rail-night" aria-label={`Tonight ${night.start}, ${night.queued} queued`}
          title={`Tonight ${night.start}, ${night.queued} queued`} tabIndex={-1}
          onClick={() => onPick(nightId)} data-program={nightId} data-testid="programs-rail-night">{night.queued}</Button>
      ) : null}
    </nav>
  );
}
