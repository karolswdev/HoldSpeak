/** Programs (PROGRAMS-DESIGN-2026-10-28 §9): the pullout families whose
 *  object is the hub's, not a desk primitive. `pullout:program:<id>` is the
 *  Program window; it reads its own record. The family's stand-in object
 *  (objectWindows.ts) carries the family name as its kind. */
import type { PulloutContent } from "./types";
import { ProgramPullout } from "../programs/ProgramWindow";
import { ProgramShotPullout } from "../programs/ProgramShot";

export const PULLOUT_FAMILIES: Readonly<Record<string, PulloutContent>> = {
  program: ProgramPullout,
  // PG-REQ (REQ12): a Shot requirement's image, `pullout:program-shot:<program>:<requirement>`.
  "program-shot": ProgramShotPullout,
};
