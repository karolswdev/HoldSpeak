/** PHILO-13-04 (A3) — a failure face says what did not happen and why, in
 * plain words (UX-CANON A.3, A.10; Tenet 4). It never prints the hub's own
 * text (`detail` strings, error codes, model paths): that text stays out of
 * the face. The face beside it carries the verb (Try again, Retry, OK).
 *
 * Label grammar: `<what did not happen> · <why>`, for example
 * `Brief did not load · Hub failed` (WORDS-VOCAB 2026-10-30: the words are
 * said in sentence case here; no caller re-cases them). */
import { ApiError } from "../../lib/api";
import { stateWords } from "./words";

function statusOf(cause: unknown): number {
  if (cause instanceof ApiError) return cause.status;
  if (typeof Response !== "undefined" && cause instanceof Response) return cause.status;
  if (cause && typeof cause === "object") {
    const status = (cause as { status?: unknown }).status;
    if (typeof status === "number") return status;
  }
  return 0;
}

/** Why it failed, in plain words. */
export function plainReason(cause: unknown): string {
  if (cause instanceof TypeError) return "Hub unreachable";
  if (cause instanceof Error && cause.name === "AbortError") return "Stopped";
  const status = statusOf(cause);
  if (status === 401 || status === 403) return "Access refused";
  if (status === 404) return "Not found";
  if (status === 408 || status === 504) return "Timed out";
  if (status === 409 || status === 412) return "Changed elsewhere";
  if (status === 413) return "Too large";
  if (status === 423) return "Locked";
  if (status === 429) return "Too many tries";
  if (status === 400 || status === 422) return "Not accepted";
  if (status === 501 || status === 503) return "Not available now";
  if (status >= 500) return "Hub failed";
  return "Did not work";
}

/** `<what> · <why>` — what did not happen, then why. A caller's caps key
 *  (`NOT SAVED`) reads in sentence case (`Not saved · Hub failed`). */
export function plainFailure(what: string, cause: unknown): string {
  return `${stateWords(what)} · ${plainReason(cause)}`;
}

/** W6-G words: why it failed, for a hover title only (`Hub unreachable`,
 *  `Not available now · HTTP 503`). The face never shows it. */
export function failureTitle(cause: unknown): string {
  const said = plainReason(cause);
  const status = statusOf(cause);
  return status ? `${said} · HTTP ${status}` : said;
}

/** W6-G words: a failure face in plain words and sentence case: what failed
 *  and what stayed (`Could not load people · Nothing changed`), then what to
 *  do next when no Try again Button stands beside it (`· Try again`). The
 *  reason goes in the hover title (`failureTitle`). */
export function plainWords(failed: string, stayed = "Nothing changed", next?: string): string {
  return next ? `${failed} · ${stayed} · ${next}` : `${failed} · ${stayed}`;
}

/** A failure for a face: the plain words and the hover title. */
export type PlainFail = { words: string; title: string };

export function plainFail(failed: string, cause: unknown, stayed?: string, next?: string): PlainFail {
  return { words: plainWords(failed, stayed, next), title: failureTitle(cause) };
}
