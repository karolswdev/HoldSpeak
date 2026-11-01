/* Programs PG-WINDOW W2 (PROGRAM-WINDOW-2026-10-31, canvas
 * program-window-2026-10-31.html, direction A "the line and the note").
 *
 * The line: the program's steps as one station track (the surface
 * StationTrack, word form), one station per step and the end ("Done when")
 * when the program has its own requirements. Done stations are grey with
 * their PR; a running step breathes blue; the step that waits on him
 * breathes ember and is the current station; a step that waits on his
 * answer is marked `blocked` (warn ink). It is a picture, not a control:
 * the rows under it are what he presses. Under it: the goal, and the rounds
 * he answered before Start as one quiet Token. */
import { StationTrack, type TrackStation } from "./StationTrack";
import { Token } from "../surface/Token";
import { countWords } from "../surface";
import { stepTone, stepWord } from "./model";
import type { Program, ProgramStep } from "./types";

const RUNNING = new Set(["briefed", "working", "checking", "review", "pr_open"]);

function stationOf(step: ProgramStep, held: Set<string>, blocked: Set<number>, here: string | null): TrackStation {
  // The number is the word; the title is its sub (hidden at the phone
  // width, where the line is numbers only and the rows carry the names).
  const word = String(step.ordinal);
  const sub = step.title;
  if (step.state === "merged" || step.state === "done") {
    const pr = step.pr?.number ?? step.history?.pr_number;
    return { key: step.id, word, sub, note: pr ? `PR #${pr} merged` : stepWord(step), state: "passed", tone: "ok", mark: "done" };
  }
  if (step.id === here || held.has(step.id)) {
    return { key: step.id, word, sub, note: "Waits on you", state: step.id === here ? "current" : "ahead", tone: "ask", live: true, mark: "here" };
  }
  if (blocked.has(step.ordinal)) {
    return { key: step.id, word, sub, note: `Waits on ${step.after.join(" and ")}`, state: "ahead", tone: "warn", mark: "blocked" };
  }
  if (RUNNING.has(step.state)) {
    return { key: step.id, word, sub, note: stepWord(step), state: here ? "ahead" : "current", tone: "info", live: true, mark: "running" };
  }
  const tone = stepTone(step.state);
  // A planned step says its size by rule (`Planned · 3k`).
  const size = (step.state === "planned" || step.state === "ready") && step.estimate?.words && step.estimate.fits !== false
    ? ` · ${step.estimate.words.split(" of ")[0]}` : "";
  return { key: step.id, word, sub, note: `${stepWord(step)}${size}`, state: "ahead", tone: tone === "idle" ? "idle" : tone, mark: tone === "fail" ? "red" : "planned" };
}

/** The stations of the line, the held step lit. */
export function lineStations(program: Program): TrackStation[] {
  const steps = program.steps.filter((step) => !step.race_of);
  const items = program.your_turn_items ?? [];
  const held = new Set(items.map((item) => item.step_id).filter(Boolean));
  const here = items[0]?.step_id || null;
  const blocked = new Set(items[0]?.brief?.blocked ?? []);
  const stations = steps.map((step) => stationOf(step, held, blocked, here));
  // #1697: a night program sleeps until its window (Drafting, or Running
  // before the night): the first station says so.
  if (program.night && (program.state === "drafting" || !steps.some((step) => step.state !== "planned" && step.state !== "ready"))) {
    stations.unshift({ key: "night", word: `Sleeps until ${program.night.start}`, note: program.night.line,
      state: "ahead", tone: "idle", mark: "night" });
  }
  const own = (program.requirements ?? []).filter((row) => row.scope === "program" || row.scope === "every_step");
  if (own.length) {
    const met = own.every((row) => row.state === "met" || row.state === "waived");
    stations.push({
      key: "end", word: "Done", sub: "when", note: countWords(own.length, "requirement") ?? undefined,
      state: program.state === "done" ? "passed" : "ahead", tone: met ? "ok" : "idle", mark: "end",
    });
  }
  return stations;
}

function lineLabel(program: Program, stations: readonly TrackStation[]): string {
  const here = stations.find((station) => station.mark === "here");
  const run = stations.find((station) => station.mark === "running");
  const done = stations.filter((station) => station.mark === "done").length;
  const total = program.steps.filter((step) => !step.race_of).length;
  // Never "0 of 3 done" (the zero law): the count of steps until one is done.
  const parts = [done ? `${done} of ${total} done` : `${total} ${total === 1 ? "step" : "steps"}`];
  if (run) parts.push(`step ${run.word}, ${run.sub}, runs`);
  if (here) parts.push(`step ${here.word}, ${here.sub}, waits on you`);
  return parts.join(", ");
}

export function ProgramLine({ program, goal = true }: { program: Program; /** Drafting edits the goal in its headline. */ goal?: boolean }) {
  const stations = lineStations(program);
  if (!stations.length) return null;
  const asked = (program.rounds ?? []).filter((round) => round.answered > 0);
  // PG-IMPORT IMP1: a Done program's second mark, achromatic.
  const finished = program.state === "done" ? program.finished_words : undefined;
  return (
    <div className="pg-line" data-testid="programs-line">
      <StationTrack stations={stations} form="words"
        label={finished ? `${lineLabel(program, stations)}, ${finished}` : lineLabel(program, stations)} />
      {finished ? <p className="pg-line-finished"><span className="pg-finished" data-finished={program.finished}
        data-testid="programs-line-finished">{finished}</span></p> : null}
      {(goal && program.goal) || asked.length ? (
        <p className="pg-line-goal">
          {goal && program.goal ? <span className="pg-line-goal-words" title={program.goal}>{`Goal: ${program.goal.split("\n")[0]}`}</span> : null}
          {asked.length ? <Token>{`Asked first: ${asked.map((round) => round.name).join(" · ")}`}</Token> : null}
        </p>
      ) : null}
    </div>
  );
}
