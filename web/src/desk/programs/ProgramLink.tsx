import { Button } from "../../components/signal/Signal";
import { openProgramStep } from "../openObject";
import type { FlightProgram } from "./flightProgram";

/** Agent-to-program door; the system Button owns its material and target. */
export function ProgramLink({
  program,
}: {
  program: FlightProgram | null | undefined;
}) {
  return program ? (
    <Button
      dense
      variant="ghost"
      onClick={() => openProgramStep(program.id, program.stepId || "")}
      data-testid="agent-program-step"
    >
      {program.stepOrdinal
        ? `Step ${program.stepOrdinal} of ${program.title || "a program"}`
        : `A step of ${program.title || "a program"}`}
    </Button>
  ) : null;
}
