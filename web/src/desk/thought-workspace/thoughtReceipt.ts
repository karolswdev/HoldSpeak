/* PHILO-3-04 — the thought's receipt (canvas ratified 2026-09-23,
 * pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-04-canvas).
 *
 * Line 1 is the write: KEPT · <time> from the hub's stamp on the last kept
 * write, SAVING… from an edit until the write lands, DID NOT SAVE · <cause>,
 * or CHANGED ELSEWHERE. Line 2 is the filing state. */
import { keptReceipt } from "../keptReceipt";
import type { Thought } from "../thoughts";
import type { ThoughtSaveFailure } from "../pullouts/editors/useThoughtNoteWriter";

export const SAVE_FAILURE_CAUSE: Record<ThoughtSaveFailure, string> = {
  no_answer: "THE HUB DID NOT ANSWER",
  not_accepted: "THE HUB DID NOT ACCEPT THE CHANGE",
};

/** The hub stamps ISO UTC (`...Z`); an older SQLite stamp has no zone and is UTC too. */
export function hubStampMs(stamp: string | null | undefined): number | null {
  if (!stamp) return null;
  const iso = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?$/.test(stamp) ? `${stamp.replace(" ", "T")}Z` : stamp;
  const at = Date.parse(iso);
  return Number.isNaN(at) ? null : at;
}

export type ThoughtWriteState = {
  pending: boolean;
  saving: boolean;
  failure: ThoughtSaveFailure | null;
  conflicted: boolean;
  keptAt: string | null;
};

export function thoughtWriteLine(state: ThoughtWriteState): { text: string; danger: boolean } | null {
  if (state.conflicted) return { text: "CHANGED ELSEWHERE", danger: true };
  if (state.failure) return { text: `DID NOT SAVE · ${SAVE_FAILURE_CAUSE[state.failure]}`, danger: true };
  if (state.pending || state.saving) return { text: "SAVING…", danger: false };
  const kept = keptReceipt(hubStampMs(state.keptAt));
  return kept ? { text: kept.toUpperCase(), danger: false } : null;
}

export function thoughtFilingLine(thought: Thought, finished: boolean): string {
  const name = (thought.directory_name || "").trim();
  const filing = thought.filing_status === "filed" ? (name ? `IN ${name.toUpperCase()}` : "IN A DRAWER") : "NOT IN A DRAWER";
  return finished ? `${filing} · FINISHED` : filing;
}
