/* New program, filled in from another window (2026-11-08: an old queue
 * automation is set up as a program from its tasks). The Programs window
 * reads the place once and clears it; nothing is made until he presses
 * Create. */
import { keepPlace } from "../deskMemory";
import { useDesk } from "../store";

/** What New program starts with when another window opens it. */
export interface NewProgramPrefill {
  title: string;
  goal?: string;
  /** Written at once as the Program's steps (each an agent step). */
  steps?: Array<{ title: string; brief: string }>;
}

export const NEW_PROGRAM_PLACE = "programs/new";

/** Open Programs on New program, filled in. */
export function openNewProgram(prefill: NewProgramPrefill): void {
  keepPlace(NEW_PROGRAM_PLACE, JSON.stringify(prefill));
  useDesk.getState().openSurfaceWindow("open-programs");
}
