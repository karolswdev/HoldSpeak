// HS-172 — the detail's NEEDS YOU section.
// Board: caption `NEEDS YOU 3` with optional `Run summary` at trailing.
// Each row: Decide:/Confirm: prefix (accent) + text + verbs.
// UX-CANON A.8: when zero rows AND not OFF-with-words, the section is ABSENT.
// HS-172: QUEUED/FAILED verbs (Skip, Retry) in the header verb slot.
import { Button } from "../../../components/signal/Signal";
import { countLabel } from "../../../desk/surface";
import { RefusalToken, RouteDisclosure, routeTitle } from "../../../meetings/RouteDisclosure";
import {
  routeReady,
  type PlannedRoute,
  type RunReceipt,
  type SummaryRefusal,
} from "../../../meetings/summaryRoute";
import type { NeedsRow } from "./helpers";
import { MeetingRunVerb } from "../../../meetings/runSlot";
import { ToolGlyph } from "../../../desk/surface/kit";

/** True when the record draws its filled `Run summary`. One rule, two
 *  readers: this table draws the verb, and the Decide well steps down to
 *  ghost while it is on the face (surface/contract.md: one filled primary). */
export function showsRunSummary({
  intelOff, hasTranscript, plannedRoute, onRunIntelligence,
}: {
  intelOff: boolean;
  hasTranscript: boolean;
  plannedRoute?: PlannedRoute | null;
  onRunIntelligence?: () => void;
}): boolean {
  return intelOff && hasTranscript && Boolean(onRunIntelligence) && routeReady(plannedRoute);
}

export function NeedsYouTable({
  needsRows,
  needsCount,
  intelOff,
  intelState,
  hasTranscript,
  plannedRoute,
  refusal,
  durableRefusal,
  onRunIntelligence,
  onRetryIntelligence,
  onSkipIntelligence,
}: {
  needsRows: NeedsRow[];
  needsCount: number;
  intelOff: boolean;
  /** The raw intel state string: "disabled", "queued", "running", "error", "failed", "complete". */
  intelState?: string;
  hasTranscript: boolean;
  /** HS-201-04 — the disclosed route the next run will use (Article III). */
  plannedRoute?: PlannedRoute | null;
  /** HS-201-04 — the hub's 409 on this record's last run gesture. */
  refusal?: SummaryRefusal | null;
  /** HS-201-04 — the hub's own durable `last_refusal` receipt. */
  durableRefusal?: RunReceipt | null;
  onRunIntelligence?: () => void;
  onRetryIntelligence?: () => void;
  onSkipIntelligence?: () => void;
}) {
  // HS-201-04 (UX-CANON A.11): a run verb with no route to run on is a
  // lie. It is withheld, and the disclosure says the reason in its place.
  const canRun = routeReady(plannedRoute);
  const wantsRun = intelOff && hasTranscript && Boolean(onRunIntelligence);
  const isFailed = intelState === "error" || intelState === "failed";
  const isQueued = intelState === "queued" || intelState === "pending";
  const wantsRetry = isFailed && Boolean(onRetryIntelligence);
  const showRunIntel = showsRunSummary({ intelOff, hasTranscript, plannedRoute, onRunIntelligence });
  const showRetry = wantsRetry && canRun;
  const showSkip = (isFailed || isQueued) && Boolean(onSkipIntelligence);
  // The disclosure rides beside the verb the gesture WOULD use.
  const showRoute = wantsRun || wantsRetry;
  const hasVerbs =
    showRunIntel || showRetry || showSkip || showRoute ||
    Boolean(refusal) || Boolean(durableRefusal);

  if (needsRows.length === 0 && !hasVerbs) return null;

  return (
    <div className="meetings-detail-needs" data-testid="meeting-needs-you">
      <div className="meetings-detail-needs-head">
        {needsRows.length > 0 ? (
          <span className="surface-caption">
            {/* PHILO-13-03: this meeting's proposals, narrower than "needs you". */}
            {countLabel("TO REVIEW", needsCount)}
          </span>
        ) : null}
        {showRoute ? (
          <RouteDisclosure route={plannedRoute} testId="detail-route" />
        ) : null}
        <RefusalToken
          refusal={refusal}
          durable={durableRefusal}
          testId="detail-refusal"
        />
        {/* Window grammar: the run verbs sit in the meeting window's toolbar. */}
        <MeetingRunVerb>
          {showRunIntel ? (
            <Button
              dense
              variant="primary"
              title={routeTitle(plannedRoute)}
              onClick={onRunIntelligence}
              data-testid="detail-run-intelligence-btn"
            >
              <ToolGlyph kind="summary" />
              Run summary
            </Button>
          ) : null}
          {showRetry ? (
            <Button
              dense
              variant="ghost"
              title={routeTitle(plannedRoute)}
              onClick={onRetryIntelligence}
              data-testid="detail-retry-btn"
            >
              <ToolGlyph kind="retry" />
              Retry
            </Button>
          ) : null}
          {showSkip ? (
            <Button
              dense
              variant="ghost"
              onClick={onSkipIntelligence}
              data-testid="detail-skip-btn"
            >
              Skip
            </Button>
          ) : null}
        </MeetingRunVerb>
      </div>
      {needsRows.length > 0 ? (
        <ul className="meetings-detail-outcomes">
          {needsRows.map((row, i) => (
            <li key={i} className="meetings-detail-outcome-row">
              <span className="meetings-detail-outcome-text">{row.cells[0]}</span>
              <span className="meetings-detail-outcome-verb">{row.verbs}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
