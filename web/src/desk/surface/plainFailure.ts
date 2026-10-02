/** PHILO-13-04 (A3) — a failure face says what did not happen and why, in
 * plain words (UX-CANON A.3, A.10; Tenet 4). It never prints the hub's own
 * text (`detail` strings, error codes, model paths): that text stays out of
 * the face. The face beside it carries the verb (Try again, Retry, OK).
 *
 * Label grammar: `<WHAT DID NOT HAPPEN> · <WHY>`, for example
 * `BRIEF DID NOT LOAD · HUB FAILED`. */
import { ApiError } from "../../lib/api";

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
  if (cause instanceof TypeError) return "HUB UNREACHABLE";
  if (cause instanceof Error && cause.name === "AbortError") return "STOPPED";
  const status = statusOf(cause);
  if (status === 401 || status === 403) return "ACCESS REFUSED";
  if (status === 404) return "NOT FOUND";
  if (status === 408 || status === 504) return "TIMED OUT";
  if (status === 409 || status === 412) return "CHANGED ELSEWHERE";
  if (status === 413) return "TOO LARGE";
  if (status === 423) return "LOCKED";
  if (status === 429) return "TOO MANY TRIES";
  if (status === 400 || status === 422) return "NOT ACCEPTED";
  if (status === 501 || status === 503) return "NOT AVAILABLE NOW";
  if (status >= 500) return "HUB FAILED";
  return "DID NOT WORK";
}

/** `<what> · <why>` — what did not happen, then why. */
export function plainFailure(what: string, cause: unknown): string {
  return `${what.toUpperCase()} · ${plainReason(cause)}`;
}
