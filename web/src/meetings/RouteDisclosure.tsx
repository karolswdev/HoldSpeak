/** HS-201-04 — the disclosure that rides beside every summary verb.
 *
 *  BEFORE the click: the host the run WILL use (`legs[0].host`) and each
 *  disclosed fallback (`+ FALLBACK <host>`). AFTER the run: the hosts
 *  actually contacted, in order, from the receipt's attempts.
 *
 *  UX-CANON A.9 (egress exactly where egress happens) and Article III
 *  (the point of decision). The chip species is the library EgressChip;
 *  the label mapper is the one canonical `egressFor`.
 */
import { Fragment } from "react";
import { EgressChip } from "../desk/surface/gadgets";
import { egressFor } from "../desk/surface/egress";
import type { PlannedRoute, RunReceipt, SummaryRefusal } from "./summaryRoute";
import { refusalFact, routeReasonToken, routeReady } from "./summaryRoute";

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
  const label = refusal ? `REFUSED · ${refusalFact(refusal)}` : "REFUSED";
  const title = refusal
    ? refusal.plainReason
    : `The last run was refused before any model was contacted (${durable?.selection_hash ?? "no selection"}).`;
  return (
    <span
      className="surface-token summary-refusal"
      data-chip
      data-tone="danger"
      data-testid={testId}
      title={title}
    >
      {label}
    </span>
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
        data-testid={`${testId}-unavailable`}
      >
        {`NO SUMMARY ROUTE · ${routeReasonToken(route)}`}
      </span>
    );
  }
  const [first, ...fallbacks] = route.legs;
  const lead = egressFor(first.host);
  return (
    <span className="summary-route" data-testid={testId}>
      <EgressChip
        label={lead.label}
        scope={lead.scope}
        title={lead.label}
        ariaLabel={`Summary runs on ${lead.label}`}
      />
      {fallbacks.map((leg) => {
        const fallback = egressFor(leg.host);
        return (
          <EgressChip
            key={leg.ordinal}
            label={`+ FALLBACK ${fallback.label}`}
            scope={fallback.scope}
            title={`+ FALLBACK ${fallback.label}`}
          />
        );
      })}
    </span>
  );
}

/** The destinations contacted, in order, after a run. Failed dispatches
 *  are shown with their outcome token — the receipt never hides one. */
export function RunAttempts({
  receipt,
  testId = "summary-attempts",
}: {
  receipt: RunReceipt | null | undefined;
  testId?: string;
}) {
  if (!receipt || receipt.attempts.length === 0) return null;
  return (
    <span className="summary-route" data-testid={testId}>
      {receipt.attempts.map((attempt, index) => {
        const contacted = egressFor(attempt.host);
        const failed = attempt.outcome !== "succeeded";
        return (
          <Fragment key={`${attempt.leg_ordinal}-${index}`}>
            <EgressChip label={contacted.label} scope={contacted.scope} title={contacted.label} />
            {failed ? (
              <span className="surface-token" data-chip data-tone="danger">
                {attempt.outcome.toUpperCase()}
              </span>
            ) : null}
          </Fragment>
        );
      })}
    </span>
  );
}
