/** Programs (PROGRAMS-DESIGN-2026-10-28 §9): the pullout families whose
 *  object is the hub's, not a desk primitive. `pullout:program:<id>` is the
 *  Program window; it reads its own record. The family's stand-in object
 *  (objectWindows.ts) carries the family name as its kind. */
import { createElement, lazy, Suspense } from "react";
import type { PulloutContent } from "./types";
import { ProgramShotPullout } from "../programs/ProgramShot";
import { SurfaceState } from "../surface";
import { watchChunk } from "../../runtime/freshBuild";

/** The Program window is not on glass at first paint: its code is its own
 *  chunk (measure 2026-11-08), loaded when the window opens, with the
 *  surface's loading face until it arrives. */
const ProgramCore = lazy(watchChunk(() => import("../programs/ProgramWindow")));

const ProgramPullout: PulloutContent = (props) =>
  createElement(Suspense, { fallback: createElement(SurfaceState, { loading: true }) }, createElement(ProgramCore, props));

export const PULLOUT_FAMILIES: Readonly<Record<string, PulloutContent>> = {
  program: ProgramPullout,
  // PG-REQ (REQ12): a Shot requirement's image, `pullout:program-shot:<program>:<requirement>`.
  "program-shot": ProgramShotPullout,
};
