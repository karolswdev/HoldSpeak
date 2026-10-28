/* PHILO-3-04 — the thought's receipt (canvas ratified 2026-09-23,
 * pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-04-canvas).
 *
 * Line 1 is the write: Saved <time> from the hub's stamp on the last kept
 * write, SAVING… from an edit until the write lands, `Could not save · <cause> ·
 * Your words stay here`,
 * or CHANGED ELSEWHERE. Line 2 is the filing state. */
import { wireDate } from "../surface/format";
import { keptReceipt } from "../keptReceipt";
import type { Thought } from "../thoughts";
import type { ThoughtSaveFailure } from "../pullouts/editors/useThoughtNoteWriter";

export const SAVE_FAILURE_CAUSE: Record<ThoughtSaveFailure, string> = {
  no_answer: "The hub did not answer",
  not_accepted: "The hub did not accept the change",
};

/** The hub stamps ISO UTC (`...Z`); an older SQLite stamp has no zone and is UTC too. */
export function hubStampMs(stamp: string | null | undefined): number | null {
  return wireDate(stamp)?.getTime() ?? null;
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
  // W6-H words: what failed, why, and what stayed, in sentence case; Retry is beside it.
  if (state.failure) return { text: `Could not save · ${SAVE_FAILURE_CAUSE[state.failure]} · Your words stay here`, danger: true };
  if (state.pending || state.saving) return { text: "SAVING…", danger: false };
  const kept = keptReceipt(hubStampMs(state.keptAt));
  return kept ? { text: kept.replace(/^Kept · /, "Saved "), danger: false } : null;
}

export function thoughtFilingLine(thought: Thought, finished: boolean): string {
  const name = (thought.directory_name || "").trim();
  // W6-H words: sentence case; the drawer's name keeps its own case.
  const filing = thought.filing_status === "filed" ? (name ? `In ${name}` : "In a drawer") : "Not in a drawer";
  return finished ? `${filing} · Finished` : filing;
}

/** Window grammar, delight (2026-10-24): the Note's status bar says the
 *  write in warm, sentence-case words with a lamp tone — "Saved just now",
 *  "Saved 5 min ago", then the kept time. The same facts as
 *  `thoughtWriteLine`, which other editors keep. */
export function thoughtStatusWords(
  state: ThoughtWriteState,
  now: number = Date.now(),
): { text: string; tone: "ok" | "busy" | "danger" } | null {
  if (state.conflicted) return { text: "Changed elsewhere", tone: "danger" };
  if (state.failure) {
    const cause = SAVE_FAILURE_CAUSE[state.failure].toLowerCase();
    return { text: `Did not save · ${cause}`, tone: "danger" };
  }
  if (state.pending || state.saving) return { text: "Saving…", tone: "busy" };
  const at = hubStampMs(state.keptAt);
  if (at === null) return null;
  const age = now - at;
  if (age >= 0 && age < 60_000) return { text: "Saved just now", tone: "ok" };
  if (age >= 0 && age < 3_600_000) return { text: `Saved ${Math.floor(age / 60_000)} min ago`, tone: "ok" };
  const kept = keptReceipt(at);
  return kept ? { text: kept.replace(/^Kept · /, "Saved "), tone: "ok" } : null;
}
