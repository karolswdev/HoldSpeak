/* Programs (design §9 Seams, "Agents"): an agent that belongs to a step
 * says "Step 4 of The hub stops stalling" under its name; a press opens
 * the Program. */
import { Button } from "../../components/signal/Signal";
import { openProgram } from "./open";
import "./programs.css";
import type { FlightProgram } from "./flightProgram";

export { flightProgramOf, type FlightProgram } from "./flightProgram";

export function stepLineWords(program: FlightProgram): string {
  const title = program.title || "a program";
  return program.stepOrdinal ? `Step ${program.stepOrdinal} of ${title}` : `A step of ${title}`;
}

export function ProgramStepLine({ program }: { program: FlightProgram | null | undefined }) {
  if (!program) return null;
  return (
    <Button dense variant="ghost" className="pg-step-line" onClick={() => openProgram(program.id)} data-testid="agent-program-step">
      {stepLineWords(program)}
    </Button>
  );
}
