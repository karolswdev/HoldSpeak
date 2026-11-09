/* The Program's mast (the language, 2026-11-08; ProgramsBold canvas): the
 * program sprite, the title in the display face, one mono facts line
 * ("AI SDLC · Claude Code · hands-off · started fri 19:30 · waits on you")
 * and the verbs in the slot (Amend, Park). The kit's Mast draws it; the
 * title steps down by a container query (programs.css: 18/22 at 393). */
import type { ReactNode } from "react";
import { Mast } from "../surface/patterns/Mast";
import { controlValue } from "./model";
import { runsOnLabel } from "./StepRow";
import type { Program } from "./types";
import { ShowMe } from "../walk/ShowMe";

/** The ladder in his words: YOLO runs hands-off. */
const CONTROL_FACT = { secure: "secure", normal: "normal", yolo: "hands-off" } as const;

const STATE_FACT: Record<string, string> = {
  waiting: "waits on you", running: "running", drafting: "drafting", done: "done", parked: "parked", failed: "failed",
};

/** `fri 19:30` (local). */
export function dayClock(at: string | null | undefined): string {
  const ms = Date.parse(String(at ?? ""));
  if (!Number.isFinite(ms)) return "";
  const when = new Date(ms);
  const day = when.toLocaleDateString("en-GB", { weekday: "short" }).toLowerCase();
  return `${day} ${when.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false })}`;
}

/** The facts line: project · agent · control · started · state. A Done
 *  Program's state is its mark ("finished · needs a decision", achromatic). */
export function programFacts(program: Program): string {
  const project = program.place?.project?.name ?? program.project?.name ?? "";
  const agent = runsOnLabel(program.default?.profile, program.default?.engine);
  const started = program.steps.map((step) => step.started_at).filter((at): at is string => Boolean(at)).sort()[0];
  const when = started ? `started ${dayClock(started)}` : program.state === "drafting" ? "" : `made ${dayClock(program.created_at)}`;
  return [project, agent, CONTROL_FACT[controlValue(program.control)], when.trim() === "made" ? "" : when,
    finishedOf(program) ? "" : STATE_FACT[program.state] ?? program.state_word].filter(Boolean).join(" · ");
}

const finishedOf = (program: Program) => (program.state === "done" ? program.finished_words : undefined);

export function ProgramMast({ program, children }: { program: Program; children?: ReactNode }) {
  return (
    <Mast kind="program" id={program.id} title={program.title} className="pg-mast" data-testid="programs-mast"
      facts={finishedOf(program) ? (
        <>
          {`${programFacts(program)} · `}
          <span className="pg-finished" data-finished={program.finished} data-testid="programs-line-finished">{finishedOf(program)}</span>
        </>
      ) : programFacts(program)}>
      {children}
      <ShowMe app="surface-programs" />
    </Mast>
  );
}
