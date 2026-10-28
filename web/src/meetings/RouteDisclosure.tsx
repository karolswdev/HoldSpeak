/** HS-201-04 — the disclosure that rides beside every summary verb.
 *
 *  Owner ruling 2026-10-25 (UX-CANON A.9, amended): no host chip on a
 *  working window. BEFORE the click the summary verb's hover title names
 *  the host the run WILL use and each fallback (`routeTitle`); a route that
 *  cannot run says its reason. AFTER the run only a failed attempt shows,
 *  as its outcome, with the host in its hover title. Settings ▸ Engines
 *  shows where each engine runs. The label mapper is the one canonical
 *  `egressFor`.
 */
import { Fragment } from "react";
import { egressFor } from "../desk/surface/egress";
import { DotWord } from "../desk/surface/kit";
import type { PlannedRoute, RunReceipt, SummaryRefusal } from "./summaryRoute";
import { refusalFact, routeOff, routeReasonToken, routeReady } from "./summaryRoute";

/** A refused run, said once and said short (UX-CANON A.3).
 *
 *  `refusal` is this session's 409, with the hub's code and sentence.
 *  `durable` is the hub's own `last_refusal` receipt, which survives a
 *  reload and a restart but carries no words of its own — so it says the
 *  state and nothing it cannot prove. The full sentence rides the title. */
export function RefusalToken({
  refusal,
  durable,
  testId,
}: {
  refusal?: SummaryRefusal | null;
  durable?: RunReceipt | null;
  testId: string;
}) {
  if (!refusal && !durable) return null;
  // W6-H words: what did not happen and why, in sentence case, as a dot +
  // words; the summary verb beside it is the next move.
  const label = refusal
    ? `Summary did not start · ${refusalFact(refusal)}`
    : "The last summary did not start";
  const title = refusal
    ? refusal.plainReason
    : `The last run was refused before any model was contacted (${durable?.selection_hash ?? "no selection"}).`;
  return (
    <DotWord tone="fail" className="summary-refusal" data-testid={testId} title={title}>
      {label}
    </DotWord>
  );
}

/** The planned destinations, before the click. Withheld when there is
 *  nothing true to say; an unresolved route says its reason instead. */
export function RouteDisclosure({
  route,
  testId = "summary-route",
}: {
  route: PlannedRoute | null | undefined;
  testId?: string;
}) {
  if (!route) return null;
  if (!routeReady(route)) {
    return (
      <span
        className="surface-token"
        data-chip
        data-tone="warn"
        data-plain=""
        title={routeOff(route) ? undefined : routeReasonToken(route)}
        data-testid={`${testId}-unavailable`}
      >
        {/* PHILO-15 01 ruling: OFF is the owner's choice, not a missing route.
            PHILO-17 ALIVE: plain words; the wire reason rides the title. */}
        {routeOff(route) ? "Summaries off" : "No engine for summaries"}
      </span>
    );
  }
  // Ready: nothing on the row. The verb's hover title names the host.
  return null;
}

/** The hover title for a summary verb: where the run goes, and each
 *  fallback. Undefined when the route cannot run. */
export function routeTitle(route: PlannedRoute | null | undefined): string | undefined {
  if (!route || !routeReady(route)) return undefined;
  const [first, ...fallbacks] = route.legs;
  return [
    `Summary runs on ${egressFor(first.host).label || "this device"}`,
    ...fallbacks.map((leg) => `fallback ${egressFor(leg.host).label || "this device"}`),
  ].join(", ");
}

/** W5-WORDS: an attempt's outcome as a sentence-case word (`Failed`,
 *  `Timed out`), never a caps token. */
export function outcomeWord(outcome: string): string {
  const words = String(outcome ?? "").replace(/_/g, " ").trim().toLowerCase();
  if (words === "timeout") return "Timed out";
  return words ? words.charAt(0).toUpperCase() + words.slice(1) : "Failed";
}

/** A run's failed attempts, in order: the outcome token, the host in its
 *  hover title. A succeeded attempt says nothing (owner ruling 2026-10-25). */
export function RunAttempts({
  receipt,
  testId = "summary-attempts",
}: {
  receipt: RunReceipt | null | undefined;
  testId?: string;
}) {
  if (!receipt || receipt.attempts.length === 0) return null;
  const failed = receipt.attempts.filter((attempt) => attempt.outcome !== "succeeded");
  if (failed.length === 0) return null;
  return (
    <span className="summary-route" data-testid={testId}>
      {failed.map((attempt, index) => (
        <Fragment key={`${attempt.leg_ordinal}-${index}`}>
          <span className="summary-attempt" title={egressFor(attempt.host).label || undefined}>
            <DotWord tone="fail">{outcomeWord(attempt.outcome)}</DotWord>
          </span>
        </Fragment>
      ))}
    </span>
  );
}
